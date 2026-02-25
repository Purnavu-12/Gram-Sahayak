/**
 * Core interfaces for Voice Engine Service
 * Handles speech-to-text, text-to-speech, and audio processing
 */

export type SessionId = string;
export type LanguageCode = string;
export type DialectCode = string;

export interface AudioFeatures {
  sampleRate: number;
  channels: number;
  bitDepth: number;
  duration: number;
}

export interface TranscriptionResult {
  text: string;
  confidence: number;
  language: LanguageCode;
  timestamp: Date;
  isFinal: boolean;
  isOffline?: boolean; // Indicates if transcription was done offline
}

export interface VoiceProfile {
  gender: 'male' | 'female' | 'neutral';
  age: 'young' | 'middle' | 'senior';
  speed: number; // 0.5 to 2.0
  pitch: number; // 0.5 to 2.0
}

export interface SessionSummary {
  sessionId: SessionId;
  duration: number;
  totalUtterances: number;
  averageConfidence: number;
  detectedLanguage: LanguageCode;
}

/**
 * Voice Engine Service Interface
 * Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5
 */
export interface VoiceEngine {
  /**
   * Start a new voice session for a user
   * @param userId - Unique user identifier
   * @param preferredLanguage - Optional preferred language code
   * @returns Promise resolving to session ID
   */
  startVoiceSession(userId: string, preferredLanguage?: string): Promise<SessionId>;

  /**
   * Process incoming audio stream chunk
   * @param sessionId - Active session identifier
   * @param audioChunk - Raw audio data buffer
   * @returns Promise resolving to transcription result
   */
  processAudioStream(sessionId: SessionId, audioChunk: ArrayBuffer): Promise<TranscriptionResult>;

  /**
   * Synthesize speech from text in specified dialect
   * @param text - Text to convert to speech
   * @param dialect - Target dialect code
   * @param voice - Voice profile configuration
   * @returns Promise resolving to audio buffer
   */
  synthesizeSpeech(text: string, dialect: DialectCode, voice: VoiceProfile): Promise<ArrayBuffer>;

  /**
   * End voice session and get summary
   * @param sessionId - Session to terminate
   * @returns Promise resolving to session summary
   */
  endVoiceSession(sessionId: SessionId): Promise<SessionSummary>;
}
