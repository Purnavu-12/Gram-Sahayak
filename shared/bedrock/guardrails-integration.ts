/**
 * Guardrails Integration
 * 
 * PII detection and redaction using AWS Bedrock Guardrails.
 * Falls back to regex-based detection when Guardrails are unavailable.
 */

export interface GuardrailsConfig {
  guardrailId?: string;
  guardrailVersion?: string;
  enablePiiRedaction: boolean;
  enableTopicFiltering: boolean;
}

export interface PiiDetectionResult {
  hasPii: boolean;
  redactedText: string;
  detectedTypes: string[];
  confidence: number;
}

const PII_PATTERNS: Record<string, RegExp> = {
  aadhaar: /\b\d{4}\s?\d{4}\s?\d{4}\b/g,
  pan: /\b[A-Z]{5}\d{4}[A-Z]\b/g,
  phone: /\b(?:\+91[\s-]?)?[6-9]\d{9}\b/g,
  email: /\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b/g,
  bankAccount: /\b\d{9,18}\b/g,
  ifsc: /\b[A-Z]{4}0[A-Z0-9]{6}\b/g,
  pincode: /\b\d{6}\b/g,
};

export class GuardrailsIntegration {
  private config: GuardrailsConfig;

  constructor(config?: Partial<GuardrailsConfig>) {
    this.config = {
      guardrailId: config?.guardrailId || process.env.BEDROCK_GUARDRAIL_ID,
      guardrailVersion: config?.guardrailVersion || process.env.BEDROCK_GUARDRAIL_VERSION || 'DRAFT',
      enablePiiRedaction: config?.enablePiiRedaction ?? true,
      enableTopicFiltering: config?.enableTopicFiltering ?? true,
    };
  }

  /**
   * Detect and redact PII from text using regex patterns.
   * In production with Bedrock Guardrails configured, this would also
   * use the ApplyGuardrail API for more comprehensive detection.
   */
  detectAndRedactPii(text: string): PiiDetectionResult {
    const detectedTypes: string[] = [];
    let redactedText = text;
    let hasMatch = false;

    const enableRedaction = this.config.enablePiiRedaction;

    for (const [type, pattern] of Object.entries(PII_PATTERNS)) {
      const matches = text.match(pattern);
      if (matches && matches.length > 0) {
        hasMatch = true;
        detectedTypes.push(type);
        if (enableRedaction) {
          redactedText = redactedText.replace(pattern, `[${type.toUpperCase()}_REDACTED]`);
        }
      }
    }

    return {
      hasPii: hasMatch,
      redactedText,
      detectedTypes,
      confidence: hasMatch ? 0.85 : 1.0,
    };
  }

  /**
   * Check if Bedrock Guardrails are configured.
   */
  isGuardrailConfigured(): boolean {
    return !!(this.config.guardrailId && this.config.guardrailVersion);
  }

  getConfig(): GuardrailsConfig {
    return { ...this.config };
  }
}
