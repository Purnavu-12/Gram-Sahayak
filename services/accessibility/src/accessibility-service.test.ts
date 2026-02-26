/**
 * Unit tests for Accessibility Service
 * Tests multi-modal input/output alternatives
 */

import { AccessibilityServiceImpl } from './accessibility-service';
import {
  AccessibilityPreferences,
  TextInputEvent,
  CaptionData,
  ButtonGroup,
  VisualFormDisplay,
  FormField,
  ScreenReaderAnnouncement,
  KeyboardNavigationConfig,
  AriaAttributes
} from '../../../shared/types/accessibility';

describe('AccessibilityService', () => {
  let service: AccessibilityServiceImpl;

  beforeEach(() => {
    service = new AccessibilityServiceImpl();
  });

  describe('User Preferences Management', () => {
    it('should return default preferences for new user', async () => {
      const userId = 'user123';
      const prefs = await service.getPreferences(userId);

      expect(prefs.userId).toBe(userId);
      expect(prefs.inputMode).toBe('voice');
      expect(prefs.outputMode).toBe('audio');
      expect(prefs.textInput.enabled).toBe(true);
      expect(prefs.transcriptionDisplay.enabled).toBe(true);
      expect(prefs.buttonNavigation.enabled).toBe(true);
    });

    it('should update user preferences', async () => {
      const userId = 'user123';
      
      await service.updatePreferences(userId, {
        inputMode: 'text',
        outputMode: 'visual'
      });

      const prefs = await service.getPreferences(userId);
      expect(prefs.inputMode).toBe('text');
      expect(prefs.outputMode).toBe('visual');
    });

    it('should preserve userId when updating preferences', async () => {
      const userId = 'user123';
      
      await service.updatePreferences(userId, {
        userId: 'hacker456', // Attempt to change userId
        inputMode: 'text'
      } as any);

      const prefs = await service.getPreferences(userId);
      expect(prefs.userId).toBe(userId); // Should remain original
    });

    it('should update nested preference objects', async () => {
      const userId = 'user123';
      
      await service.updatePreferences(userId, {
        visualSettings: {
          fontSize: 'large',
          contrastMode: 'high',
          lineSpacing: 2.0,
          letterSpacing: 2
        }
      });

      const prefs = await service.getPreferences(userId);
      expect(prefs.visualSettings.fontSize).toBe('large');
      expect(prefs.visualSettings.contrastMode).toBe('high');
      expect(prefs.visualSettings.lineSpacing).toBe(2.0);
    });
  });

  describe('Text Input Processing (Requirement 10.1)', () => {
    it('should process valid text input', async () => {
      const event: TextInputEvent = {
        sessionId: 'session123',
        text: 'I want to apply for PM-KISAN',
        timestamp: new Date(),
        inputMethod: 'keyboard'
      };

      await expect(service.processTextInput(event)).resolves.not.toThrow();
    });

    it('should reject empty text input', async () => {
      const event: TextInputEvent = {
        sessionId: 'session123',
        text: '',
        timestamp: new Date(),
        inputMethod: 'keyboard'
      };

      await expect(service.processTextInput(event)).rejects.toThrow('Text input cannot be empty');
    });

    it('should reject whitespace-only text input', async () => {
      const event: TextInputEvent = {
        sessionId: 'session123',
        text: '   ',
        timestamp: new Date(),
        inputMethod: 'keyboard'
      };

      await expect(service.processTextInput(event)).rejects.toThrow('Text input cannot be empty');
    });

    it('should call registered text input handler', async () => {
      const sessionId = 'session123';
      const handler = jest.fn();
      
      service.registerTextInputHandler(sessionId, handler);

      const event: TextInputEvent = {
        sessionId,
        text: 'Test input',
        timestamp: new Date(),
        inputMethod: 'keyboard'
      };

      await service.processTextInput(event);
      expect(handler).toHaveBeenCalledWith(event);
    });

    it('should add text input to captions', async () => {
      const sessionId = 'session123';
      const event: TextInputEvent = {
        sessionId,
        text: 'Test input',
        timestamp: new Date(),
        inputMethod: 'keyboard'
      };

      await service.processTextInput(event);
      
      const captions = await service.getLiveCaptions(sessionId);
      expect(captions).toHaveLength(1);
      expect(captions[0].text).toBe('Test input');
      expect(captions[0].isFinal).toBe(true);
      expect(captions[0].confidence).toBe(1.0);
    });

    it('should support different input methods', async () => {
      const inputMethods: Array<'keyboard' | 'paste' | 'voice-to-text'> = [
        'keyboard',
        'paste',
        'voice-to-text'
      ];

      for (const method of inputMethods) {
        const event: TextInputEvent = {
          sessionId: 'session123',
          text: `Input via ${method}`,
          timestamp: new Date(),
          inputMethod: method
        };

        await expect(service.processTextInput(event)).resolves.not.toThrow();
      }
    });
  });

  describe('Live Captions (Requirement 10.2)', () => {
    it('should return empty array for session with no captions', async () => {
      const captions = await service.getLiveCaptions('session123');
      expect(captions).toEqual([]);
    });

    it('should add and retrieve captions', async () => {
      const sessionId = 'session123';
      const caption: CaptionData = {
        text: 'Welcome to Gram Sahayak',
        timestamp: new Date(),
        isFinal: true,
        confidence: 0.95,
        speaker: 'system'
      };

      await service.addCaption(sessionId, caption);
      
      const captions = await service.getLiveCaptions(sessionId);
      expect(captions).toHaveLength(1);
      expect(captions[0].text).toBe('Welcome to Gram Sahayak');
    });

    it('should maintain caption order', async () => {
      const sessionId = 'session123';
      
      for (let i = 1; i <= 5; i++) {
        await service.addCaption(sessionId, {
          text: `Caption ${i}`,
          timestamp: new Date(),
          isFinal: true,
          confidence: 0.9
        });
      }

      const captions = await service.getLiveCaptions(sessionId);
      expect(captions).toHaveLength(5);
      expect(captions[0].text).toBe('Caption 1');
      expect(captions[4].text).toBe('Caption 5');
    });

    it('should limit captions to 50 most recent', async () => {
      const sessionId = 'session123';
      
      // Add 60 captions
      for (let i = 1; i <= 60; i++) {
        await service.addCaption(sessionId, {
          text: `Caption ${i}`,
          timestamp: new Date(),
          isFinal: true,
          confidence: 0.9
        });
      }

      const captions = await service.getLiveCaptions(sessionId);
      expect(captions).toHaveLength(50);
      expect(captions[0].text).toBe('Caption 11'); // First 10 removed
      expect(captions[49].text).toBe('Caption 60');
    });

    it('should clear captions for a session', async () => {
      const sessionId = 'session123';
      
      await service.addCaption(sessionId, {
        text: 'Test caption',
        timestamp: new Date(),
        isFinal: true,
        confidence: 0.9
      });

      await service.clearCaptions(sessionId);
      
      const captions = await service.getLiveCaptions(sessionId);
      expect(captions).toEqual([]);
    });

    it('should handle interim captions', async () => {
      const sessionId = 'session123';
      
      await service.addCaption(sessionId, {
        text: 'I want to',
        timestamp: new Date(),
        isFinal: false,
        confidence: 0.7
      });

      await service.addCaption(sessionId, {
        text: 'I want to apply',
        timestamp: new Date(),
        isFinal: true,
        confidence: 0.95
      });

      const captions = await service.getLiveCaptions(sessionId);
      expect(captions).toHaveLength(2);
      expect(captions[0].isFinal).toBe(false);
      expect(captions[1].isFinal).toBe(true);
    });
  });

  describe('Button Navigation (Requirement 10.4)', () => {
    it('should return main menu buttons', async () => {
      const buttons = await service.getButtonNavigation('main-menu');
      
      expect(buttons).toHaveLength(1);
      expect(buttons[0].id).toBe('main-actions');
      expect(buttons[0].buttons).toHaveLength(4);
      
      const buttonIds = buttons[0].buttons.map(b => b.id);
      expect(buttonIds).toContain('find-schemes');
      expect(buttonIds).toContain('my-applications');
      expect(buttonIds).toContain('profile');
      expect(buttonIds).toContain('help');
    });

    it('should return scheme details buttons', async () => {
      const buttons = await service.getButtonNavigation('scheme-details');
      
      expect(buttons).toHaveLength(2);
      expect(buttons[0].id).toBe('scheme-actions');
      expect(buttons[1].id).toBe('navigation');
    });

    it('should return form filling buttons', async () => {
      const buttons = await service.getButtonNavigation('form-filling');
      
      expect(buttons).toHaveLength(2);
      expect(buttons[0].id).toBe('form-actions');
      expect(buttons[1].id).toBe('input-mode');
    });

    it('should return empty array for unknown context', async () => {
      const buttons = await service.getButtonNavigation('unknown-context');
      expect(buttons).toEqual([]);
    });

    it('should include ARIA labels for all buttons', async () => {
      const buttons = await service.getButtonNavigation('main-menu');
      
      for (const group of buttons) {
        for (const button of group.buttons) {
          expect(button.ariaLabel).toBeDefined();
          expect(button.ariaLabel.length).toBeGreaterThan(0);
        }
      }
    });

    it('should provide large touch targets', () => {
      const standardSize = service.getTouchTargetSize('standard');
      const largeSize = service.getTouchTargetSize('large');
      const extraLargeSize = service.getTouchTargetSize('extra-large');

      expect(standardSize).toBe(36);
      expect(largeSize).toBe(44); // WCAG minimum
      expect(extraLargeSize).toBe(56);
    });
  });

  describe('Visual Accessibility Settings (Requirement 10.4)', () => {
    it('should apply normal contrast mode', async () => {
      const content = '<p>Test content</p>';
      const settings = {
        fontSize: 'medium' as const,
        contrastMode: 'normal' as const,
        lineSpacing: 1.5,
        letterSpacing: 0
      };

      const styled = await service.applyVisualSettings(content, settings);
      
      expect(styled).toContain('font-size: 16px');
      expect(styled).toContain('line-height: 1.5');
      expect(styled).toContain('background-color: #ffffff');
      expect(styled).toContain('color: #000000');
    });

    it('should apply high contrast mode', async () => {
      const content = '<p>Test content</p>';
      const settings = {
        fontSize: 'large' as const,
        contrastMode: 'high' as const,
        lineSpacing: 1.8,
        letterSpacing: 1
      };

      const styled = await service.applyVisualSettings(content, settings);
      
      expect(styled).toContain('font-size: 20px');
      expect(styled).toContain('background-color: #000000');
      expect(styled).toContain('color: #ffffff');
      expect(styled).toContain('letter-spacing: 1px');
    });

    it('should apply inverted contrast mode', async () => {
      const content = '<p>Test content</p>';
      const settings = {
        fontSize: 'extra-large' as const,
        contrastMode: 'inverted' as const,
        lineSpacing: 2.0,
        letterSpacing: 2
      };

      const styled = await service.applyVisualSettings(content, settings);
      
      expect(styled).toContain('font-size: 24px');
      expect(styled).toContain('background-color: #1a1a1a');
      expect(styled).toContain('color: #f0f0f0');
    });

    it('should apply color blind mode filters', async () => {
      const content = '<p>Test content</p>';
      const colorBlindModes: Array<'protanopia' | 'deuteranopia' | 'tritanopia'> = [
        'protanopia',
        'deuteranopia',
        'tritanopia'
      ];

      for (const mode of colorBlindModes) {
        const settings = {
          fontSize: 'medium' as const,
          contrastMode: 'normal' as const,
          lineSpacing: 1.5,
          letterSpacing: 0,
          colorBlindMode: mode
        };

        const styled = await service.applyVisualSettings(content, settings);
        expect(styled).toContain(`filter: url(#${mode}-filter)`);
      }
    });

    it('should support all font sizes', async () => {
      const content = '<p>Test</p>';
      const fontSizes: Array<'small' | 'medium' | 'large' | 'extra-large'> = [
        'small',
        'medium',
        'large',
        'extra-large'
      ];
      const expectedSizes = [14, 16, 20, 24];

      for (let i = 0; i < fontSizes.length; i++) {
        const settings = {
          fontSize: fontSizes[i],
          contrastMode: 'normal' as const,
          lineSpacing: 1.5,
          letterSpacing: 0
        };

        const styled = await service.applyVisualSettings(content, settings);
        expect(styled).toContain(`font-size: ${expectedSizes[i]}px`);
      }
    });
  });

  describe('Configuration Validation', () => {
    it('should validate text input configuration', () => {
      const validConfig = {
        enabled: true,
        keyboardType: 'standard',
        autocomplete: true,
        spellcheck: true
      };

      expect(service.validateTextInputConfig(validConfig)).toBe(true);
    });

    it('should reject invalid text input configuration', () => {
      const invalidConfigs = [
        { enabled: 'yes', keyboardType: 'standard', autocomplete: true, spellcheck: true },
        { enabled: true, keyboardType: 'invalid', autocomplete: true, spellcheck: true },
        { enabled: true, keyboardType: 'standard', autocomplete: 'yes', spellcheck: true }
      ];

      for (const config of invalidConfigs) {
        expect(service.validateTextInputConfig(config)).toBe(false);
      }
    });

    it('should validate transcription display configuration', () => {
      const validConfig = {
        enabled: true,
        liveCaptions: true,
        fontSize: 'medium',
        contrastMode: 'normal',
        position: 'bottom',
        maxLines: 3
      };

      expect(service.validateTranscriptionConfig(validConfig)).toBe(true);
    });

    it('should reject invalid transcription configuration', () => {
      const invalidConfigs = [
        { enabled: true, liveCaptions: true, fontSize: 'huge', contrastMode: 'normal', position: 'bottom', maxLines: 3 },
        { enabled: true, liveCaptions: true, fontSize: 'medium', contrastMode: 'invalid', position: 'bottom', maxLines: 3 },
        { enabled: true, liveCaptions: true, fontSize: 'medium', contrastMode: 'normal', position: 'invalid', maxLines: 3 },
        { enabled: true, liveCaptions: true, fontSize: 'medium', contrastMode: 'normal', position: 'bottom', maxLines: 0 }
      ];

      for (const config of invalidConfigs) {
        expect(service.validateTranscriptionConfig(config)).toBe(false);
      }
    });

    it('should validate button navigation configuration', () => {
      const validConfig = {
        enabled: true,
        touchTargetSize: 'large',
        spacing: 16,
        hapticFeedback: true,
        audioFeedback: true
      };

      expect(service.validateButtonNavigationConfig(validConfig)).toBe(true);
    });

    it('should reject invalid button navigation configuration', () => {
      const invalidConfigs = [
        { enabled: true, touchTargetSize: 'huge', spacing: 16, hapticFeedback: true, audioFeedback: true },
        { enabled: true, touchTargetSize: 'large', spacing: -1, hapticFeedback: true, audioFeedback: true },
        { enabled: true, touchTargetSize: 'large', spacing: 16, hapticFeedback: 'yes', audioFeedback: true }
      ];

      for (const config of invalidConfigs) {
        expect(service.validateButtonNavigationConfig(config)).toBe(false);
      }
    });
  });

  describe('Edge Cases', () => {
    it('should handle multiple sessions independently', async () => {
      const session1 = 'session1';
      const session2 = 'session2';

      await service.addCaption(session1, {
        text: 'Session 1 caption',
        timestamp: new Date(),
        isFinal: true,
        confidence: 0.9
      });

      await service.addCaption(session2, {
        text: 'Session 2 caption',
        timestamp: new Date(),
        isFinal: true,
        confidence: 0.9
      });

      const captions1 = await service.getLiveCaptions(session1);
      const captions2 = await service.getLiveCaptions(session2);

      expect(captions1).toHaveLength(1);
      expect(captions2).toHaveLength(1);
      expect(captions1[0].text).toBe('Session 1 caption');
      expect(captions2[0].text).toBe('Session 2 caption');
    });

    it('should handle unregistered text input handler gracefully', async () => {
      const event: TextInputEvent = {
        sessionId: 'unregistered-session',
        text: 'Test input',
        timestamp: new Date(),
        inputMethod: 'keyboard'
      };

      await expect(service.processTextInput(event)).resolves.not.toThrow();
    });

    it('should handle handler unregistration', () => {
      const sessionId = 'session123';
      const handler = jest.fn();

      service.registerTextInputHandler(sessionId, handler);
      service.unregisterTextInputHandler(sessionId);

      // Handler should not be called after unregistration
      const event: TextInputEvent = {
        sessionId,
        text: 'Test',
        timestamp: new Date(),
        inputMethod: 'keyboard'
      };

      service.processTextInput(event);
      expect(handler).not.toHaveBeenCalled();
    });
  });

  describe('Visual Form Display with Audio Sync (Requirement 10.3)', () => {
    it('should display form with synchronized audio', async () => {
      const formData: VisualFormDisplay = {
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
          },
          {
            id: 'age',
            label: 'Age',
            value: '',
            type: 'number',
            required: true,
            ariaLabel: 'Enter your age'
          }
        ],
        currentFieldIndex: 0,
        audioSyncEnabled: true
      };

      await service.displayFormWithAudio(formData);

      const retrieved = await service.getFormDisplay('form123');
      expect(retrieved).not.toBeNull();
      expect(retrieved?.title).toBe('PM-KISAN Application');
      expect(retrieved?.fields).toHaveLength(2);
    });

    it('should announce form to screen reader when audio sync enabled', async () => {
      const formData: VisualFormDisplay = {
        formId: 'form123',
        title: 'Test Form',
        description: 'Test description',
        fields: [
          {
            id: 'field1',
            label: 'Field 1',
            value: '',
            type: 'text',
            required: true,
            ariaLabel: 'Field 1'
          }
        ],
        currentFieldIndex: 0,
        audioSyncEnabled: true
      };

      await service.displayFormWithAudio(formData);

      const announcements = await service.getScreenReaderAnnouncements(5);
      expect(announcements.length).toBeGreaterThan(0);
      expect(announcements[0].text).toContain('Test Form');
    });

    it('should not announce when audio sync disabled', async () => {
      const formData: VisualFormDisplay = {
        formId: 'form123',
        title: 'Test Form',
        description: 'Test description',
        fields: [
          {
            id: 'field1',
            label: 'Field 1',
            value: '',
            type: 'text',
            required: false,
            ariaLabel: 'Field 1'
          }
        ],
        currentFieldIndex: 0,
        audioSyncEnabled: false
      };

      await service.displayFormWithAudio(formData);

      const announcements = await service.getScreenReaderAnnouncements(5);
      expect(announcements).toHaveLength(0);
    });

    it('should reject form without formId', async () => {
      const formData: any = {
        title: 'Test Form',
        fields: []
      };

      await expect(service.displayFormWithAudio(formData)).rejects.toThrow('Invalid form data');
    });

    it('should reject form without fields', async () => {
      const formData: any = {
        formId: 'form123',
        title: 'Test Form'
      };

      await expect(service.displayFormWithAudio(formData)).rejects.toThrow('Invalid form data');
    });

    it('should return null for non-existent form', async () => {
      const form = await service.getFormDisplay('non-existent');
      expect(form).toBeNull();
    });

    it('should announce current field with help text', async () => {
      const formData: VisualFormDisplay = {
        formId: 'form123',
        title: 'Test Form',
        description: 'Test',
        fields: [
          {
            id: 'field1',
            label: 'Name',
            value: '',
            type: 'text',
            required: true,
            ariaLabel: 'Enter name',
            helpText: 'Enter your full legal name'
          }
        ],
        currentFieldIndex: 0,
        audioSyncEnabled: true
      };

      await service.displayFormWithAudio(formData);

      const announcements = await service.getScreenReaderAnnouncements(5);
      const fieldAnnouncement = announcements.find(a => a.text.includes('Name'));
      expect(fieldAnnouncement).toBeDefined();
      expect(fieldAnnouncement?.text).toContain('Required');
      expect(fieldAnnouncement?.text).toContain('Enter your full legal name');
    });
  });

  describe('Screen Reader Support (Requirement 10.5)', () => {
    it('should announce message to screen reader', async () => {
      const announcement: ScreenReaderAnnouncement = {
        text: 'Application submitted successfully',
        priority: 'assertive',
        timestamp: new Date()
      };

      await service.announceToScreenReader(announcement);

      const announcements = await service.getScreenReaderAnnouncements(1);
      expect(announcements).toHaveLength(1);
      expect(announcements[0].text).toBe('Application submitted successfully');
      expect(announcements[0].priority).toBe('assertive');
    });

    it('should support different announcement priorities', async () => {
      const priorities: Array<'polite' | 'assertive' | 'off'> = ['polite', 'assertive', 'off'];

      for (const priority of priorities) {
        await service.announceToScreenReader({
          text: `Test ${priority}`,
          priority,
          timestamp: new Date()
        });
      }

      const announcements = await service.getScreenReaderAnnouncements(3);
      expect(announcements).toHaveLength(3);
    });

    it('should limit announcements to 100 most recent', async () => {
      for (let i = 1; i <= 110; i++) {
        await service.announceToScreenReader({
          text: `Announcement ${i}`,
          priority: 'polite',
          timestamp: new Date()
        });
      }

      const announcements = await service.getScreenReaderAnnouncements(200);
      expect(announcements).toHaveLength(100);
      expect(announcements[0].text).toBe('Announcement 11');
      expect(announcements[99].text).toBe('Announcement 110');
    });

    it('should retrieve limited number of announcements', async () => {
      for (let i = 1; i <= 20; i++) {
        await service.announceToScreenReader({
          text: `Announcement ${i}`,
          priority: 'polite',
          timestamp: new Date()
        });
      }

      const announcements = await service.getScreenReaderAnnouncements(5);
      expect(announcements).toHaveLength(5);
      expect(announcements[4].text).toBe('Announcement 20');
    });
  });

  describe('Keyboard Navigation (Requirement 10.5)', () => {
    it('should provide default keyboard navigation config', async () => {
      const config = await service.getKeyboardNavigation();

      expect(config.enabled).toBe(true);
      expect(config.focusIndicatorStyle).toBe('both');
      expect(config.shortcuts).toBeDefined();
      expect(config.shortcuts.length).toBeGreaterThan(0);
      expect(config.skipLinks).toBeDefined();
      expect(config.skipLinks.length).toBeGreaterThan(0);
    });

    it('should include essential keyboard shortcuts', async () => {
      const config = await service.getKeyboardNavigation();

      const shortcutKeys = config.shortcuts.map(s => s.key);
      expect(shortcutKeys).toContain('h'); // Home
      expect(shortcutKeys).toContain('Tab'); // Navigation
      expect(shortcutKeys).toContain('Enter'); // Activate
      expect(shortcutKeys).toContain('Escape'); // Back
    });

    it('should include skip links for accessibility', async () => {
      const config = await service.getKeyboardNavigation();

      const skipLinkIds = config.skipLinks.map(s => s.id);
      expect(skipLinkIds).toContain('skip-to-main');
      expect(skipLinkIds).toContain('skip-to-nav');
    });

    it('should support modifier keys', async () => {
      const config = await service.getKeyboardNavigation();

      const shiftTabShortcut = config.shortcuts.find(
        s => s.key === 'Tab' && s.modifiers.includes('shift')
      );
      expect(shiftTabShortcut).toBeDefined();
      expect(shiftTabShortcut?.action).toBe('focus:previous');
    });

    it('should update keyboard navigation config', async () => {
      await service.updateKeyboardNavigation({
        enabled: false,
        focusIndicatorStyle: 'outline'
      });

      const config = await service.getKeyboardNavigation();
      expect(config.enabled).toBe(false);
      expect(config.focusIndicatorStyle).toBe('outline');
    });

    it('should preserve shortcuts when updating other properties', async () => {
      const originalConfig = await service.getKeyboardNavigation();
      const originalShortcutCount = originalConfig.shortcuts.length;

      await service.updateKeyboardNavigation({
        enabled: false
      });

      const updatedConfig = await service.getKeyboardNavigation();
      expect(updatedConfig.shortcuts.length).toBe(originalShortcutCount);
    });
  });

  describe('ARIA Attributes Generation (Requirement 10.5)', () => {
    it('should generate ARIA attributes for button', async () => {
      const attrs = await service.generateAriaAttributes('button', {
        label: 'Submit',
        disabled: true
      });

      expect(attrs.role).toBe('button');
      expect(attrs.label).toBe('Submit');
      expect(attrs.disabled).toBe(true);
    });

    it('should generate ARIA attributes for form', async () => {
      const attrs = await service.generateAriaAttributes('form', {
        title: 'Application Form',
        descriptionId: 'form-desc'
      });

      expect(attrs.role).toBe('form');
      expect(attrs.label).toBe('Application Form');
      expect(attrs.describedBy).toBe('form-desc');
    });

    it('should generate ARIA attributes for form field', async () => {
      const attrs = await service.generateAriaAttributes('form-field', {
        label: 'Name',
        type: 'text',
        required: true,
        invalid: false,
        helpTextId: 'name-help'
      });

      expect(attrs.role).toBe('textbox');
      expect(attrs.label).toBe('Name');
      expect(attrs.required).toBe(true);
      expect(attrs.invalid).toBe(false);
      expect(attrs.describedBy).toBe('name-help');
    });

    it('should generate ARIA attributes for select field', async () => {
      const attrs = await service.generateAriaAttributes('form-field', {
        label: 'State',
        type: 'select',
        required: true
      });

      expect(attrs.role).toBe('combobox');
      expect(attrs.label).toBe('State');
      expect(attrs.required).toBe(true);
    });

    it('should generate ARIA attributes for navigation', async () => {
      const attrs = await service.generateAriaAttributes('navigation', {
        label: 'Main navigation'
      });

      expect(attrs.role).toBe('navigation');
      expect(attrs.label).toBe('Main navigation');
    });

    it('should generate ARIA attributes for alert', async () => {
      const attrs = await service.generateAriaAttributes('alert', {});

      expect(attrs.role).toBe('alert');
      expect(attrs.live).toBe('assertive');
      expect(attrs.atomic).toBe(true);
    });

    it('should generate ARIA attributes for status', async () => {
      const attrs = await service.generateAriaAttributes('status', {});

      expect(attrs.role).toBe('status');
      expect(attrs.live).toBe('polite');
      expect(attrs.atomic).toBe(true);
    });

    it('should generate ARIA attributes for progressbar', async () => {
      const attrs = await service.generateAriaAttributes('progressbar', {
        value: 50,
        min: 0,
        max: 100,
        valueText: '50 percent complete'
      });

      expect(attrs.role).toBe('progressbar');
      expect(attrs.valueNow).toBe(50);
      expect(attrs.valueMin).toBe(0);
      expect(attrs.valueMax).toBe(100);
      expect(attrs.valueText).toBe('50 percent complete');
    });

    it('should generate ARIA attributes for checkbox', async () => {
      const attrs = await service.generateAriaAttributes('checkbox', {
        label: 'I agree',
        checked: true,
        required: false
      });

      expect(attrs.role).toBe('checkbox');
      expect(attrs.label).toBe('I agree');
      expect(attrs.checked).toBe(true);
      expect(attrs.required).toBe(false);
    });

    it('should generate ARIA attributes for dialog', async () => {
      const attrs = await service.generateAriaAttributes('dialog', {
        title: 'Confirm Action',
        descriptionId: 'dialog-desc'
      });

      expect(attrs.role).toBe('dialog');
      expect(attrs.label).toBe('Confirm Action');
      expect(attrs.describedBy).toBe('dialog-desc');
    });

    it('should convert ARIA attributes to HTML string', async () => {
      const attrs: AriaAttributes = {
        role: 'button',
        label: 'Submit',
        disabled: false,
        pressed: true
      };

      const html = service.ariaAttributesToHtml(attrs);

      expect(html).toContain('role="button"');
      expect(html).toContain('aria-label="Submit"');
      expect(html).toContain('aria-disabled="false"');
      expect(html).toContain('aria-pressed="true"');
    });

    it('should handle all ARIA attributes in HTML conversion', async () => {
      const attrs: AriaAttributes = {
        role: 'progressbar',
        label: 'Loading',
        live: 'polite',
        atomic: true,
        busy: true,
        valueNow: 50,
        valueMin: 0,
        valueMax: 100,
        valueText: '50%'
      };

      const html = service.ariaAttributesToHtml(attrs);

      expect(html).toContain('role="progressbar"');
      expect(html).toContain('aria-label="Loading"');
      expect(html).toContain('aria-live="polite"');
      expect(html).toContain('aria-atomic="true"');
      expect(html).toContain('aria-busy="true"');
      expect(html).toContain('aria-valuenow="50"');
      expect(html).toContain('aria-valuemin="0"');
      expect(html).toContain('aria-valuemax="100"');
      expect(html).toContain('aria-valuetext="50%"');
    });
  });
});

