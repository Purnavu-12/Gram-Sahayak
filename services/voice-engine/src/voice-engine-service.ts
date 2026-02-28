import { VoiceEngine, SessionId, TranscriptionResult, VoiceProfile, SessionSummary } from '../../../shared/types';
import { DialectCode } from '../../../shared/types/voice-engine';
import { WebRTCStreamingService, AudioChunkData } from './webrtc-streaming';
import { VoiceActivityDetector, VADState, SpeechSegment } from './voice-activity-detection';
import { AudioPreprocessor, AudioBufferManager } from './audio-preprocessing';
import { OfflineVoiceProcessor } from './offline-processing';
import { NetworkOptimizationService, NetworkCondition, SyncOperationType, SyncPriority } from './network-optimization';

interface VoiceSession {
  userId: string;
  preferredLanguage?: string;
  startTime: number;
  utterances: TranscriptionResult[];
  vad: VoiceActivityDetector;
  preprocessor: AudioPreprocessor;
  isActive: boolean;
}

export class VoiceEngineService implements VoiceEngine {
  private sessions: Map<SessionId, VoiceSession> = new Map();
  private webrtcService: WebRTCStreamingService;
  private bufferManager: AudioBufferManager;
  private offlineProcessor: OfflineVoiceProcessor;
  private networkOptimizer: NetworkOptimizationService;
  private isOnline: boolean = true;

  constructor() {
    this.webrtcService = new WebRTCStreamingService();
    this.bufferManager = new AudioBufferManager();
    this.offlineProcessor = new OfflineVoiceProcessor();
    this.networkOptimizer = new NetworkOptimizationService();
    this.setupWebRTCListeners();
    this.setupOfflineListeners();
    this.setupNetworkListeners();
  }

  /**
   * Setup WebRTC event listeners
   */
  private setupWebRTCListeners(): void {
    // Handle incoming audio chunks from WebRTC
    this.webrtcService.on('audio:chunk', async (data: AudioChunkData) => {
      const session = this.sessions.get(data.sessionId);
      if (session) {
        await this.handleAudioChunk(data.sessionId, data.audioData);
      }
    });

    // Handle connection failures
    this.webrtcService.on('connection:failed', ({ sessionId }) => {
      console.error(`WebRTC connection failed for session ${sessionId}`);
      // Switch to offline mode
      this.handleConnectionFailure(sessionId);
    });
  }

  /**
   * Setup offline processor event listeners
   */
  private setupOfflineListeners(): void {
    this.offlineProcessor.on('network:online', () => {
      console.log('Network connectivity restored');
      this.isOnline = true;
    });

    this.offlineProcessor.on('network:offline', () => {
      console.log('Network connectivity lost');
      this.isOnline = false;
    });

    this.offlineProcessor.on('sync:completed', ({ syncTime }) => {
      console.log(`Offline data synced at ${syncTime}`);
    });
  }

  /**
   * Setup network optimization event listeners
   */
  private setupNetworkListeners(): void {
    this.networkOptimizer.on('network:online', () => {
      console.log('Network optimizer: connectivity restored');
      this.isOnline = true;
      this.offlineProcessor.setOnlineStatus(true);
    });

    this.networkOptimizer.on('network:offline', () => {
      console.log('Network optimizer: connectivity lost');
      this.isOnline = false;
      this.offlineProcessor.setOnlineStatus(false);
    });

    this.networkOptimizer.on('condition:changed', ({ oldCondition, newCondition }) => {
      console.log(`Network condition changed: ${oldCondition} -> ${newCondition}`);
    });

    this.networkOptimizer.on('quality:adjusted', ({ newQuality, condition }) => {
      console.log(`Audio quality adjusted for ${condition}:`, newQuality);
    });

    this.networkOptimizer.on('audio:compressed', ({ originalSize, compressedSize, compressionRatio }) => {
      console.log(`Audio compressed: ${originalSize} -> ${compressedSize} bytes (${compressionRatio.toFixed(2)}x)`);
    });
  }

  /**
   * Handle connection failure by switching to offline mode
   */
  private handleConnectionFailure(sessionId: SessionId): void {
    const session = this.sessions.get(sessionId);
    if (!session) return;

    // Check if offline mode is available
    const language = session.preferredLanguage || 'hi';
    if (this.offlineProcessor.isOfflineModeAvailable(language)) {
      console.log(`Switching session ${sessionId} to offline mode`);
      this.isOnline = false;
      this.offlineProcessor.setOnlineStatus(false);
    }
  }

  /**
   * Start a new voice session with WebRTC streaming
   */
  async startVoiceSession(userId: string, preferredLanguage?: string): Promise<SessionId> {
    const sessionId = `session_${Date.now()}_${userId}`;
    
    // Create VAD and preprocessor for this session
    const vad = new VoiceActivityDetector({
      sampleRate: 16000,
      frameDuration: 30,
      energyThreshold: 0.01,
      silenceDuration: 500,
      speechDuration: 100
    });

    const preprocessor = new AudioPreprocessor({
      sampleRate: 16000,
      channels: 1,
      noiseReduction: true,
      echoCancellation: true,
      autoGainControl: true
    });

    // Setup VAD event listeners
    this.setupVADListeners(sessionId, vad);

    // Create session
    const session: VoiceSession = {
      userId,
      preferredLanguage,
      startTime: Date.now(),
      utterances: [],
      vad,
      preprocessor,
      isActive: true
    };

    this.sessions.set(sessionId, session);

    // Initialize WebRTC session
    await this.webrtcService.createSession(sessionId, userId);
    await this.webrtcService.initializePeerConnection(sessionId);
    this.webrtcService.createDataChannel(sessionId);

    return sessionId;
  }

  /**
   * Setup VAD event listeners for a session
   */
  private setupVADListeners(sessionId: SessionId, vad: VoiceActivityDetector): void {
    vad.on('speech:start', ({ timestamp }) => {
      console.log(`Speech started in session ${sessionId} at ${timestamp}`);
    });

    vad.on('speech:end', ({ timestamp, duration }) => {
      console.log(`Speech ended in session ${sessionId} at ${timestamp}, duration: ${duration}ms`);
    });

    vad.on('speech:segment', async (segment: SpeechSegment) => {
      // Process complete speech segment
      await this.processSpeechSegment(sessionId, segment);
    });
  }

  /**
   * Process incoming audio stream chunk
   */
  async processAudioStream(sessionId: SessionId, audioChunk: ArrayBuffer): Promise<TranscriptionResult> {
    const session = this.sessions.get(sessionId);
    if (!session) {
      throw new Error('Session not found');
    }

    return await this.handleAudioChunk(sessionId, audioChunk);
  }

  /**
   * Handle audio chunk processing
   */
  private async handleAudioChunk(sessionId: SessionId, audioChunk: ArrayBuffer): Promise<TranscriptionResult> {
    const session = this.sessions.get(sessionId);
    if (!session) {
      throw new Error('Session not found');
    }

    // Apply audio preprocessing
    let processedAudio = await session.preprocessor.processAudio(audioChunk);

    // Apply compression if needed based on network conditions
    const compressionResult = await this.networkOptimizer.compressAudio(processedAudio);
    processedAudio = compressionResult.compressedData;

    // Add to buffer
    this.bufferManager.addChunk(sessionId, processedAudio);

    // Process with VAD
    const vadResult = session.vad.processFrame(processedAudio, Date.now());

    // If offline, use offline processor
    if (!this.isOnline) {
      const language = session.preferredLanguage || 'hi';
      try {
        const result = await this.offlineProcessor.processOfflineSpeech(
          processedAudio,
          language
        );
        
        // Queue for sync when online
        this.networkOptimizer.queueOperation({
          type: SyncOperationType.TRANSCRIPTION,
          priority: SyncPriority.HIGH,
          data: result,
          maxRetries: 3
        });
        
        return result;
      } catch (error) {
        console.error('Offline processing failed:', error);
        // Return error result
        return {
          text: '',
          confidence: 0,
          language,
          timestamp: new Date(),
          isFinal: false,
          isOffline: true
        };
      }
    }

    // Create transcription result (placeholder - would integrate with actual ASR)
    const result: TranscriptionResult = {
      text: '',
      confidence: Math.max(0.01, vadResult.confidence),
      language: session.preferredLanguage || 'hi',
      timestamp: new Date(),
      isFinal: vadResult.isSpeech && session.vad.getState() === VADState.SPEECH_END,
      isOffline: false
    };

    if (result.isFinal) {
      session.utterances.push(result);
    }

    return result;
  }

  /**
   * Process complete speech segment
   */
  private async processSpeechSegment(sessionId: SessionId, segment: SpeechSegment): Promise<void> {
    const session = this.sessions.get(sessionId);
    if (!session) return;

    // Concatenate audio data from segment
    const totalLength = segment.audioData.reduce((sum, chunk) => sum + chunk.byteLength, 0);
    const concatenated = new Uint8Array(totalLength);
    
    let offset = 0;
    for (const chunk of segment.audioData) {
      concatenated.set(new Uint8Array(chunk), offset);
      offset += chunk.byteLength;
    }

    // Here we would send to actual ASR service
    // For now, create a placeholder result
    const result: TranscriptionResult = {
      text: `[Speech segment: ${segment.duration}ms]`,
      confidence: 0.95,
      language: session.preferredLanguage || 'hi',
      timestamp: new Date(segment.endTime),
      isFinal: true
    };

    session.utterances.push(result);
  }

  /**
   * Synthesize speech from text
   */
  async synthesizeSpeech(text: string, dialect: DialectCode, voice: VoiceProfile): Promise<ArrayBuffer> {
    // Placeholder implementation - would integrate with TTS service
    return new ArrayBuffer(0);
  }

  /**
   * End voice session and cleanup
   */
  async endVoiceSession(sessionId: SessionId): Promise<SessionSummary> {
    const session = this.sessions.get(sessionId);
    if (!session) {
      throw new Error('Session not found');
    }

    // Close WebRTC session
    await this.webrtcService.closeSession(sessionId);

    // Clear audio buffer
    this.bufferManager.clearBuffer(sessionId);

    // Reset VAD
    session.vad.reset();

    // Calculate summary
    const summary: SessionSummary = {
      sessionId,
      duration: Date.now() - session.startTime,
      totalUtterances: session.utterances.length,
      averageConfidence: session.utterances.reduce((sum, u) => sum + u.confidence, 0) / session.utterances.length || 0,
      detectedLanguage: session.preferredLanguage || 'hi'
    };

    session.isActive = false;
    this.sessions.delete(sessionId);

    return summary;
  }

  /**
   * Get WebRTC service for advanced operations
   */
  getWebRTCService(): WebRTCStreamingService {
    return this.webrtcService;
  }

  /**
   * Get session VAD state
   */
  getVADState(sessionId: SessionId): VADState | null {
    const session = this.sessions.get(sessionId);
    return session ? session.vad.getState() : null;
  }

  /**
   * Check if speech is active in session
   */
  isSpeechActive(sessionId: SessionId): boolean {
    const session = this.sessions.get(sessionId);
    return session ? session.vad.isSpeechActive() : false;
  }

  /**
   * Get offline processor for advanced operations
   */
  getOfflineProcessor(): OfflineVoiceProcessor {
    return this.offlineProcessor;
  }

  /**
   * Get network optimizer for advanced operations
   */
  getNetworkOptimizer(): NetworkOptimizationService {
    return this.networkOptimizer;
  }

  /**
   * Set online/offline status manually
   */
  setOnlineStatus(isOnline: boolean): void {
    this.isOnline = isOnline;
    this.offlineProcessor.setOnlineStatus(isOnline);
  }

  /**
   * Check if offline mode is available for a language
   */
  isOfflineModeAvailable(language: string, dialect?: DialectCode): boolean {
    return this.offlineProcessor.isOfflineModeAvailable(language, dialect);
  }

  /**
   * Get sync status
   */
  getSyncStatus() {
    return this.offlineProcessor.getSyncStatus();
  }
}
