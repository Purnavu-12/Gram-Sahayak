# Accessibility Service

Multi-modal accessibility service for Gram Sahayak that provides alternative input/output methods for users with varying abilities and preferences.

## Features

### Text Input Alternatives (Requirement 10.1)
- Keyboard input as alternative to voice
- Support for standard, numeric, and phone keyboards
- Autocomplete and spellcheck capabilities
- Multiple input methods: keyboard, paste, voice-to-text

### Visual Transcription Display (Requirement 10.2)
- Live captions for all audio output
- Configurable caption display (top, bottom, overlay)
- Adjustable font size and contrast
- Support for interim and final captions
- Automatic caption history management (50 most recent)

### Visual Form Display with Audio Sync (Requirement 10.3)
- Display forms visually while reading them aloud
- Synchronized audio reading of form fields
- Field-by-field navigation with audio announcements
- Support for required fields and help text
- Real-time form state management

### Button-Based Navigation (Requirement 10.4)
- Large touch targets (minimum 44x44px for accessibility)
- Context-aware button groups
- Haptic and audio feedback options
- ARIA labels for screen reader compatibility
- Configurable spacing and sizing

### Visual Accessibility Settings (Requirement 10.4)
- Adjustable font sizes (small, medium, large, extra-large)
- High-contrast and inverted contrast modes
- Adjustable line spacing and letter spacing
- Color blind mode support (protanopia, deuteranopia, tritanopia)
- Screen reader compatibility

### Screen Reader Support (Requirement 10.5)
- Compatible with NVDA, JAWS, and TalkBack
- Polite and assertive announcement priorities
- Automatic announcement history management
- Live region updates for dynamic content

### Keyboard Navigation (Requirement 10.5)
- Full keyboard navigation support
- Customizable keyboard shortcuts
- Skip links for quick navigation
- Focus indicators (outline, highlight, or both)
- Support for modifier keys (Ctrl, Alt, Shift, Meta)

### ARIA Integration (Requirement 10.5)
- Comprehensive ARIA attribute generation
- Support for all standard ARIA roles
- Dynamic ARIA attribute updates
- HTML attribute string conversion
- Context-aware attribute generation

## Usage

```typescript
import { accessibilityService } from '@gram-sahayak/accessibility';

// Get user preferences
const prefs = await accessibilityService.getPreferences('user123');

// Update preferences
await accessibilityService.updatePreferences('user123', {
  inputMode: 'text',
  outputMode: 'visual',
  visualSettings: {
    fontSize: 'large',
    contrastMode: 'high',
    lineSpacing: 2.0,
    letterSpacing: 1
  }
});

// Process text input
await accessibilityService.processTextInput({
  sessionId: 'session123',
  text: 'I want to apply for PM-KISAN',
  timestamp: new Date(),
  inputMethod: 'keyboard'
});

// Add caption for audio output
await accessibilityService.addCaption('session123', {
  text: 'Welcome to Gram Sahayak',
  timestamp: new Date(),
  isFinal: true,
  confidence: 0.95,
  speaker: 'system'
});

// Get live captions
const captions = await accessibilityService.getLiveCaptions('session123');

// Get button navigation for context
const buttons = await accessibilityService.getButtonNavigation('main-menu');

// Apply visual settings to content
const styledContent = await accessibilityService.applyVisualSettings(
  '<p>Content</p>',
  prefs.visualSettings
);

// Display form with synchronized audio reading
await accessibilityService.displayFormWithAudio({
  formId: 'form123',
  title: 'PM-KISAN Application',
  description: 'Apply for PM-KISAN scheme',
  fields: [
    {
      id: 'name',
      label: 'Full Name',
      value: '',
      type: 'text',
      required: true,
      ariaLabel: 'Enter your full name',
      helpText: 'As per Aadhaar card'
    }
  ],
  currentFieldIndex: 0,
  audioSyncEnabled: true
});

// Get form display state
const formDisplay = await accessibilityService.getFormDisplay('form123');

// Announce to screen readers
await accessibilityService.announceToScreenReader({
  text: 'Application submitted successfully',
  priority: 'assertive',
  timestamp: new Date()
});

// Get keyboard navigation configuration
const keyboardNav = await accessibilityService.getKeyboardNavigation();

// Generate ARIA attributes
const ariaAttrs = await accessibilityService.generateAriaAttributes('button', {
  label: 'Submit',
  disabled: false
});

// Convert ARIA attributes to HTML string
const htmlString = accessibilityService.ariaAttributesToHtml(ariaAttrs);
```

## API Reference

### AccessibilityService Interface

#### `getPreferences(userId: string): Promise<AccessibilityPreferences>`
Get accessibility preferences for a user. Returns default preferences for new users.

#### `updatePreferences(userId: string, preferences: Partial<AccessibilityPreferences>): Promise<void>`
Update accessibility preferences for a user.

#### `processTextInput(event: TextInputEvent): Promise<void>`
Process text input as alternative to voice input.

#### `getLiveCaptions(sessionId: string): Promise<CaptionData[]>`
Get live captions for a session.

#### `addCaption(sessionId: string, caption: CaptionData): Promise<void>`
Add a caption for audio output.

#### `getButtonNavigation(context: string): Promise<ButtonGroup[]>`
Get button navigation interface for current context.

#### `applyVisualSettings(content: string, settings: VisualAccessibilitySettings): Promise<string>`
Apply visual accessibility settings to content.

#### `displayFormWithAudio(formData: VisualFormDisplay): Promise<void>`
Display form visually with synchronized audio reading. (Requirement 10.3)

#### `getFormDisplay(formId: string): Promise<VisualFormDisplay | null>`
Get current form display state. (Requirement 10.3)

#### `announceToScreenReader(announcement: ScreenReaderAnnouncement): Promise<void>`
Announce message to screen readers (NVDA, JAWS, TalkBack). (Requirement 10.5)

#### `getScreenReaderAnnouncements(limit?: number): Promise<ScreenReaderAnnouncement[]>`
Get recent screen reader announcements. (Requirement 10.5)

#### `getKeyboardNavigation(): Promise<KeyboardNavigationConfig>`
Get keyboard navigation configuration with shortcuts and skip links. (Requirement 10.5)

#### `updateKeyboardNavigation(config: Partial<KeyboardNavigationConfig>): Promise<void>`
Update keyboard navigation configuration. (Requirement 10.5)

#### `generateAriaAttributes(elementType: string, context: any): Promise<AriaAttributes>`
Generate ARIA attributes for an element based on type and context. (Requirement 10.5)

#### `ariaAttributesToHtml(attributes: AriaAttributes): string`
Convert ARIA attributes object to HTML attribute string. (Requirement 10.5)

## Configuration

### Default Preferences

```typescript
{
  inputMode: 'voice',
  outputMode: 'audio',
  textInput: {
    enabled: true,
    keyboardType: 'standard',
    autocomplete: true,
    spellcheck: true
  },
  transcriptionDisplay: {
    enabled: true,
    liveCaptions: true,
    fontSize: 'medium',
    contrastMode: 'normal',
    position: 'bottom',
    maxLines: 3
  },
  buttonNavigation: {
    enabled: true,
    touchTargetSize: 'large',
    spacing: 16,
    hapticFeedback: true,
    audioFeedback: true
  },
  visualSettings: {
    fontSize: 'medium',
    contrastMode: 'normal',
    lineSpacing: 1.5,
    letterSpacing: 0
  },
  screenReaderEnabled: false,
  reducedMotion: false
}
```

## Testing

Run unit tests:
```bash
npm test
```

Run tests with coverage:
```bash
npm test -- --coverage
```

## Accessibility Standards

This service follows WCAG 2.1 Level AA guidelines:
- Touch targets minimum 44x44px
- Contrast ratios meet AA standards
- Keyboard navigation support
- Screen reader compatibility
- Text alternatives for non-text content
