/**
 * Tests for AWS Bedrock Integration Module
 * 
 * Tests FallbackHandler, ResponseValidator, MetricsCollector,
 * GuardrailsIntegration, KBIngestionPipeline, and Config.
 */

import { FallbackHandler, CircuitState } from './fallback-handler';
import { ResponseValidator } from './response-validator';
import { MetricsCollector } from './metrics-collector';
import { GuardrailsIntegration } from './guardrails-integration';
import { KBIngestionPipeline, SchemeDocument } from './kb-ingestion-pipeline';
import { loadBedrockConfig } from './bedrock-config';

describe('FallbackHandler', () => {
  let handler: FallbackHandler;

  beforeEach(() => {
    handler = new FallbackHandler({ failureThreshold: 3, resetTimeoutMs: 100 });
  });

  it('should start in CLOSED state', () => {
    expect(handler.getState()).toBe(CircuitState.CLOSED);
  });

  it('should execute primary function when circuit is closed', async () => {
    const result = await handler.execute(async () => 'success');
    expect(result).toBe('success');
  });

  it('should open circuit after threshold failures', async () => {
    const failingFn = async () => { throw new Error('fail'); };
    const fallbackFn = async () => 'fallback';

    for (let i = 0; i < 3; i++) {
      await handler.execute(failingFn, fallbackFn);
    }

    expect(handler.getState()).toBe(CircuitState.OPEN);
  });

  it('should use fallback when circuit is open', async () => {
    const failingFn = async () => { throw new Error('fail'); };
    const fallbackFn = async () => 'fallback';

    // Trigger circuit open
    for (let i = 0; i < 3; i++) {
      await handler.execute(failingFn, fallbackFn);
    }

    const result = await handler.execute(failingFn, fallbackFn);
    expect(result).toBe('fallback');
  });

  it('should transition to half-open after reset timeout', async () => {
    const failingFn = async () => { throw new Error('fail'); };
    const fallbackFn = async () => 'fallback';

    for (let i = 0; i < 3; i++) {
      await handler.execute(failingFn, fallbackFn);
    }

    // Wait for reset timeout
    await new Promise(resolve => setTimeout(resolve, 150));

    const successFn = async () => 'recovered';
    const result = await handler.execute(successFn, fallbackFn);
    expect(result).toBe('recovered');
    expect(handler.getState()).toBe(CircuitState.CLOSED);
  });

  it('should reset properly', () => {
    handler.reset();
    expect(handler.getState()).toBe(CircuitState.CLOSED);
    expect(handler.getFailureCount()).toBe(0);
  });
});

describe('ResponseValidator', () => {
  let validator: ResponseValidator;

  beforeEach(() => {
    validator = new ResponseValidator({ maxResponseLength: 100 });
  });

  it('should validate valid responses', () => {
    const result = validator.validate('This is a valid response');
    expect(result.isValid).toBe(true);
    expect(result.issues).toHaveLength(0);
  });

  it('should reject empty responses', () => {
    const result = validator.validate('');
    expect(result.isValid).toBe(false);
    expect(result.issues).toContain('Response is empty');
  });

  it('should truncate long responses', () => {
    const longText = 'a'.repeat(200);
    const result = validator.validate(longText);
    expect(result.isValid).toBe(false);
    expect(result.sanitizedText.length).toBe(100);
  });

  it('should detect blocked patterns', () => {
    const validatorWithBlocked = new ResponseValidator({
      blockedPatterns: [/secret\s*key/i],
    });
    const result = validatorWithBlocked.validate('The secret key is ABC123');
    expect(result.isValid).toBe(false);
    expect(result.sanitizedText).toContain('[REDACTED]');
  });
});

describe('MetricsCollector', () => {
  let collector: MetricsCollector;

  beforeEach(() => {
    collector = new MetricsCollector();
  });

  it('should record latency metrics', () => {
    collector.recordLatency('invokeModel', 250, 'claude-3');
    const summary = collector.getSummary();
    expect(summary['bedrock_api_latency_ms']).toBe(250);
  });

  it('should record token usage', () => {
    collector.recordTokenUsage(100, 200, 'claude-3');
    const summary = collector.getSummary();
    expect(summary['bedrock_input_tokens']).toBe(100);
    expect(summary['bedrock_output_tokens']).toBe(200);
  });

  it('should record errors', () => {
    collector.recordError('invokeModel', 'throttling');
    const summary = collector.getSummary();
    expect(summary['bedrock_api_errors']).toBe(1);
  });

  it('should generate Prometheus metrics format', () => {
    collector.recordLatency('invokeModel', 250, 'claude-3');
    const prometheus = collector.getPrometheusMetrics();
    expect(prometheus).toContain('bedrock_api_latency_ms');
    expect(prometheus).toContain('250');
  });

  it('should reset metrics', () => {
    collector.recordLatency('invokeModel', 250, 'claude-3');
    collector.reset();
    const summary = collector.getSummary();
    expect(Object.keys(summary)).toHaveLength(0);
  });
});

describe('GuardrailsIntegration', () => {
  let guardrails: GuardrailsIntegration;

  beforeEach(() => {
    guardrails = new GuardrailsIntegration();
  });

  it('should detect Aadhaar numbers', () => {
    const result = guardrails.detectAndRedactPii('My Aadhaar is 1234 5678 9012');
    expect(result.hasPii).toBe(true);
    expect(result.detectedTypes).toContain('aadhaar');
    expect(result.redactedText).toContain('[AADHAAR_REDACTED]');
  });

  it('should detect PAN numbers', () => {
    const result = guardrails.detectAndRedactPii('PAN: ABCDE1234F');
    expect(result.hasPii).toBe(true);
    expect(result.detectedTypes).toContain('pan');
  });

  it('should detect phone numbers', () => {
    const result = guardrails.detectAndRedactPii('Call me at 9876543210');
    expect(result.hasPii).toBe(true);
    expect(result.detectedTypes).toContain('phone');
  });

  it('should detect email addresses', () => {
    const result = guardrails.detectAndRedactPii('Email: test@example.com');
    expect(result.hasPii).toBe(true);
    expect(result.detectedTypes).toContain('email');
  });

  it('should return clean result for no PII', () => {
    const result = guardrails.detectAndRedactPii('Hello, I need help with schemes');
    expect(result.hasPii).toBe(false);
    expect(result.confidence).toBe(1.0);
  });

  it('should detect but not redact when enablePiiRedaction is false', () => {
    const detectOnly = new GuardrailsIntegration({ enablePiiRedaction: false });
    const result = detectOnly.detectAndRedactPii('My Aadhaar is 1234 5678 9012');
    expect(result.hasPii).toBe(true);
    expect(result.detectedTypes).toContain('aadhaar');
    expect(result.redactedText).not.toContain('[AADHAAR_REDACTED]');
    expect(result.redactedText).toContain('1234 5678 9012');
  });
});

describe('KBIngestionPipeline', () => {
  let pipeline: KBIngestionPipeline;

  const sampleScheme: SchemeDocument = {
    schemeId: 'PM-KISAN-001',
    name: 'PM-KISAN',
    nameHi: 'प्रधानमंत्री किसान सम्मान निधि',
    description: 'Income support to farmer families',
    descriptionHi: 'किसान परिवारों को आय सहायता',
    eligibilityCriteria: ['Small and marginal farmers', 'Land ownership required'],
    benefits: ['₹6,000 per year in 3 installments'],
    requiredDocuments: ['Aadhaar Card', 'Land Records'],
    applicationProcess: ['Visit nearest CSC', 'Fill application form'],
    ministry: 'Ministry of Agriculture',
    category: 'Agriculture',
    lastUpdated: '2024-01-01',
  };

  beforeEach(() => {
    pipeline = new KBIngestionPipeline();
  });

  it('should prepare documents for ingestion', () => {
    const doc = pipeline.prepareDocument(sampleScheme);
    expect(doc).toContain('PM-KISAN');
    expect(doc).toContain('Small and marginal farmers');
    expect(doc).toContain('Ministry of Agriculture');
  });

  it('should validate complete documents', () => {
    const result = pipeline.validateDocument(sampleScheme);
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('should reject incomplete documents', () => {
    const incomplete = { ...sampleScheme, schemeId: '', name: '' } as SchemeDocument;
    const result = pipeline.validateDocument(incomplete);
    expect(result.valid).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
  });
});

describe('Config', () => {
  it('should load default configuration', () => {
    const config = loadBedrockConfig();
    expect(config.region).toBeDefined();
    expect(config.modelId).toBeDefined();
    expect(config.maxTokens).toBeGreaterThan(0);
    expect(config.temperature).toBeGreaterThanOrEqual(0);
    expect(config.temperature).toBeLessThanOrEqual(1);
  });

  it('should use environment variables when set', () => {
    const originalRegion = process.env.AWS_REGION;
    process.env.AWS_REGION = 'ap-south-1';

    const config = loadBedrockConfig();
    expect(config.region).toBe('ap-south-1');

    // Restore
    if (originalRegion) {
      process.env.AWS_REGION = originalRegion;
    } else {
      delete process.env.AWS_REGION;
    }
  });
});
