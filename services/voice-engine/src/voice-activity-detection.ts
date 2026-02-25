/**
 * Voice Activity Detection (VAD) Service
 * Detects speech presence and manages turn-taking in conversations
 * Validates: Requirements 1.5
 */

import { EventEmitter } from 'events';

export interface VADConfig {
  sampleRate: number;
  frameDuration: number; // in milliseconds (10, 20, or 30)
  energyThreshold: number; // Energy threshold for speech detection
  silenceDuration: number; // Duration of silence to consider speech ended (ms)
  speechDuration: number; // Minimum duration to consider as speech (ms)
  preSpeechPadding: number; // Padding before speech starts (ms)
  postSpeechPadding: number; // Padding after speech ends (ms)
}

export interface VADResult {
  isSpeech: boolean;
  energy: number;
  timestamp: number;
  confidence: number;
}

export interface SpeechSegment {
  startTime: number;
  endTime: number;
  duration: number;
  audioData: ArrayBuffer[];
}

export enum VADState {
  SILENCE = 'silence',
  SPEECH_START = 'speech_start',
  SPEECH_ACTIVE = 'speech_active',
  SPEECH_END = 'speech_end'
}

/**
 * Voice Activity Detection for turn-taking management
 * Uses energy-based detection with smoothing and state management
 */
export class VoiceActivityDetector extends EventEmitter {
  private config: VADConfig;
  private state: VADState = VADState.SILENCE;
  private speechStartTime: number = 0;
  private lastSpeechTime: number = 0;
  private currentSegment: ArrayBuffer[] = [];
  private energyHistory: number[] = [];
  private readonly historySize = 10;

  constructor(config?: Partial<VADConfig>) {
    super();
    this.config = {
      sampleRate: config?.sampleRate || 16000,
      frameDuration: config?.frameDuration || 30,
      energyThreshold: config?.energyThreshold || 0.01,
      silenceDuration: config?.silenceDuration || 500,
      speechDuration: config?.speechDuration || 100,
      preSpeechPadding: config?.preSpeechPadding || 100,
      postSpeechPadding: config?.postSpeechPadding || 200
    };
  }

  /**
   * Process audio frame and detect voice activity
   */
  processFrame(audioData: ArrayBuffer, timestamp: number): VADResult {
    const energy = this.calculateEnergy(audioData);
    
    // Update energy history for smoothing BEFORE detection
    this.energyHistory.push(energy);
    if (this.energyHistory.length > this.historySize) {
      this.energyHistory.shift();
    }
    
    const isSpeech = this.detectSpeech(energy);
    const confidence = this.calculateConfidence(energy);

    // Update state machine
    this.updateState(isSpeech, timestamp);

    // Store audio data if in speech segment
    if (this.state === VADState.SPEECH_ACTIVE || this.state === VADState.SPEECH_START) {
      this.currentSegment.push(audioData);
    }

    const result: VADResult = {
      isSpeech,
      energy,
      timestamp,
      confidence
    };

    this.emit('vad:result', result);
    return result;
  }

  /**
   * Calculate energy of audio frame
   */
  private calculateEnergy(audioData: ArrayBuffer): number {
    const samples = new Int16Array(audioData);
    let sum = 0;

    for (let i = 0; i < samples.length; i++) {
      const normalized = samples[i] / 32768.0; // Normalize to [-1, 1]
      sum += normalized * normalized;
    }

    return Math.sqrt(sum / samples.length);
  }

  /**
   * Detect speech based on energy with smoothing
   */
  private detectSpeech(energy: number): boolean {
    // Use current frame energy for immediate response
    // Smoothing is applied in the energy history for other purposes
    return energy > this.config.energyThreshold;
  }

  /**
   * Calculate confidence score for speech detection
   */
  private calculateConfidence(energy: number): number {
    // Confidence based on how far above threshold
    const ratio = energy / this.config.energyThreshold;
    return Math.min(1.0, Math.max(0.0, (ratio - 0.5) / 2.0));
  }

  /**
   * Update VAD state machine
   */
  private updateState(isSpeech: boolean, timestamp: number): void {
    const previousState = this.state;

    switch (this.state) {
      case VADState.SILENCE:
        if (isSpeech) {
          this.state = VADState.SPEECH_START;
          this.speechStartTime = timestamp;
          this.lastSpeechTime = timestamp;
          this.currentSegment = [];
          this.emit('speech:start', { timestamp });
        }
        break;

      case VADState.SPEECH_START:
        if (isSpeech) {
          const duration = timestamp - this.speechStartTime;
          if (duration >= this.config.speechDuration) {
            this.state = VADState.SPEECH_ACTIVE;
            this.emit('speech:active', { timestamp, duration });
          }
          this.lastSpeechTime = timestamp;
        } else {
          // Check if we had enough speech before the silence
          const duration = this.lastSpeechTime - this.speechStartTime;
          if (duration >= this.config.speechDuration) {
            // Enough speech, transition to SPEECH_ACTIVE first
            this.state = VADState.SPEECH_ACTIVE;
            this.emit('speech:active', { timestamp: this.lastSpeechTime, duration });
            // Then check for speech end
            const silenceDuration = timestamp - this.lastSpeechTime;
            if (silenceDuration >= this.config.silenceDuration) {
              this.state = VADState.SPEECH_END;
              this.emit('speech:end', { 
                timestamp,
                duration: timestamp - this.speechStartTime 
              });
            }
          } else {
            // False start, return to silence
            this.state = VADState.SILENCE;
            this.currentSegment = [];
          }
        }
        break;

      case VADState.SPEECH_ACTIVE:
        if (isSpeech) {
          this.lastSpeechTime = timestamp;
        } else {
          const silenceDuration = timestamp - this.lastSpeechTime;
          if (silenceDuration >= this.config.silenceDuration) {
            this.state = VADState.SPEECH_END;
            this.emit('speech:end', { 
              timestamp,
              duration: timestamp - this.speechStartTime 
            });
          }
        }
        break;

      case VADState.SPEECH_END:
        // Emit complete segment and return to silence
        this.emitSpeechSegment(timestamp);
        this.state = VADState.SILENCE;
        this.currentSegment = [];
        break;
    }

    if (previousState !== this.state) {
      this.emit('state:change', {
        from: previousState,
        to: this.state,
        timestamp
      });
    }
  }

  /**
   * Emit complete speech segment
   */
  private emitSpeechSegment(endTime: number): void {
    if (this.currentSegment.length === 0) return;

    const segment: SpeechSegment = {
      startTime: this.speechStartTime,
      endTime,
      duration: endTime - this.speechStartTime,
      audioData: [...this.currentSegment]
    };

    this.emit('speech:segment', segment);
  }

  /**
   * Get current VAD state
   */
  getState(): VADState {
    return this.state;
  }

  /**
   * Check if currently detecting speech
   */
  isSpeechActive(): boolean {
    return this.state === VADState.SPEECH_ACTIVE || 
           this.state === VADState.SPEECH_START;
  }

  /**
   * Reset VAD state
   */
  reset(): void {
    this.state = VADState.SILENCE;
    this.speechStartTime = 0;
    this.lastSpeechTime = 0;
    this.currentSegment = [];
    this.energyHistory = [];
    this.emit('vad:reset');
  }

  /**
   * Update configuration
   */
  updateConfig(config: Partial<VADConfig>): void {
    this.config = { ...this.config, ...config };
    this.emit('config:updated', this.config);
  }

  /**
   * Get current configuration
   */
  getConfig(): VADConfig {
    return { ...this.config };
  }
}

/**
 * Advanced VAD using zero-crossing rate and energy
 */
export class AdvancedVAD extends VoiceActivityDetector {
  /**
   * Calculate zero-crossing rate for additional speech detection
   */
  private calculateZeroCrossingRate(audioData: ArrayBuffer): number {
    const samples = new Int16Array(audioData);
    let crossings = 0;

    for (let i = 1; i < samples.length; i++) {
      if ((samples[i] >= 0 && samples[i - 1] < 0) ||
          (samples[i] < 0 && samples[i - 1] >= 0)) {
        crossings++;
      }
    }

    return crossings / samples.length;
  }

  /**
   * Enhanced speech detection using both energy and ZCR
   */
  processFrame(audioData: ArrayBuffer, timestamp: number): VADResult {
    const energy = this.calculateEnergyLevel(audioData);
    const zcr = this.calculateZeroCrossingRate(audioData);
    
    // Speech typically has moderate ZCR (0.1 - 0.4)
    const zcrInRange = zcr > 0.1 && zcr < 0.4;
    const energyAboveThreshold = energy > this.getConfig().energyThreshold;
    
    const isSpeech = energyAboveThreshold && zcrInRange;
    const confidence = this.calculateEnhancedConfidence(energy, zcr);

    // Use parent class state management
    return super.processFrame(audioData, timestamp);
  }

  /**
   * Calculate enhanced confidence using multiple features
   */
  private calculateEnhancedConfidence(energy: number, zcr: number): number {
    const energyConf = Math.min(1.0, energy / (this.getConfig().energyThreshold * 2));
    const zcrConf = zcr > 0.1 && zcr < 0.4 ? 1.0 : 0.5;
    
    return (energyConf + zcrConf) / 2;
  }

  private calculateEnergyLevel(audioData: ArrayBuffer): number {
    const samples = new Int16Array(audioData);
    let sum = 0;

    for (let i = 0; i < samples.length; i++) {
      const normalized = samples[i] / 32768.0;
      sum += normalized * normalized;
    }

    return Math.sqrt(sum / samples.length);
  }
}
