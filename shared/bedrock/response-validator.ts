/**
 * Response Validator
 * 
 * Validates and sanitizes model responses from AWS Bedrock
 * to ensure quality and safety before returning to users.
 */

export interface ValidationResult {
  isValid: boolean;
  issues: string[];
  sanitizedText: string;
}

export interface ValidationConfig {
  maxResponseLength: number;
  minResponseLength: number;
  blockedPatterns: RegExp[];
  requireNonEmpty: boolean;
}

export class ResponseValidator {
  private config: ValidationConfig;

  constructor(config?: Partial<ValidationConfig>) {
    this.config = {
      maxResponseLength: config?.maxResponseLength ?? 10000,
      minResponseLength: config?.minResponseLength ?? 1,
      blockedPatterns: config?.blockedPatterns ?? [],
      requireNonEmpty: config?.requireNonEmpty ?? true,
    };
  }

  /**
   * Validate a model response.
   */
  validate(response: string): ValidationResult {
    const issues: string[] = [];
    let sanitizedText = response;

    // Check for empty response
    if (this.config.requireNonEmpty && (!response || response.trim().length === 0)) {
      issues.push('Response is empty');
      return { isValid: false, issues, sanitizedText: '' };
    }

    // Check length
    if (response.length > this.config.maxResponseLength) {
      issues.push(`Response exceeds maximum length of ${this.config.maxResponseLength}`);
      sanitizedText = response.substring(0, this.config.maxResponseLength);
    }

    if (response.trim().length < this.config.minResponseLength) {
      issues.push(`Response is shorter than minimum length of ${this.config.minResponseLength}`);
    }

    // Check blocked patterns
    for (const pattern of this.config.blockedPatterns) {
      if (pattern.test(response)) {
        issues.push(`Response contains blocked pattern: ${pattern.source}`);
        sanitizedText = sanitizedText.replace(pattern, '[REDACTED]');
      }
    }

    return {
      isValid: issues.length === 0,
      issues,
      sanitizedText,
    };
  }
}
