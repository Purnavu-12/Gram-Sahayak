# Bedrock Integration Guide

## Overview

Gram Sahayak integrates with **AWS Bedrock** to enhance its voice-first AI capabilities while maintaining full backward compatibility through a fallback-first architecture.

### Bedrock Models Used

| Model | Purpose | Fallback |
|-------|---------|----------|
| **Claude 3.5 Sonnet** | Demographic extraction from voice conversations | Claude 3 Haiku → Existing NLP |
| **Amazon Nova Pro** | Speech-to-text and text-to-speech | Existing IndicWhisper/TTS |
| **Amazon Titan Embeddings** | Semantic scheme search | Neo4j graph queries |
| **Bedrock Guardrails** | PII detection and redaction | Local regex patterns |

### Architecture

```
┌─────────────┐     ┌──────────────────────────────────────────┐
│  Client/App  │────▶│            API Gateway (:3000)            │
└─────────────┘     │  /health/bedrock  /metrics/bedrock        │
                    │  /config/bedrock                           │
                    └───────────┬───────────────────────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                  ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ Voice Engine  │  │ Scheme       │  │ Dialect      │
    │ (:3001)       │  │ Matcher      │  │ Detector     │
    │               │  │ (:8002)      │  │ (:8001)      │
    │ Nova Pro ──┐  │  │ KB Search ─┐│  │ Nova Pro ──┐ │
    │ Existing ◀─┘  │  │ Neo4j    ◀─┘│  │ Existing ◀─┘ │
    └──────────────┘  └──────────────┘  └──────────────┘
              │                 │                  │
              └─────────────────┼──────────────────┘
                                ▼
                  ┌──────────────────────────┐
                  │   Shared Bedrock Layer   │
                  │                          │
                  │ • BedrockAgentWrapper    │
                  │ • FallbackHandler        │
                  │ • GuardrailsIntegration  │
                  │ • MetricsCollector       │
                  │ • ResponseValidator      │
                  │ • KBIngestionPipeline    │
                  └──────────────────────────┘
                                │
                  ┌─────────────┼─────────────┐
                  ▼             ▼              ▼
           ┌──────────┐  ┌──────────┐  ┌──────────┐
           │  Claude   │  │ Nova Pro │  │  Titan   │
           │  3.5      │  │ STT/TTS  │  │ Embed    │
           └──────────┘  └──────────┘  └──────────┘
```

## Quick Start

### 1. Configure Environment

Copy `.env.example` and set your AWS Bedrock credentials:

```bash
cp .env.example .env

# Required Bedrock settings
BEDROCK_ENABLED=true
BEDROCK_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Optional: Knowledge Base and Guardrails
BEDROCK_KB_ID=your-kb-id
BEDROCK_GUARDRAILS_POLICY_ID=your-policy-id
```

### 2. Start Services

```bash
# With Docker Compose (recommended)
docker-compose up

# Or individually for development
npm run dev
```

### 3. Ingest Sample Schemes

```bash
npx ts-node scripts/ingest-sample-schemes.ts
```

### 4. Verify Integration

```bash
# Check Bedrock health
curl http://localhost:3000/health/bedrock

# Check service-specific status
curl http://localhost:3001/bedrock/status  # Voice Engine
curl http://localhost:8002/bedrock/status  # Scheme Matcher
curl http://localhost:8001/bedrock/status  # Dialect Detector

# View metrics
curl http://localhost:3000/metrics/bedrock
curl "http://localhost:3000/metrics/bedrock?format=prometheus"

# View configuration
curl http://localhost:3000/config/bedrock
```

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BEDROCK_ENABLED` | `false` | Enable Bedrock integration |
| `BEDROCK_REGION` | `us-east-1` | AWS region for Bedrock |
| `AWS_ACCESS_KEY_ID` | - | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | - | AWS secret key |
| `BEDROCK_CLAUDE_MODEL_ID` | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Claude model ID |
| `BEDROCK_CLAUDE_FALLBACK_MODEL_ID` | `anthropic.claude-3-haiku-20240307-v1:0` | Claude fallback |
| `BEDROCK_NOVA_PRO_STT_MODEL_ID` | `amazon.nova-pro-v1:0` | Nova Pro STT model |
| `BEDROCK_NOVA_PRO_TTS_MODEL_ID` | `amazon.nova-pro-v1:0` | Nova Pro TTS model |
| `BEDROCK_TITAN_EMBEDDINGS_MODEL_ID` | `amazon.titan-embed-text-v2:0` | Titan embeddings |
| `BEDROCK_GUARDRAILS_POLICY_ID` | - | Guardrails policy ID |
| `BEDROCK_KB_ID` | - | Knowledge Base ID |
| `BEDROCK_KB_DATA_SOURCE_ID` | - | KB data source ID |
| `BEDROCK_FALLBACK_TIMEOUT` | `3000` | Fallback timeout (ms) |
| `BEDROCK_FALLBACK_RETRIES` | `2` | Retry count |

### Per-Service Toggle

Each service can be toggled independently:

```bash
# Toggle Voice Engine Bedrock
curl -X POST http://localhost:3001/bedrock/toggle -H "Content-Type: application/json" -d '{"enabled": true}'

# Toggle Scheme Matcher Bedrock
curl -X POST http://localhost:8002/bedrock/toggle -H "Content-Type: application/json" -d '{"enabled": true}'
```

## Fallback Behavior

The system uses a **fallback-first** architecture:

1. **Bedrock Enabled**: Try Bedrock model → If fails, try fallback model → If fails, use existing implementation
2. **Bedrock Disabled**: Always use existing implementation
3. **Invalid Credentials**: Start with Bedrock disabled, log warning

### Circuit Breaker

- Opens after 5 consecutive failures (configurable)
- Half-open after 60 seconds
- Closes after 2 consecutive successes
- All requests route to fallback when open

## Monitoring

### Metrics Endpoint

```
GET /metrics/bedrock
GET /metrics/bedrock?format=prometheus
```

Tracks:
- API call counts by model and status
- Latency percentiles (p50, p95, p99)
- Cost by model (estimated)
- Fallback counts by service and reason
- Guardrails PII detections
- Knowledge Base query metrics

### Alerts

Automatic alert when:
- Fallback rate exceeds 20% for 5 minutes
- Circuit breaker open for > 10 minutes
- End-to-end latency P95 > 5 seconds

## Sample Schemes

The Knowledge Base includes 20 government schemes:

| # | Scheme | Category |
|---|--------|----------|
| 1 | PM-KISAN | Agriculture |
| 2 | MGNREGA | Employment |
| 3 | PM Jan Dhan Yojana | Financial Inclusion |
| 4 | Ayushman Bharat | Health |
| 5 | PM Awas Yojana Gramin | Housing |
| 6 | National Social Assistance | Pension |
| 7 | Mid Day Meal | Education |
| 8 | PM Ujjwala Yojana | Women/Energy |
| 9 | PM Suraksha Bima | Insurance |
| 10 | PM Jeevan Jyoti Bima | Insurance |
| 11 | Atal Pension Yojana | Pension |
| 12 | Sukanya Samriddhi | Women/Savings |
| 13 | PM MUDRA | Entrepreneurship |
| 14 | PM Fasal Bima | Agriculture |
| 15 | PM Kaushal Vikas | Skill Development |
| 16 | DDU Grameen Kaushalya | Rural Skills |
| 17 | National Scholarship | Education |
| 18 | Swachh Bharat Gramin | Sanitation |
| 19 | PM Matru Vandana | Women/Maternity |
| 20 | Soil Health Card | Agriculture |

All schemes include bilingual descriptions (Hindi and English).

## Testing

```bash
# Run Bedrock integration tests
npx jest shared/bedrock/bedrock-integration.test.ts --no-coverage --forceExit

# Run all tests
npm test
```

### Test Coverage

- **28 tests** covering all Bedrock components
- Property-based tests (fast-check) for:
  - Fallback routing on failure
  - Model tier fallback sequence
  - Continuous operation during outage
  - Response validation
  - Confidence score thresholds
  - Metrics collection
  - PII detection and redaction
  - Scheme data validation
  - Configuration management

## File Structure

```
shared/
├── bedrock/
│   ├── index.ts                    # Barrel exports
│   ├── bedrock-agent-wrapper.ts    # AWS Bedrock API wrapper
│   ├── bedrock-config.ts           # Configuration management
│   ├── fallback-handler.ts         # Fallback routing + circuit breaker
│   ├── guardrails-integration.ts   # PII detection/redaction
│   ├── kb-ingestion-pipeline.ts    # Knowledge Base ingestion
│   ├── metrics-collector.ts        # Prometheus-compatible metrics
│   ├── response-validator.ts       # Model response validation
│   ├── sample-schemes.json         # 20 bilingual government schemes
│   └── bedrock-integration.test.ts # 28 property-based tests
├── types/
│   └── bedrock.ts                  # All Bedrock TypeScript interfaces
scripts/
└── ingest-sample-schemes.ts        # Scheme ingestion script
```
