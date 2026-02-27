/**
 * Shared type definitions for Gram Sahayak microservices
 */

// Voice engine types (exclude LanguageCode/DialectCode which are canonical in user-profile)
export { SessionId, AudioFeatures, TranscriptionResult, VoiceProfile, SessionSummary, VoiceEngine } from './voice-engine';

export * from './dialect-detector';

// Scheme matcher types (exclude types that conflict with user-profile)
export { SchemeMatch, EligibilityResult, SchemeUpdate, UserPreferences, RankedScheme, SchemeMatcher } from './scheme-matcher';

export * from './form-generator';

// User profile is the canonical source for shared types
export * from './user-profile';

export * from './accessibility';

// Bedrock integration types (use named exports to avoid conflicts with existing types)
export {
  BedrockConfig,
  ClaudeConfig,
  ClaudeResponse,
  KBFilter,
  KBResult,
  KBSchemeResult,
  SchemeData,
  IngestionResult,
  IngestionError,
  GuardrailsResult,
  PIIDetection,
  Assessment,
  PIIRedactionResult,
  PIIContext,
  FallbackOptions,
  FallbackResult,
  FallbackMetrics,
  BedrockMetrics,
  LatencyStats,
  BedrockServiceStatus,
  BedrockHealthStatus,
  EnhancedUserProfile,
  ResponseValidation,
  TTSResult,
} from './bedrock';
