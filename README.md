# Gram Sahayak

Voice-first AI assistant for rural India's government welfare access.

## Architecture

Gram Sahayak is built as a microservices architecture with the following services:

- **API Gateway** (TypeScript/Express): Authentication, rate limiting, and request routing
- **Voice Engine** (TypeScript): Speech-to-text and text-to-speech processing
- **Dialect Detector** (Python/FastAPI): Indian language and dialect identification
- **Scheme Matcher** (Python/FastAPI): Government scheme discovery and eligibility matching
- **Form Generator** (TypeScript): Conversational form filling and PDF generation

## Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)

## Quick Start

1. Start all services with Docker Compose:
```bash
docker-compose up
```

2. Services will be available at:
   - API Gateway: http://localhost:3000
   - Voice Engine: http://localhost:3001
   - Dialect Detector: http://localhost:8001
   - Scheme Matcher: http://localhost:8002
   - Form Generator: http://localhost:3002

## Development

### Install dependencies

```bash
npm install
```

### Run tests

```bash
# All tests
npm test

# TypeScript services
npm test --workspace=services/voice-engine

# Python services
cd services/dialect-detector && pytest
cd services/scheme-matcher && pytest
```

### Build services

```bash
npm run build
```

## Testing Frameworks

- **Jest**: Unit testing for TypeScript services
- **Pytest**: Unit testing for Python services
- **Hypothesis**: Property-based testing for Python services
- **fast-check**: Property-based testing for TypeScript services

## Project Structure

```
gram-sahayak/
├── services/
│   ├── api-gateway/          # API Gateway service
│   ├── voice-engine/         # Voice processing service
│   ├── dialect-detector/     # Dialect detection service
│   ├── scheme-matcher/       # Scheme matching service
│   └── form-generator/       # Form generation service
├── shared/
│   └── types/                # Shared TypeScript interfaces
├── docker-compose.yml        # Docker orchestration
└── package.json              # Root package configuration
```

## Core Interfaces

The system defines core TypeScript interfaces for service contracts:

- `VoiceEngine`: Speech processing interface
- `DialectDetector`: Dialect identification interface
- `SchemeMatcher`: Scheme matching interface

See `shared/types/` for complete interface definitions.
