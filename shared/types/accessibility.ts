/**
 * Core interfaces for Accessibility Service
 * Provides multi-modal input/output alternatives for users with varying abilities
 */

export type InputMode = 'voice' | 'text' | 'button';
export type OutputMode = 'audio' | 'visual' | 'both';
export type ContrastMode = 'normal' | 'high' | 'inverted';
export type FontSize = 'small' | 'medium' | 'large' | 'extra-large';

/**
 * Text input configuration
 * Validates: Requirement 10.1
 */
export interface TextInputConfig {
  enabled: boolean;
  keyboardType: 'standard' | 'numeric' | 'phone';
  autocomplete: boolean;
  spellcheck: boolean;
  placeholder?: string;
}

/**
 * Visual transcription configuration
 * Validates: Requirement 10.2
 */
export interface TranscriptionDisplayConfig {
  enabled: boolean;
  liveCaptions: boolean;
  fontSize: FontSize;
  contrastMode: ContrastMode;
  position: 'top' | 'bottom' | 'overlay';
  maxLines: number;
}

/**
 * Button navigation configuration
 * Validates: Requirement 10.4
 */
export interface ButtonNavigationConfig {
  enabled: boolean;
  touchTargetSize: 'standard' | 'large' | 'extra-large'; // min 44x44px for large
  spacing: number; // pixels between buttons
  hapticFeedback: boolean;
  audioFeedback: boolean;
}

/**
 * Visual accessibility settings
 * Validates: Requirement 10.4
 */
export interface VisualAccessibilitySettings {
  fontSize: FontSize;
  contrastMode: ContrastMode;
  lineSpacing: number; // 1.0 to 2.0
  letterSpacing: number; // 0 to 5px
  colorBlindMode?: 'protanopia' | 'deuteranopia' | 'tritanopia';
}

/**
 * Accessibility preferences for a user
 */
export interface AccessibilityPreferences {
  userId: string;
  inputMode: InputMode;
  outputMode: OutputMode;
  textInput: TextInputConfig;
  transcriptionDisplay: TranscriptionDisplayConfig;
  buttonNavigation: ButtonNavigationConfig;
  visualSettings: VisualAccessibilitySettings;
  screenReaderEnabled: boolean;
  reducedMotion: boolean;
}

/**
 * Text input event
 */
export interface TextInputEvent {
  sessionId: string;
  text: string;
  timestamp: Date;
  inputMethod: 'keyboard' | 'paste' | 'voice-to-text';
}

/**
 * Caption data for live transcription
 */
export interface CaptionData {
  text: string;
  timestamp: Date;
  isFinal: boolean;
  confidence: number;
  speaker?: string;
}

/**
 * Button action definition
 */
export interface ButtonAction {
  id: string;
  label: string;
  icon?: string;
  action: string;
  disabled?: boolean;
  ariaLabel: string;
}

/**
 * Navigation button group
 */
export interface ButtonGroup {
  id: string;
  title: string;
  buttons: ButtonAction[];
  layout: 'horizontal' | 'vertical' | 'grid';
}

/**
 * Form field for visual display
 * Validates: Requirement 10.3
 */
export interface FormField {
  id: string;
  label: string;
  value: string;
  type: 'text' | 'number' | 'date' | 'select' | 'textarea';
  required: boolean;
  ariaLabel: string;
  ariaDescribedBy?: string;
  helpText?: string;
}

/**
 * Visual form display data
 * Validates: Requirement 10.3
 */
export interface VisualFormDisplay {
  formId: string;
  title: string;
  description: string;
  fields: FormField[];
  currentFieldIndex: number;
  audioSyncEnabled: boolean;
}

/**
 * Screen reader announcement
 * Validates: Requirement 10.5
 */
export interface ScreenReaderAnnouncement {
  text: string;
  priority: 'polite' | 'assertive' | 'off';
  timestamp: Date;
}

/**
 * Keyboard navigation configuration
 * Validates: Requirement 10.5
 */
export interface KeyboardNavigationConfig {
  enabled: boolean;
  shortcuts: KeyboardShortcut[];
  focusIndicatorStyle: 'outline' | 'highlight' | 'both';
  skipLinks: SkipLink[];
}

/**
 * Keyboard shortcut definition
 */
export interface KeyboardShortcut {
  key: string;
  modifiers: ('ctrl' | 'alt' | 'shift' | 'meta')[];
  action: string;
  description: string;
  ariaLabel: string;
}

/**
 * Skip link for keyboard navigation
 */
export interface SkipLink {
  id: string;
  label: string;
  targetId: string;
  ariaLabel: string;
}

/**
 * ARIA attributes for assistive technology
 * Validates: Requirement 10.5
 */
export interface AriaAttributes {
  role?: string;
  label?: string;
  labelledBy?: string;
  describedBy?: string;
  live?: 'polite' | 'assertive' | 'off';
  atomic?: boolean;
  relevant?: string;
  busy?: boolean;
  hidden?: boolean;
  expanded?: boolean;
  pressed?: boolean;
  selected?: boolean;
  checked?: boolean;
  disabled?: boolean;
  invalid?: boolean;
  required?: boolean;
  valueNow?: number;
  valueMin?: number;
  valueMax?: number;
  valueText?: string;
}

/**
 * Accessibility Service Interface
 * Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5
 */
export interface AccessibilityService {
  /**
   * Get accessibility preferences for a user
   */
  getPreferences(userId: string): Promise<AccessibilityPreferences>;

  /**
   * Update accessibility preferences
   */
  updatePreferences(userId: string, preferences: Partial<AccessibilityPreferences>): Promise<void>;

  /**
   * Process text input as alternative to voice
   */
  processTextInput(event: TextInputEvent): Promise<void>;

  /**
   * Get live captions for audio output
   */
  getLiveCaptions(sessionId: string): Promise<CaptionData[]>;

  /**
   * Get button navigation interface for current context
   */
  getButtonNavigation(context: string): Promise<ButtonGroup[]>;

  /**
   * Apply visual accessibility settings to content
   */
  applyVisualSettings(content: string, settings: VisualAccessibilitySettings): Promise<string>;

  /**
   * Display form visually with synchronized audio reading
   * Validates: Requirement 10.3
   */
  displayFormWithAudio(formData: VisualFormDisplay): Promise<void>;

  /**
   * Get current form display state
   * Validates: Requirement 10.3
   */
  getFormDisplay(formId: string): Promise<VisualFormDisplay | null>;

  /**
   * Announce message to screen readers
   * Validates: Requirement 10.5
   */
  announceToScreenReader(announcement: ScreenReaderAnnouncement): Promise<void>;

  /**
   * Get keyboard navigation configuration
   * Validates: Requirement 10.5
   */
  getKeyboardNavigation(): Promise<KeyboardNavigationConfig>;

  /**
   * Generate ARIA attributes for an element
   * Validates: Requirement 10.5
   */
  generateAriaAttributes(elementType: string, context: any): Promise<AriaAttributes>;
}
