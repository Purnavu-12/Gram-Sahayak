/**
 * Core interfaces for Dialect Detection Service
 * Handles language and dialect identification
 */

import { AudioFeatures, DialectCode, LanguageCode, SessionId } from './voice-engine';

export interface DialectResult {
  primaryDialect: DialectCode;
  primaryLanguage: LanguageCode;
  confidence: number;
  alternativeDialects: Array<{
    dialect: DialectCode;
    confidence: number;
  }>;
  detectionTime: number; // milliseconds
  codeSwitchingDetected: boolean;
}

export interface DialectInfo {
  dialectCode: DialectCode;
  languageCode: LanguageCode;
  name: string;
  region: string;
  speakers: number;
  isSupported: boolean;
}

export interface FeedbackData {
  correctDialect?: DialectCode;
  userSatisfaction: number; // 1-5 scale
  comments?: string;
}

/**
 * Dialect Detector Service Interface
 * Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
 */
export interface DialectDetector {
  /**
   * Detect dialect from audio features
   * @param audioFeatures - Audio characteristics for analysis
   * @returns Promise resolving to dialect detection result
   */
  detectDialect(audioFeatures: AudioFeatures): Promise<DialectResult>;

  /**
   * Update confidence scores based on user feedback
   * @param sessionId - Session identifier
   * @param userFeedback - User feedback data
   * @returns Promise resolving when update is complete
   */
  updateConfidence(sessionId: SessionId, userFeedback: FeedbackData): Promise<void>;

  /**
   * Get list of all supported dialects
   * @returns Promise resolving to array of dialect information
   */
  getSupportedDialects(): Promise<DialectInfo[]>;
}
