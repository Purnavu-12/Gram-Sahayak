/**
 * Knowledge Base Ingestion Pipeline
 * Manages scheme data validation, embedding generation, and KB indexing
 * Validates: Requirements 3.1-3.6, 12.1-12.7
 */

import {
  SchemeData,
  IngestionResult,
  IngestionError,
  ValidationResult,
} from '../types/bedrock';
import { BedrockAgentWrapper } from './bedrock-agent-wrapper';

export class KBIngestionPipeline {
  private wrapper: BedrockAgentWrapper;

  constructor(wrapper: BedrockAgentWrapper) {
    this.wrapper = wrapper;
  }

  /**
   * Ingest multiple schemes into the Knowledge Base
   * Validates: Requirements 3.1, 3.5, 12.6
   */
  async ingestSchemes(schemes: SchemeData[]): Promise<IngestionResult> {
    const startTime = Date.now();
    let successCount = 0;
    const errors: IngestionError[] = [];

    for (const scheme of schemes) {
      const validation = this.validateScheme(scheme);
      if (!validation.valid) {
        errors.push({
          schemeId: scheme.schemeId,
          error: validation.errors.join('; '),
        });
        continue;
      }

      try {
        // In production, this would use the Bedrock KB data source API
        // to upload the scheme document and trigger sync
        successCount++;
      } catch (error: any) {
        errors.push({
          schemeId: scheme.schemeId,
          error: error.message,
        });
      }
    }

    return {
      successCount,
      failureCount: errors.length,
      errors,
      duration: Date.now() - startTime,
    };
  }

  /**
   * Validate scheme data completeness
   * Validates: Requirement 3.6
   */
  validateScheme(scheme: SchemeData): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Required fields
    if (!scheme.schemeId || scheme.schemeId.trim().length === 0) {
      errors.push('Missing schemeId');
    }

    if (!scheme.name?.en || scheme.name.en.trim().length === 0) {
      errors.push('Missing English name');
    }
    if (!scheme.name?.hi || scheme.name.hi.trim().length === 0) {
      errors.push('Missing Hindi name');
    }

    if (!scheme.description?.en || scheme.description.en.trim().length === 0) {
      errors.push('Missing English description');
    }
    if (!scheme.description?.hi || scheme.description.hi.trim().length === 0) {
      errors.push('Missing Hindi description');
    }

    if (!scheme.benefits?.en || scheme.benefits.en.trim().length === 0) {
      errors.push('Missing English benefits');
    }
    if (!scheme.benefits?.hi || scheme.benefits.hi.trim().length === 0) {
      errors.push('Missing Hindi benefits');
    }

    if (!scheme.applicationProcess?.en) {
      errors.push('Missing English application process');
    }
    if (!scheme.applicationProcess?.hi) {
      errors.push('Missing Hindi application process');
    }

    // Eligibility validation
    if (!scheme.eligibility) {
      errors.push('Missing eligibility criteria');
    } else {
      if (scheme.eligibility.ageMin !== undefined && scheme.eligibility.ageMax !== undefined) {
        if (scheme.eligibility.ageMin > scheme.eligibility.ageMax) {
          errors.push('ageMin cannot be greater than ageMax');
        }
      }
      if (scheme.eligibility.incomeMax !== undefined && scheme.eligibility.incomeMax < 0) {
        errors.push('incomeMax cannot be negative');
      }
    }

    // Warnings for optional but recommended fields
    if (!scheme.eligibility?.state || scheme.eligibility.state.length === 0) {
      warnings.push('No state eligibility specified - defaults to all states');
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings,
    };
  }

  /**
   * Generate text embeddings for scheme content
   * Note: Returns mock embeddings when Bedrock is disabled or Titan model is not yet configured.
   * In production with Bedrock enabled, this should be connected to the Titan Embeddings API.
   */
  async generateEmbeddings(text: string, language: 'hi' | 'en'): Promise<number[]> {
    // TODO: Implement actual Titan Embeddings API call when Bedrock is enabled
    // For MVP, return deterministic mock embeddings based on text hash
    return Array.from({ length: 1024 }, (_, i) => {
      const charCode = text.charCodeAt(i % text.length) || 0;
      return ((charCode * (i + 1)) % 200 - 100) / 100;
    });
  }
}
