# AWS Bedrock Integration Guide

This guide explains how to integrate Gram Sahayak with AWS Bedrock for AI-powered scheme recommendations, natural language understanding, and knowledge base retrieval.

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────────┐     ┌───────────────────┐
│   Gram Sahayak  │     │    AWS Bedrock        │     │  Knowledge Base   │
│   Services      │────▶│    Runtime API        │────▶│  (Scheme Data)    │
│                 │     │                       │     │                   │
│ - API Gateway   │     │ - Claude 3 Sonnet     │     │ - S3 Data Source  │
│ - Conversation  │     │ - Guardrails          │     │ - OpenSearch      │
│   Orchestrator  │     │ - Knowledge Base      │     │   Serverless      │
└─────────────────┘     └──────────────────────┘     └───────────────────┘
```

## Prerequisites

1. **AWS Account** with Bedrock access enabled
2. **Model Access**: Request access to Claude 3 Sonnet (or your preferred model) in the AWS Bedrock console
3. **IAM Role/User** with the following permissions:
   - `bedrock:InvokeModel`
   - `bedrock:InvokeModelWithResponseStream`
   - `bedrock-agent:Retrieve`
   - `bedrock-agent:RetrieveAndGenerate`

## Setup Steps

### 1. Install AWS SDK Dependencies

```bash
npm install @aws-sdk/client-bedrock-runtime @aws-sdk/client-bedrock-agent-runtime
```

### 2. Configure Environment Variables

```bash
# AWS Configuration
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=<your-access-key>
export AWS_SECRET_ACCESS_KEY=<your-secret-key>

# Bedrock Configuration
export BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
export BEDROCK_MAX_TOKENS=4096
export BEDROCK_TEMPERATURE=0.7

# Knowledge Base (optional)
export BEDROCK_KB_ID=<your-knowledge-base-id>
export BEDROCK_KB_DATA_SOURCE_ID=<your-data-source-id>

# Guardrails (optional)
export BEDROCK_GUARDRAIL_ID=<your-guardrail-id>
export BEDROCK_GUARDRAIL_VERSION=1
```

### 3. Create a Knowledge Base for Scheme Data

1. Go to **AWS Bedrock Console** → **Knowledge Bases** → **Create**
2. Choose **S3** as the data source
3. Upload scheme documents using the ingestion pipeline:

```typescript
import { KBIngestionPipeline } from './shared/bedrock';

const pipeline = new KBIngestionPipeline();
const doc = pipeline.prepareDocument({
  schemeId: 'PM-KISAN-001',
  name: 'PM-KISAN',
  nameHi: 'प्रधानमंत्री किसान सम्मान निधि',
  description: 'Income support to small and marginal farmer families',
  eligibilityCriteria: ['Small and marginal farmers', 'Land ownership required'],
  benefits: ['₹6,000 per year in 3 installments'],
  requiredDocuments: ['Aadhaar Card', 'Land Records', 'Bank Account Details'],
  applicationProcess: ['Visit nearest CSC', 'Fill application form', 'Submit documents'],
  ministry: 'Ministry of Agriculture',
  category: 'Agriculture',
  lastUpdated: '2024-01-01',
});
// Upload `doc` to your S3 data source bucket
```

4. Sync the data source in the Bedrock console

### 4. Set Up Guardrails (Recommended)

1. Go to **AWS Bedrock Console** → **Guardrails** → **Create**
2. Configure:
   - **PII Detection**: Enable for Aadhaar, PAN, phone numbers, bank accounts
   - **Topic Filtering**: Block irrelevant topics (not related to government schemes)
   - **Content Filtering**: Enable for harmful content

### 5. Initialize in Your Code

```typescript
import { BedrockAgentWrapper, FallbackHandler, GuardrailsIntegration, MetricsCollector } from './shared/bedrock';

// Initialize
const bedrock = new BedrockAgentWrapper();
await bedrock.initialize();

const fallback = new FallbackHandler({ failureThreshold: 5, resetTimeoutMs: 60000 });
const guardrails = new GuardrailsIntegration();
const metrics = new MetricsCollector();

// Use with circuit breaker for resilience
const response = await fallback.execute(
  // Primary: Use Bedrock
  async () => {
    const result = await bedrock.invokeModel({
      prompt: 'What schemes is a 30-year-old farmer in Maharashtra eligible for?',
      systemPrompt: 'You are Gram Sahayak, a helpful assistant for Indian government schemes.',
    });
    metrics.recordLatency('invokeModel', result.latencyMs, result.modelId);
    metrics.recordTokenUsage(result.inputTokens, result.outputTokens, result.modelId);
    return result;
  },
  // Fallback: Return cached/default response
  async () => {
    return { text: 'I am currently unable to process your request. Please try again later.' };
  }
);

// Sanitize response for PII
const sanitized = guardrails.detectAndRedactPii(response.text);
```

### 6. Use Knowledge Base for Scheme Queries

```typescript
const kbResponse = await bedrock.retrieveAndGenerate({
  query: 'What documents do I need for PM-KISAN?',
  knowledgeBaseId: process.env.BEDROCK_KB_ID,
});

console.log(kbResponse.text);
console.log('Sources:', kbResponse.citations);
```

## Module Reference

| Module | Description |
|--------|------------|
| `BedrockAgentWrapper` | Core wrapper for Bedrock Runtime API calls |
| `FallbackHandler` | Circuit breaker for API resilience |
| `GuardrailsIntegration` | PII detection (Aadhaar, PAN, phone, email, IFSC) |
| `ResponseValidator` | Response quality and safety checks |
| `MetricsCollector` | Prometheus-format metrics for monitoring |
| `KBIngestionPipeline` | Prepare and validate scheme documents for KB |

## Cost Considerations

- **Claude 3 Sonnet**: ~$3/M input tokens, ~$15/M output tokens
- **Knowledge Base**: OpenSearch Serverless costs + S3 storage
- **Guardrails**: $0.75/1K text units for PII detection

Use the `MetricsCollector` to monitor token usage and set up CloudWatch alarms.
