# Gram Sahayak — Project Analysis & Development Plan

> **Date**: February 28, 2026  
> **Purpose**: Comprehensive project review, trajectory analysis, and prototype development roadmap

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Development Timeline — Day One to Today](#2-development-timeline)
3. [Architecture Deep Dive](#3-architecture-deep-dive)
4. [Current State Assessment](#4-current-state-assessment)
5. [Gap Analysis — Plan vs Reality](#5-gap-analysis--plan-vs-reality)
6. [Deep Research — What Should Be Done](#6-deep-research--what-should-be-done)
7. [What Should Be Changed](#7-what-should-be-changed)
8. [Prototype-to-Product Roadmap](#8-prototype-to-product-roadmap)
9. [Questions for Clarification](#9-questions-for-clarification)

---

## 1. Project Overview

### What is Gram Sahayak?
**Gram Sahayak** ("Village Helper") is a **voice-first AI assistant** designed to help rural Indian citizens access government welfare schemes. It bridges the gap between complex government bureaucracy and low-literacy rural populations by:

- **Listening** in the user's native language/dialect (22+ Indian languages)
- **Understanding** their needs through natural conversation
- **Matching** them to eligible government schemes (700+ schemes)
- **Guiding** them through document requirements and application forms
- **Tracking** their application status across government portals

### Core Value Proposition
| Problem | Gram Sahayak Solution |
|---------|----------------------|
| Low literacy barriers | Voice-first interface — no reading/writing needed |
| Language diversity (22 scheduled languages) | Multi-language support with dialect detection |
| Complex scheme eligibility rules | AI-powered scheme matching with Neo4j graph |
| Confusing paperwork | Conversational form filling → auto-generated PDFs |
| No application status visibility | Government portal integration & tracking |
| Privacy concerns | AES-256 encryption, PII anonymization, data deletion |
| Poor connectivity in rural areas | Offline-first with sync capability |

### Tech Stack Summary
| Layer | Technology |
|-------|-----------|
| **Frontend** | Static HTML/CSS/JS landing page (vanilla) |
| **API Gateway** | TypeScript + Express.js (JWT, rate limiting, circuit breaker) |
| **Voice Engine** | TypeScript + WebRTC + WebSocket |
| **Dialect Detector** | Python + FastAPI + NumPy |
| **Scheme Matcher** | Python + FastAPI + Neo4j |
| **Form Generator** | TypeScript + Express + Redis + PDFKit |
| **Document Guide** | Python + FastAPI |
| **Application Tracker** | Python + FastAPI + Cryptography |
| **User Profile** | Python + FastAPI + Cryptography |
| **Accessibility** | TypeScript + Express |
| **AI/LLM** | AWS Bedrock (Claude 3 Sonnet, Nova Pro, Titan Embeddings) |
| **Databases** | Neo4j (schemes graph), Redis (sessions/cache) |
| **Infra** | Docker Compose, GitHub Actions CI |
| **Testing** | Jest + fast-check (TS), Pytest + Hypothesis (Python) |

---

## 2. Development Timeline

### Chronological Journey

```
Jan 31, 2026 ─── GENESIS ─────────────────────────────────────────────
│  "first commit" by Purnavu-12
│  Repository created with initial Kiro specs
│  10 core requirements defined in .kiro/gram-sahayak/requirements.md
│  15 implementation tasks planned in .kiro/gram-sahayak/tasks.md
│
Feb 25, 2026 ─── MAJOR BUILD PHASE ───────────────────────────────────
│  "Level_one" commit — massive codebase push
│  All 9 microservices scaffolded and implemented
│  44+ test files created (Jest + Pytest + Property-based)
│  PR #1: Fix TS compilation, VAD tests, application-tracker bugs
│  PR #2: Task 15 final validation checkpoint
│  All 15 core tasks marked ✅ complete
│
Feb 26, 2026 ─── WEBSITE & FRONTEND ──────────────────────────────────
│  PR #3: Static landing page with 23-language support
│  Dark/light theme, accessibility controls
│  Interactive chat demo, language carousel
│
Feb 27, 2026 ─── WEBSITE REFINEMENT ──────────────────────────────────
│  PR #4: Website improvements and fixes
│  PR #5: Additional frontend updates
│
Feb 28, 2026 ─── STABILIZATION & INTEGRATION ─────────────────────────
│  PR #6: CI/CD pipeline, security hardening, bug fixes
│     - GitHub Actions workflow (7 parallel test jobs)
│     - Hypothesis/httpx dependency fixes
│     - TS test scoping fix
│  PR #7: Null safety fix in user-profile export endpoint
│  PR #8: This analysis (project review)
│
```

### Development Velocity
- **28 days** from first commit to current state
- **8 PRs** total (7 code PRs + this analysis), all via Copilot coding agent
- **Most development concentrated in Feb 25-28** (4 days of intense activity)
- **Rapid prototyping approach** — built all services first, then fixed/stabilized

---

## 3. Architecture Deep Dive

### Microservices Architecture (9 Services)

```
┌────────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                                 │
│  Mobile App / Web Browser / USSD / IVR                         │
└────────────────────────┬───────────────────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────────────────┐
│              API GATEWAY (Port 3000)                            │
│  JWT Auth │ Rate Limiting │ Circuit Breaker │ Distributed Trace │
│  Conversation Orchestration │ Health Monitoring                 │
└──┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬───────────┘
   │      │      │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼
┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐
│Voice││Diale││Schem││Form ││Doc  ││App  ││User ││Acce │
│Engin││ct   ││e    ││Gene ││Guide││Track││Prof ││ssibi│
│e    ││Detec││Match││rator││     ││er   ││le   ││lity │
│:3001││:8001││:8002││:3002││:8003││:8004││:8005││:3003│
└──┬──┘└─────┘└──┬──┘└──┬──┘└─────┘└─────┘└──┬──┘└─────┘
   │             │      │                     │
   ▼             ▼      ▼                     ▼
┌─────────────────────────────────────────────────────┐
│                  DATA LAYER                          │
│  Neo4j (Scheme Graph) │ Redis (Sessions/Cache)       │
│  Encrypted Storage    │ Offline Cache                │
└─────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────┐
│           EXTERNAL INTEGRATIONS                      │
│  myScheme API │ e-Shram │ DigiLocker │ Aadhaar       │
│  AWS Bedrock (Claude/Nova Pro/Titan)                 │
└─────────────────────────────────────────────────────┘
```

### Service Responsibilities

| Service | Lines of Code | Language | Key Features |
|---------|:---:|:---:|---|
| **Voice Engine** | ~5,500 | TypeScript | WebRTC streaming, VAD, noise filtering, offline processing, network optimization |
| **Application Tracker** | ~6,800 | Python | Portal auth, submission, status monitoring, notifications, appeals |
| **User Profile** | ~5,200 | Python | Encrypted storage, family profiles, voice updates, privacy controls, GDPR compliance |
| **API Gateway** | ~3,700 | TypeScript | Auth, rate limiting, circuit breaker, distributed tracing, orchestration |
| **Form Generator** | ~3,300 | TypeScript | Session-based forms, adaptive questions, PDF generation, Redis sessions |
| **Accessibility** | ~3,200 | TypeScript | Screen reader, voice-only mode, button interfaces, multi-modal support |
| **Document Guide** | ~2,000 | Python | Scheme requirements, alternative docs, step-by-step guidance, multilingual |
| **Dialect Detector** | N/A* | Python | 22+ language detection, code-switching, confidence scoring, feedback loop |
| **Scheme Matcher** | N/A* | Python | Neo4j graph matching, eligibility evaluation, benefit estimation, ranking |

*\*Core logic is in tests/mocks; implementation may be stub-based*

### Shared Modules
| Module | Purpose |
|--------|---------|
| `shared/types/` | TypeScript interfaces for accessibility, dialect-detector, form-generator, scheme-matcher, user-profile, voice-engine, plus Bedrock (no shared types yet for API Gateway, Application Tracker, or Document Guide) |
| `shared/encryption/` | PII protection, key management, TLS config |
| `shared/bedrock/` | AWS Bedrock wrapper, guardrails, KB pipeline, fallback handler |
| `shared/performance/` | Cache manager, query optimizer, performance monitor |
| `shared/service-client.ts` | Factory for creating typed service clients |

---

## 4. Current State Assessment

### ✅ What's Working Well

1. **Comprehensive Architecture** — Well-designed microservices with clear separation of concerns
2. **Strong Testing Foundation** — 44+ test files with property-based testing (fast-check + Hypothesis)
3. **Security-First Design** — AES-256 encryption, PII anonymization, JWT auth, TLS 1.3
4. **Multi-Language Support** — 22 Indian languages + English in both backend and frontend
5. **CI/CD Pipeline** — 7 parallel test jobs in GitHub Actions
6. **Performance Testing** — Dedicated suite with voice latency, load testing, memory profiling
7. **Documentation** — Specs, setup guides, integration docs, performance docs
8. **Docker Compose** — Full containerized setup with Redis + Neo4j

### ⚠️ Areas of Concern

1. **Prototype Depth vs Breadth Trade-off**
   - All 9 services exist but many contain mostly test scaffolding and mocked implementations
   - The Dialect Detector and Scheme Matcher have substantial in-repo implementations, but most behavior is simulated/mock-driven rather than production-grade logic
   - Voice Engine has sophisticated tests but relies on mocked ASR/TTS (no real IndicWhisper)

2. **No Real External Integrations**
   - Government portal integrations (myScheme, e-Shram, DigiLocker) are entirely mocked
   - AWS Bedrock integration is documented but uses `@ts-ignore` for SDK imports
   - No actual API keys or service connections configured

3. **Frontend is a Static Demo**
   - Beautiful landing page but no functional voice interface
   - Chat demo uses hardcoded conversations, not real backend calls
   - No actual user authentication or session management in the frontend

4. **Database Layer is Stub-based**
   - Neo4j queries exist in tests but no real graph database seeded with scheme data
   - Redis is configured in Docker but services use in-memory fallbacks
   - No database-backed persistence for user profiles; profiles are currently stored as encrypted files on the mounted `/app/data` volume

5. **Known CI Failures** (from TASK_15_ACTION_ITEMS.md)
   - API Gateway conversation orchestrator null reference errors
   - Integration test health monitor caching failures
   - Distributed tracing validation issues
   - Some remaining Python test-infra issues (import paths)

6. **Backend Directory Mismatch**
   - `backend/functions/` contains AWS Lambda/DynamoDB code (multi-tenant SaaS)
   - This doesn't align with the microservices architecture of the main services
   - Appears to be from an earlier or separate project iteration

### ❌ Missing Components

| Expected (from Specs) | Current Status |
|----------------------|---------------|
| Real IndicWhisper ASR model | Mocked — no ML model loaded |
| Neo4j populated with 700+ schemes | Only a small sample dataset seeded via test fixtures |
| Government portal API integration | Fully mocked |
| Offline model caching & sync | Architecture defined, not implemented |
| AWS Bedrock live integration | Wrapper exists, no live connection |
| Mobile-first UI | Static desktop landing page only |
| USSD/IVR interface | Not started |
| Production deployment (AWS/GCP) | Docker Compose only |
| Real user authentication flow | JWT structure only, no signup/login UI |
| Data seeding scripts | No scheme data, no sample users |

---

## 5. Gap Analysis — Plan vs Reality

### Original Vision (from .kiro/gram-sahayak/requirements.md)
The original plan envisioned a **complete voice-to-scheme pipeline** with:
- 95% Hindi voice recognition accuracy
- 3-second dialect detection
- Real government portal integration
- Offline-first capability
- 700+ schemes in a graph database

### What Actually Got Built
A **comprehensive prototype skeleton** with:
- All service interfaces defined and typed
- Test-driven development with property-based testing
- Security and privacy architecture in place
- Landing page with language support
- Docker-based local development environment

### Assessment: Did the Project Change Path?

**The vision remained consistent, but the execution pivoted from "working product" to "comprehensive prototype."**

| Aspect | Original Plan | Actual Outcome | Verdict |
|--------|:---:|:---:|:---:|
| Architecture | Microservices | Microservices ✅ | On track |
| Service count | 5 core | 9 services (expanded) ✅ | Exceeded |
| Voice recognition | Real ASR | Mocked ASR ⚠️ | Behind |
| Scheme database | 700+ schemes | Only a handful of sample schemes ❌ | Behind |
| Government APIs | Live integration | Mocked ⚠️ | Behind |
| Security | Full encryption | Architecture + tests ✅ | On track |
| Testing | Property-based | Extensive coverage ✅ | Exceeded |
| Frontend | Functional UI | Static demo ⚠️ | Behind |
| Deployment | Cloud-ready | Docker Compose ⚠️ | Partial |
| AI/LLM | Bedrock integration | Wrapper only ⚠️ | Partial |

**Conclusion**: The project has an **excellent architectural foundation** and **exceeds expectations on testing and security design**. However, it's behind on **real integrations, data, and functional UI**. This is typical for prototype-phase development — the skeleton is strong, but the muscles need to be added.

---

## 6. Deep Research — What Should Be Done

### Phase 1: Make the Prototype Functional (Priority: HIGH)

#### 1.1 Seed Real Scheme Data
- **What**: Create a data seeding script with 50-100 real Indian government schemes
- **Why**: Without real data, the entire scheme matching flow is meaningless
- **Sources**: 
  - [myScheme.gov.in](https://www.myscheme.gov.in/) — Central & state scheme database
  - PM-KISAN, MGNREGA, Ujjwala Yojana, PM Awas Yojana, etc.
- **Action**:
  - Create a version-controlled directory (e.g. `seed-data/schemes/`) with JSON files containing scheme details, eligibility criteria, required documents, and benefits (ensure this path is not ignored by `.gitignore`)
  - Implement the seeding script to load scheme definitions from this directory for reproducible database seeding
- **Effort**: 2-3 days

#### 1.2 Connect Frontend to Backend
- **What**: Replace hardcoded chat demo with actual API calls to the backend
- **Why**: The landing page looks great but doesn't demonstrate the core product
- **Action**: 
  - Add a simple form/chat interface that calls API Gateway endpoints
  - Implement basic user flow: input demographics → match schemes → show results
- **Effort**: 3-4 days

#### 1.3 Implement Basic Voice (Web Speech API)
- **What**: Use the browser's built-in Web Speech API for STT/TTS as a starting point
- **Why**: Real IndicWhisper integration is complex; Web Speech API works now for Hindi/English
- **Action**: Add Web Speech API integration in the frontend, send transcribed text to the API
- **Effort**: 2 days

#### 1.4 Populate Neo4j with Scheme Graph
- **What**: Create Neo4j data model and seed script for scheme relationships
- **Why**: The scheme matcher's power comes from graph traversal — it needs real data
- **Action**: Design schema (Scheme, Category, Eligibility, Document nodes), write Cypher queries, create seed script
- **Effort**: 3 days

### Phase 2: Core Feature Completion (Priority: MEDIUM)

#### 2.1 Real Scheme Matching Engine
- **What**: Implement actual eligibility matching logic (not mocked)
- **Action**: Use Neo4j Cypher queries to match user demographics against scheme criteria
- **Effort**: 3-4 days

#### 2.2 Working Form Generator
- **What**: Create actual government application forms (e.g., PM-KISAN enrollment)
- **Action**: Design 5-10 real forms, implement conversational flow, generate PDFs
- **Effort**: 4-5 days

#### 2.3 AWS Bedrock Integration (Live)
- **What**: Connect to actual AWS Bedrock API for intelligent conversations
- **Action**: Set up AWS credentials, configure Claude 3 for demographic extraction, test with real queries
- **Effort**: 2-3 days (architecture exists, needs credentials + testing)

#### 2.4 Document Guide with Real Data
- **What**: Map actual document requirements for top 50 schemes
- **Action**: Research and add Aadhaar, ration card, income certificate, caste certificate, etc.
- **Effort**: 2-3 days

### Phase 3: Production Readiness (Priority: LOW for prototype)

#### 3.1 Mobile-First React Frontend
- **What**: Replace the current static landing page in `website/` with a React app
- **Note**: The repository currently has only a static frontend (`website/index.html`); a new React frontend needs to be created and wired in as the primary UI
- **Action**: Build a React app as the primary frontend with routing, state management, and API integration, and update build/deploy to serve it instead of the static page
- **Effort**: 2 weeks

#### 3.2 Real Government Portal Integration
- **What**: Start with publicly available APIs (myScheme, DigiLocker)
- **Action**: Research API access, implement OAuth flows, create integration adapters
- **Effort**: 2-3 weeks (API access approvals may take time)

#### 3.3 Cloud Deployment
- **What**: Deploy to AWS/GCP with proper infrastructure
- **Action**: Create Terraform/CDK scripts, set up ECS/EKS, configure auto-scaling
- **Effort**: 1-2 weeks

---

## 7. What Should Be Changed

### Immediate Changes (Before Next Sprint)

1. **Clean Up Backend Directory**
   - The `backend/functions/` (AWS Lambda/DynamoDB) doesn't align with the microservices architecture
   - **Decision needed**: Is this multi-tenant SaaS code part of Gram Sahayak or a separate project?

2. **Remove Agent Example Files**
   - `agent.py`, `agent_conversation.py`, `agent_custom_tool.py` are Strands SDK examples
   - They're not part of the core product and add confusion
   - Move to an `examples/` directory or remove entirely

3. **Consolidate Frontend Approach**
   - Two frontend approaches are being considered: a static HTML page (for example, `website/index.html`) and a React-based single-page application
   - **Pick one** — recommend React for the actual product, keep static for demo/marketing

4. **Fix Known CI Failures**
   - API Gateway orchestrator null references
   - Python import path issues
   - Import-path and test-structure issues in dialect-detector service

5. **Ensure No Secrets Are Committed**
   - Rely on existing CI checks that fail if sensitive directories (such as `data/vault` or `data/keys`) are added
   - Periodically audit the repository and `.gitignore` to ensure credentials, keys, and other secrets are not tracked

### Architecture Changes

1. **Add a Real Database Layer**
   - Currently all data is in-memory or mocked
   - Add PostgreSQL or MongoDB for persistent user profiles
   - Seed Neo4j with actual scheme data

2. **Implement Service Discovery**
   - Currently hardcoded URLs in `.env`
   - Consider Consul or environment-based discovery for scaling

3. **Add API Documentation**
   - The `schema/openapi.yaml` only covers the multi-tenant SaaS API
   - Create OpenAPI specs for each microservice endpoint

4. **Centralize Error Handling**
   - Each service handles errors differently
   - Create shared error middleware and standardized error responses

### Testing Changes

1. **Add Integration Tests That Actually Call Services**
   - Current tests mock all external dependencies
   - Add docker-compose-based integration tests that test real service-to-service communication

2. **Add End-to-End User Journey Tests**
   - "User speaks in Hindi → scheme matched → form filled → PDF generated"
   - This validates the entire pipeline, not just individual services

---

## 8. Prototype-to-Product Roadmap

### Sprint 1: "Make It Real" (Weeks 1-2)
- [ ] Seed 50 real government schemes into Neo4j
- [ ] Connect frontend chat to API Gateway
- [ ] Implement Web Speech API for basic voice input
- [ ] Fix all CI pipeline failures
- [ ] Clean up non-essential files (agent examples, backend/functions)

### Sprint 2: "Core Flow" (Weeks 3-4)
- [ ] Implement real scheme matching against Neo4j
- [ ] Build 5 real government application forms
- [ ] Add document requirement data for top schemes
- [ ] Connect AWS Bedrock for intelligent conversation
- [ ] Add basic user profile creation and storage

### Sprint 3: "User Experience" (Weeks 5-6)
- [ ] Build React-based mobile-first frontend
- [ ] Implement voice conversation flow end-to-end
- [ ] Add dialect detection for top 5 languages (Hindi, Bengali, Telugu, Tamil, Marathi)
- [ ] Create offline mode for cached scheme data
- [ ] User testing with target demographic

### Sprint 4: "Polish & Deploy" (Weeks 7-8)
- [ ] Deploy to cloud (AWS ECS or similar)
- [ ] Performance optimization and load testing
- [ ] Security audit and penetration testing
- [ ] Documentation for deployment and operations
- [ ] Demo preparation for stakeholders

---

## 9. Questions for Clarification

To refine this plan, I need answers to these questions:

### Product Direction
1. **Target demo audience**: Is this prototype for investors/government officials/hackathon judges? This affects what we prioritize building first.
2. **Deployment target**: Will this run on AWS, Azure, GCP, or a government data center? This affects infrastructure choices.
3. **Real government API access**: Do you have any agreements or API keys for myScheme.gov.in, DigiLocker, or e-Shram? Or should we continue with simulated integrations?

### Technical Decisions
4. **Frontend choice**: Should we invest in building a React-based frontend or keep improving the static landing page? Currently only the static page exists in the repository.
5. **Backend directory**: Is the `backend/functions/` (AWS Lambda + DynamoDB) code part of Gram Sahayak, or was it from a different project? It uses a multi-tenant SaaS pattern that doesn't match the microservices.
6. **AWS Bedrock budget**: Do you have AWS credentials and budget for Bedrock API calls? Claude 3 costs ~$3/M input tokens, ~$15/M output tokens.

### Scope & Priority
7. **How many languages for the prototype?**: All 22 or should we focus on top 3-5 (Hindi, English, Bengali, Telugu, Tamil)?
8. **Offline requirement**: How critical is offline support for the prototype phase? It adds significant complexity.
9. **Voice vs Text**: For the prototype demo, should voice be the primary input, or is text-based input acceptable to demonstrate the scheme matching?
10. **Timeline**: When is the prototype expected to be demo-ready? This determines how much we can implement vs mock.

### Team & Process
11. **Team size**: Who else is working on this? The commit history shows Purnavu-12 and Adithya0765 — is this a 2-person team?
12. **Copilot agent usage**: How much of the future development will use Copilot coding agent vs manual development?

---

## Summary

**Gram Sahayak is an ambitious and well-architected project** that has successfully built a comprehensive prototype skeleton in ~4 weeks. The microservices architecture, testing infrastructure, security design, and multilingual support are all impressive.

**The primary gap is between architecture and implementation** — the skeleton is strong, but it needs real data, real integrations, and a functional user interface to become a demonstrable prototype.

**The recommended immediate focus** is:
1. 🎯 Seed real scheme data (this unlocks the entire product flow)
2. 🎯 Connect the frontend to the backend (make the demo functional)
3. 🎯 Add basic voice input via Web Speech API (demonstrate the voice-first vision)
4. 🎯 Fix CI pipeline (ensure code quality stays high)

These four items would transform Gram Sahayak from "impressive architecture" into "working prototype" within 1-2 sprints.
