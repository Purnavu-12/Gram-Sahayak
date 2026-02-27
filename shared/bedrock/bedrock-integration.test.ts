/**
 * Property-Based Tests for Bedrock Shared Infrastructure
 * Feature: bedrock-integration
 *
 * Tests the FallbackHandler, ResponseValidator, MetricsCollector,
 * GuardrailsIntegration, and KBIngestionPipeline
 *
 * **Validates: Requirements 1.5, 1.6, 1.7, 3.6, 4.1-4.3, 7.1-7.6, 8.1-8.7, 11.1-11.7**
 */

import * as fc from 'fast-check';
import { FallbackHandler } from './fallback-handler';
import { ResponseValidator } from './response-validator';
import { BedrockMetricsCollector } from './metrics-collector';
import { GuardrailsIntegration } from './guardrails-integration';
import { KBIngestionPipeline } from './kb-ingestion-pipeline';
import { BedrockAgentWrapper } from './bedrock-agent-wrapper';
import { ClaudeResponse, SchemeData } from '../types/bedrock';

describe('Bedrock Integration - FallbackHandler', () => {
  /**
   * Property 2: Fallback Routing on Failure
   * For any Bedrock model invocation that fails, the FallbackHandler should
   * automatically route to the existing service implementation.
   * Validates: Requirements 1.5, 1.6, 7.1, 7.2
   */
  describe('Property 2: Fallback Routing on Failure', () => {
    it('should route to fallback on primary failure for any failure type', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom('timeout', 'error', 'rate_limit', 'service_unavailable'),
          fc.constantFrom('voice-engine', 'scheme-matcher', 'dialect-detector'),
          async (failureType, serviceId) => {
            const handler = new FallbackHandler({ timeout: 1000, retries: 0, retryDelay: 10, circuitBreakerThreshold: 50, circuitBreakerWindow: 60 });

            const primary = async () => {
              throw new Error(failureType);
            };
            const fallback = async () => ({ success: true, source: 'fallback' as const });

            const result = await handler.executeWithFallback(primary, fallback, undefined, serviceId);

            expect(result.source).toBe('fallback');
            expect(result.data).toEqual({ success: true, source: 'fallback' });
            expect(result.latency).toBeGreaterThanOrEqual(0);
          }
        ),
        { numRuns: 50 }
      );
    });
  });

  /**
   * Property 3: Model Tier Fallback Sequence
   * Validates: Requirement 1.7
   */
  describe('Property 3: Model Tier Fallback Sequence', () => {
    it('should follow Claude 3.5 Sonnet → Claude 3 Haiku → Existing sequence', async () => {
      const handler = new FallbackHandler({ timeout: 1000, retries: 0, retryDelay: 10, circuitBreakerThreshold: 50, circuitBreakerWindow: 60 });

      // Primary and fallback both fail, existing should succeed
      const primaryModel = async () => { throw new Error('primary_failed'); };
      const fallbackModel = async () => { throw new Error('fallback_failed'); };
      const existingImpl = async () => ({ result: 'from_existing' });

      const result = await handler.executeWithModelTierFallback(
        primaryModel, fallbackModel, existingImpl, 'claude'
      );

      expect(result.source).toBe('fallback');
      expect(result.data).toEqual({ result: 'from_existing' });
    });

    it('should use primary when available', async () => {
      const handler = new FallbackHandler();

      const primaryModel = async () => ({ result: 'from_primary' });
      const fallbackModel = async () => ({ result: 'from_fallback' });
      const existingImpl = async () => ({ result: 'from_existing' });

      const result = await handler.executeWithModelTierFallback(
        primaryModel, fallbackModel, existingImpl
      );

      expect(result.source).toBe('primary');
      expect(result.data).toEqual({ result: 'from_primary' });
    });
  });

  /**
   * Property 19: Continuous Operation During Bedrock Outage
   * Validates: Requirement 7.5
   */
  describe('Property 19: Continuous Operation During Outage', () => {
    it('should continue operating via fallback during sustained failures', async () => {
      const handler = new FallbackHandler({ timeout: 500, retries: 0, retryDelay: 10, circuitBreakerThreshold: 50, circuitBreakerWindow: 60 });

      const failures = Array.from({ length: 20 }, (_, i) => i);
      for (const _ of failures) {
        const result = await handler.executeWithFallback(
          async () => { throw new Error('outage'); },
          async () => ({ operational: true }),
          undefined,
          'voice-engine'
        );
        expect(result.source).toBe('fallback');
        expect(result.data).toEqual({ operational: true });
      }

      // Metrics should reflect failures handled
      const metrics = handler.getMetrics();
      expect(metrics.fallbackSuccesses).toBe(20);
      expect(metrics.totalRequests).toBe(20);
    });
  });

  describe('Circuit breaker management', () => {
    it('should start in CLOSED state', () => {
      const handler = new FallbackHandler();
      const state = handler.getCircuitState('test-service');
      expect(state.state).toBe('CLOSED');
      expect(state.failureCount).toBe(0);
    });

    it('should allow resetting circuit state', () => {
      const handler = new FallbackHandler();
      handler.resetCircuit('test-service');
      const state = handler.getCircuitState('test-service');
      expect(state.state).toBe('CLOSED');
    });
  });
});

describe('Bedrock Integration - ResponseValidator', () => {
  const validator = new ResponseValidator();

  /**
   * Property 21: Model Response Validation
   * Validates: Requirements 8.1, 8.2, 8.3, 8.4
   */
  describe('Property 21: Model Response Validation', () => {
    it('should validate user profile extraction with various responses', async () => {
      await fc.assert(
        fc.property(
          fc.record({
            age: fc.integer({ min: 0, max: 120 }),
            income: fc.integer({ min: 0, max: 1000000 }),
            state: fc.constantFrom('UP', 'Bihar', 'MP', 'Rajasthan', 'Maharashtra'),
          }),
          (profileData) => {
            const response: ClaudeResponse = {
              content: JSON.stringify(profileData),
              stopReason: 'end_turn',
              usage: { inputTokens: 100, outputTokens: 50 },
              confidence: 0.85,
            };

            const result = validator.validateUserProfileExtraction(response);
            expect(result.valid).toBe(true);
            expect(result.confidence).toBeGreaterThanOrEqual(0.7);
          }
        ),
        { numRuns: 50 }
      );
    });

    it('should reject responses with empty content', () => {
      const response: ClaudeResponse = {
        content: '',
        stopReason: 'end_turn',
        usage: { inputTokens: 100, outputTokens: 0 },
      };

      const result = validator.validateUserProfileExtraction(response);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Empty response content');
    });

    it('should reject responses with invalid JSON', () => {
      const response: ClaudeResponse = {
        content: 'not valid json',
        stopReason: 'end_turn',
        usage: { inputTokens: 100, outputTokens: 50 },
        confidence: 0.85,
      };

      const result = validator.validateUserProfileExtraction(response);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Response is not valid JSON');
    });
  });

  /**
   * Property 23: Confidence Score Threshold
   * Validates: Requirement 8.7
   */
  describe('Property 23: Confidence Score Threshold', () => {
    it('should reject all responses below 70% confidence', async () => {
      await fc.assert(
        fc.property(
          fc.double({ min: 0, max: 0.69, noNaN: true }),
          (confidence) => {
            expect(validator.meetsConfidenceThreshold(confidence)).toBe(false);
          }
        ),
        { numRuns: 50 }
      );
    });

    it('should accept all responses at or above 70% confidence', async () => {
      await fc.assert(
        fc.property(
          fc.double({ min: 0.7, max: 1.0, noNaN: true }),
          (confidence) => {
            expect(validator.meetsConfidenceThreshold(confidence)).toBe(true);
          }
        ),
        { numRuns: 50 }
      );
    });
  });

  describe('Transcription validation', () => {
    it('should reject empty transcriptions', () => {
      const result = validator.validateTranscription('', 0.5);
      expect(result.valid).toBe(false);
    });

    it('should accept valid transcriptions with high confidence', () => {
      const result = validator.validateTranscription('Hello world', 0.9);
      expect(result.valid).toBe(true);
    });
  });

  describe('Scheme results validation', () => {
    it('should validate empty results as valid', () => {
      const result = validator.validateSchemeResults([]);
      expect(result.valid).toBe(true);
    });

    it('should reject results with missing content', () => {
      const result = validator.validateSchemeResults([
        { content: '', metadata: {}, score: 0.8 },
      ]);
      expect(result.valid).toBe(false);
    });
  });
});

describe('Bedrock Integration - MetricsCollector', () => {
  /**
   * Property 24: Comprehensive Metrics Collection
   * Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5
   */
  describe('Property 24: Comprehensive Metrics Collection', () => {
    it('should track API calls, costs, fallbacks, and guardrails metrics', async () => {
      await fc.assert(
        fc.property(
          fc.record({
            model: fc.constantFrom('claude', 'nova-pro', 'titan-embeddings'),
            status: fc.constantFrom('success', 'error') as fc.Arbitrary<'success' | 'error'>,
            latency: fc.integer({ min: 50, max: 5000 }),
            inputTokens: fc.integer({ min: 10, max: 5000 }),
            outputTokens: fc.integer({ min: 10, max: 2000 }),
          }),
          (data) => {
            const collector = new BedrockMetricsCollector();

            collector.recordApiCall(data.model, data.status, data.latency);
            collector.recordCost(data.model, data.inputTokens, data.outputTokens);

            const metrics = collector.getMetrics();
            expect(metrics.apiCalls.total).toBe(1);
            expect(metrics.apiCalls.byModel[data.model]).toBe(1);
            expect(metrics.apiCalls.byStatus[data.status]).toBe(1);
            expect(metrics.costs.inputTokens).toBe(data.inputTokens);
            expect(metrics.costs.outputTokens).toBe(data.outputTokens);
          }
        ),
        { numRuns: 50 }
      );
    });

    it('should generate Prometheus format output', () => {
      const collector = new BedrockMetricsCollector();
      collector.recordApiCall('claude', 'success', 500);
      collector.recordFallback('voice-engine', 'timeout');
      collector.recordGuardrailsCheck(true, false);

      const prometheus = collector.toPrometheusFormat();
      expect(prometheus).toContain('bedrock_api_calls_total');
      expect(prometheus).toContain('bedrock_fallback_total');
      expect(prometheus).toContain('bedrock_guardrails_pii_detections_total');
    });

    it('should alert when fallback rate exceeds 20%', () => {
      const collector = new BedrockMetricsCollector();

      // Record 10 calls with 3 fallbacks (30%)
      for (let i = 0; i < 10; i++) {
        collector.recordApiCall('claude', i < 3 ? 'error' : 'success', 500);
      }
      for (let i = 0; i < 3; i++) {
        collector.recordFallback('claude', 'error');
      }

      expect(collector.shouldAlert()).toBe(true);
    });

    it('should not alert when fallback rate is low', () => {
      const collector = new BedrockMetricsCollector();

      for (let i = 0; i < 10; i++) {
        collector.recordApiCall('claude', 'success', 500);
      }
      collector.recordFallback('claude', 'error');

      expect(collector.shouldAlert()).toBe(false);
    });
  });
});

describe('Bedrock Integration - GuardrailsIntegration', () => {
  /**
   * Property 11: PII Detection and Redaction (Local Fallback)
   * Validates: Requirements 4.1, 4.2, 4.3
   */
  describe('Property 11: PII Detection and Redaction (Local)', () => {
    it('should detect and redact Aadhaar numbers', async () => {
      const disabledConfig = {
        enabled: false,
        region: 'us-east-1',
        credentials: { accessKeyId: '', secretAccessKey: '' },
        models: { claude: { modelId: '', fallbackModelId: '', maxTokens: 0, temperature: 0 }, novaPro: { sttModelId: '', ttsModelId: '', supportedLanguages: [] }, titanEmbeddings: { modelId: '', dimensions: 0 } },
        guardrails: { policyId: '', policyVersion: '', enabledDetectors: [] },
        knowledgeBase: { kbId: '', dataSourceId: '', maxResults: 0 },
        fallback: { timeout: 0, retries: 0, circuitBreakerThreshold: 0, circuitBreakerWindow: 0 },
        monitoring: { enableMetrics: false, enableTracing: false, logLevel: 'info' as const },
      };

      const wrapper = new BedrockAgentWrapper(disabledConfig);
      const guardrails = new GuardrailsIntegration(wrapper);

      const result = await guardrails.detectAndRedactPII(
        'My Aadhaar number is 1234 5678 9012', 'en'
      );

      expect(result.redactedText).toContain('[AADHAAR]');
      expect(result.redactedText).not.toContain('1234 5678 9012');
      expect(result.detections.length).toBeGreaterThan(0);
      expect(result.detections[0].type).toBe('AADHAAR');
    });

    it('should detect and redact phone numbers', async () => {
      const disabledConfig = {
        enabled: false, region: 'us-east-1', credentials: { accessKeyId: '', secretAccessKey: '' },
        models: { claude: { modelId: '', fallbackModelId: '', maxTokens: 0, temperature: 0 }, novaPro: { sttModelId: '', ttsModelId: '', supportedLanguages: [] }, titanEmbeddings: { modelId: '', dimensions: 0 } },
        guardrails: { policyId: '', policyVersion: '', enabledDetectors: [] },
        knowledgeBase: { kbId: '', dataSourceId: '', maxResults: 0 },
        fallback: { timeout: 0, retries: 0, circuitBreakerThreshold: 0, circuitBreakerWindow: 0 },
        monitoring: { enableMetrics: false, enableTracing: false, logLevel: 'info' as const },
      };

      const wrapper = new BedrockAgentWrapper(disabledConfig);
      const guardrails = new GuardrailsIntegration(wrapper);

      const result = await guardrails.detectAndRedactPII(
        'Call me at 9876543210', 'en'
      );

      expect(result.redactedText).toContain('[PHONE]');
      expect(result.redactedText).not.toContain('9876543210');
    });

    it('should store and restore PII context', async () => {
      const disabledConfig = {
        enabled: false, region: 'us-east-1', credentials: { accessKeyId: '', secretAccessKey: '' },
        models: { claude: { modelId: '', fallbackModelId: '', maxTokens: 0, temperature: 0 }, novaPro: { sttModelId: '', ttsModelId: '', supportedLanguages: [] }, titanEmbeddings: { modelId: '', dimensions: 0 } },
        guardrails: { policyId: '', policyVersion: '', enabledDetectors: [] },
        knowledgeBase: { kbId: '', dataSourceId: '', maxResults: 0 },
        fallback: { timeout: 0, retries: 0, circuitBreakerThreshold: 0, circuitBreakerWindow: 0 },
        monitoring: { enableMetrics: false, enableTracing: false, logLevel: 'info' as const },
      };

      const wrapper = new BedrockAgentWrapper(disabledConfig);
      const guardrails = new GuardrailsIntegration(wrapper);

      const context = {
        originalText: 'Call me at 9876543210',
        redactedText: 'Call me at [PHONE]',
        detections: [{ type: 'PHONE', match: '9876543210', startOffset: 11, endOffset: 21 }],
        timestamp: new Date(),
      };

      await guardrails.storePIIContext('session-1', context);
      const restored = await guardrails.restorePIIContext('session-1', 'Call me at [PHONE]');
      expect(restored).toBe('Call me at 9876543210');
    });
  });
});

describe('Bedrock Integration - KBIngestionPipeline', () => {
  /**
   * Property 9: Scheme Data Validation
   * Validates: Requirement 3.6
   */
  describe('Property 9: Scheme Data Validation', () => {
    it('should validate complete schemes as valid', async () => {
      await fc.assert(
        fc.property(
          fc.record({
            schemeId: fc.stringMatching(/^[A-Z][A-Z0-9-]{2,20}$/),
            nameEn: fc.string({ minLength: 5, maxLength: 100 }),
            nameHi: fc.string({ minLength: 5, maxLength: 100 }),
            descEn: fc.string({ minLength: 10, maxLength: 500 }),
            descHi: fc.string({ minLength: 10, maxLength: 500 }),
            benefitsEn: fc.string({ minLength: 5, maxLength: 200 }),
            benefitsHi: fc.string({ minLength: 5, maxLength: 200 }),
            processEn: fc.string({ minLength: 5, maxLength: 200 }),
            processHi: fc.string({ minLength: 5, maxLength: 200 }),
          }),
          (data) => {
            const disabledConfig = {
              enabled: false, region: 'us-east-1', credentials: { accessKeyId: '', secretAccessKey: '' },
              models: { claude: { modelId: '', fallbackModelId: '', maxTokens: 0, temperature: 0 }, novaPro: { sttModelId: '', ttsModelId: '', supportedLanguages: [] }, titanEmbeddings: { modelId: '', dimensions: 0 } },
              guardrails: { policyId: '', policyVersion: '', enabledDetectors: [] },
              knowledgeBase: { kbId: '', dataSourceId: '', maxResults: 0 },
              fallback: { timeout: 0, retries: 0, circuitBreakerThreshold: 0, circuitBreakerWindow: 0 },
              monitoring: { enableMetrics: false, enableTracing: false, logLevel: 'info' as const },
            };

            const wrapper = new BedrockAgentWrapper(disabledConfig);
            const pipeline = new KBIngestionPipeline(wrapper);

            const scheme: SchemeData = {
              schemeId: data.schemeId,
              name: { en: data.nameEn, hi: data.nameHi },
              description: { en: data.descEn, hi: data.descHi },
              eligibility: { state: ['all'] },
              benefits: { en: data.benefitsEn, hi: data.benefitsHi },
              applicationProcess: { en: data.processEn, hi: data.processHi },
            };

            const result = pipeline.validateScheme(scheme);
            expect(result.valid).toBe(true);
            expect(result.errors.length).toBe(0);
          }
        ),
        { numRuns: 30 }
      );
    });

    it('should reject schemes with missing required fields', () => {
      const disabledConfig = {
        enabled: false, region: 'us-east-1', credentials: { accessKeyId: '', secretAccessKey: '' },
        models: { claude: { modelId: '', fallbackModelId: '', maxTokens: 0, temperature: 0 }, novaPro: { sttModelId: '', ttsModelId: '', supportedLanguages: [] }, titanEmbeddings: { modelId: '', dimensions: 0 } },
        guardrails: { policyId: '', policyVersion: '', enabledDetectors: [] },
        knowledgeBase: { kbId: '', dataSourceId: '', maxResults: 0 },
        fallback: { timeout: 0, retries: 0, circuitBreakerThreshold: 0, circuitBreakerWindow: 0 },
        monitoring: { enableMetrics: false, enableTracing: false, logLevel: 'info' as const },
      };

      const wrapper = new BedrockAgentWrapper(disabledConfig);
      const pipeline = new KBIngestionPipeline(wrapper);

      const result = pipeline.validateScheme({
        schemeId: '',
        name: { en: '', hi: '' },
        description: { en: '', hi: '' },
        eligibility: {},
        benefits: { en: '', hi: '' },
        applicationProcess: { en: '', hi: '' },
      });

      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });

    it('should reject schemes where ageMin > ageMax', () => {
      const disabledConfig = {
        enabled: false, region: 'us-east-1', credentials: { accessKeyId: '', secretAccessKey: '' },
        models: { claude: { modelId: '', fallbackModelId: '', maxTokens: 0, temperature: 0 }, novaPro: { sttModelId: '', ttsModelId: '', supportedLanguages: [] }, titanEmbeddings: { modelId: '', dimensions: 0 } },
        guardrails: { policyId: '', policyVersion: '', enabledDetectors: [] },
        knowledgeBase: { kbId: '', dataSourceId: '', maxResults: 0 },
        fallback: { timeout: 0, retries: 0, circuitBreakerThreshold: 0, circuitBreakerWindow: 0 },
        monitoring: { enableMetrics: false, enableTracing: false, logLevel: 'info' as const },
      };

      const wrapper = new BedrockAgentWrapper(disabledConfig);
      const pipeline = new KBIngestionPipeline(wrapper);

      const result = pipeline.validateScheme({
        schemeId: 'TEST',
        name: { en: 'Test Scheme', hi: 'टेस्ट योजना' },
        description: { en: 'A test scheme', hi: 'एक टेस्ट योजना' },
        eligibility: { ageMin: 50, ageMax: 18 },
        benefits: { en: 'Test benefits', hi: 'टेस्ट लाभ' },
        applicationProcess: { en: 'Apply online', hi: 'ऑनलाइन आवेदन करें' },
      });

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('ageMin cannot be greater than ageMax');
    });
  });

  describe('Sample schemes validation', () => {
    it('should validate all 20 sample schemes', async () => {
      const schemesData = require('./sample-schemes.json');

      const disabledConfig = {
        enabled: false, region: 'us-east-1', credentials: { accessKeyId: '', secretAccessKey: '' },
        models: { claude: { modelId: '', fallbackModelId: '', maxTokens: 0, temperature: 0 }, novaPro: { sttModelId: '', ttsModelId: '', supportedLanguages: [] }, titanEmbeddings: { modelId: '', dimensions: 0 } },
        guardrails: { policyId: '', policyVersion: '', enabledDetectors: [] },
        knowledgeBase: { kbId: '', dataSourceId: '', maxResults: 0 },
        fallback: { timeout: 0, retries: 0, circuitBreakerThreshold: 0, circuitBreakerWindow: 0 },
        monitoring: { enableMetrics: false, enableTracing: false, logLevel: 'info' as const },
      };

      const wrapper = new BedrockAgentWrapper(disabledConfig);
      const pipeline = new KBIngestionPipeline(wrapper);

      expect(schemesData.schemes.length).toBe(20);

      for (const scheme of schemesData.schemes) {
        const result = pipeline.validateScheme(scheme);
        expect(result.valid).toBe(true);
        // Verify bilingual support
        expect(scheme.name.en.length).toBeGreaterThan(0);
        expect(scheme.name.hi.length).toBeGreaterThan(0);
        expect(scheme.description.en.length).toBeGreaterThan(0);
        expect(scheme.description.hi.length).toBeGreaterThan(0);
      }
    });
  });
});

describe('Bedrock Integration - Configuration', () => {
  it('should load config from environment', () => {
    const { loadBedrockConfig } = require('./bedrock-config');
    const config = loadBedrockConfig();

    expect(config).toBeDefined();
    expect(config.enabled).toBe(false); // Default when env not set
    expect(config.region).toBe('us-east-1');
    expect(config.models.claude.modelId).toContain('claude');
    expect(config.fallback.timeout).toBeGreaterThan(0);
  });

  it('should validate config correctly', () => {
    const { validateBedrockConfig } = require('./bedrock-config');

    // Valid disabled config
    const result1 = validateBedrockConfig({ enabled: false, credentials: {} });
    expect(result1.valid).toBe(true);

    // Invalid enabled config (missing credentials)
    const result2 = validateBedrockConfig({
      enabled: true,
      region: 'us-east-1',
      credentials: { accessKeyId: '', secretAccessKey: '' },
    });
    expect(result2.valid).toBe(false);
    expect(result2.errors.length).toBeGreaterThan(0);
  });
});
