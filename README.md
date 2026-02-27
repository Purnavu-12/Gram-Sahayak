# Gram Sahayak (ग्राम सहायक)

Voice-first AI assistant for rural India's government welfare access — now with a multilingual website supporting **23 Indian languages**.

## Website

The Gram Sahayak website provides a user-friendly interface for discovering government schemes, managing profiles, and tracking applications — fully translated into all 22 scheduled Indian languages plus English.

### Supported Languages

Hindi (हिन्दी), Bengali (বাংলা), Telugu (తెలుగు), Marathi (मराठी), Tamil (தமிழ்), Gujarati (ગુજરાતી), Kannada (ಕನ್ನಡ), Malayalam (മലയാളം), Odia (ଓଡ଼ିଆ), Punjabi (ਪੰਜਾਬੀ), Assamese (অসমীয়া), Urdu (اردو), Maithili (मैथिली), Santali (ᱥᱟᱱᱛᱟᱲᱤ), Kashmiri (कॉशुर), Nepali (नेपाली), Sindhi (سنڌي), Dogri (डोगरी), Konkani (कोंकणी), Manipuri (মণিপুরী), Bodo (बड़ो), Sanskrit (संस्कृतम्), English

### Run the Website

```bash
cd website
npm install
npm run dev
# Opens at http://localhost:5173
```

### Website Pages

- **Home** — Hero section, features, stats, how-it-works guide
- **Find Schemes** — Form to enter profile details and discover matching government schemes
- **My Profile** — Save personal, location, and economic details
- **Track Applications** — View status of submitted applications
- **About** — Mission, features, and technology information

## Architecture

Gram Sahayak is built as a microservices architecture with the following components:

- **Website** (React/TypeScript/Vite): Multilingual frontend with i18n for 23 languages
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
   - Website: http://localhost:5173
   - API Gateway: http://localhost:3000
   - Voice Engine: http://localhost:3001
   - Dialect Detector: http://localhost:8001
   - Scheme Matcher: http://localhost:8002
   - Form Generator: http://localhost:3002

## Development

### Install dependencies

```bash
# Root (backend services)
npm install

# Website
cd website && npm install
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

### Build

```bash
# Backend services
npm run build

# Website
cd website && npm run build
```

## Testing Frameworks

- **Jest**: Unit testing for TypeScript services
- **Pytest**: Unit testing for Python services
- **Hypothesis**: Property-based testing for Python services
- **fast-check**: Property-based testing for TypeScript services

## Project Structure

```
gram-sahayak/
├── website/                   # React frontend (Vite + TypeScript)
│   ├── src/
│   │   ├── components/        # Navbar, Footer, LanguageSelector
│   │   ├── pages/             # Home, Schemes, Profile, Track, About
│   │   ├── i18n/              # Internationalization setup
│   │   │   └── locales/       # 23 language translation files
│   │   └── styles/            # CSS styles
│   └── package.json
├── services/
│   ├── api-gateway/           # API Gateway service
│   ├── voice-engine/          # Voice processing service
│   ├── dialect-detector/      # Dialect detection service
│   ├── scheme-matcher/        # Scheme matching service
│   └── form-generator/        # Form generation service
├── shared/
│   └── types/                 # Shared TypeScript interfaces
├── docker-compose.yml         # Docker orchestration
└── package.json               # Root package configuration
```

## Core Interfaces

The system defines core TypeScript interfaces for service contracts:

- `VoiceEngine`: Speech processing interface
- `DialectDetector`: Dialect identification interface
- `SchemeMatcher`: Scheme matching interface

See `shared/types/` for complete interface definitions.
