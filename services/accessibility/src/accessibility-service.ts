/**
 * Accessibility Service Implementation
 * Provides multi-modal input/output alternatives for users with varying abilities
 * Validates: Requirements 10.1, 10.2, 10.4
 */

import {
  AccessibilityService,
  AccessibilityPreferences,
  TextInputEvent,
  CaptionData,
  ButtonGroup,
  ButtonAction,
  VisualAccessibilitySettings,
  InputMode,
  OutputMode,
  ContrastMode,
  FontSize,
  VisualFormDisplay,
  FormField,
  ScreenReaderAnnouncement,
  KeyboardNavigationConfig,
  KeyboardShortcut,
  SkipLink,
  AriaAttributes
} from '../../../shared/types/accessibility';

/**
 * Default accessibility preferences
 */
const DEFAULT_PREFERENCES: Omit<AccessibilityPreferences, 'userId'> = {
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
};

/**
 * Font size mappings in pixels
 */
const FONT_SIZE_MAP: Record<FontSize, number> = {
  'small': 14,
  'medium': 16,
  'large': 20,
  'extra-large': 24
};

/**
 * Touch target size mappings in pixels
 */
const TOUCH_TARGET_MAP = {
  'standard': 36,
  'large': 44,
  'extra-large': 56
};

/**
 * Accessibility Service Implementation
 */
export class AccessibilityServiceImpl implements AccessibilityService {
  private preferences: Map<string, AccessibilityPreferences> = new Map();
  private captions: Map<string, CaptionData[]> = new Map();
  private textInputHandlers: Map<string, (event: TextInputEvent) => void> = new Map();
  private formDisplays: Map<string, VisualFormDisplay> = new Map();
  private screenReaderAnnouncements: ScreenReaderAnnouncement[] = [];
  private keyboardNavConfig: KeyboardNavigationConfig | null = null;

  /**
   * Get accessibility preferences for a user
   * Validates: Requirements 10.1, 10.2, 10.4
   */
  async getPreferences(userId: string): Promise<AccessibilityPreferences> {
    if (!this.preferences.has(userId)) {
      // Create default preferences for new user
      const defaultPrefs: AccessibilityPreferences = {
        userId,
        ...DEFAULT_PREFERENCES
      };
      this.preferences.set(userId, defaultPrefs);
    }
    return this.preferences.get(userId)!;
  }

  /**
   * Update accessibility preferences
   * Validates: Requirements 10.1, 10.2, 10.4
   */
  async updatePreferences(
    userId: string,
    preferences: Partial<AccessibilityPreferences>
  ): Promise<void> {
    const current = await this.getPreferences(userId);
    const updated: AccessibilityPreferences = {
      ...current,
      ...preferences,
      userId // Ensure userId is not overwritten
    };
    this.preferences.set(userId, updated);
  }

  /**
   * Process text input as alternative to voice
   * Validates: Requirement 10.1
   */
  async processTextInput(event: TextInputEvent): Promise<void> {
    // Validate text input
    if (!event.text || event.text.trim().length === 0) {
      throw new Error('Text input cannot be empty');
    }

    // Store the text input event
    const handler = this.textInputHandlers.get(event.sessionId);
    if (handler) {
      handler(event);
    }

    // Add to captions if transcription display is enabled
    const caption: CaptionData = {
      text: event.text,
      timestamp: event.timestamp,
      isFinal: true,
      confidence: 1.0,
      speaker: 'user'
    };

    const sessionCaptions = this.captions.get(event.sessionId) || [];
    sessionCaptions.push(caption);
    this.captions.set(event.sessionId, sessionCaptions);
  }

  /**
   * Register a text input handler for a session
   */
  registerTextInputHandler(
    sessionId: string,
    handler: (event: TextInputEvent) => void
  ): void {
    this.textInputHandlers.set(sessionId, handler);
  }

  /**
   * Unregister a text input handler
   */
  unregisterTextInputHandler(sessionId: string): void {
    this.textInputHandlers.delete(sessionId);
  }

  /**
   * Get live captions for audio output
   * Validates: Requirement 10.2
   */
  async getLiveCaptions(sessionId: string): Promise<CaptionData[]> {
    return this.captions.get(sessionId) || [];
  }

  /**
   * Add a caption for audio output
   * Validates: Requirement 10.2
   */
  async addCaption(sessionId: string, caption: CaptionData): Promise<void> {
    const sessionCaptions = this.captions.get(sessionId) || [];
    sessionCaptions.push(caption);
    
    // Keep only recent captions (last 50)
    if (sessionCaptions.length > 50) {
      sessionCaptions.shift();
    }
    
    this.captions.set(sessionId, sessionCaptions);
  }

  /**
   * Clear captions for a session
   */
  async clearCaptions(sessionId: string): Promise<void> {
    this.captions.delete(sessionId);
  }

  /**
   * Get button navigation interface for current context
   * Validates: Requirement 10.4
   */
  async getButtonNavigation(context: string): Promise<ButtonGroup[]> {
    // Define button groups based on context
    const buttonGroups: Record<string, ButtonGroup[]> = {
      'main-menu': [
        {
          id: 'main-actions',
          title: 'Main Actions',
          layout: 'vertical',
          buttons: [
            {
              id: 'find-schemes',
              label: 'Find Schemes',
              icon: 'search',
              action: 'navigate:schemes',
              ariaLabel: 'Find government schemes you are eligible for'
            },
            {
              id: 'my-applications',
              label: 'My Applications',
              icon: 'document',
              action: 'navigate:applications',
              ariaLabel: 'View your submitted applications'
            },
            {
              id: 'profile',
              label: 'My Profile',
              icon: 'user',
              action: 'navigate:profile',
              ariaLabel: 'View and edit your profile'
            },
            {
              id: 'help',
              label: 'Help',
              icon: 'help',
              action: 'navigate:help',
              ariaLabel: 'Get help and support'
            }
          ]
        }
      ],
      'scheme-details': [
        {
          id: 'scheme-actions',
          title: 'Scheme Actions',
          layout: 'horizontal',
          buttons: [
            {
              id: 'apply',
              label: 'Apply Now',
              icon: 'check',
              action: 'apply:scheme',
              ariaLabel: 'Start application for this scheme'
            },
            {
              id: 'save',
              label: 'Save for Later',
              icon: 'bookmark',
              action: 'save:scheme',
              ariaLabel: 'Save this scheme to review later'
            },
            {
              id: 'share',
              label: 'Share',
              icon: 'share',
              action: 'share:scheme',
              ariaLabel: 'Share this scheme with others'
            }
          ]
        },
        {
          id: 'navigation',
          title: 'Navigation',
          layout: 'horizontal',
          buttons: [
            {
              id: 'back',
              label: 'Back',
              icon: 'arrow-left',
              action: 'navigate:back',
              ariaLabel: 'Go back to previous screen'
            },
            {
              id: 'home',
              label: 'Home',
              icon: 'home',
              action: 'navigate:home',
              ariaLabel: 'Go to home screen'
            }
          ]
        }
      ],
      'form-filling': [
        {
          id: 'form-actions',
          title: 'Form Actions',
          layout: 'horizontal',
          buttons: [
            {
              id: 'save-draft',
              label: 'Save Draft',
              icon: 'save',
              action: 'save:draft',
              ariaLabel: 'Save form as draft'
            },
            {
              id: 'submit',
              label: 'Submit',
              icon: 'send',
              action: 'submit:form',
              ariaLabel: 'Submit completed form'
            }
          ]
        },
        {
          id: 'input-mode',
          title: 'Input Mode',
          layout: 'horizontal',
          buttons: [
            {
              id: 'voice-input',
              label: 'Voice',
              icon: 'microphone',
              action: 'mode:voice',
              ariaLabel: 'Switch to voice input'
            },
            {
              id: 'text-input',
              label: 'Text',
              icon: 'keyboard',
              action: 'mode:text',
              ariaLabel: 'Switch to text input'
            }
          ]
        }
      ]
    };

    return buttonGroups[context] || [];
  }

  /**
   * Apply visual accessibility settings to content
   * Validates: Requirement 10.4
   */
  async applyVisualSettings(
    content: string,
    settings: VisualAccessibilitySettings
  ): Promise<string> {
    // Generate CSS styles based on settings
    const fontSize = FONT_SIZE_MAP[settings.fontSize];
    const lineHeight = settings.lineSpacing;
    const letterSpacing = settings.letterSpacing;

    // Apply contrast mode
    let backgroundColor = '#ffffff';
    let textColor = '#000000';
    
    switch (settings.contrastMode) {
      case 'high':
        backgroundColor = '#000000';
        textColor = '#ffffff';
        break;
      case 'inverted':
        backgroundColor = '#1a1a1a';
        textColor = '#f0f0f0';
        break;
    }

    // Apply color blind mode adjustments if specified
    let colorFilter = '';
    if (settings.colorBlindMode) {
      switch (settings.colorBlindMode) {
        case 'protanopia':
          colorFilter = 'url(#protanopia-filter)';
          break;
        case 'deuteranopia':
          colorFilter = 'url(#deuteranopia-filter)';
          break;
        case 'tritanopia':
          colorFilter = 'url(#tritanopia-filter)';
          break;
      }
    }

    // Wrap content with styled container
    const styledContent = `
      <div style="
        font-size: ${fontSize}px;
        line-height: ${lineHeight};
        letter-spacing: ${letterSpacing}px;
        background-color: ${backgroundColor};
        color: ${textColor};
        ${colorFilter ? `filter: ${colorFilter};` : ''}
        padding: 16px;
      ">
        ${content}
      </div>
    `;

    return styledContent;
  }

  /**
   * Get touch target size for button navigation
   */
  getTouchTargetSize(size: 'standard' | 'large' | 'extra-large'): number {
    return TOUCH_TARGET_MAP[size];
  }

  /**
   * Validate text input configuration
   */
  validateTextInputConfig(config: any): boolean {
    return (
      typeof config.enabled === 'boolean' &&
      ['standard', 'numeric', 'phone'].includes(config.keyboardType) &&
      typeof config.autocomplete === 'boolean' &&
      typeof config.spellcheck === 'boolean'
    );
  }

  /**
   * Validate transcription display configuration
   */
  validateTranscriptionConfig(config: any): boolean {
    return (
      typeof config.enabled === 'boolean' &&
      typeof config.liveCaptions === 'boolean' &&
      ['small', 'medium', 'large', 'extra-large'].includes(config.fontSize) &&
      ['normal', 'high', 'inverted'].includes(config.contrastMode) &&
      ['top', 'bottom', 'overlay'].includes(config.position) &&
      typeof config.maxLines === 'number' && config.maxLines > 0
    );
  }

  /**
   * Validate button navigation configuration
   */
  validateButtonNavigationConfig(config: any): boolean {
    return (
      typeof config.enabled === 'boolean' &&
      ['standard', 'large', 'extra-large'].includes(config.touchTargetSize) &&
      typeof config.spacing === 'number' && config.spacing >= 0 &&
      typeof config.hapticFeedback === 'boolean' &&
      typeof config.audioFeedback === 'boolean'
    );
  }

  /**
   * Display form visually with synchronized audio reading
   * Validates: Requirement 10.3
   */
  async displayFormWithAudio(formData: VisualFormDisplay): Promise<void> {
    // Validate form data
    if (!formData.formId || !formData.fields || formData.fields.length === 0) {
      throw new Error('Invalid form data');
    }

    // Store form display state
    this.formDisplays.set(formData.formId, formData);

    // If audio sync is enabled, announce form to screen reader
    if (formData.audioSyncEnabled) {
      await this.announceToScreenReader({
        text: `Form: ${formData.title}. ${formData.description}. ${formData.fields.length} fields.`,
        priority: 'polite',
        timestamp: new Date()
      });

      // Announce current field
      if (formData.currentFieldIndex >= 0 && formData.currentFieldIndex < formData.fields.length) {
        const currentField = formData.fields[formData.currentFieldIndex];
        await this.announceToScreenReader({
          text: `${currentField.label}. ${currentField.required ? 'Required.' : ''} ${currentField.helpText || ''}`,
          priority: 'polite',
          timestamp: new Date()
        });
      }
    }
  }

  /**
   * Get current form display state
   * Validates: Requirement 10.3
   */
  async getFormDisplay(formId: string): Promise<VisualFormDisplay | null> {
    return this.formDisplays.get(formId) || null;
  }

  /**
   * Update form field value and move to next field
   */
  async updateFormField(formId: string, fieldId: string, value: string): Promise<void> {
    const form = this.formDisplays.get(formId);
    if (!form) {
      throw new Error('Form not found');
    }

    // Update field value
    const fieldIndex = form.fields.findIndex(f => f.id === fieldId);
    if (fieldIndex === -1) {
      throw new Error('Field not found');
    }

    form.fields[fieldIndex].value = value;

    // Move to next field if audio sync is enabled
    if (form.audioSyncEnabled && fieldIndex < form.fields.length - 1) {
      form.currentFieldIndex = fieldIndex + 1;
      const nextField = form.fields[form.currentFieldIndex];
      
      await this.announceToScreenReader({
        text: `${nextField.label}. ${nextField.required ? 'Required.' : ''} ${nextField.helpText || ''}`,
        priority: 'polite',
        timestamp: new Date()
      });
    }

    this.formDisplays.set(formId, form);
  }

  /**
   * Announce message to screen readers
   * Validates: Requirement 10.5
   */
  async announceToScreenReader(announcement: ScreenReaderAnnouncement): Promise<void> {
    // Store announcement
    this.screenReaderAnnouncements.push(announcement);

    // Keep only recent announcements (last 100)
    if (this.screenReaderAnnouncements.length > 100) {
      this.screenReaderAnnouncements.shift();
    }

    // In a real implementation, this would trigger ARIA live region updates
    // For now, we just store the announcements for testing
  }

  /**
   * Get recent screen reader announcements
   */
  async getScreenReaderAnnouncements(limit: number = 10): Promise<ScreenReaderAnnouncement[]> {
    return this.screenReaderAnnouncements.slice(-limit);
  }

  /**
   * Get keyboard navigation configuration
   * Validates: Requirement 10.5
   */
  async getKeyboardNavigation(): Promise<KeyboardNavigationConfig> {
    if (!this.keyboardNavConfig) {
      // Initialize default keyboard navigation configuration
      this.keyboardNavConfig = {
        enabled: true,
        focusIndicatorStyle: 'both',
        shortcuts: [
          {
            key: 'h',
            modifiers: [],
            action: 'navigate:home',
            description: 'Go to home screen',
            ariaLabel: 'Press H to go to home screen'
          },
          {
            key: 's',
            modifiers: [],
            action: 'navigate:schemes',
            description: 'Go to schemes',
            ariaLabel: 'Press S to go to schemes'
          },
          {
            key: 'a',
            modifiers: [],
            action: 'navigate:applications',
            description: 'Go to applications',
            ariaLabel: 'Press A to go to applications'
          },
          {
            key: 'p',
            modifiers: [],
            action: 'navigate:profile',
            description: 'Go to profile',
            ariaLabel: 'Press P to go to profile'
          },
          {
            key: 'Escape',
            modifiers: [],
            action: 'navigate:back',
            description: 'Go back',
            ariaLabel: 'Press Escape to go back'
          },
          {
            key: 'Enter',
            modifiers: [],
            action: 'activate',
            description: 'Activate focused element',
            ariaLabel: 'Press Enter to activate'
          },
          {
            key: 'Tab',
            modifiers: [],
            action: 'focus:next',
            description: 'Move to next element',
            ariaLabel: 'Press Tab to move to next element'
          },
          {
            key: 'Tab',
            modifiers: ['shift'],
            action: 'focus:previous',
            description: 'Move to previous element',
            ariaLabel: 'Press Shift+Tab to move to previous element'
          },
          {
            key: '?',
            modifiers: [],
            action: 'help:shortcuts',
            description: 'Show keyboard shortcuts',
            ariaLabel: 'Press ? to show keyboard shortcuts'
          }
        ],
        skipLinks: [
          {
            id: 'skip-to-main',
            label: 'Skip to main content',
            targetId: 'main-content',
            ariaLabel: 'Skip to main content'
          },
          {
            id: 'skip-to-nav',
            label: 'Skip to navigation',
            targetId: 'main-navigation',
            ariaLabel: 'Skip to navigation'
          },
          {
            id: 'skip-to-footer',
            label: 'Skip to footer',
            targetId: 'footer',
            ariaLabel: 'Skip to footer'
          }
        ]
      };
    }

    return this.keyboardNavConfig;
  }

  /**
   * Update keyboard navigation configuration
   */
  async updateKeyboardNavigation(config: Partial<KeyboardNavigationConfig>): Promise<void> {
    const current = await this.getKeyboardNavigation();
    this.keyboardNavConfig = {
      ...current,
      ...config
    };
  }

  /**
   * Generate ARIA attributes for an element
   * Validates: Requirement 10.5
   */
  async generateAriaAttributes(elementType: string, context: any): Promise<AriaAttributes> {
    const attributes: AriaAttributes = {};

    switch (elementType) {
      case 'button':
        attributes.role = 'button';
        attributes.label = context.label || context.text;
        if (context.disabled) attributes.disabled = true;
        if (context.pressed !== undefined) attributes.pressed = context.pressed;
        break;

      case 'form':
        attributes.role = 'form';
        attributes.label = context.title;
        attributes.describedBy = context.descriptionId;
        break;

      case 'form-field':
        attributes.role = context.type === 'select' ? 'combobox' : 'textbox';
        attributes.label = context.label;
        attributes.required = context.required;
        attributes.invalid = context.invalid;
        if (context.helpTextId) attributes.describedBy = context.helpTextId;
        break;

      case 'navigation':
        attributes.role = 'navigation';
        attributes.label = context.label || 'Main navigation';
        break;

      case 'main-content':
        attributes.role = 'main';
        attributes.label = 'Main content';
        break;

      case 'alert':
        attributes.role = 'alert';
        attributes.live = 'assertive';
        attributes.atomic = true;
        break;

      case 'status':
        attributes.role = 'status';
        attributes.live = 'polite';
        attributes.atomic = true;
        break;

      case 'dialog':
        attributes.role = 'dialog';
        attributes.label = context.title;
        attributes.describedBy = context.descriptionId;
        break;

      case 'list':
        attributes.role = 'list';
        attributes.label = context.label;
        break;

      case 'listitem':
        attributes.role = 'listitem';
        break;

      case 'link':
        attributes.role = 'link';
        attributes.label = context.label || context.text;
        break;

      case 'heading':
        attributes.role = 'heading';
        attributes.label = context.text;
        break;

      case 'region':
        attributes.role = 'region';
        attributes.label = context.label;
        break;

      case 'progressbar':
        attributes.role = 'progressbar';
        attributes.valueNow = context.value;
        attributes.valueMin = context.min || 0;
        attributes.valueMax = context.max || 100;
        attributes.valueText = context.valueText || `${context.value}%`;
        break;

      case 'checkbox':
        attributes.role = 'checkbox';
        attributes.label = context.label;
        attributes.checked = context.checked;
        attributes.required = context.required;
        break;

      case 'radio':
        attributes.role = 'radio';
        attributes.label = context.label;
        attributes.checked = context.checked;
        break;

      case 'tab':
        attributes.role = 'tab';
        attributes.label = context.label;
        attributes.selected = context.selected;
        break;

      case 'tabpanel':
        attributes.role = 'tabpanel';
        attributes.labelledBy = context.tabId;
        break;

      default:
        // Generic element
        if (context.label) attributes.label = context.label;
        if (context.describedBy) attributes.describedBy = context.describedBy;
    }

    return attributes;
  }

  /**
   * Convert ARIA attributes to HTML attribute string
   */
  ariaAttributesToHtml(attributes: AriaAttributes): string {
    const parts: string[] = [];

    if (attributes.role) parts.push(`role="${attributes.role}"`);
    if (attributes.label) parts.push(`aria-label="${attributes.label}"`);
    if (attributes.labelledBy) parts.push(`aria-labelledby="${attributes.labelledBy}"`);
    if (attributes.describedBy) parts.push(`aria-describedby="${attributes.describedBy}"`);
    if (attributes.live) parts.push(`aria-live="${attributes.live}"`);
    if (attributes.atomic !== undefined) parts.push(`aria-atomic="${attributes.atomic}"`);
    if (attributes.relevant) parts.push(`aria-relevant="${attributes.relevant}"`);
    if (attributes.busy !== undefined) parts.push(`aria-busy="${attributes.busy}"`);
    if (attributes.hidden !== undefined) parts.push(`aria-hidden="${attributes.hidden}"`);
    if (attributes.expanded !== undefined) parts.push(`aria-expanded="${attributes.expanded}"`);
    if (attributes.pressed !== undefined) parts.push(`aria-pressed="${attributes.pressed}"`);
    if (attributes.selected !== undefined) parts.push(`aria-selected="${attributes.selected}"`);
    if (attributes.checked !== undefined) parts.push(`aria-checked="${attributes.checked}"`);
    if (attributes.disabled !== undefined) parts.push(`aria-disabled="${attributes.disabled}"`);
    if (attributes.invalid !== undefined) parts.push(`aria-invalid="${attributes.invalid}"`);
    if (attributes.required !== undefined) parts.push(`aria-required="${attributes.required}"`);
    if (attributes.valueNow !== undefined) parts.push(`aria-valuenow="${attributes.valueNow}"`);
    if (attributes.valueMin !== undefined) parts.push(`aria-valuemin="${attributes.valueMin}"`);
    if (attributes.valueMax !== undefined) parts.push(`aria-valuemax="${attributes.valueMax}"`);
    if (attributes.valueText) parts.push(`aria-valuetext="${attributes.valueText}"`);

    return parts.join(' ');
  }
}

// Export singleton instance
export const accessibilityService = new AccessibilityServiceImpl();
