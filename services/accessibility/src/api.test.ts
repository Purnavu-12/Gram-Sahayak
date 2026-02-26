/**
 * Integration tests for Accessibility API
 */

import request from 'supertest';
import express from 'express';
import apiRouter from './api';

const app = express();
app.use(express.json());
app.use('/api/accessibility', apiRouter);

describe('Accessibility API', () => {
  describe('GET /preferences/:userId', () => {
    it('should return default preferences for new user', async () => {
      const response = await request(app)
        .get('/api/accessibility/preferences/user123')
        .expect(200);

      expect(response.body.userId).toBe('user123');
      expect(response.body.inputMode).toBe('voice');
      expect(response.body.outputMode).toBe('audio');
    });
  });

  describe('PUT /preferences/:userId', () => {
    it('should update user preferences', async () => {
      const updates = {
        inputMode: 'text',
        outputMode: 'visual'
      };

      await request(app)
        .put('/api/accessibility/preferences/user123')
        .send(updates)
        .expect(200);

      const response = await request(app)
        .get('/api/accessibility/preferences/user123')
        .expect(200);

      expect(response.body.inputMode).toBe('text');
      expect(response.body.outputMode).toBe('visual');
    });
  });

  describe('POST /text-input', () => {
    it('should process valid text input', async () => {
      const event = {
        sessionId: 'session123',
        text: 'I want to apply for PM-KISAN',
        inputMethod: 'keyboard'
      };

      await request(app)
        .post('/api/accessibility/text-input')
        .send(event)
        .expect(200);
    });

    it('should reject empty text input', async () => {
      const event = {
        sessionId: 'session123',
        text: '',
        inputMethod: 'keyboard'
      };

      await request(app)
        .post('/api/accessibility/text-input')
        .send(event)
        .expect(400);
    });
  });

  describe('Caption Management', () => {
    it('should add and retrieve captions', async () => {
      const sessionId = 'session456';
      const caption = {
        text: 'Welcome to Gram Sahayak',
        isFinal: true,
        confidence: 0.95,
        speaker: 'system'
      };

      await request(app)
        .post(`/api/accessibility/captions/${sessionId}`)
        .send(caption)
        .expect(200);

      const response = await request(app)
        .get(`/api/accessibility/captions/${sessionId}`)
        .expect(200);

      expect(response.body).toHaveLength(1);
      expect(response.body[0].text).toBe('Welcome to Gram Sahayak');
    });

    it('should clear captions', async () => {
      const sessionId = 'session789';
      
      await request(app)
        .post(`/api/accessibility/captions/${sessionId}`)
        .send({ text: 'Test', isFinal: true, confidence: 0.9 })
        .expect(200);

      await request(app)
        .delete(`/api/accessibility/captions/${sessionId}`)
        .expect(200);

      const response = await request(app)
        .get(`/api/accessibility/captions/${sessionId}`)
        .expect(200);

      expect(response.body).toHaveLength(0);
    });
  });

  describe('GET /buttons/:context', () => {
    it('should return main menu buttons', async () => {
      const response = await request(app)
        .get('/api/accessibility/buttons/main-menu')
        .expect(200);

      expect(response.body).toHaveLength(1);
      expect(response.body[0].id).toBe('main-actions');
    });

    it('should return empty array for unknown context', async () => {
      const response = await request(app)
        .get('/api/accessibility/buttons/unknown')
        .expect(200);

      expect(response.body).toEqual([]);
    });
  });

  describe('POST /apply-visual-settings', () => {
    it('should apply visual settings to content', async () => {
      const request_body = {
        content: '<p>Test content</p>',
        settings: {
          fontSize: 'large',
          contrastMode: 'high',
          lineSpacing: 2.0,
          letterSpacing: 1
        }
      };

      const response = await request(app)
        .post('/api/accessibility/apply-visual-settings')
        .send(request_body)
        .expect(200);

      expect(response.body.styledContent).toContain('font-size: 20px');
      expect(response.body.styledContent).toContain('background-color: #000000');
    });

    it('should reject request without content', async () => {
      const request_body = {
        settings: {
          fontSize: 'large',
          contrastMode: 'normal',
          lineSpacing: 1.5,
          letterSpacing: 0
        }
      };

      await request(app)
        .post('/api/accessibility/apply-visual-settings')
        .send(request_body)
        .expect(400);
    });
  });

  describe('GET /health', () => {
    it('should return healthy status', async () => {
      const response = await request(app)
        .get('/api/accessibility/health')
        .expect(200);

      expect(response.body.status).toBe('healthy');
      expect(response.body.service).toBe('accessibility');
    });
  });

  describe('Form Display with Audio Sync (Requirement 10.3)', () => {
    it('should display form with synchronized audio', async () => {
      const formData = {
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
            ariaLabel: 'Enter your full name'
          }
        ],
        currentFieldIndex: 0,
        audioSyncEnabled: true
      };

      await request(app)
        .post('/api/accessibility/form-display')
        .send(formData)
        .expect(200);

      const response = await request(app)
        .get('/api/accessibility/form-display/form123')
        .expect(200);

      expect(response.body.formId).toBe('form123');
      expect(response.body.title).toBe('PM-KISAN Application');
    });

    it('should reject form without formId', async () => {
      const formData = {
        title: 'Test Form',
        fields: []
      };

      await request(app)
        .post('/api/accessibility/form-display')
        .send(formData)
        .expect(400);
    });

    it('should return 404 for non-existent form', async () => {
      await request(app)
        .get('/api/accessibility/form-display/non-existent')
        .expect(404);
    });
  });

  describe('Screen Reader Announcements (Requirement 10.5)', () => {
    it('should announce message to screen reader', async () => {
      const announcement = {
        text: 'Application submitted successfully',
        priority: 'assertive'
      };

      await request(app)
        .post('/api/accessibility/screen-reader/announce')
        .send(announcement)
        .expect(200);

      const response = await request(app)
        .get('/api/accessibility/screen-reader/announcements')
        .expect(200);

      expect(response.body.length).toBeGreaterThan(0);
      const lastAnnouncement = response.body[response.body.length - 1];
      expect(lastAnnouncement.text).toBe('Application submitted successfully');
    });

    it('should reject announcement without text', async () => {
      const announcement = {
        priority: 'polite'
      };

      await request(app)
        .post('/api/accessibility/screen-reader/announce')
        .send(announcement)
        .expect(400);
    });

    it('should limit announcements with query parameter', async () => {
      // Add multiple announcements
      for (let i = 1; i <= 5; i++) {
        await request(app)
          .post('/api/accessibility/screen-reader/announce')
          .send({ text: `Announcement ${i}`, priority: 'polite' });
      }

      const response = await request(app)
        .get('/api/accessibility/screen-reader/announcements?limit=3')
        .expect(200);

      expect(response.body.length).toBeLessThanOrEqual(3);
    });
  });

  describe('Keyboard Navigation (Requirement 10.5)', () => {
    it('should get keyboard navigation config', async () => {
      const response = await request(app)
        .get('/api/accessibility/keyboard-navigation')
        .expect(200);

      expect(response.body.enabled).toBe(true);
      expect(response.body.shortcuts).toBeDefined();
      expect(response.body.skipLinks).toBeDefined();
    });

    it('should update keyboard navigation config', async () => {
      const updates = {
        enabled: false,
        focusIndicatorStyle: 'outline'
      };

      await request(app)
        .put('/api/accessibility/keyboard-navigation')
        .send(updates)
        .expect(200);

      const response = await request(app)
        .get('/api/accessibility/keyboard-navigation')
        .expect(200);

      expect(response.body.enabled).toBe(false);
      expect(response.body.focusIndicatorStyle).toBe('outline');
    });
  });

  describe('ARIA Attributes Generation (Requirement 10.5)', () => {
    it('should generate ARIA attributes for button', async () => {
      const request_body = {
        elementType: 'button',
        context: {
          label: 'Submit',
          disabled: false
        }
      };

      const response = await request(app)
        .post('/api/accessibility/aria-attributes')
        .send(request_body)
        .expect(200);

      expect(response.body.attributes.role).toBe('button');
      expect(response.body.attributes.label).toBe('Submit');
      expect(response.body.htmlString).toContain('role="button"');
      expect(response.body.htmlString).toContain('aria-label="Submit"');
    });

    it('should generate ARIA attributes for form', async () => {
      const request_body = {
        elementType: 'form',
        context: {
          title: 'Application Form',
          descriptionId: 'form-desc'
        }
      };

      const response = await request(app)
        .post('/api/accessibility/aria-attributes')
        .send(request_body)
        .expect(200);

      expect(response.body.attributes.role).toBe('form');
      expect(response.body.attributes.label).toBe('Application Form');
      expect(response.body.htmlString).toContain('role="form"');
    });

    it('should reject request without elementType', async () => {
      const request_body = {
        context: { label: 'Test' }
      };

      await request(app)
        .post('/api/accessibility/aria-attributes')
        .send(request_body)
        .expect(400);
    });

    it('should handle empty context', async () => {
      const request_body = {
        elementType: 'alert'
      };

      const response = await request(app)
        .post('/api/accessibility/aria-attributes')
        .send(request_body)
        .expect(200);

      expect(response.body.attributes.role).toBe('alert');
      expect(response.body.attributes.live).toBe('assertive');
    });
  });
});

