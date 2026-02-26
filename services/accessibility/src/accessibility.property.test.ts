/**
 * Property-Based Tests for Accessibility Service
 * Feature: gram-sahayak
 * 
 * **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**
 */

import * as fc from 'fast-check';
import { AccessibilityServiceImpl } from './accessibility-service';
import {
  AccessibilityPreferences,
  TextInputEvent,
  CaptionData,
  VisualFormDisplay,
  ScreenReaderAnnouncement,
  VisualAccessibilitySettings,
  FormField
} from '../../../shared/types/accessibility';

describe('Accessibility Property Tests', () => {
  /**
   * Property 14: Multi-Modal Accessibility
   * 
   * For any user with accessibility needs, the system should provide text 
   * alternatives to voice input, display transcriptions for audio output, 
   * show visual confirmations of forms, offer button-based navigation, and 
   * support screen readers and assistive technologies.
   * 
   * **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**
   */
  describe('Property 14: Multi-Modal Accessibility', () => {
    let service: AccessibilityServiceImpl;

    beforeEach(() => {
      service = new AccessibilityServiceImpl();
    });

    it('should provide text input alternatives to voice input for any user (Requirement 10.1)', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            userId: fc.string({ minLength: 5, maxLength: 20 }),
            sessionId: fc.string({ minLength: 10, maxLength: 30 }),
            textContent: fc.string({ minLength: 1, maxLength: 500 }).filter(s => s.trim().length > 0),
            inputMethod: fc.constantFrom<'keyboard' | 'paste' | 'voice-to-text'>('keyboard', 'paste', 'voice-to-text')
          }),
          async ({ userId, sessionId, textContent, inputMethod }) => {
            // Arrange - Enable text input for user
            await service.updatePreferences(userId, {
              inputMode: 'text',
              textInput: {
                enabled: true,
                keyboardType: 'standard',
                autocomplete: true,
                spellcheck: true
              }
            });

            const prefs = await service.getPreferences(userId);

            // Property: Text input should be enabled as alternative to voice
            expect(prefs.textInput.enabled).toBe(true);
            expect(prefs.inputMode).toBe('text');

            // Act - Process text input
            const event: TextInputEvent = {
              sessionId,
              text: textContent,
              timestamp: new Date(),
              inputMethod
            };

            await service.processTextInput(event);

            // Assert - Property: Text input should be processed successfully
            const captions = await service.getLiveCaptions(sessionId);
            expect(captions.length).toBeGreaterThan(0);
            
            const lastCaption = captions[captions.length - 1];
            expect(lastCaption.text).toBe(textContent);
            expect(lastCaption.isFinal).toBe(true);
            expect(lastCaption.confidence).toBe(1.0);
            expect(lastCaption.speaker).toBe('user');

            // Property: All input methods should be supported
            expect(['keyboard', 'paste', 'voice-to-text']).toContain(inputMethod);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should display transcriptions for all audio output (Requirement 10.2)', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            userId: fc.string({ minLength: 5, maxLength: 20 }),
            sessionId: fc.string({ minLength: 10, maxLength: 30 }),
            audioMessages: fc.array(
              fc.record({
                text: fc.string({ minLength: 5, maxLength: 200 }),
                isFinal: fc.boolean(),
                confidence: fc.double({ min: 0.5, max: 1.0, noNaN: true }),
                speaker: fc.constantFrom('system', 'user', 'assistant')
              }),
              { minLength: 1, maxLength: 10 }
            ),
            fontSize: fc.constantFrom<'small' | 'medium' | 'large' | 'extra-large'>('small', 'medium', 'large', 'extra-large'),
            contrastMode: fc.constantFrom<'normal' | 'high' | 'inverted'>('normal', 'high', 'inverted')
          }),
          async ({ userId, sessionId, audioMessages, fontSize, contrastMode }) => {
            // Arrange - Enable transcription display
            await service.updatePreferences(userId, {
              transcriptionDisplay: {
                enabled: true,
                liveCaptions: true,
                fontSize,
                contrastMode,
                position: 'bottom',
                maxLines: 3
              }
            });

            const prefs = await service.getPreferences(userId);

            // Property: Transcription display should be enabled
            expect(prefs.transcriptionDisplay.enabled).toBe(true);
            expect(prefs.transcriptionDisplay.liveCaptions).toBe(true);

            // Act - Add captions for audio output
            for (const message of audioMessages) {
              const caption: CaptionData = {
                text: message.text,
                timestamp: new Date(),
                isFinal: message.isFinal,
                confidence: message.confidence,
                speaker: message.speaker
              };
              await service.addCaption(sessionId, caption);
            }

            // Assert - Property: All audio should have text transcriptions
            const captions = await service.getLiveCaptions(sessionId);
            expect(captions.length).toBe(audioMessages.length);

            for (let i = 0; i < audioMessages.length; i++) {
              expect(captions[i].text).toBe(audioMessages[i].text);
              expect(captions[i].isFinal).toBe(audioMessages[i].isFinal);
              expect(captions[i].confidence).toBeGreaterThanOrEqual(0.5);
              expect(captions[i].confidence).toBeLessThanOrEqual(1.0);
              expect(captions[i].speaker).toBe(audioMessages[i].speaker);
            }

            // Property: Transcription settings should be customizable
            expect(['small', 'medium', 'large', 'extra-large']).toContain(prefs.transcriptionDisplay.fontSize);
            expect(['normal', 'high', 'inverted']).toContain(prefs.transcriptionDisplay.contrastMode);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should show visual confirmations of forms with audio sync (Requirement 10.3)', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            formId: fc.string({ minLength: 5, maxLength: 20 }),
            formTitle: fc.string({ minLength: 5, maxLength: 50 }),
            formDescription: fc.string({ minLength: 10, maxLength: 100 }),
            fields: fc.array(
              fc.record({
                id: fc.string({ minLength: 3, maxLength: 15 }),
                label: fc.string({ minLength: 3, maxLength: 30 }),
                type: fc.constantFrom<'text' | 'number' | 'date' | 'select' | 'textarea'>('text', 'number', 'date', 'select', 'textarea'),
                required: fc.boolean(),
                helpText: fc.option(fc.string({ minLength: 5, maxLength: 50 }), { nil: undefined })
              }),
              { minLength: 1, maxLength: 10 }
            ),
            audioSyncEnabled: fc.boolean()
          }),
          async ({ formId, formTitle, formDescription, fields, audioSyncEnabled }) => {
            // Arrange - Create form fields with proper structure
            const formFields: FormField[] = fields.map(f => ({
              id: f.id,
              label: f.label,
              value: '',
              type: f.type,
              required: f.required,
              ariaLabel: `Enter ${f.label}`,
              helpText: f.helpText
            }));

            const formData: VisualFormDisplay = {
              formId,
              title: formTitle,
              description: formDescription,
              fields: formFields,
              currentFieldIndex: 0,
              audioSyncEnabled
            };

            // Act - Display form with visual confirmation
            await service.displayFormWithAudio(formData);

            // Assert - Property: Form should be displayed visually
            const displayedForm = await service.getFormDisplay(formId);
            expect(displayedForm).not.toBeNull();
            expect(displayedForm!.formId).toBe(formId);
            expect(displayedForm!.title).toBe(formTitle);
            expect(displayedForm!.description).toBe(formDescription);
            expect(displayedForm!.fields.length).toBe(formFields.length);

            // Property: All form fields should be visible
            for (let i = 0; i < formFields.length; i++) {
              expect(displayedForm!.fields[i].id).toBe(formFields[i].id);
              expect(displayedForm!.fields[i].label).toBe(formFields[i].label);
              expect(displayedForm!.fields[i].type).toBe(formFields[i].type);
              expect(displayedForm!.fields[i].required).toBe(formFields[i].required);
            }

            // Property: Audio sync should be configurable
            expect(displayedForm!.audioSyncEnabled).toBe(audioSyncEnabled);

            // Property: If audio sync enabled, screen reader announcements should be made
            if (audioSyncEnabled) {
              const announcements = await service.getScreenReaderAnnouncements(5);
              expect(announcements.length).toBeGreaterThan(0);
              
              // Should announce form title
              const formAnnouncement = announcements.find(a => a.text.includes(formTitle));
              expect(formAnnouncement).toBeDefined();
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should offer button-based navigation for any context (Requirement 10.4)', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            userId: fc.string({ minLength: 5, maxLength: 20 }),
            context: fc.constantFrom('main-menu', 'scheme-details', 'form-filling'),
            touchTargetSize: fc.constantFrom<'standard' | 'large' | 'extra-large'>('standard', 'large', 'extra-large'),
            spacing: fc.integer({ min: 8, max: 32 }),
            hapticFeedback: fc.boolean(),
            audioFeedback: fc.boolean()
          }),
          async ({ userId, context, touchTargetSize, spacing, hapticFeedback, audioFeedback }) => {
            // Arrange - Enable button navigation
            await service.updatePreferences(userId, {
              buttonNavigation: {
                enabled: true,
                touchTargetSize,
                spacing,
                hapticFeedback,
                audioFeedback
              }
            });

            const prefs = await service.getPreferences(userId);

            // Property: Button navigation should be enabled
            expect(prefs.buttonNavigation.enabled).toBe(true);
            expect(prefs.buttonNavigation.touchTargetSize).toBe(touchTargetSize);

            // Act - Get button navigation for context
            const buttonGroups = await service.getButtonNavigation(context);

            // Assert - Property: Button navigation should be available for all contexts
            expect(buttonGroups).toBeDefined();
            expect(Array.isArray(buttonGroups)).toBe(true);

            if (buttonGroups.length > 0) {
              // Property: All button groups should have valid structure
              for (const group of buttonGroups) {
                expect(group.id).toBeDefined();
                expect(group.title).toBeDefined();
                expect(group.buttons).toBeDefined();
                expect(Array.isArray(group.buttons)).toBe(true);
                expect(['horizontal', 'vertical', 'grid']).toContain(group.layout);

                // Property: All buttons should have accessibility labels
                for (const button of group.buttons) {
                  expect(button.id).toBeDefined();
                  expect(button.label).toBeDefined();
                  expect(button.action).toBeDefined();
                  expect(button.ariaLabel).toBeDefined();
                  expect(button.ariaLabel.length).toBeGreaterThan(0);
                }
              }

              // Property: Touch targets should meet accessibility standards
              const targetSize = service.getTouchTargetSize(touchTargetSize);
              expect(targetSize).toBeGreaterThanOrEqual(36); // Minimum standard
              if (touchTargetSize === 'large') {
                expect(targetSize).toBeGreaterThanOrEqual(44); // WCAG minimum
              }
            }

            // Property: Button navigation preferences should be customizable
            expect(prefs.buttonNavigation.spacing).toBe(spacing);
            expect(prefs.buttonNavigation.hapticFeedback).toBe(hapticFeedback);
            expect(prefs.buttonNavigation.audioFeedback).toBe(audioFeedback);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should support screen readers and assistive technologies (Requirement 10.5)', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            userId: fc.string({ minLength: 5, maxLength: 20 }),
            announcements: fc.array(
              fc.record({
                text: fc.string({ minLength: 5, maxLength: 100 }),
                priority: fc.constantFrom<'polite' | 'assertive' | 'off'>('polite', 'assertive', 'off')
              }),
              { minLength: 1, maxLength: 10 }
            ),
            elementType: fc.constantFrom(
              'button', 'form', 'form-field', 'navigation', 'alert', 
              'status', 'dialog', 'progressbar', 'checkbox'
            ),
            focusIndicatorStyle: fc.constantFrom<'outline' | 'highlight' | 'both'>('outline', 'highlight', 'both')
          }),
          async ({ userId, announcements, elementType, focusIndicatorStyle }) => {
            // Arrange - Enable screen reader support
            await service.updatePreferences(userId, {
              screenReaderEnabled: true
            });

            const prefs = await service.getPreferences(userId);

            // Property: Screen reader should be enabled
            expect(prefs.screenReaderEnabled).toBe(true);

            // Act - Make screen reader announcements
            for (const announcement of announcements) {
              const srAnnouncement: ScreenReaderAnnouncement = {
                text: announcement.text,
                priority: announcement.priority,
                timestamp: new Date()
              };
              await service.announceToScreenReader(srAnnouncement);
            }

            // Assert - Property: All announcements should be captured
            const capturedAnnouncements = await service.getScreenReaderAnnouncements(announcements.length);
            expect(capturedAnnouncements.length).toBe(announcements.length);

            for (let i = 0; i < announcements.length; i++) {
              expect(capturedAnnouncements[i].text).toBe(announcements[i].text);
              expect(capturedAnnouncements[i].priority).toBe(announcements[i].priority);
              expect(['polite', 'assertive', 'off']).toContain(capturedAnnouncements[i].priority);
            }

            // Property: Keyboard navigation should be available
            const keyboardNav = await service.getKeyboardNavigation();
            expect(keyboardNav).toBeDefined();
            expect(keyboardNav.enabled).toBe(true);
            expect(keyboardNav.shortcuts).toBeDefined();
            expect(keyboardNav.shortcuts.length).toBeGreaterThan(0);
            expect(keyboardNav.skipLinks).toBeDefined();
            expect(keyboardNav.skipLinks.length).toBeGreaterThan(0);

            // Property: Focus indicator should be customizable
            await service.updateKeyboardNavigation({ focusIndicatorStyle });
            const updatedNav = await service.getKeyboardNavigation();
            expect(updatedNav.focusIndicatorStyle).toBe(focusIndicatorStyle);

            // Property: ARIA attributes should be generated for all element types
            const ariaAttrs = await service.generateAriaAttributes(elementType, {
              label: 'Test Element',
              title: 'Test Title',
              type: 'text',
              required: false,
              value: 50,
              min: 0,
              max: 100,
              checked: false
            });

            expect(ariaAttrs).toBeDefined();
            expect(ariaAttrs.role).toBeDefined();
            
            // Property: ARIA attributes should be convertible to HTML
            const htmlAttrs = service.ariaAttributesToHtml(ariaAttrs);
            expect(htmlAttrs).toBeDefined();
            expect(htmlAttrs.length).toBeGreaterThan(0);
            expect(htmlAttrs).toContain('role=');
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should apply visual accessibility settings for any content (Requirement 10.4)', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            content: fc.string({ minLength: 10, maxLength: 200 }),
            fontSize: fc.constantFrom<'small' | 'medium' | 'large' | 'extra-large'>('small', 'medium', 'large', 'extra-large'),
            contrastMode: fc.constantFrom<'normal' | 'high' | 'inverted'>('normal', 'high', 'inverted'),
            lineSpacing: fc.double({ min: 1.0, max: 2.0, noNaN: true }),
            letterSpacing: fc.integer({ min: 0, max: 5 }),
            colorBlindMode: fc.option(
              fc.constantFrom<'protanopia' | 'deuteranopia' | 'tritanopia'>('protanopia', 'deuteranopia', 'tritanopia'),
              { nil: undefined }
            )
          }),
          async ({ content, fontSize, contrastMode, lineSpacing, letterSpacing, colorBlindMode }) => {
            // Arrange - Create visual settings
            const settings: VisualAccessibilitySettings = {
              fontSize,
              contrastMode,
              lineSpacing,
              letterSpacing,
              colorBlindMode
            };

            // Act - Apply visual settings to content
            const styledContent = await service.applyVisualSettings(content, settings);

            // Assert - Property: Content should be styled with accessibility settings
            expect(styledContent).toBeDefined();
            expect(styledContent.length).toBeGreaterThan(content.length); // Should include styling

            // Property: Font size should be applied
            const fontSizeMap: Record<'small' | 'medium' | 'large' | 'extra-large', number> = { 
              small: 14, medium: 16, large: 20, 'extra-large': 24 
            };
            expect(styledContent).toContain(`font-size: ${fontSizeMap[fontSize]}px`);

            // Property: Line spacing should be applied
            expect(styledContent).toContain(`line-height: ${lineSpacing}`);

            // Property: Letter spacing should be applied
            expect(styledContent).toContain(`letter-spacing: ${letterSpacing}px`);

            // Property: Contrast mode should be applied
            if (contrastMode === 'normal') {
              expect(styledContent).toContain('background-color: #ffffff');
              expect(styledContent).toContain('color: #000000');
            } else if (contrastMode === 'high') {
              expect(styledContent).toContain('background-color: #000000');
              expect(styledContent).toContain('color: #ffffff');
            } else if (contrastMode === 'inverted') {
              expect(styledContent).toContain('background-color: #1a1a1a');
              expect(styledContent).toContain('color: #f0f0f0');
            }

            // Property: Color blind mode filter should be applied if specified
            if (colorBlindMode) {
              expect(styledContent).toContain(`filter: url(#${colorBlindMode}-filter)`);
            }

            // Property: Original content should be preserved
            expect(styledContent).toContain(content);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should maintain accessibility preferences across sessions for any user', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            userId: fc.string({ minLength: 5, maxLength: 20 }),
            inputMode: fc.constantFrom<'voice' | 'text' | 'button'>('voice', 'text', 'button'),
            outputMode: fc.constantFrom<'audio' | 'visual' | 'both'>('audio', 'visual', 'both'),
            screenReaderEnabled: fc.boolean(),
            reducedMotion: fc.boolean()
          }),
          async ({ userId, inputMode, outputMode, screenReaderEnabled, reducedMotion }) => {
            // Arrange & Act - Set preferences
            await service.updatePreferences(userId, {
              inputMode,
              outputMode,
              screenReaderEnabled,
              reducedMotion
            });

            // Assert - Property: Preferences should be persisted
            const prefs = await service.getPreferences(userId);
            expect(prefs.userId).toBe(userId);
            expect(prefs.inputMode).toBe(inputMode);
            expect(prefs.outputMode).toBe(outputMode);
            expect(prefs.screenReaderEnabled).toBe(screenReaderEnabled);
            expect(prefs.reducedMotion).toBe(reducedMotion);

            // Property: Preferences should be retrievable in subsequent calls
            const prefs2 = await service.getPreferences(userId);
            expect(prefs2.userId).toBe(userId);
            expect(prefs2.inputMode).toBe(inputMode);
            expect(prefs2.outputMode).toBe(outputMode);
            expect(prefs2.screenReaderEnabled).toBe(screenReaderEnabled);
            expect(prefs2.reducedMotion).toBe(reducedMotion);

            // Property: User ID should never be overwritten
            await service.updatePreferences(userId, {
              userId: 'hacker-attempt' as any,
              inputMode: 'voice'
            });

            const prefs3 = await service.getPreferences(userId);
            expect(prefs3.userId).toBe(userId); // Should remain original
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle form field updates with audio announcements (Requirement 10.3)', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            formId: fc.string({ minLength: 5, maxLength: 20 }),
            fields: fc.array(
              fc.record({
                id: fc.string({ minLength: 3, maxLength: 15 }),
                label: fc.string({ minLength: 3, maxLength: 30 }),
                value: fc.string({ minLength: 0, maxLength: 50 })
              }),
              { minLength: 2, maxLength: 5 }
            ),
            audioSyncEnabled: fc.boolean()
          }),
          async ({ formId, fields, audioSyncEnabled }) => {
            // Arrange - Create form with multiple fields
            const formFields: FormField[] = fields.map(f => ({
              id: f.id,
              label: f.label,
              value: '',
              type: 'text' as const,
              required: true,
              ariaLabel: `Enter ${f.label}`
            }));

            const formData: VisualFormDisplay = {
              formId,
              title: 'Test Form',
              description: 'Test',
              fields: formFields,
              currentFieldIndex: 0,
              audioSyncEnabled
            };

            await service.displayFormWithAudio(formData);

            // Act - Update each field
            for (let i = 0; i < fields.length; i++) {
              await service.updateFormField(formId, fields[i].id, fields[i].value);

              // Assert - Property: Field value should be updated
              const updatedForm = await service.getFormDisplay(formId);
              expect(updatedForm).not.toBeNull();
              
              const updatedField = updatedForm!.fields.find(f => f.id === fields[i].id);
              expect(updatedField).toBeDefined();
              expect(updatedField!.value).toBe(fields[i].value);

              // Property: If audio sync enabled and not last field, should announce next field
              if (audioSyncEnabled && i < fields.length - 1) {
                expect(updatedForm!.currentFieldIndex).toBe(i + 1);
                
                const announcements = await service.getScreenReaderAnnouncements(10);
                expect(announcements.length).toBeGreaterThan(0);
              }
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should validate accessibility configuration for any settings', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.record({
            textInputConfig: fc.record({
              enabled: fc.boolean(),
              keyboardType: fc.constantFrom('standard', 'numeric', 'phone'),
              autocomplete: fc.boolean(),
              spellcheck: fc.boolean()
            }),
            transcriptionConfig: fc.record({
              enabled: fc.boolean(),
              liveCaptions: fc.boolean(),
              fontSize: fc.constantFrom('small', 'medium', 'large', 'extra-large'),
              contrastMode: fc.constantFrom('normal', 'high', 'inverted'),
              position: fc.constantFrom('top', 'bottom', 'overlay'),
              maxLines: fc.integer({ min: 1, max: 10 })
            }),
            buttonNavConfig: fc.record({
              enabled: fc.boolean(),
              touchTargetSize: fc.constantFrom('standard', 'large', 'extra-large'),
              spacing: fc.integer({ min: 0, max: 32 }),
              hapticFeedback: fc.boolean(),
              audioFeedback: fc.boolean()
            })
          }),
          async ({ textInputConfig, transcriptionConfig, buttonNavConfig }) => {
            // Act - Validate configurations
            const textInputValid = service.validateTextInputConfig(textInputConfig);
            const transcriptionValid = service.validateTranscriptionConfig(transcriptionConfig);
            const buttonNavValid = service.validateButtonNavigationConfig(buttonNavConfig);

            // Assert - Property: Valid configurations should pass validation
            expect(textInputValid).toBe(true);
            expect(transcriptionValid).toBe(true);
            expect(buttonNavValid).toBe(true);

            // Property: Invalid configurations should fail validation
            const invalidTextInput = { ...textInputConfig, keyboardType: 'invalid' };
            expect(service.validateTextInputConfig(invalidTextInput)).toBe(false);

            const invalidTranscription = { ...transcriptionConfig, fontSize: 'huge' };
            expect(service.validateTranscriptionConfig(invalidTranscription)).toBe(false);

            const invalidButtonNav = { ...buttonNavConfig, spacing: -1 };
            expect(service.validateButtonNavigationConfig(invalidButtonNav)).toBe(false);
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});
