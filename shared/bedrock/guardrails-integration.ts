/**
 * Guardrails Integration Layer
 * PII detection, redaction, and context management
 * Validates: Requirements 4.1-4.7
 */

import {
  PIIDetection,
  PIIRedactionResult,
  PIIContext,
} from '../types/bedrock';
import { BedrockAgentWrapper } from './bedrock-agent-wrapper';

export class GuardrailsIntegration {
  private wrapper: BedrockAgentWrapper;
  private piiContextStore: Map<string, PIIContext> = new Map();
  private falsePositiveLog: Array<{
    detection: PIIDetection;
    reason: string;
    timestamp: Date;
  }> = [];

  // Regex patterns for local PII detection (fallback when Guardrails unavailable)
  private readonly PII_PATTERNS: Record<string, RegExp> = {
    AADHAAR: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g,
    PHONE: /\b(?:\+91[\s-]?)?[6-9]\d{9}\b/g,
    NAME: /\b(?:Mr\.|Mrs\.|Ms\.|Shri|Smt\.?)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b/g,
    PAN: /\b[A-Z]{5}\d{4}[A-Z]\b/g,
  };

  private readonly PLACEHOLDER_MAP: Record<string, string> = {
    NAME: '[NAME]',
    ADDRESS: '[ADDRESS]',
    PHONE: '[PHONE]',
    AADHAAR: '[AADHAAR]',
    PAN: '[PAN]',
    EMAIL: '[EMAIL]',
  };

  constructor(wrapper: BedrockAgentWrapper) {
    this.wrapper = wrapper;
  }

  /**
   * Detect and redact PII from text
   * Validates: Requirements 4.1, 4.2, 4.3
   */
  async detectAndRedactPII(text: string, language: 'hi' | 'en'): Promise<PIIRedactionResult> {
    try {
      if (this.wrapper.isEnabled()) {
        // Use Bedrock Guardrails for PII detection
        const result = await this.wrapper.applyGuardrails(text);
        return {
          redactedText: result.outputText,
          detections: result.piiDetections,
          action: result.action,
          confidence: result.piiDetections.length > 0 ? 0.9 : 1.0,
        };
      }
    } catch (error) {
      console.warn('Bedrock Guardrails unavailable, using local PII detection');
    }

    // Fallback: local regex-based PII detection
    return this.localPIIDetection(text);
  }

  /**
   * Store PII context for later restoration
   * Validates: Requirement 4.7
   */
  async storePIIContext(sessionId: string, context: PIIContext): Promise<void> {
    this.piiContextStore.set(sessionId, context);
  }

  /**
   * Restore PII context for final user response
   * Validates: Requirement 4.7
   */
  async restorePIIContext(sessionId: string, text: string): Promise<string> {
    const context = this.piiContextStore.get(sessionId);
    if (!context) return text;

    let restored = text;
    for (const detection of context.detections) {
      const placeholder = this.PLACEHOLDER_MAP[detection.type] || `[${detection.type}]`;
      restored = restored.replace(placeholder, detection.match);
    }

    return restored;
  }

  /**
   * Log a false positive PII detection
   * Validates: Requirement 4.5
   */
  async logFalsePositive(detection: PIIDetection, reason: string): Promise<void> {
    this.falsePositiveLog.push({
      detection,
      reason,
      timestamp: new Date(),
    });
    console.info(`[Guardrails] False positive logged: ${detection.type} - ${reason}`);
  }

  /**
   * Get false positive statistics
   */
  getFalsePositiveStats(): { total: number; byType: Record<string, number> } {
    const byType: Record<string, number> = {};
    for (const entry of this.falsePositiveLog) {
      byType[entry.detection.type] = (byType[entry.detection.type] || 0) + 1;
    }
    return { total: this.falsePositiveLog.length, byType };
  }

  /**
   * Local PII detection using regex patterns (fallback)
   */
  private localPIIDetection(text: string): PIIRedactionResult {
    const detections: PIIDetection[] = [];
    let redactedText = text;

    for (const [type, pattern] of Object.entries(this.PII_PATTERNS)) {
      const regex = new RegExp(pattern.source, pattern.flags);
      let match;
      while ((match = regex.exec(text)) !== null) {
        detections.push({
          type,
          match: match[0],
          startOffset: match.index,
          endOffset: match.index + match[0].length,
        });
      }
    }

    // Redact detected PII (sort by offset descending to avoid index shifts)
    const sortedDetections = [...detections].sort((a, b) => b.startOffset - a.startOffset);
    for (const detection of sortedDetections) {
      const placeholder = this.PLACEHOLDER_MAP[detection.type] || `[${detection.type}]`;
      redactedText =
        redactedText.substring(0, detection.startOffset) +
        placeholder +
        redactedText.substring(detection.endOffset);
    }

    return {
      redactedText,
      detections,
      action: 'ALLOWED',
      confidence: detections.length > 0 ? 0.7 : 1.0,
    };
  }

  /**
   * Clean up session context
   */
  clearContext(sessionId: string): void {
    this.piiContextStore.delete(sessionId);
  }
}
