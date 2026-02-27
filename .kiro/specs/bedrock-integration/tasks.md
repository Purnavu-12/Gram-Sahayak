# Implementation Plan: Bedrock Integration

## Overview

This plan implements AWS Bedrock integration into gram-sahayak as a 24-hour MVP enhancement. The implementation follows a hybrid architecture where Bedrock models serve as enhanced options while existing implementations remain as resilient fallbacks. The approach leverages existing infrastructure (CircuitBreaker, RetryPolicy, ServiceClient) and follows established patterns from the codebase.

Key implementation principles:
- Extend existing infrastructure rather than rebuild
- Maintain backward compatibility with all existing APIs
- TypeScript for shared infrastructure and Voice Engine
- Python for Scheme Matcher and Dialect Detector enhancements
- Property-based tests for all universal correctness properties
- 24-hour MVP scope: voice-to-scheme-matching flow, 10-20 schemes, Hindi/English only

## Tasks

- [ ] 1. Set up Bedrock shared infrastructure
  - Create shared/bedrock/ directory for common Bedrock utilities
  - Define TypeScript interfaces for Bedrock models (Claude, Nova Pro, Titan, Guardrails)
  - Create BedrockConfig type extending existing config patterns
  - Set up AWS SDK v3 dependencies in shared/package.json
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 10.1, 10.2_

- [ ] 2. Implement Bedrock Agent Wrapper
  - [ ] 2.1 Create BedrockAgentWrapper class in shared/bedrock/bedrock-agent-wrapper.ts
    - Implement invokeClaudeModel() for demographic extraction
    - Implement invokeNovaProSTT() for speech-to-text
    - Implement invokeNovaProTTS() for text-to-speech
    - Implement queryKnowledgeBase() for semantic search
    - Implement applyGuardrails() for PII detection
    - Add credential management and authentication
    - Add request/response logging
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [ ]* 2.2 Write property test for Bedrock model invocation correctness
    - **Property 1: Bedrock Model Invocation Correctness**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
    - Test all operations (STT, TTS, extraction, search) with generated inputs
    - Verify correct model invocation and valid responses
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 9.1_

  - [ ]* 2.3 Write unit tests for BedrockAgentWrapper
    - Test successful Claude invocation with valid response
    - Test Nova Pro STT with Hindi and English audio
    - Test Nova Pro TTS with Hindi and English text
    - Test Knowledge Base query with filters
    - Test Guardrails PII detection
    - Test authentication failure handling
    - Test timeout handling
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 3. Extend FallbackHandler for Bedrock integration
  - [ ] 3.1 Enhance existing CircuitBreaker in services/api-gateway/src/services/circuit-breaker.ts
    - Add Bedrock-specific circuit breaker instances
    - Add model tier fallback logic (Claude 3.5 Sonnet → Claude 3 Haiku)
    - Integrate with existing health monitoring
    - _Requirements: 1.5, 1.6, 1.7, 7.1, 7.2_

  - [ ] 3.2 Create FallbackHandler class in shared/bedrock/fallback-handler.ts
    - Implement executeWithFallback() using existing CircuitBreaker
    - Add fallback routing within 100ms threshold
    - Add fallback event logging
    - Integrate with existing RetryPolicy
    - _Requirements: 1.5, 1.6, 7.1, 7.2, 7.3, 7.4_

  - [ ]* 3.3 Write property test for fallback routing on failure
    - **Property 2: Fallback Routing on Failure**
    - **Validates: Requirements 1.5, 1.6, 7.1, 7.2**
    - Test timeout, error, and rate limit scenarios
    - Verify fallback completion within 100ms
    - _Requirements: 1.5, 1.6, 7.1, 7.2, 9.4_

  - [ ]* 3.4 Write property test for model tier fallback sequence
    - **Property 3: Model Tier Fallback Sequence**
    - **Validates: Requirements 1.7**
    - Verify Claude 3.5 Sonnet → Claude 3 Haiku → Existing sequence
    - _Requirements: 1.7, 9.4_

  - [ ]* 3.5 Write unit tests for FallbackHandler
    - Test circuit breaker state transitions
    - Test fallback routing on timeout
    - Test fallback routing on error
    - Test model tier fallback
    - Test metrics collection
    - _Requirements: 1.5, 1.6, 1.7, 7.1, 7.2_

- [ ] 4. Checkpoint - Verify shared infrastructure
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement Guardrails Integration Layer
  - [ ] 5.1 Create GuardrailsIntegration class in shared/bedrock/guardrails-integration.ts
    - Implement detectAndRedactPII() using BedrockAgentWrapper
    - Implement storePIIContext() for session management
    - Implement restorePIIContext() for final responses
    - Add false positive logging
    - Support names, addresses, phones, Aadhaar numbers
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 5.2 Write property test for PII detection and redaction
    - **Property 11: PII Detection and Redaction**
    - **Validates: Requirements 4.1, 4.2, 4.3**
    - Generate text with various PII types
    - Verify all PII is redacted
    - _Requirements: 4.1, 4.2, 4.3, 9.2_

  - [ ]* 5.3 Write unit tests for GuardrailsIntegration
    - Test PII detection for each type (name, phone, Aadhaar, address)
    - Test PII redaction with placeholder tokens
    - Test context storage and restoration
    - Test false positive logging
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 6. Implement Knowledge Base ingestion pipeline
  - [ ] 6.1 Create KBIngestionPipeline class in shared/bedrock/kb-ingestion-pipeline.ts
    - Implement ingestSchemes() for batch ingestion
    - Implement validateScheme() for data validation
    - Implement generateEmbeddings() using Titan
    - Add bilingual content support (Hindi/English)
    - Create sample scheme set (10-20 schemes)
    - _Requirements: 3.1, 3.2, 3.4, 3.5, 3.6, 12.1, 12.2, 12.3, 12.4, 12.5_

  - [ ]* 6.2 Write property test for scheme data validation
    - **Property 9: Scheme Data Validation**
    - **Validates: Requirements 3.6**
    - Generate schemes with missing/invalid fields
    - Verify validation catches all issues
    - _Requirements: 3.6, 9.7_

  - [ ]* 6.3 Write unit tests for KBIngestionPipeline
    - Test valid scheme ingestion
    - Test invalid scheme rejection
    - Test duplicate scheme handling
    - Test bilingual content indexing
    - Test embedding generation
    - _Requirements: 3.1, 3.2, 3.4, 3.5, 3.6_

  - [ ] 6.4 Create sample scheme data file
    - Create shared/bedrock/sample-schemes.json with 10-20 schemes
    - Include PM-KISAN, MGNREGA, and other diverse schemes
    - Add Hindi and English descriptions for each
    - Cover different age groups, income levels, regions
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

  - [ ] 6.5 Create ingestion script
    - Create scripts/ingest-sample-schemes.ts
    - Load sample-schemes.json
    - Validate and ingest into Knowledge Base
    - Log ingestion results
    - _Requirements: 3.5, 12.6_

- [ ] 7. Checkpoint - Verify Knowledge Base setup
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Enhance Voice Engine with Bedrock integration
  - [ ] 8.1 Extend VoiceEngine in services/voice-engine/src/index.ts
    - Add bedrockEnabled configuration flag
    - Integrate BedrockAgentWrapper for Nova Pro STT/TTS
    - Integrate FallbackHandler for automatic fallback
    - Maintain existing IndicWhisper/TTS as fallback
    - Add Bedrock status endpoint
    - _Requirements: 1.2, 1.3, 2.3, 2.5, 5.1, 5.5_

  - [ ] 8.2 Update processAudioStream() method
    - Try Nova Pro STT first when Bedrock enabled
    - Fall back to existing STT on failure
    - Apply Guardrails PII protection to transcription
    - Log source (Bedrock vs fallback)
    - _Requirements: 1.2, 2.3, 5.1, 5.7_

  - [ ] 8.3 Update synthesizeSpeech() method
    - Try Nova Pro TTS first when Bedrock enabled
    - Fall back to existing TTS on failure
    - Maintain language and dialect support
    - Log source (Bedrock vs fallback)
    - _Requirements: 1.3, 2.3, 5.5_

  - [ ]* 8.4 Write property test for hybrid implementation support
    - **Property 4: Hybrid Implementation Support**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
    - Test Voice Engine with Bedrock enabled and disabled
    - Verify both produce valid results
    - _Requirements: 2.3, 9.1_

  - [ ]* 8.5 Write property test for transcription accuracy thresholds
    - **Property 15: Transcription Accuracy Thresholds**
    - **Validates: Requirements 6.1, 6.2**
    - Test Hindi audio samples (85% accuracy threshold)
    - Test English audio samples (90% accuracy threshold)
    - _Requirements: 6.1, 6.2, 9.6_

  - [ ]* 8.6 Write unit tests for enhanced Voice Engine
    - Test Bedrock STT with Hindi audio
    - Test Bedrock STT with English audio
    - Test Bedrock TTS with Hindi text
    - Test Bedrock TTS with English text
    - Test fallback on Bedrock failure
    - Test Bedrock status endpoint
    - _Requirements: 1.2, 1.3, 2.3, 5.1, 5.5_

- [ ] 9. Enhance Scheme Matcher with Knowledge Base search
  - [ ] 9.1 Extend SchemeMatcher in services/scheme-matcher/main.py
    - Add bedrock_enabled configuration flag
    - Integrate BedrockAgentWrapper (Python boto3 version)
    - Create searchKnowledgeBase() method
    - Create mergeResults() to combine KB and Neo4j results
    - Maintain existing Neo4j queries as fallback
    - _Requirements: 2.2, 2.5, 3.3, 5.3_

  - [ ] 9.2 Update find_eligible_schemes() method
    - Try Knowledge Base search first when Bedrock enabled
    - Fall back to Neo4j on failure
    - Merge and deduplicate results
    - Return top 3 schemes ranked by relevance
    - _Requirements: 2.2, 3.3, 5.3, 5.4_

  - [ ]* 9.3 Write property test for Knowledge Base result limiting
    - **Property 7: Knowledge Base Result Limiting**
    - **Validates: Requirements 3.3, 5.4**
    - Generate diverse user profiles
    - Verify at most 3 schemes returned
    - Verify ranking by relevance score
    - _Requirements: 3.3, 5.4, 9.7_

  - [ ]* 9.4 Write property test for bilingual Knowledge Base support
    - **Property 8: Bilingual Knowledge Base Support**
    - **Validates: Requirements 3.4, 6.5**
    - Test semantic search in Hindi and English
    - Verify both languages return valid results
    - _Requirements: 3.4, 6.5, 9.6_

  - [ ]* 9.5 Write property test for eligibility metadata queryability
    - **Property 10: Eligibility Metadata Queryability**
    - **Validates: Requirements 3.7**
    - Test filtering by age, income, location, caste, gender
    - Verify metadata queries work correctly
    - _Requirements: 3.7, 9.7_

  - [ ]* 9.6 Write unit tests for enhanced Scheme Matcher
    - Test Knowledge Base search with user profile
    - Test result merging from KB and Neo4j
    - Test fallback to Neo4j on KB failure
    - Test top 3 scheme limiting
    - Test bilingual search
    - _Requirements: 2.2, 3.3, 3.4, 5.3, 5.4_

- [ ] 10. Enhance Dialect Detector with Nova Pro
  - [ ] 10.1 Extend DialectDetector in services/dialect-detector/dialect_detector_service.py
    - Add bedrock_enabled configuration flag
    - Integrate BedrockAgentWrapper for Nova Pro detection
    - Add Nova Pro as additional model in ensemble
    - Maintain existing ensemble as fallback
    - _Requirements: 2.1, 2.5_

  - [ ]* 10.2 Write property test for multilingual demographic extraction
    - **Property 16: Multilingual Demographic Extraction**
    - **Validates: Requirements 6.3, 6.4**
    - Generate demographic text in Hindi and English
    - Verify Claude extracts valid User_Profile
    - _Requirements: 6.3, 6.4, 9.3_

  - [ ]* 10.3 Write unit tests for enhanced Dialect Detector
    - Test Nova Pro detection with Hindi audio
    - Test Nova Pro detection with English audio
    - Test ensemble with Nova Pro included
    - Test fallback on Nova Pro failure
    - _Requirements: 2.1_

- [ ] 11. Checkpoint - Verify service enhancements
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Implement end-to-end voice flow integration
  - [ ] 12.1 Create end-to-end flow orchestration in services/api-gateway/src/services/conversation-orchestrator.ts
    - Add voiceToSchemeMatching() method
    - Orchestrate: Voice Engine STT → Guardrails → Claude extraction → Scheme Matcher → Voice Engine TTS
    - Apply PII protection throughout flow
    - Track latency at each step
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.7_

  - [ ]* 12.2 Write property test for PII-protected processing flow
    - **Property 12: PII-Protected Processing Flow**
    - **Validates: Requirements 4.6, 4.7, 5.7**
    - Generate input with PII
    - Verify PII redacted before extraction
    - Verify processing completes successfully
    - _Requirements: 4.6, 4.7, 5.7, 9.2_

  - [ ]* 12.3 Write property test for end-to-end voice flow correctness
    - **Property 13: End-to-End Voice Flow Correctness**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.5, 6.8**
    - Test complete flow from audio input to audio output
    - Verify language consistency (Hindi in → Hindi out)
    - _Requirements: 5.1, 5.2, 5.3, 5.5, 6.8, 9.1_

  - [ ]* 12.4 Write property test for end-to-end latency target
    - **Property 14: End-to-End Latency Target**
    - **Validates: Requirements 5.6**
    - Run 100 requests, measure latency
    - Verify 90th percentile < 3 seconds
    - _Requirements: 5.6, 9.5_

  - [ ]* 12.5 Write property test for voice transcription round-trip
    - **Property 25: Voice Transcription Round-Trip**
    - **Validates: Requirements 1.2, 1.3, 5.1, 5.5**
    - Generate User_Profile → text → audio → transcription → extraction
    - Verify demographic information preserved
    - _Requirements: 1.2, 1.3, 5.1, 5.5, 9.1_

  - [ ]* 12.6 Write unit tests for end-to-end flow
    - Test complete voice-to-scheme-matching flow
    - Test PII protection throughout flow
    - Test language consistency
    - Test error handling at each step
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.7_

- [ ] 13. Implement monitoring and observability
  - [ ] 13.1 Create BedrockMetricsCollector in shared/bedrock/metrics-collector.ts
    - Track API calls by model and status
    - Track latency (average, p50, p95, p99) by model
    - Track costs by model (input/output tokens)
    - Track fallback counts by service and reason
    - Track Guardrails PII detections
    - Track Knowledge Base query metrics
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ] 13.2 Add Prometheus metrics endpoint
    - Create /metrics/bedrock endpoint in API Gateway
    - Expose metrics in Prometheus format
    - Include all BedrockMetricsCollector metrics
    - _Requirements: 11.6_

  - [ ] 13.3 Add health check endpoint
    - Create /health/bedrock endpoint in API Gateway
    - Check Claude, Nova Pro, Knowledge Base, Guardrails availability
    - Check credential validity
    - Return overall health status
    - _Requirements: 10.7_

  - [ ]* 13.4 Write property test for comprehensive metrics collection
    - **Property 24: Comprehensive Metrics Collection**
    - **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5**
    - Make various Bedrock API calls
    - Verify all metrics collected correctly
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ]* 13.5 Write unit tests for monitoring
    - Test metrics collection for each model
    - Test Prometheus endpoint format
    - Test health check endpoint
    - Test alert conditions
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

- [ ] 14. Implement configuration management
  - [ ] 14.1 Create Bedrock configuration schema
    - Define BedrockConfig interface in shared/types/bedrock.ts
    - Add configuration validation
    - Support per-service enable/disable flags
    - Support model ID configuration
    - Support fallback timeout configuration
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [ ] 14.2 Add configuration endpoints to API Gateway
    - Create GET /config/bedrock endpoint
    - Create PUT /config/bedrock endpoint (admin only)
    - Create POST /config/bedrock/services/:serviceId/toggle endpoint
    - Add configuration validation
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [ ] 14.3 Add startup credential validation
    - Validate Bedrock credentials at application startup
    - Disable Bedrock integration if credentials invalid
    - Log credential validation results
    - _Requirements: 10.5, 10.6_

  - [ ]* 14.4 Write unit tests for configuration management
    - Test configuration validation
    - Test per-service toggle
    - Test credential validation
    - Test configuration endpoints
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [ ] 15. Implement model response validation
  - [ ] 15.1 Create ResponseValidator in shared/bedrock/response-validator.ts
    - Validate Claude User_Profile has required fields
    - Validate Nova Pro transcription is non-empty
    - Validate Knowledge Base schemes have name and eligibility
    - Check confidence scores against 70% threshold
    - Invoke FallbackHandler on validation failure
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.7_

  - [ ]* 15.2 Write property test for model response validation
    - **Property 21: Model Response Validation**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**
    - Generate various model responses
    - Verify validation catches invalid responses
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ]* 15.3 Write property test for confidence score threshold
    - **Property 23: Confidence Score Threshold**
    - **Validates: Requirements 8.7**
    - Generate responses with various confidence scores
    - Verify responses below 70% are rejected
    - _Requirements: 8.7_

  - [ ]* 15.4 Write unit tests for ResponseValidator
    - Test User_Profile validation
    - Test transcription validation
    - Test scheme validation
    - Test confidence score checking
    - Test fallback invocation on failure
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.7_

- [ ] 16. Checkpoint - Verify monitoring and validation
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 17. Implement resilience property tests
  - [ ]* 17.1 Write property test for Bedrock priority when enabled
    - **Property 5: Bedrock Priority When Enabled**
    - **Validates: Requirements 2.5, 2.7**
    - Test service requests with Bedrock enabled
    - Verify Bedrock attempted first
    - _Requirements: 2.5, 2.7, 9.4_

  - [ ]* 17.2 Write property test for data preservation during integration
    - **Property 6: Data Preservation During Integration**
    - **Validates: Requirements 2.6**
    - Verify Neo4j data intact after Bedrock integration
    - Test queries return same results
    - _Requirements: 2.6_

  - [ ]* 17.3 Write property test for network failure detection speed
    - **Property 17: Network Failure Detection Speed**
    - **Validates: Requirements 7.3**
    - Simulate network failures
    - Verify detection within 500ms
    - _Requirements: 7.3, 9.4_

  - [ ]* 17.4 Write property test for fallback event logging
    - **Property 18: Fallback Event Logging**
    - **Validates: Requirements 7.4**
    - Trigger various fallback scenarios
    - Verify all events logged with details
    - _Requirements: 7.4, 9.4_

  - [ ]* 17.5 Write property test for continuous operation during outage
    - **Property 19: Continuous Operation During Bedrock Outage**
    - **Validates: Requirements 7.5**
    - Simulate complete Bedrock outage
    - Verify system continues with existing implementations
    - _Requirements: 7.5, 9.4_

  - [ ]* 17.6 Write property test for automatic recovery after outage
    - **Property 20: Automatic Recovery After Outage**
    - **Validates: Requirements 7.6**
    - Simulate Bedrock becoming available after outage
    - Verify automatic resume of Bedrock usage
    - _Requirements: 7.6, 9.4_

  - [ ]* 17.7 Write property test for quality comparison measurement
    - **Property 22: Quality Comparison Measurement**
    - **Validates: Requirements 8.5, 8.6**
    - Process requests with both implementations
    - Verify quality metrics logged for comparison
    - _Requirements: 8.5, 8.6_

- [ ] 18. Integration testing and documentation
  - [ ] 18.1 Create integration test suite
    - Test complete voice-to-scheme-matching flow with real Bedrock APIs (staging)
    - Test fallback scenarios with simulated outages
    - Test concurrent user sessions
    - Test configuration changes during active sessions
    - Test Knowledge Base ingestion followed by queries
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 7.5, 7.6_

  - [ ] 18.2 Create Bedrock integration README
    - Document architecture and design decisions
    - Document configuration options
    - Document API endpoints
    - Document monitoring and metrics
    - Document troubleshooting guide
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 11.6_

  - [ ] 18.3 Update existing service documentation
    - Update Voice Engine README with Bedrock integration
    - Update Scheme Matcher README with Knowledge Base search
    - Update Dialect Detector README with Nova Pro
    - Update API Gateway README with new endpoints
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 19. Final checkpoint - Complete system validation
  - Run all property tests (100+ iterations each)
  - Run all unit tests
  - Run integration test suite
  - Verify end-to-end latency < 3 seconds for 90% of requests
  - Verify all 10-20 sample schemes queryable
  - Verify Hindi and English language support
  - Verify PII protection throughout flow
  - Verify fallback behavior under simulated failures
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties (100+ iterations)
- Unit tests validate specific examples and edge cases
- The implementation leverages existing infrastructure (CircuitBreaker, RetryPolicy, ServiceClient)
- TypeScript is used for shared infrastructure and Voice Engine
- Python is used for Scheme Matcher and Dialect Detector enhancements
- The 24-hour MVP scope focuses on voice-to-scheme-matching flow with 10-20 sample schemes
- Hindi and English language support only for MVP
- Basic PII protection (names, addresses, phones, Aadhaar numbers)
