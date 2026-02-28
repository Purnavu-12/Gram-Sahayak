/**
 * AWS Bedrock Agent Wrapper
 * 
 * Provides a unified interface to AWS Bedrock Runtime for invoking
 * foundation models (Claude, Nova Pro, Titan) with proper error handling,
 * retry logic, and response validation.
 */

import { BedrockConfig, loadBedrockConfig } from './bedrock-config';

export interface InvokeModelRequest {
  prompt: string;
  systemPrompt?: string;
  maxTokens?: number;
  temperature?: number;
  topP?: number;
  stopSequences?: string[];
}

export interface InvokeModelResponse {
  text: string;
  inputTokens: number;
  outputTokens: number;
  stopReason: string;
  latencyMs: number;
  modelId: string;
}

export interface RetrieveAndGenerateRequest {
  query: string;
  knowledgeBaseId?: string;
  modelId?: string;
  maxResults?: number;
}

export interface RetrieveAndGenerateResponse {
  text: string;
  citations: Citation[];
  latencyMs: number;
}

export interface Citation {
  text: string;
  sourceUri: string;
  score: number;
}

export class BedrockAgentWrapper {
  private config: BedrockConfig;
  private bedrockClient: any;
  private kbClient: any;

  constructor(config?: Partial<BedrockConfig>) {
    this.config = { ...loadBedrockConfig(), ...config };
  }

  /**
   * Initialize AWS SDK clients.
   * Call this after setting up AWS credentials.
   */
  async initialize(): Promise<void> {
    try {
      // Dynamic import to avoid hard dependency on AWS SDK at module load time
      const { BedrockRuntimeClient } = await import('@aws-sdk/client-bedrock-runtime');
      const { BedrockAgentRuntimeClient } = await import('@aws-sdk/client-bedrock-agent-runtime');

      this.bedrockClient = new BedrockRuntimeClient({
        region: this.config.region,
        maxAttempts: this.config.maxRetries,
      });

      this.kbClient = new BedrockAgentRuntimeClient({
        region: this.config.region,
        maxAttempts: this.config.maxRetries,
      });
    } catch (error: any) {
      throw new Error(
        `Failed to initialize Bedrock clients. Ensure @aws-sdk/client-bedrock-runtime ` +
        `and @aws-sdk/client-bedrock-agent-runtime are installed. Error: ${error.message}`
      );
    }
  }

  /**
   * Invoke a Bedrock foundation model (e.g., Claude, Nova Pro).
   */
  async invokeModel(request: InvokeModelRequest): Promise<InvokeModelResponse> {
    if (!this.bedrockClient) {
      throw new Error('Bedrock client not initialized. Call initialize() first.');
    }

    const startTime = Date.now();
    const { InvokeModelCommand } = await import('@aws-sdk/client-bedrock-runtime');

    const messages = [{ role: 'user', content: request.prompt }];
    const body = JSON.stringify({
      anthropic_version: 'bedrock-2023-05-31',
      max_tokens: request.maxTokens || this.config.maxTokens,
      temperature: request.temperature ?? this.config.temperature,
      top_p: request.topP ?? this.config.topP,
      system: request.systemPrompt || '',
      messages,
      stop_sequences: request.stopSequences || [],
    });

    const command = new InvokeModelCommand({
      modelId: this.config.modelId,
      contentType: 'application/json',
      accept: 'application/json',
      body: new TextEncoder().encode(body),
    });

    const response = await this.bedrockClient.send(command);
    const responseBody = JSON.parse(new TextDecoder().decode(response.body));
    const latencyMs = Date.now() - startTime;

    return {
      text: responseBody.content?.[0]?.text || '',
      inputTokens: responseBody.usage?.input_tokens || 0,
      outputTokens: responseBody.usage?.output_tokens || 0,
      stopReason: responseBody.stop_reason || 'unknown',
      latencyMs,
      modelId: this.config.modelId,
    };
  }

  /**
   * Retrieve and generate using a Bedrock Knowledge Base.
   */
  async retrieveAndGenerate(request: RetrieveAndGenerateRequest): Promise<RetrieveAndGenerateResponse> {
    if (!this.kbClient) {
      throw new Error('Knowledge Base client not initialized. Call initialize() first.');
    }

    const startTime = Date.now();
    const { RetrieveAndGenerateCommand } = await import('@aws-sdk/client-bedrock-agent-runtime');

    const kbId = request.knowledgeBaseId || this.config.knowledgeBaseId;
    if (!kbId) {
      throw new Error('Knowledge Base ID not configured. Set BEDROCK_KB_ID environment variable.');
    }

    const command = new RetrieveAndGenerateCommand({
      input: { text: request.query },
      retrieveAndGenerateConfiguration: {
        type: 'KNOWLEDGE_BASE',
        knowledgeBaseConfiguration: {
          knowledgeBaseId: kbId,
          modelArn: `arn:aws:bedrock:${this.config.region}::foundation-model/${request.modelId || this.config.modelId}`,
          retrievalConfiguration: {
            vectorSearchConfiguration: {
              numberOfResults: request.maxResults || 5,
            },
          },
        },
      },
    });

    const response = await this.kbClient.send(command);
    const latencyMs = Date.now() - startTime;

    const citations: Citation[] = (response.citations || []).map((c: any) => ({
      text: c.generatedResponsePart?.textResponsePart?.text || '',
      sourceUri: c.retrievedReferences?.[0]?.location?.s3Location?.uri || '',
      score: c.retrievedReferences?.[0]?.score || 0,
    }));

    return {
      text: response.output?.text || '',
      citations,
      latencyMs,
    };
  }

  /**
   * Get the current configuration.
   */
  getConfig(): BedrockConfig {
    return { ...this.config };
  }
}
