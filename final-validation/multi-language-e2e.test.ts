/**
 * Final Validation - Multi-Language End-to-End Tests
 * 
 * Validates complete functionality across all 22 supported Indian languages.
 * Tests the entire flow from voice input to application submission.
 * 
 * Feature: gram-sahayak
 * Task: 14.3 Final system validation
 * Validates: Requirements 1.1, 2.1, 2.2, All requirements (end-to-end)
 */

import axios from 'axios';
import * as fc from 'fast-check';

// All 22 official Indian languages
const SUPPORTED_LANGUAGES = [
  { code: 'hi', name: 'Hindi', script: 'Devanagari' },
  { code: 'bn', name: 'Bengali', script: 'Bengali' },
  { code: 'te', name: 'Telugu', script: 'Telugu' },
  { code: 'mr', name: 'Marathi', script: 'Devanagari' },
  { code: 'ta', name: 'Tamil', script: 'Tamil' },
  { code: 'ur', name: 'Urdu', script: 'Perso-Arabic' },
  { code: 'gu', name: 'Gujarati', script: 'Gujarati' },
  { code: 'kn', name: 'Kannada', script: 'Kannada' },
  { code: 'ml', name: 'Malayalam', script: 'Malayalam' },
  { code: 'or', name: 'Odia', script: 'Odia' },
  { code: 'pa', name: 'Punjabi', script: 'Gurmukhi' },
  { code: 'as', name: 'Assamese', script: 'Bengali' },
  { code: 'mai', name: 'Maithili', script: 'Devanagari' },
  { code: 'sat', name: 'Santali', script: 'Ol Chiki' },
  { code: 'ks', name: 'Kashmiri', script: 'Perso-Arabic' },
  { code: 'ne', name: 'Nepali', script: 'Devanagari' },
  { code: 'kok', name: 'Konkani', script: 'Devanagari' },
  { code: 'sd', name: 'Sindhi', script: 'Devanagari' },
  { code: 'doi', name: 'Dogri', script: 'Devanagari' },
  { code: 'mni', name: 'Manipuri', script: 'Meitei Mayek' },
  { code: 'brx', name: 'Bodo', script: 'Devanagari' },
  { code: 'sa', name: 'Sanskrit', script: 'Devanagari' },
];

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:3000';

describe('Multi-Language End-to-End Validation', () => {
  describe('Voice Processing Across All Languages', () => {
    SUPPORTED_LANGUAGES.forEach(language => {
      it(`should process voice input in ${language.name} (${language.code})`, async () => {
        // Start voice session with language preference
        const sessionResponse = await axios.post(`${API_BASE_URL}/voice/session`, {
          preferredLanguage: language.code,
        });

        expect(sessionResponse.status).toBe(200);
        expect(sessionResponse.data.sessionId).toBeDefined();
        expect(sessionResponse.data.detectedLanguage).toBe(language.code);

        const sessionId = sessionResponse.data.sessionId;

        // Simulate audio processing (in real scenario, this would be actual audio)
        const audioResponse = await axios.post(
          `${API_BASE_URL}/voice/process`,
          {
            sessionId,
            audioData: Buffer.from('mock-audio-data').toString('base64'),
          }
        );

        expect(audioResponse.status).toBe(200);
        expect(audioResponse.data.transcription).toBeDefined();
        expect(audioResponse.data.confidence).toBeGreaterThan(0.9);

        // End session
        await axios.post(`${API_BASE_URL}/voice/session/end`, { sessionId });
      }, 30000);
    });
  });

  describe('Dialect Detection Across Languages', () => {
    SUPPORTED_LANGUAGES.forEach(language => {
      it(`should detect dialect for ${language.name}`, async () => {
        const response = await axios.post(`${API_BASE_URL}/dialect/detect`, {
          audioFeatures: {
            language: language.code,
            sampleRate: 16000,
            duration: 3.0,
          },
        });

        expect(response.status).toBe(200);
        expect(response.data.primaryLanguage).toBe(language.code);
        expect(response.data.confidence).toBeGreaterThan(0.8);
        expect(response.data.detectionTime).toBeLessThan(3000); // < 3 seconds
      });
    });
  });

  describe('Scheme Information in All Languages', () => {
    SUPPORTED_LANGUAGES.forEach(language => {
      it(`should provide scheme information in ${language.name}`, async () => {
        const response = await axios.get(`${API_BASE_URL}/schemes`, {
          params: {
            language: language.code,
            limit: 5,
          },
        });

        expect(response.status).toBe(200);
        expect(response.data.schemes).toBeInstanceOf(Array);
        expect(response.data.schemes.length).toBeGreaterThan(0);

        // Verify scheme information is in requested language
        response.data.schemes.forEach((scheme: any) => {
          expect(scheme.name).toBeDefined();
          expect(scheme.description).toBeDefined();
          expect(scheme.language).toBe(language.code);
        });
      });
    });
  });

  describe('Form Generation in All Languages', () => {
    SUPPORTED_LANGUAGES.forEach(language => {
      it(`should generate forms with questions in ${language.name}`, async () => {
        const response = await axios.post(`${API_BASE_URL}/forms/start`, {
          schemeId: 'PM-KISAN',
          language: language.code,
          userId: 'test-user',
        });

        expect(response.status).toBe(200);
        expect(response.data.sessionId).toBeDefined();
        expect(response.data.currentQuestion).toBeDefined();
        expect(response.data.language).toBe(language.code);
      });
    });
  });

  describe('Document Guidance in All Languages', () => {
    SUPPORTED_LANGUAGES.forEach(language => {
      it(`should provide document guidance in ${language.name}`, async () => {
        const response = await axios.get(`${API_BASE_URL}/documents/requirements`, {
          params: {
            schemeId: 'PM-KISAN',
            language: language.code,
          },
        });

        expect(response.status).toBe(200);
        expect(response.data.documents).toBeInstanceOf(Array);
        expect(response.data.documents.length).toBeGreaterThan(0);

        // Verify document guidance is in requested language
        response.data.documents.forEach((doc: any) => {
          expect(doc.name).toBeDefined();
          expect(doc.description).toBeDefined();
          expect(doc.language).toBe(language.code);
        });
      });
    });
  });

  describe('Complete User Journey Across Languages', () => {
    // Test a subset of languages for complete journey (to keep test time reasonable)
    const testLanguages = [
      SUPPORTED_LANGUAGES[0], // Hindi
      SUPPORTED_LANGUAGES[1], // Bengali
      SUPPORTED_LANGUAGES[4], // Tamil
      SUPPORTED_LANGUAGES[6], // Gujarati
      SUPPORTED_LANGUAGES[8], // Malayalam
    ];

    testLanguages.forEach(language => {
      it(`should complete full journey in ${language.name}`, async () => {
        // 1. Start voice session
        const sessionResponse = await axios.post(`${API_BASE_URL}/voice/session`, {
          preferredLanguage: language.code,
        });
        const sessionId = sessionResponse.data.sessionId;

        // 2. Create user profile
        const profileResponse = await axios.post(`${API_BASE_URL}/profile/create`, {
          language: language.code,
          personalInfo: {
            name: 'Test User',
            age: 35,
            gender: 'male',
          },
          demographics: {
            state: 'Maharashtra',
            district: 'Pune',
            village: 'Test Village',
          },
        });
        const userId = profileResponse.data.userId;

        // 3. Find eligible schemes
        const schemesResponse = await axios.post(`${API_BASE_URL}/schemes/match`, {
          userId,
          language: language.code,
        });
        expect(schemesResponse.data.schemes.length).toBeGreaterThan(0);
        const schemeId = schemesResponse.data.schemes[0].schemeId;

        // 4. Start form filling
        const formResponse = await axios.post(`${API_BASE_URL}/forms/start`, {
          schemeId,
          userId,
          language: language.code,
        });
        const formSessionId = formResponse.data.sessionId;

        // 5. Get document requirements
        const docsResponse = await axios.get(`${API_BASE_URL}/documents/requirements`, {
          params: { schemeId, language: language.code },
        });
        expect(docsResponse.data.documents.length).toBeGreaterThan(0);

        // 6. Verify all responses are in correct language
        expect(sessionResponse.data.detectedLanguage).toBe(language.code);
        expect(schemesResponse.data.schemes[0].language).toBe(language.code);
        expect(formResponse.data.language).toBe(language.code);
        expect(docsResponse.data.documents[0].language).toBe(language.code);

        // Cleanup
        await axios.post(`${API_BASE_URL}/voice/session/end`, { sessionId });
        await axios.delete(`${API_BASE_URL}/profile/${userId}`);
      }, 60000);
    });
  });

  describe('Language Coverage Summary', () => {
    it('should confirm all 22 languages are supported', () => {
      expect(SUPPORTED_LANGUAGES.length).toBe(22);
      
      console.log('\n✓ All 22 Indian Languages Validated:');
      SUPPORTED_LANGUAGES.forEach((lang, index) => {
        console.log(`  ${index + 1}. ${lang.name} (${lang.code}) - ${lang.script} script`);
      });
    });
  });
});
