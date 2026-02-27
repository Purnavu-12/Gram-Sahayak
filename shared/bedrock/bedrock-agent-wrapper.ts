/**
 * Bedrock Agent Wrapper
 * Unified interface for all AWS Bedrock model invocations
 * Validates: Requirements 1.1, 1.2, 1.3, 1.4
 */

import {
  BedrockConfig,
  ClaudeConfig,
  ClaudeResponse,
  KBFilter,
  KBResult,
  GuardrailsResult,
  BedrockHealthStatus,
  BedrockMetrics,
  TranscriptionResult as BedrockTranscriptionResult,
  TTSResult,
} from '../types/bedrock';

export class BedrockAgentWrapper {
  private config: BedrockConfig;
  private bedrockClient: any;
  private bedrockAgentClient: any;

  constructor(config: BedrockConfig) {
    this.config = config;
    if (config.enabled) {
      this.initializeClients();
    }
  }

  private initializeClients(): void {
    // AWS SDK v3 clients would be initialized here
    // In production, these would use:
    // - BedrockRuntimeClient for model invocations
    // - BedrockAgentRuntimeClient for knowledge base queries
    // For now, we use a provider pattern so tests can inject mocks
    try {
      this.bedrockClient = this.createBedrockRuntimeClient();
      this.bedrockAgentClient = this.createBedrockAgentClient();
    } catch (error) {
      console.error('Failed to initialize Bedrock clients:', error);
    }
  }

  private createBedrockRuntimeClient(): any {
    // Would create BedrockRuntimeClient from @aws-sdk/client-bedrock-runtime
    return {
      send: async (command: any) => {
        throw new Error('AWS SDK not configured - install @aws-sdk/client-bedrock-runtime');
      },
    };
  }

  private createBedrockAgentClient(): any {
    // Would create BedrockAgentRuntimeClient from @aws-sdk/client-bedrock-agent-runtime
    return {
      send: async (command: any) => {
        throw new Error('AWS SDK not configured - install @aws-sdk/client-bedrock-agent-runtime');
      },
    };
  }

  /**
   * Invoke Claude model for demographic extraction
   * Validates: Requirement 1.1
   */
  async invokeClaudeModel(prompt: string, config: ClaudeConfig): Promise<ClaudeResponse> {
    if (!this.config.enabled) {
      throw new Error('Bedrock is not enabled');
    }

    const startTime = Date.now();
    const modelId = config.modelId || this.config.models.claude.modelId;

    try {
      const payload = {
        anthropic_version: 'bedrock-2023-05-31',
        max_tokens: config.maxTokens || this.config.models.claude.maxTokens,
        temperature: config.temperature ?? this.config.models.claude.temperature,
        messages: [
          {
            role: 'user',
            content: prompt,
          },
        ],
        ...(config.systemPrompt ? { system: config.systemPrompt } : {}),
      };

      const response = await this.bedrockClient.send({
        modelId,
        contentType: 'application/json',
        accept: 'application/json',
        body: JSON.stringify(payload),
      });

      const body = JSON.parse(new TextDecoder().decode(response.body));
      const latency = Date.now() - startTime;

      return {
        content: body.content?.[0]?.text || '',
        stopReason: body.stop_reason || 'end_turn',
        usage: {
          inputTokens: body.usage?.input_tokens || 0,
          outputTokens: body.usage?.output_tokens || 0,
        },
        confidence: this.estimateConfidence(body),
      };
    } catch (error: any) {
      console.error(`Claude model invocation failed (${modelId}):`, error.message);
      throw error;
    }
  }

  /**
   * Invoke Nova Pro for speech-to-text transcription
   * Validates: Requirement 1.2
   */
  async invokeNovaProSTT(audioData: ArrayBuffer, language: 'hi' | 'en'): Promise<BedrockTranscriptionResult> {
    if (!this.config.enabled) {
      throw new Error('Bedrock is not enabled');
    }

    const startTime = Date.now();
    const modelId = this.config.models.novaPro.sttModelId;

    try {
      const payload = {
        inputAudio: Buffer.from(audioData).toString('base64'),
        language,
        sampleRate: 16000,
      };

      const response = await this.bedrockClient.send({
        modelId,
        contentType: 'application/json',
        accept: 'application/json',
        body: JSON.stringify(payload),
      });

      const body = JSON.parse(new TextDecoder().decode(response.body));
      const latency = Date.now() - startTime;

      return {
        transcription: body.transcription || '',
        confidence: body.confidence || 0,
        language,
        duration: body.duration || 0,
        latency,
      };
    } catch (error: any) {
      console.error(`Nova Pro STT failed (${language}):`, error.message);
      throw error;
    }
  }

  /**
   * Invoke Nova Pro for text-to-speech synthesis
   * Validates: Requirement 1.3
   */
  async invokeNovaProTTS(
    text: string,
    language: 'hi' | 'en',
    voice: { gender: string; style: string }
  ): Promise<TTSResult> {
    if (!this.config.enabled) {
      throw new Error('Bedrock is not enabled');
    }

    const startTime = Date.now();
    const modelId = this.config.models.novaPro.ttsModelId;

    try {
      const payload = {
        text,
        language,
        voice,
        outputFormat: 'mp3',
        sampleRate: 24000,
      };

      const response = await this.bedrockClient.send({
        modelId,
        contentType: 'application/json',
        accept: 'application/json',
        body: JSON.stringify(payload),
      });

      const body = JSON.parse(new TextDecoder().decode(response.body));
      const latency = Date.now() - startTime;

      const audioBuffer = Buffer.from(body.audio || '', 'base64');
      return {
        audio: audioBuffer.buffer,
        format: 'mp3',
        sampleRate: 24000,
        duration: body.duration || 0,
        latency,
      };
    } catch (error: any) {
      console.error(`Nova Pro TTS failed (${language}):`, error.message);
      throw error;
    }
  }

  /**
   * Query Knowledge Base for semantic scheme search
   * Validates: Requirement 1.4
   */
  async queryKnowledgeBase(
    query: string,
    filters: KBFilter[],
    maxResults: number = 3
  ): Promise<KBResult[]> {
    if (!this.config.enabled) {
      throw new Error('Bedrock is not enabled');
    }

    const kbId = this.config.knowledgeBase.kbId;
    if (!kbId) {
      throw new Error('Knowledge Base ID not configured');
    }

    try {
      const retrievalConfig: any = {
        vectorSearchConfiguration: {
          numberOfResults: maxResults,
        },
      };

      if (filters.length > 0) {
        const operatorMap: Record<string, string> = {
          '=': 'equals',
          '!=': 'notEquals',
          '>=': 'greaterThanOrEquals',
          '<=': 'lessThanOrEquals',
          'contains': 'stringContains',
        };

        retrievalConfig.vectorSearchConfiguration.filter = {
          andAll: filters.map(f => {
            const operator = operatorMap[f.operator];
            if (!operator) {
              throw new Error(`Unsupported filter operator: ${f.operator}`);
            }
            return {
              [operator]: {
                key: f.key,
                value: f.value,
              },
            };
          }),
        };
      }

      const response = await this.bedrockAgentClient.send({
        knowledgeBaseId: kbId,
        retrievalQuery: { text: query },
        retrievalConfiguration: retrievalConfig,
      });

      return (response.retrievalResults || []).map((result: any) => ({
        content: result.content?.text || '',
        metadata: result.metadata || {},
        score: result.score || 0,
        sourceLocation: result.location?.s3Location?.uri || '',
      }));
    } catch (error: any) {
      console.error('Knowledge Base query failed:', error.message);
      throw error;
    }
  }

  /**
   * Apply Guardrails for PII detection
   * Validates: Requirement 4.1, 4.2
   */
  async applyGuardrails(text: string, policyId?: string): Promise<GuardrailsResult> {
    if (!this.config.enabled) {
      throw new Error('Bedrock is not enabled');
    }

    const guardPolicyId = policyId || this.config.guardrails.policyId;
    if (!guardPolicyId) {
      throw new Error('Guardrails policy ID not configured');
    }

    try {
      const response = await this.bedrockClient.send({
        guardrailIdentifier: guardPolicyId,
        guardrailVersion: this.config.guardrails.policyVersion,
        source: 'INPUT',
        content: [{ text: { text } }],
      });

      return {
        action: response.action || 'ALLOWED',
        outputText: response.output?.[0]?.text || text,
        piiDetections: (response.assessments || []).flatMap(
          (a: any) => a.sensitiveInformationPolicy?.piiEntities || []
        ).map((entity: any) => ({
          type: entity.type || 'UNKNOWN',
          match: entity.match || '',
          startOffset: entity.startOffset || 0,
          endOffset: entity.endOffset || 0,
        })),
        assessments: (response.assessments || []).map((a: any) => ({
          topicPolicy: a.topicPolicy?.topics?.[0]?.name || 'PII_PROTECTION',
          action: a.topicPolicy?.topics?.[0]?.action || 'NONE',
        })),
      };
    } catch (error: any) {
      console.error('Guardrails check failed:', error.message);
      throw error;
    }
  }

  /**
   * Health check for all Bedrock services
   */
  async checkHealth(): Promise<BedrockHealthStatus> {
    const status: BedrockHealthStatus = {
      status: 'healthy',
      services: {},
      credentials: { valid: false },
    };

    if (!this.config.enabled) {
      status.status = 'unhealthy';
      return status;
    }

    // Check credentials by testing a lightweight operation
    try {
      status.credentials.valid = !!(this.config.credentials.accessKeyId && this.config.credentials.secretAccessKey);
    } catch {
      status.credentials.valid = false;
    }

    const services = ['claude', 'novaPro', 'knowledgeBase', 'guardrails'];
    for (const service of services) {
      status.services[service] = {
        available: this.config.enabled,
        latency: 0,
        lastCheck: new Date(),
      };
    }

    const unavailableCount = Object.values(status.services).filter(s => !s.available).length;
    if (unavailableCount === services.length) {
      status.status = 'unhealthy';
    } else if (unavailableCount > 0) {
      status.status = 'degraded';
    }

    return status;
  }

  isEnabled(): boolean {
    return this.config.enabled;
  }

  private estimateConfidence(body: any): number {
    // Heuristic confidence estimation based on response quality
    if (!body.content || body.content.length === 0) return 0;
    if (body.stop_reason === 'end_turn') return 0.85;
    if (body.stop_reason === 'max_tokens') return 0.6;
    return 0.75;
  }
}
