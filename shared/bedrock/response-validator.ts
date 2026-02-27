/**
 * Model Response Validator
 * Validates Bedrock model responses before using them
 * Validates: Requirements 8.1-8.4, 8.7
 */

import { ClaudeResponse, ResponseValidation } from '../types/bedrock';

export class ResponseValidator {
  private readonly CONFIDENCE_THRESHOLD = 0.7;

  /**
   * Validate Claude demographic extraction response
   * Validates: Requirement 8.1
   */
  validateUserProfileExtraction(response: ClaudeResponse): ResponseValidation {
    const errors: string[] = [];

    if (!response.content || response.content.trim().length === 0) {
      errors.push('Empty response content');
      return { valid: false, errors, confidence: 0 };
    }

    // Try to parse as JSON
    try {
      const profile = JSON.parse(response.content);

      if (profile.age === undefined || profile.age === null) {
        errors.push('Missing required field: age');
      }
      if (!profile.state && !profile.location) {
        errors.push('Missing required field: state/location');
      }
      if (profile.age !== undefined && (profile.age < 0 || profile.age > 150)) {
        errors.push('Invalid age value');
      }
      if (profile.income !== undefined && profile.income < 0) {
        errors.push('Invalid income value');
      }
    } catch {
      errors.push('Response is not valid JSON');
    }

    const confidence = response.confidence || this.estimateConfidence(response);
    if (confidence < this.CONFIDENCE_THRESHOLD) {
      errors.push(`Confidence score ${confidence} below threshold ${this.CONFIDENCE_THRESHOLD}`);
    }

    return {
      valid: errors.length === 0,
      errors,
      confidence,
    };
  }

  /**
   * Validate Nova Pro transcription response
   * Validates: Requirement 8.2
   */
  validateTranscription(transcription: string, confidence: number): ResponseValidation {
    const errors: string[] = [];

    if (!transcription || transcription.trim().length === 0) {
      errors.push('Empty transcription');
    }

    if (confidence < this.CONFIDENCE_THRESHOLD) {
      errors.push(`Confidence score ${confidence} below threshold ${this.CONFIDENCE_THRESHOLD}`);
    }

    return {
      valid: errors.length === 0,
      errors,
      confidence,
    };
  }

  /**
   * Validate Knowledge Base scheme results
   * Validates: Requirement 8.3
   */
  validateSchemeResults(results: Array<{ content: string; metadata: any; score: number }>): ResponseValidation {
    const errors: string[] = [];
    let avgConfidence = 0;

    if (!results || results.length === 0) {
      return { valid: true, errors: [], confidence: 1.0 }; // Empty results are valid
    }

    for (let i = 0; i < results.length; i++) {
      const result = results[i];

      if (!result.content || result.content.trim().length === 0) {
        errors.push(`Result ${i}: missing content`);
      }

      if (!result.metadata?.schemeId && !result.metadata?.name) {
        errors.push(`Result ${i}: missing scheme name or ID in metadata`);
      }

      avgConfidence += result.score || 0;
    }

    avgConfidence = avgConfidence / results.length;

    if (avgConfidence < this.CONFIDENCE_THRESHOLD) {
      errors.push(`Average relevance score ${avgConfidence.toFixed(2)} below threshold ${this.CONFIDENCE_THRESHOLD}`);
    }

    return {
      valid: errors.length === 0,
      errors,
      confidence: avgConfidence,
    };
  }

  /**
   * Check confidence score against threshold
   * Validates: Requirement 8.7
   */
  meetsConfidenceThreshold(confidence: number): boolean {
    return confidence >= this.CONFIDENCE_THRESHOLD;
  }

  getConfidenceThreshold(): number {
    return this.CONFIDENCE_THRESHOLD;
  }

  private estimateConfidence(response: ClaudeResponse): number {
    if (!response.content) return 0;
    if (response.stopReason === 'end_turn') return 0.85;
    if (response.stopReason === 'max_tokens') return 0.6;
    return 0.75;
  }
}
