/**
 * Audio Preprocessing Pipeline
 * Implements noise reduction and audio enhancement
 * Validates: Requirements 1.3
 */

import { EventEmitter } from 'events';

export interface PreprocessingConfig {
  sampleRate: number;
  channels: number;
  noiseReduction: boolean;
  echoCancellation: boolean;
  autoGainControl: boolean;
  highPassFilter: boolean;
  highPassCutoff: number; // Hz
  lowPassFilter: boolean;
  lowPassCutoff: number; // Hz
  normalization: boolean;
  targetLevel: number; // Target RMS level for normalization
}

export interface AudioStats {
  rms: number;
  peak: number;
  snr: number; // Signal-to-noise ratio estimate
  clipping: boolean;
}

/**
 * Audio preprocessing pipeline for noise reduction and enhancement
 */
export class AudioPreprocessor extends EventEmitter {
  private config: PreprocessingConfig;
  private noiseProfile: Float32Array | null = null;
  private noiseEstimationFrames: Float32Array[] = [];
  private readonly noiseEstimationCount = 10;

  constructor(config?: Partial<PreprocessingConfig>) {
    super();
    this.config = {
      sampleRate: config?.sampleRate || 16000,
      channels: config?.channels || 1,
      noiseReduction: config?.noiseReduction ?? true,
      echoCancellation: config?.echoCancellation ?? true,
      autoGainControl: config?.autoGainControl ?? true,
      highPassFilter: config?.highPassFilter ?? true,
      highPassCutoff: config?.highPassCutoff || 80,
      lowPassFilter: config?.lowPassFilter ?? true,
      lowPassCutoff: config?.lowPassCutoff || 8000,
      normalization: config?.normalization ?? true,
      targetLevel: config?.targetLevel || 0.3
    };
  }

  /**
   * Process audio buffer through preprocessing pipeline
   */
  async processAudio(audioData: ArrayBuffer): Promise<ArrayBuffer> {
    let samples = this.convertToFloat32(audioData);

    // Apply preprocessing stages
    if (this.config.highPassFilter) {
      samples = this.applyHighPassFilter(samples);
    }

    if (this.config.lowPassFilter) {
      samples = this.applyLowPassFilter(samples);
    }

    if (this.config.noiseReduction) {
      samples = await this.applyNoiseReduction(samples);
    }

    if (this.config.autoGainControl) {
      samples = this.applyAutoGainControl(samples);
    }

    if (this.config.normalization) {
      samples = this.normalizeAudio(samples);
    }

    // Calculate and emit statistics
    const stats = this.calculateStats(samples);
    this.emit('audio:stats', stats);

    return this.convertToInt16(samples);
  }

  /**
   * Convert Int16Array to Float32Array for processing
   */
  private convertToFloat32(audioData: ArrayBuffer): Float32Array {
    // Ensure buffer length is even for Int16Array (2 bytes per sample)
    let buffer = audioData;
    if (audioData.byteLength % 2 !== 0) {
      buffer = audioData.slice(0, audioData.byteLength - 1);
    }
    
    const int16Array = new Int16Array(buffer);
    const float32Array = new Float32Array(int16Array.length);

    for (let i = 0; i < int16Array.length; i++) {
      float32Array[i] = int16Array[i] / 32768.0;
    }

    return float32Array;
  }

  /**
   * Convert Float32Array back to Int16Array
   */
  private convertToInt16(samples: Float32Array): ArrayBuffer {
    const int16Array = new Int16Array(samples.length);

    for (let i = 0; i < samples.length; i++) {
      const clamped = Math.max(-1, Math.min(1, samples[i]));
      int16Array[i] = Math.round(clamped * 32767);
    }

    return int16Array.buffer;
  }

  /**
   * Apply high-pass filter to remove low-frequency noise
   */
  private applyHighPassFilter(samples: Float32Array): Float32Array {
    const output = new Float32Array(samples.length);
    const rc = 1.0 / (2 * Math.PI * this.config.highPassCutoff);
    const dt = 1.0 / this.config.sampleRate;
    const alpha = rc / (rc + dt);

    output[0] = samples[0];
    for (let i = 1; i < samples.length; i++) {
      output[i] = alpha * (output[i - 1] + samples[i] - samples[i - 1]);
    }

    return output;
  }

  /**
   * Apply low-pass filter to remove high-frequency noise
   */
  private applyLowPassFilter(samples: Float32Array): Float32Array {
    const output = new Float32Array(samples.length);
    const rc = 1.0 / (2 * Math.PI * this.config.lowPassCutoff);
    const dt = 1.0 / this.config.sampleRate;
    const alpha = dt / (rc + dt);

    output[0] = samples[0];
    for (let i = 1; i < samples.length; i++) {
      output[i] = output[i - 1] + alpha * (samples[i] - output[i - 1]);
    }

    return output;
  }

  /**
   * Apply spectral subtraction for noise reduction
   */
  private async applyNoiseReduction(samples: Float32Array): Promise<Float32Array> {
    // Build noise profile if not available
    if (!this.noiseProfile) {
      this.buildNoiseProfile(samples);
      return samples; // Return original during noise profiling
    }

    // Apply spectral subtraction
    const output = new Float32Array(samples.length);
    const frameSize = 512;
    const hopSize = 256;

    for (let i = 0; i < samples.length - frameSize; i += hopSize) {
      const frame = samples.slice(i, i + frameSize);
      const processedFrame = this.spectralSubtraction(frame);
      
      // Overlap-add
      for (let j = 0; j < processedFrame.length && i + j < output.length; j++) {
        output[i + j] += processedFrame[j];
      }
    }

    return output;
  }

  /**
   * Build noise profile from initial frames
   */
  private buildNoiseProfile(samples: Float32Array): void {
    this.noiseEstimationFrames.push(new Float32Array(samples));

    if (this.noiseEstimationFrames.length >= this.noiseEstimationCount) {
      // Average the noise frames
      const profileLength = this.noiseEstimationFrames[0].length;
      this.noiseProfile = new Float32Array(profileLength);

      for (let i = 0; i < profileLength; i++) {
        let sum = 0;
        for (const frame of this.noiseEstimationFrames) {
          sum += Math.abs(frame[i]);
        }
        this.noiseProfile[i] = sum / this.noiseEstimationFrames.length;
      }

      this.emit('noise:profile:ready');
    }
  }

  /**
   * Spectral subtraction for noise reduction
   */
  private spectralSubtraction(frame: Float32Array): Float32Array {
    if (!this.noiseProfile) return frame;

    const output = new Float32Array(frame.length);
    const alpha = 2.0; // Over-subtraction factor
    const beta = 0.01; // Spectral floor

    for (let i = 0; i < frame.length; i++) {
      const signal = Math.abs(frame[i]);
      const noise = this.noiseProfile[Math.min(i, this.noiseProfile.length - 1)];
      const subtracted = signal - alpha * noise;
      const floored = Math.max(subtracted, beta * signal);
      output[i] = floored * Math.sign(frame[i]);
    }

    return output;
  }

  /**
   * Apply automatic gain control
   */
  private applyAutoGainControl(samples: Float32Array): Float32Array {
    const rms = this.calculateRMS(samples);
    if (rms < 0.001) return samples; // Avoid amplifying silence

    const targetRMS = 0.2; // Target RMS level
    const gain = Math.min(4.0, targetRMS / rms); // Limit max gain to 4x

    const output = new Float32Array(samples.length);
    for (let i = 0; i < samples.length; i++) {
      output[i] = samples[i] * gain;
    }

    return output;
  }

  /**
   * Normalize audio to target level
   */
  private normalizeAudio(samples: Float32Array): Float32Array {
    const peak = this.calculatePeak(samples);
    if (peak < 0.001) return samples;

    const gain = this.config.targetLevel / peak;
    const output = new Float32Array(samples.length);

    for (let i = 0; i < samples.length; i++) {
      output[i] = Math.max(-1, Math.min(1, samples[i] * gain));
    }

    return output;
  }

  /**
   * Calculate RMS (Root Mean Square) level
   */
  private calculateRMS(samples: Float32Array): number {
    let sum = 0;
    for (let i = 0; i < samples.length; i++) {
      sum += samples[i] * samples[i];
    }
    return Math.sqrt(sum / samples.length);
  }

  /**
   * Calculate peak level
   */
  private calculatePeak(samples: Float32Array): number {
    let peak = 0;
    for (let i = 0; i < samples.length; i++) {
      peak = Math.max(peak, Math.abs(samples[i]));
    }
    return peak;
  }

  /**
   * Calculate audio statistics
   */
  private calculateStats(samples: Float32Array): AudioStats {
    const rms = this.calculateRMS(samples);
    const peak = this.calculatePeak(samples);
    
    // Estimate SNR (simplified)
    const signalPower = rms * rms;
    const noisePower = this.noiseProfile 
      ? this.calculateRMS(this.noiseProfile) ** 2 
      : 0.001;
    const snr = 10 * Math.log10(signalPower / noisePower);

    const clipping = peak > 0.99;

    return { rms, peak, snr, clipping };
  }

  /**
   * Reset noise profile
   */
  resetNoiseProfile(): void {
    this.noiseProfile = null;
    this.noiseEstimationFrames = [];
    this.emit('noise:profile:reset');
  }

  /**
   * Update configuration
   */
  updateConfig(config: Partial<PreprocessingConfig>): void {
    this.config = { ...this.config, ...config };
    this.emit('config:updated', this.config);
  }

  /**
   * Get current configuration
   */
  getConfig(): PreprocessingConfig {
    return { ...this.config };
  }

  /**
   * Check if noise profile is ready
   */
  isNoiseProfileReady(): boolean {
    return this.noiseProfile !== null;
  }
}

/**
 * Real-time audio buffer manager
 */
export class AudioBufferManager {
  private buffers: Map<string, ArrayBuffer[]> = new Map();
  private maxBufferSize: number;

  constructor(maxBufferSize: number = 100) {
    this.maxBufferSize = maxBufferSize;
  }

  /**
   * Add audio chunk to buffer
   */
  addChunk(sessionId: string, chunk: ArrayBuffer): void {
    if (!this.buffers.has(sessionId)) {
      this.buffers.set(sessionId, []);
    }

    const buffer = this.buffers.get(sessionId)!;
    buffer.push(chunk);

    // Maintain buffer size limit
    if (buffer.length > this.maxBufferSize) {
      buffer.shift();
    }
  }

  /**
   * Get all chunks for session
   */
  getChunks(sessionId: string): ArrayBuffer[] {
    return this.buffers.get(sessionId) || [];
  }

  /**
   * Concatenate all chunks into single buffer
   */
  concatenateChunks(sessionId: string): ArrayBuffer | null {
    const chunks = this.getChunks(sessionId);
    if (chunks.length === 0) return null;

    const totalLength = chunks.reduce((sum, chunk) => sum + chunk.byteLength, 0);
    const result = new Uint8Array(totalLength);
    
    let offset = 0;
    for (const chunk of chunks) {
      result.set(new Uint8Array(chunk), offset);
      offset += chunk.byteLength;
    }

    return result.buffer;
  }

  /**
   * Clear buffer for session
   */
  clearBuffer(sessionId: string): void {
    this.buffers.delete(sessionId);
  }

  /**
   * Get buffer size for session
   */
  getBufferSize(sessionId: string): number {
    return this.buffers.get(sessionId)?.length || 0;
  }
}
