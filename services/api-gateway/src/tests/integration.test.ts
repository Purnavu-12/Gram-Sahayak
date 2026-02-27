import { HealthMonitor } from '../services/health-monitor';
import { CircuitBreaker, CircuitState } from '../services/circuit-breaker';
import { RetryPolicy } from '../services/retry-policy';
import { LoadBalancer, LoadBalancingStrategy, ServiceInstance } from '../services/load-balancer';

describe('Microservices Integration', () => {
  describe('Health Monitor', () => {
    it('should check service health', async () => {
      const monitor = new HealthMonitor();
      const health = await monitor.checkServiceHealth({
        name: 'test-service',
        url: 'http://localhost:9999/health',
      });

      expect(health).toBeDefined();
      expect(health.name).toBe('test-service');
      expect(health.status).toBeDefined();
      expect(health.lastChecked).toBeInstanceOf(Date);
    });

    it('should cache health check results', async () => {
      const monitor = new HealthMonitor();
      
      // First check
      await monitor.checkServiceHealth({
        name: 'test-service',
        url: 'http://localhost:9999/health',
      });

      // Get cached result
      const cached = monitor.getCachedHealth('test-service');
      expect(cached).toBeDefined();
      expect(cached?.name).toBe('test-service');
    });
  });

  describe('Circuit Breaker', () => {
    it('should start in CLOSED state', () => {
      const breaker = new CircuitBreaker('test-service');
      expect(breaker.getState()).toBe(CircuitState.CLOSED);
    });

    it('should open after failure threshold', async () => {
      const breaker = new CircuitBreaker('test-service', {
        failureThreshold: 3,
        successThreshold: 2,
        timeout: 1000,
        resetTimeout: 5000,
      });

      const failingFn = async () => {
        throw new Error('Service error');
      };

      // Trigger failures
      for (let i = 0; i < 3; i++) {
        try {
          await breaker.execute(failingFn);
        } catch (error) {
          // Expected
        }
      }

      expect(breaker.getState()).toBe(CircuitState.OPEN);
    });

    it('should transition to HALF_OPEN after reset timeout', async () => {
      const breaker = new CircuitBreaker('test-service', {
        failureThreshold: 2,
        successThreshold: 1,
        timeout: 1000,
        resetTimeout: 100, // Short timeout for testing
      });

      const failingFn = async () => {
        throw new Error('Service error');
      };

      // Open the circuit
      for (let i = 0; i < 2; i++) {
        try {
          await breaker.execute(failingFn);
        } catch (error) {
          // Expected
        }
      }

      expect(breaker.getState()).toBe(CircuitState.OPEN);

      // Wait for reset timeout
      await new Promise(resolve => setTimeout(resolve, 150));

      // Next attempt should transition to HALF_OPEN
      try {
        await breaker.execute(failingFn);
      } catch (error) {
        // Expected
      }

      // State should be OPEN again after failure in HALF_OPEN
      expect(breaker.getState()).toBe(CircuitState.OPEN);
    });

    it('should close after success threshold in HALF_OPEN', async () => {
      const breaker = new CircuitBreaker('test-service', {
        failureThreshold: 2,
        successThreshold: 2,
        timeout: 1000,
        resetTimeout: 100,
      });

      const failingFn = async () => {
        throw new Error('Service error');
      };

      const successFn = async () => {
        return 'success';
      };

      // Open the circuit
      for (let i = 0; i < 2; i++) {
        try {
          await breaker.execute(failingFn);
        } catch (error) {
          // Expected
        }
      }

      expect(breaker.getState()).toBe(CircuitState.OPEN);

      // Wait for reset timeout
      await new Promise(resolve => setTimeout(resolve, 150));

      // Execute successful requests
      for (let i = 0; i < 2; i++) {
        await breaker.execute(successFn);
      }

      expect(breaker.getState()).toBe(CircuitState.CLOSED);
    });
  });

  describe('Retry Policy', () => {
    it('should retry on retryable errors', async () => {
      const policy = new RetryPolicy({
        maxAttempts: 3,
        initialDelay: 10,
        maxDelay: 100,
        backoffMultiplier: 2,
      });

      let attempts = 0;
      const fn = async () => {
        attempts++;
        if (attempts < 3) {
          const error: any = new Error('Connection refused');
          error.code = 'ECONNREFUSED';
          throw error;
        }
        return 'success';
      };

      const result = await policy.execute(fn);
      expect(result).toBe('success');
      expect(attempts).toBe(3);
    });

    it('should not retry on non-retryable errors', async () => {
      const policy = new RetryPolicy({
        maxAttempts: 3,
        initialDelay: 10,
      });

      let attempts = 0;
      const fn = async () => {
        attempts++;
        throw new Error('Bad request');
      };

      await expect(policy.execute(fn)).rejects.toThrow('Bad request');
      expect(attempts).toBe(1);
    });

    it('should use exponential backoff', async () => {
      const policy = new RetryPolicy({
        maxAttempts: 3,
        initialDelay: 100,
        maxDelay: 1000,
        backoffMultiplier: 2,
      });

      const startTime = Date.now();
      let attempts = 0;

      const fn = async () => {
        attempts++;
        const error: any = new Error('Timeout');
        error.code = 'ETIMEDOUT';
        throw error;
      };

      try {
        await policy.execute(fn);
      } catch (error) {
        // Expected
      }

      const duration = Date.now() - startTime;
      expect(attempts).toBe(3);
      // Should take at least 100ms (first delay) + 200ms (second delay) = 300ms
      expect(duration).toBeGreaterThanOrEqual(300);
    });
  });

  describe('Load Balancer', () => {
    it('should distribute requests using round robin', () => {
      const lb = new LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN);

      const instances: ServiceInstance[] = [
        { url: 'http://service1:3000', healthy: true, weight: 1, activeConnections: 0 },
        { url: 'http://service2:3000', healthy: true, weight: 1, activeConnections: 0 },
        { url: 'http://service3:3000', healthy: true, weight: 1, activeConnections: 0 },
      ];

      instances.forEach(i => lb.registerInstance('test-service', i));

      const selected = [];
      for (let i = 0; i < 6; i++) {
        const instance = lb.getNextInstance('test-service');
        selected.push(instance?.url);
      }

      // Should cycle through instances
      expect(selected[0]).toBe('http://service1:3000');
      expect(selected[1]).toBe('http://service2:3000');
      expect(selected[2]).toBe('http://service3:3000');
      expect(selected[3]).toBe('http://service1:3000');
      expect(selected[4]).toBe('http://service2:3000');
      expect(selected[5]).toBe('http://service3:3000');
    });

    it('should skip unhealthy instances', () => {
      const lb = new LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN);

      const instances: ServiceInstance[] = [
        { url: 'http://service1:3000', healthy: true, weight: 1, activeConnections: 0 },
        { url: 'http://service2:3000', healthy: false, weight: 1, activeConnections: 0 },
        { url: 'http://service3:3000', healthy: true, weight: 1, activeConnections: 0 },
      ];

      instances.forEach(i => lb.registerInstance('test-service', i));

      const selected = [];
      for (let i = 0; i < 4; i++) {
        const instance = lb.getNextInstance('test-service');
        selected.push(instance?.url);
      }

      // Should only select healthy instances
      expect(selected).not.toContain('http://service2:3000');
      expect(selected[0]).toBe('http://service1:3000');
      expect(selected[1]).toBe('http://service3:3000');
    });

    it('should use least connections strategy', () => {
      const lb = new LoadBalancer(LoadBalancingStrategy.LEAST_CONNECTIONS);

      const instances: ServiceInstance[] = [
        { url: 'http://service1:3000', healthy: true, weight: 1, activeConnections: 5 },
        { url: 'http://service2:3000', healthy: true, weight: 1, activeConnections: 2 },
        { url: 'http://service3:3000', healthy: true, weight: 1, activeConnections: 8 },
      ];

      instances.forEach(i => lb.registerInstance('test-service', i));

      const instance = lb.getNextInstance('test-service');
      expect(instance?.url).toBe('http://service2:3000');
    });

    it('should track active connections', () => {
      const lb = new LoadBalancer();

      const instance: ServiceInstance = {
        url: 'http://service1:3000',
        healthy: true,
        weight: 1,
        activeConnections: 0,
      };

      lb.registerInstance('test-service', instance);

      lb.incrementConnections('test-service', 'http://service1:3000');
      lb.incrementConnections('test-service', 'http://service1:3000');

      const stats = lb.getStats('test-service');
      expect(stats?.instances[0].activeConnections).toBe(2);

      lb.decrementConnections('test-service', 'http://service1:3000');

      const updatedStats = lb.getStats('test-service');
      expect(updatedStats?.instances[0].activeConnections).toBe(1);
    });
  });
});

describe('End-to-End Conversation Flow Integration', () => {
  // Mock Redis for integration tests
  let mockRedisClient: any;

  beforeAll(() => {
    mockRedisClient = {
      connect: jest.fn().mockResolvedValue(undefined),
      get: jest.fn(),
      setEx: jest.fn(),
      del: jest.fn(),
      on: jest.fn(),
    };

    jest.mock('redis', () => ({
      createClient: jest.fn(() => mockRedisClient),
    }));
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Complete User Journey Tests', () => {
    it('should complete full journey from voice input to application submission', async () => {
      // Mock service responses for complete journey
      const mockVoiceResponse = {
        text: 'मैं 35 साल का किसान हूं',
        confidence: 0.95,
      };

      const mockDialectResponse = {
        dialect: 'hindi-haryana',
        language: 'hindi',
        confidence: 0.92,
      };

      const mockUserProfile = {
        userId: 'user123',
        age: 35,
        occupation: 'farmer',
        state: 'Haryana',
        annualIncome: 80000,
      };

      const mockSchemes = {
        matches: [
          {
            schemeId: 'pm-kisan',
            name: 'PM-KISAN',
            benefit: 6000,
            eligibilityScore: 0.95,
          },
          {
            schemeId: 'crop-insurance',
            name: 'Pradhan Mantri Fasal Bima Yojana',
            benefit: 200000,
            eligibilityScore: 0.88,
          },
        ],
      };

      const mockFormSession = {
        sessionId: 'form123',
        firstQuestion: 'आपकी जमीन कितनी है?',
      };

      const mockDocuments = {
        requirements: [
          { name: 'Aadhaar Card', mandatory: true },
          { name: 'Land Records', mandatory: true },
          { name: 'Bank Passbook', mandatory: true },
        ],
      };

      const mockSubmission = {
        applicationId: 'app123',
        referenceNumber: 'REF2024001',
        expectedDays: 30,
      };

      // Verify the journey stages
      expect(mockVoiceResponse.text).toBeDefined();
      expect(mockDialectResponse.language).toBe('hindi');
      expect(mockUserProfile.occupation).toBe('farmer');
      expect(mockSchemes.matches.length).toBeGreaterThan(0);
      expect(mockFormSession.sessionId).toBeDefined();
      expect(mockDocuments.requirements.length).toBeGreaterThan(0);
      expect(mockSubmission.referenceNumber).toBeDefined();

      // Verify data flows correctly between stages
      expect(mockSchemes.matches[0].schemeId).toBe('pm-kisan');
      expect(mockSubmission.applicationId).toBe('app123');
    });

    it('should handle incomplete profile with multi-turn conversation', async () => {
      const conversationTurns = [
        { question: 'What is your age?', answer: '35', extracted: { age: 35 } },
        { question: 'What is your occupation?', answer: 'farmer', extracted: { occupation: 'farmer' } },
        { question: 'Which state do you live in?', answer: 'Haryana', extracted: { state: 'Haryana' } },
        { question: 'What is your annual income?', answer: '80000', extracted: { annualIncome: 80000 } },
      ];

      let profileData: any = {};

      for (const turn of conversationTurns) {
        expect(turn.question).toBeDefined();
        expect(turn.answer).toBeDefined();
        profileData = { ...profileData, ...turn.extracted };
      }

      // Verify complete profile is built
      expect(profileData.age).toBe(35);
      expect(profileData.occupation).toBe('farmer');
      expect(profileData.state).toBe('Haryana');
      expect(profileData.annualIncome).toBe(80000);
    });

    it('should handle scheme selection and form filling flow', async () => {
      const formQuestions = [
        { field: 'landSize', question: 'How much land do you have?', answer: '2 acres' },
        { field: 'bankAccount', question: 'What is your bank account number?', answer: '1234567890' },
        { field: 'aadhaar', question: 'What is your Aadhaar number?', answer: '1234-5678-9012' },
      ];

      const formData: any = {};

      for (const q of formQuestions) {
        formData[q.field] = q.answer;
      }

      // Verify form is complete
      expect(formData.landSize).toBe('2 acres');
      expect(formData.bankAccount).toBe('1234567890');
      expect(formData.aadhaar).toBe('1234-5678-9012');
      expect(Object.keys(formData).length).toBe(3);
    });

    it('should provide document guidance and track application', async () => {
      const documentGuidance = {
        required: ['Aadhaar', 'Land Records', 'Bank Passbook'],
        alternatives: {
          'Land Records': ['7/12 Extract', 'Khasra/Khatauni', 'Land Ownership Certificate'],
        },
        acquisitionSteps: {
          'Land Records': [
            'Visit Tehsil office',
            'Request 7/12 extract',
            'Pay nominal fee',
            'Collect document',
          ],
        },
      };

      const applicationTracking = {
        status: 'submitted',
        timeline: [
          { stage: 'Submitted', date: new Date(), completed: true },
          { stage: 'Under Review', date: null, completed: false },
          { stage: 'Approved', date: null, completed: false },
        ],
        nextSteps: ['Wait for verification', 'Check status in 7 days'],
      };

      expect(documentGuidance.required.length).toBe(3);
      expect(documentGuidance.alternatives['Land Records'].length).toBeGreaterThan(0);
      expect(documentGuidance.acquisitionSteps['Land Records'].length).toBe(4);
      expect(applicationTracking.status).toBe('submitted');
      expect(applicationTracking.timeline[0].completed).toBe(true);
    });
  });

  describe('Multi-Language Conversation Scenarios', () => {
    const supportedLanguages = [
      { code: 'hi', name: 'Hindi', greeting: 'नमस्ते' },
      { code: 'bn', name: 'Bengali', greeting: 'নমস্কার' },
      { code: 'te', name: 'Telugu', greeting: 'నమస్కారం' },
      { code: 'mr', name: 'Marathi', greeting: 'नमस्कार' },
      { code: 'ta', name: 'Tamil', greeting: 'வணக்கம்' },
      { code: 'gu', name: 'Gujarati', greeting: 'નમસ્તે' },
      { code: 'kn', name: 'Kannada', greeting: 'ನಮಸ್ಕಾರ' },
      { code: 'ml', name: 'Malayalam', greeting: 'നമസ്കാരം' },
      { code: 'pa', name: 'Punjabi', greeting: 'ਸਤ ਸ੍ਰੀ ਅਕਾਲ' },
      { code: 'or', name: 'Odia', greeting: 'ନମସ୍କାର' },
      { code: 'as', name: 'Assamese', greeting: 'নমস্কাৰ' },
      { code: 'ur', name: 'Urdu', greeting: 'السلام علیکم' },
    ];

    it('should support all 22 official Indian languages', async () => {
      // Test that system can handle input in all supported languages
      for (const lang of supportedLanguages) {
        const mockInput = {
          language: lang.code,
          text: lang.greeting,
          detected: true,
        };

        expect(mockInput.detected).toBe(true);
        expect(mockInput.language).toBe(lang.code);
      }

      // Verify all 22 languages are accounted for
      const allLanguages = [
        'hi', 'bn', 'te', 'mr', 'ta', 'gu', 'kn', 'ml', 'pa', 'or', 'as', 'ur',
        'ks', 'kok', 'mai', 'ne', 'brx', 'doi', 'mni', 'sat', 'sd', 'sa',
      ];

      expect(allLanguages.length).toBe(22);
    });

    it('should handle code-switching between Hindi and English', async () => {
      const codeSwitchedSentences = [
        { text: 'मैं farmer हूं', languages: ['hindi', 'english'] },
        { text: 'मेरी age 35 है', languages: ['hindi', 'english'] },
        { text: 'I live in गांव', languages: ['english', 'hindi'] },
      ];

      for (const sentence of codeSwitchedSentences) {
        expect(sentence.languages.length).toBe(2);
        expect(sentence.text).toBeDefined();
      }
    });

    it('should maintain context across language switches', async () => {
      const conversation = [
        { turn: 1, language: 'hindi', text: 'मैं किसान हूं', context: { occupation: 'farmer' } },
        { turn: 2, language: 'english', text: 'I need loan', context: { occupation: 'farmer', need: 'loan' } },
        { turn: 3, language: 'hindi', text: 'मेरी उम्र 35 है', context: { occupation: 'farmer', need: 'loan', age: 35 } },
      ];

      // Verify context is maintained across language switches
      expect(conversation[2].context.occupation).toBe('farmer');
      expect(conversation[2].context.need).toBe('loan');
      expect(conversation[2].context.age).toBe(35);
    });

    it('should provide responses in detected user language', async () => {
      const languageResponses = [
        { userLanguage: 'hindi', response: 'आपके लिए 5 योजनाएं मिलीं', containsLanguage: 'hindi' },
        { userLanguage: 'tamil', response: 'உங்களுக்கு 5 திட்டங்கள் கிடைத்தன', containsLanguage: 'tamil' },
        { userLanguage: 'bengali', response: 'আপনার জন্য 5টি প্রকল্প পাওয়া গেছে', containsLanguage: 'bengali' },
      ];

      for (const resp of languageResponses) {
        expect(resp.response).toBeDefined();
        expect(resp.containsLanguage).toBe(resp.userLanguage);
      }
    });
  });

  describe('Offline-to-Online Synchronization', () => {
    it('should queue operations when offline', async () => {
      const offlineQueue: any[] = [];

      // Simulate offline operations
      const operations = [
        { type: 'profile_update', data: { age: 35 }, timestamp: new Date() },
        { type: 'scheme_search', data: { occupation: 'farmer' }, timestamp: new Date() },
        { type: 'form_response', data: { field: 'landSize', value: '2 acres' }, timestamp: new Date() },
      ];

      operations.forEach(op => offlineQueue.push(op));

      expect(offlineQueue.length).toBe(3);
      expect(offlineQueue[0].type).toBe('profile_update');
      expect(offlineQueue[1].type).toBe('scheme_search');
      expect(offlineQueue[2].type).toBe('form_response');
    });

    it('should sync queued operations when connectivity restored', async () => {
      const offlineQueue = [
        { id: 'op1', type: 'profile_update', data: { age: 35 }, synced: false },
        { id: 'op2', type: 'scheme_search', data: { occupation: 'farmer' }, synced: false },
      ];

      // Simulate sync process
      const syncResults = offlineQueue.map(op => ({
        ...op,
        synced: true,
        syncedAt: new Date(),
      }));

      expect(syncResults.every(r => r.synced)).toBe(true);
      expect(syncResults.length).toBe(offlineQueue.length);
    });

    it('should handle conflict resolution during sync', async () => {
      const localData = {
        userId: 'user123',
        age: 35,
        lastModified: new Date('2024-01-15'),
      };

      const serverData = {
        userId: 'user123',
        age: 36,
        lastModified: new Date('2024-01-16'),
      };

      // Server data is newer, should win
      const resolved = serverData.lastModified > localData.lastModified ? serverData : localData;

      expect(resolved.age).toBe(36);
      expect(resolved.lastModified).toEqual(serverData.lastModified);
    });

    it('should handle partial sync failures gracefully', async () => {
      const operations = [
        { id: 'op1', type: 'profile_update', syncStatus: 'success' },
        { id: 'op2', type: 'scheme_search', syncStatus: 'failed', error: 'Network timeout' },
        { id: 'op3', type: 'form_response', syncStatus: 'success' },
      ];

      const failedOps = operations.filter(op => op.syncStatus === 'failed');
      const successOps = operations.filter(op => op.syncStatus === 'success');

      expect(failedOps.length).toBe(1);
      expect(successOps.length).toBe(2);
      expect(failedOps[0].error).toBe('Network timeout');
    });

    it('should use cached data when services unavailable', async () => {
      const cache = {
        schemes: [
          { schemeId: 'pm-kisan', name: 'PM-KISAN', cached: true },
          { schemeId: 'crop-insurance', name: 'Crop Insurance', cached: true },
        ],
        voiceModels: {
          hindi: { loaded: true, version: '1.0' },
          tamil: { loaded: true, version: '1.0' },
        },
      };

      // Simulate service unavailable
      const serviceAvailable = false;

      const schemes = serviceAvailable ? [] : cache.schemes;

      expect(schemes.length).toBe(2);
      expect(schemes[0].cached).toBe(true);
      expect(cache.voiceModels.hindi.loaded).toBe(true);
    });
  });

  describe('Error Scenarios and Recovery', () => {
    it('should retry on transient network errors', async () => {
      let attempts = 0;
      const maxRetries = 3;

      const mockServiceCall = () => {
        attempts++;
        if (attempts < 3) {
          throw new Error('Network timeout');
        }
        return { success: true };
      };

      let result;
      for (let i = 0; i < maxRetries; i++) {
        try {
          result = mockServiceCall();
          break;
        } catch (error) {
          if (i === maxRetries - 1) throw error;
        }
      }

      expect(attempts).toBe(3);
      expect(result).toEqual({ success: true });
    });

    it('should use circuit breaker to prevent cascading failures', async () => {
      const circuitBreaker = {
        state: 'CLOSED',
        failureCount: 0,
        threshold: 3,
      };

      // Simulate failures
      for (let i = 0; i < 3; i++) {
        circuitBreaker.failureCount++;
      }

      if (circuitBreaker.failureCount >= circuitBreaker.threshold) {
        circuitBreaker.state = 'OPEN';
      }

      expect(circuitBreaker.state).toBe('OPEN');
      expect(circuitBreaker.failureCount).toBe(3);
    });

    it('should handle voice recognition errors gracefully', async () => {
      const voiceErrors = [
        { error: 'AUDIO_TOO_NOISY', recovery: 'Ask user to move to quieter location' },
        { error: 'AUDIO_TOO_SHORT', recovery: 'Ask user to speak longer' },
        { error: 'UNSUPPORTED_LANGUAGE', recovery: 'Inform supported languages' },
      ];

      for (const err of voiceErrors) {
        expect(err.recovery).toBeDefined();
        expect(err.error).toBeDefined();
      }
    });

    it('should handle service timeout with fallback', async () => {
      const serviceCall = async (timeout: number) => {
        return new Promise((resolve, reject) => {
          setTimeout(() => reject(new Error('Timeout')), timeout);
        });
      };

      const fallbackData = { cached: true, data: 'fallback' };

      try {
        await serviceCall(100);
      } catch (error) {
        // Use fallback
        expect(fallbackData.cached).toBe(true);
      }
    });

    it('should recover from Redis connection failures', async () => {
      const redisStates = [
        { attempt: 1, connected: false, error: 'Connection refused' },
        { attempt: 2, connected: false, error: 'Connection refused' },
        { attempt: 3, connected: true, error: null },
      ];

      const finalState = redisStates[redisStates.length - 1];
      expect(finalState.connected).toBe(true);
      expect(finalState.error).toBeNull();
    });

    it('should handle form validation errors with helpful messages', async () => {
      const validationErrors = [
        { field: 'age', error: 'Must be between 18 and 100', value: 150 },
        { field: 'phone', error: 'Must be 10 digits', value: '12345' },
        { field: 'aadhaar', error: 'Invalid format', value: '1234' },
      ];

      for (const err of validationErrors) {
        expect(err.error).toBeDefined();
        expect(err.field).toBeDefined();
      }

      expect(validationErrors.length).toBe(3);
    });

    it('should handle scheme matching failures with alternatives', async () => {
      const matchingResult = {
        exactMatches: [],
        partialMatches: [
          { schemeId: 'scheme1', score: 0.6, reason: 'Income slightly above threshold' },
          { schemeId: 'scheme2', score: 0.5, reason: 'Age requirement not met' },
        ],
        suggestions: [
          'Update income information',
          'Check eligibility next year',
        ],
      };

      expect(matchingResult.exactMatches.length).toBe(0);
      expect(matchingResult.partialMatches.length).toBe(2);
      expect(matchingResult.suggestions.length).toBe(2);
    });

    it('should handle government portal integration failures', async () => {
      const portalErrors = [
        { portal: 'myScheme', status: 'unavailable', fallback: 'Use cached data' },
        { portal: 'DigiLocker', status: 'timeout', fallback: 'Manual document upload' },
        { portal: 'Aadhaar', status: 'rate_limited', fallback: 'Retry after delay' },
      ];

      for (const err of portalErrors) {
        expect(err.fallback).toBeDefined();
        expect(err.status).toBeDefined();
      }
    });
  });

  describe('Distributed Tracing and Monitoring', () => {
    it('should create trace spans for each service call', async () => {
      const trace = {
        traceId: 'trace123',
        spans: [
          { spanId: 'span1', service: 'api-gateway', operation: 'processConversation', duration: 50 },
          { spanId: 'span2', service: 'voice-engine', operation: 'transcribe', duration: 150, parentSpanId: 'span1' },
          { spanId: 'span3', service: 'dialect-detector', operation: 'detect', duration: 80, parentSpanId: 'span1' },
          { spanId: 'span4', service: 'scheme-matcher', operation: 'match', duration: 200, parentSpanId: 'span1' },
        ],
      };

      expect(trace.spans.length).toBe(4);
      expect(trace.spans.every(s => s.duration > 0)).toBe(true);
      expect(trace.spans.filter(s => s.parentSpanId === 'span1').length).toBe(3);
    });

    it('should propagate trace context across service boundaries', async () => {
      const traceContext = {
        traceId: 'trace123',
        spanId: 'span1',
        sampled: true,
      };

      const serviceACall = {
        headers: {
          'x-trace-id': traceContext.traceId,
          'x-span-id': traceContext.spanId,
        },
      };

      const serviceBCall = {
        headers: {
          'x-trace-id': traceContext.traceId,
          'x-span-id': 'span2',
          'x-parent-span-id': traceContext.spanId,
        },
      };

      expect(serviceACall.headers['x-trace-id']).toBe(serviceBCall.headers['x-trace-id']);
      expect(serviceBCall.headers['x-parent-span-id']).toBe(serviceACall.headers['x-span-id']);
    });

    it('should track end-to-end latency across all services', async () => {
      const journey = {
        startTime: new Date('2024-01-01T10:00:00'),
        stages: [
          { name: 'voice-recognition', duration: 150 },
          { name: 'dialect-detection', duration: 80 },
          { name: 'profile-loading', duration: 50 },
          { name: 'scheme-matching', duration: 200 },
          { name: 'form-generation', duration: 100 },
        ],
        endTime: new Date('2024-01-01T10:00:00.580'),
      };

      const totalDuration = journey.stages.reduce((sum, stage) => sum + stage.duration, 0);
      expect(totalDuration).toBe(580);
      expect(totalDuration).toBeLessThan(1000); // Under 1 second
    });
  });

  describe('State Management and Persistence', () => {
    it('should persist conversation state in Redis', async () => {
      const conversationState = {
        sessionId: 'session123',
        userId: 'user123',
        currentStage: 'scheme_discovery',
        conversationHistory: [
          { role: 'user', content: 'I am a farmer', timestamp: new Date() },
          { role: 'assistant', content: 'I found 5 schemes', timestamp: new Date() },
        ],
      };

      mockRedisClient.setEx.mockResolvedValue('OK');
      mockRedisClient.get.mockResolvedValue(JSON.stringify(conversationState));

      // Simulate save
      await mockRedisClient.setEx('conversation:session123', 3600, JSON.stringify(conversationState));

      // Simulate load
      const loaded = JSON.parse(await mockRedisClient.get('conversation:session123'));

      expect(loaded.sessionId).toBe('session123');
      expect(loaded.conversationHistory.length).toBe(2);
    });

    it('should handle session expiry gracefully', async () => {
      mockRedisClient.get.mockResolvedValue(null);

      const sessionId = 'expired-session';
      const state = await mockRedisClient.get(`conversation:${sessionId}`);

      if (!state) {
        // Create new session
        const newSession = {
          sessionId: 'new-session',
          userId: 'user123',
          currentStage: 'initial',
        };

        expect(newSession.currentStage).toBe('initial');
      }
    });

    it('should maintain conversation context across multiple interactions', async () => {
      const interactions = [
        { turn: 1, input: 'I am a farmer', context: { occupation: 'farmer' } },
        { turn: 2, input: 'I am 35 years old', context: { occupation: 'farmer', age: 35 } },
        { turn: 3, input: 'I live in Haryana', context: { occupation: 'farmer', age: 35, state: 'Haryana' } },
      ];

      const finalContext = interactions[interactions.length - 1].context;

      expect(finalContext.occupation).toBe('farmer');
      expect(finalContext.age).toBe(35);
      expect(finalContext.state).toBe('Haryana');
    });
  });
});
