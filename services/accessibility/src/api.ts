/**
 * REST API for Accessibility Service
 * Provides HTTP endpoints for accessibility features
 */

import express, { Request, Response } from 'express';
import { accessibilityService } from './accessibility-service';
import {
  AccessibilityPreferences,
  TextInputEvent,
  CaptionData,
  VisualFormDisplay,
  ScreenReaderAnnouncement,
  AriaAttributes
} from '../../../shared/types/accessibility';

const router = express.Router();

/**
 * GET /preferences/:userId
 * Get accessibility preferences for a user
 */
router.get('/preferences/:userId', async (req: Request, res: Response) => {
  try {
    const { userId } = req.params;
    const preferences = await accessibilityService.getPreferences(userId);
    res.json(preferences);
  } catch (error) {
    res.status(500).json({ error: 'Failed to get preferences' });
  }
});

/**
 * PUT /preferences/:userId
 * Update accessibility preferences for a user
 */
router.put('/preferences/:userId', async (req: Request, res: Response) => {
  try {
    const { userId } = req.params;
    const preferences: Partial<AccessibilityPreferences> = req.body;
    
    await accessibilityService.updatePreferences(userId, preferences);
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: 'Failed to update preferences' });
  }
});

/**
 * POST /text-input
 * Process text input as alternative to voice
 */
router.post('/text-input', async (req: Request, res: Response) => {
  try {
    const event: TextInputEvent = {
      ...req.body,
      timestamp: new Date(req.body.timestamp || Date.now())
    };
    
    await accessibilityService.processTextInput(event);
    res.json({ success: true });
  } catch (error: any) {
    res.status(400).json({ error: error.message || 'Failed to process text input' });
  }
});

/**
 * GET /captions/:sessionId
 * Get live captions for a session
 */
router.get('/captions/:sessionId', async (req: Request, res: Response) => {
  try {
    const { sessionId } = req.params;
    const captions = await accessibilityService.getLiveCaptions(sessionId);
    res.json(captions);
  } catch (error) {
    res.status(500).json({ error: 'Failed to get captions' });
  }
});

/**
 * POST /captions/:sessionId
 * Add a caption for audio output
 */
router.post('/captions/:sessionId', async (req: Request, res: Response) => {
  try {
    const { sessionId } = req.params;
    const caption: CaptionData = {
      ...req.body,
      timestamp: new Date(req.body.timestamp || Date.now())
    };
    
    await accessibilityService.addCaption(sessionId, caption);
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: 'Failed to add caption' });
  }
});

/**
 * DELETE /captions/:sessionId
 * Clear captions for a session
 */
router.delete('/captions/:sessionId', async (req: Request, res: Response) => {
  try {
    const { sessionId } = req.params;
    await accessibilityService.clearCaptions(sessionId);
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: 'Failed to clear captions' });
  }
});

/**
 * GET /buttons/:context
 * Get button navigation interface for current context
 */
router.get('/buttons/:context', async (req: Request, res: Response) => {
  try {
    const { context } = req.params;
    const buttons = await accessibilityService.getButtonNavigation(context);
    res.json(buttons);
  } catch (error) {
    res.status(500).json({ error: 'Failed to get button navigation' });
  }
});

/**
 * POST /apply-visual-settings
 * Apply visual accessibility settings to content
 */
router.post('/apply-visual-settings', async (req: Request, res: Response) => {
  try {
    const { content, settings } = req.body;
    
    if (!content || !settings) {
      return res.status(400).json({ error: 'Content and settings are required' });
    }
    
    const styledContent = await accessibilityService.applyVisualSettings(content, settings);
    res.json({ styledContent });
  } catch (error) {
    res.status(500).json({ error: 'Failed to apply visual settings' });
  }
});

/**
 * GET /health
 * Health check endpoint
 */
router.get('/health', (req: Request, res: Response) => {
  res.json({ status: 'healthy', service: 'accessibility' });
});

/**
 * POST /form-display
 * Display form visually with synchronized audio reading
 */
router.post('/form-display', async (req: Request, res: Response) => {
  try {
    const formData: VisualFormDisplay = req.body;
    
    if (!formData.formId || !formData.fields) {
      return res.status(400).json({ error: 'Form ID and fields are required' });
    }
    
    await accessibilityService.displayFormWithAudio(formData);
    res.json({ success: true });
  } catch (error: any) {
    res.status(400).json({ error: error.message || 'Failed to display form' });
  }
});

/**
 * GET /form-display/:formId
 * Get current form display state
 */
router.get('/form-display/:formId', async (req: Request, res: Response) => {
  try {
    const { formId } = req.params;
    const formDisplay = await accessibilityService.getFormDisplay(formId);
    
    if (!formDisplay) {
      return res.status(404).json({ error: 'Form not found' });
    }
    
    res.json(formDisplay);
  } catch (error) {
    res.status(500).json({ error: 'Failed to get form display' });
  }
});

/**
 * POST /screen-reader/announce
 * Announce message to screen readers
 */
router.post('/screen-reader/announce', async (req: Request, res: Response) => {
  try {
    const announcement: ScreenReaderAnnouncement = {
      ...req.body,
      timestamp: new Date(req.body.timestamp || Date.now())
    };
    
    if (!announcement.text) {
      return res.status(400).json({ error: 'Announcement text is required' });
    }
    
    await accessibilityService.announceToScreenReader(announcement);
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: 'Failed to announce to screen reader' });
  }
});

/**
 * GET /screen-reader/announcements
 * Get recent screen reader announcements
 */
router.get('/screen-reader/announcements', async (req: Request, res: Response) => {
  try {
    const limit = parseInt(req.query.limit as string) || 10;
    const announcements = await accessibilityService.getScreenReaderAnnouncements(limit);
    res.json(announcements);
  } catch (error) {
    res.status(500).json({ error: 'Failed to get announcements' });
  }
});

/**
 * GET /keyboard-navigation
 * Get keyboard navigation configuration
 */
router.get('/keyboard-navigation', async (req: Request, res: Response) => {
  try {
    const config = await accessibilityService.getKeyboardNavigation();
    res.json(config);
  } catch (error) {
    res.status(500).json({ error: 'Failed to get keyboard navigation' });
  }
});

/**
 * PUT /keyboard-navigation
 * Update keyboard navigation configuration
 */
router.put('/keyboard-navigation', async (req: Request, res: Response) => {
  try {
    await accessibilityService.updateKeyboardNavigation(req.body);
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: 'Failed to update keyboard navigation' });
  }
});

/**
 * POST /aria-attributes
 * Generate ARIA attributes for an element
 */
router.post('/aria-attributes', async (req: Request, res: Response) => {
  try {
    const { elementType, context } = req.body;
    
    if (!elementType) {
      return res.status(400).json({ error: 'Element type is required' });
    }
    
    const attributes = await accessibilityService.generateAriaAttributes(elementType, context || {});
    const htmlString = accessibilityService.ariaAttributesToHtml(attributes);
    
    res.json({ attributes, htmlString });
  } catch (error) {
    res.status(500).json({ error: 'Failed to generate ARIA attributes' });
  }
});

export default router;
