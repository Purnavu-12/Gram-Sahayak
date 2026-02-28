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

// Accessibility types (named exports to avoid FormField conflict with form-generator)
export {
  InputMode, OutputMode, ContrastMode, FontSize,
  TextInputConfig, TranscriptionDisplayConfig, ButtonNavigationConfig,
  VisualAccessibilitySettings, AccessibilityPreferences, TextInputEvent,
  CaptionData, ButtonAction, ButtonGroup, VisualFormDisplay,
  ScreenReaderAnnouncement, KeyboardNavigationConfig, KeyboardShortcut,
  SkipLink, AriaAttributes, AccessibilityService
} from './accessibility';
export { FormField as AccessibilityFormField } from './accessibility';

// Bedrock types (named exports to avoid conflicts)
export { BedrockModelConfig, BedrockInferenceResult, BedrockKBQueryResult, BedrockGuardrailResult } from './bedrock';
