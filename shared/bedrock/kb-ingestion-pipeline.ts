/**
 * Knowledge Base Ingestion Pipeline
 * 
 * Manages ingestion of government scheme data into AWS Bedrock Knowledge Bases
 * for semantic search and retrieval-augmented generation.
 */

export interface SchemeDocument {
  schemeId: string;
  name: string;
  nameHi?: string;
  description: string;
  descriptionHi?: string;
  eligibilityCriteria: string[];
  benefits: string[];
  requiredDocuments: string[];
  applicationProcess: string[];
  ministry: string;
  category: string;
  lastUpdated: string;
}

export interface IngestionResult {
  documentId: string;
  status: 'success' | 'failed';
  error?: string;
}

export class KBIngestionPipeline {
  private dataSourceId?: string;
  private knowledgeBaseId?: string;

  constructor(knowledgeBaseId?: string, dataSourceId?: string) {
    this.knowledgeBaseId = knowledgeBaseId || process.env.BEDROCK_KB_ID;
    this.dataSourceId = dataSourceId || process.env.BEDROCK_KB_DATA_SOURCE_ID;
  }

  /**
   * Prepare a scheme document for ingestion.
   * Formats the scheme data into a structured document suitable for
   * knowledge base embedding and retrieval.
   */
  prepareDocument(scheme: SchemeDocument): string {
    const sections = [
      `# ${scheme.name}`,
      scheme.nameHi ? `Hindi: ${scheme.nameHi}` : '',
      '',
      `## Description`,
      scheme.description,
      scheme.descriptionHi ? `\nHindi: ${scheme.descriptionHi}` : '',
      '',
      `## Eligibility Criteria`,
      ...scheme.eligibilityCriteria.map((c, i) => `${i + 1}. ${c}`),
      '',
      `## Benefits`,
      ...scheme.benefits.map((b, i) => `${i + 1}. ${b}`),
      '',
      `## Required Documents`,
      ...scheme.requiredDocuments.map((d, i) => `${i + 1}. ${d}`),
      '',
      `## Application Process`,
      ...scheme.applicationProcess.map((s, i) => `Step ${i + 1}: ${s}`),
      '',
      `Ministry: ${scheme.ministry}`,
      `Category: ${scheme.category}`,
      `Last Updated: ${scheme.lastUpdated}`,
      `Scheme ID: ${scheme.schemeId}`,
    ];

    return sections.filter(Boolean).join('\n');
  }

  /**
   * Validate a scheme document before ingestion.
   */
  validateDocument(scheme: SchemeDocument): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!scheme.schemeId) errors.push('schemeId is required');
    if (!scheme.name) errors.push('name is required');
    if (!scheme.description) errors.push('description is required');
    if (!scheme.eligibilityCriteria?.length) errors.push('eligibilityCriteria must not be empty');
    if (!scheme.benefits?.length) errors.push('benefits must not be empty');

    return { valid: errors.length === 0, errors };
  }

  /**
   * Check if the knowledge base is configured.
   */
  isConfigured(): boolean {
    return !!(this.knowledgeBaseId && this.dataSourceId);
  }

  getKnowledgeBaseId(): string | undefined {
    return this.knowledgeBaseId;
  }
}
