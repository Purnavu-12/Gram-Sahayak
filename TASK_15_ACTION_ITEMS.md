# Task 15: Action Items for Test Failures

## Priority 1: Critical Failures (Must Fix Before Deployment)

### 1. API Gateway - Conversation Orchestrator Failures

**Issue:** Multiple null reference errors in conversation flow
**Files Affected:** `services/api-gateway/src/tests/conversation-orchestrator.test.ts`

**Errors:**
```
TypeError: Cannot read properties of undefined (reading 'dialect')
TypeError: Cannot read properties of undefined (reading 'audioUrl')
```

**Root Cause:** Mock service responses not properly structured

**Action Items:**
- [ ] Review conversation orchestrator service integration
- [ ] Fix dialect detection service mock responses
- [ ] Fix voice engine service mock responses
- [ ] Ensure profile client is called correctly
- [ ] Add null checks in conversation orchestrator

**Estimated Time:** 1-2 hours

### 2. API Gateway - Integration Test Failures

**Issue:** Health monitor cache not working
**File:** `services/api-gateway/src/tests/integration.test.ts`

**Error:**
```
expect(cached).toBeDefined()
Received: undefined
```

**Action Items:**
- [ ] Debug health monitor caching logic
- [ ] Verify cache key generation
- [ ] Check cache expiration settings

**Estimated Time:** 30 minutes

### 3. API Gateway - Distributed Tracing Validation

**Issue:** Invalid trace headers not being rejected
**File:** `services/api-gateway/src/tests/distributed-tracing.test.ts`

**Error:**
```
expect(context).toBeNull()
Received: {"parentSpanId": undefined, "spanId": "", "traceId": "abc"}
```

**Action Items:**
- [ ] Add proper validation for trace header format
- [ ] Return null for invalid headers
- [ ] Add validation tests for edge cases

**Estimated Time:** 30 minutes

### 4. Python Dependencies Missing

**Issue:** `numpy` not installed, blocking 7 dialect-detector tests

**Action Items:**
- [ ] Install numpy: `pip install numpy`
- [ ] Verify all Python dependencies in requirements.txt
- [ ] Run dialect-detector tests after installation

**Estimated Time:** 15 minutes

## Priority 2: Performance Issues (Should Fix)

### 5. Database Optimization Performance Below Target

**Issue:** Cache performance not meeting targets
**File:** `performance-tests/database-optimization.test.ts`

**Failures:**
1. Cache hit rate test timeout (>10s)
2. Cache latency improvement: 15.38ms (expected <3.33ms for 10x improvement)
3. Cache invalidation: 15.95ms (expected <10ms)

**Action Items:**
- [ ] Profile cache operations to identify bottlenecks
- [ ] Optimize cache key generation
- [ ] Review cache invalidation strategy
- [ ] Consider using faster cache backend (Redis vs in-memory)
- [ ] Adjust performance targets if current implementation is acceptable

**Estimated Time:** 2-3 hours

## Priority 3: Test Infrastructure Issues (Should Fix)

### 6. Python Test File Conflicts

**Issue:** Duplicate test file names causing import errors

**Affected Files:**
- `services/application-tracker/tests/test_api_integration.py`
- `services/document-guide/tests/test_api_integration.py`
- `services/user-profile/tests/test_api_integration.py`
- `services/dialect-detector/tests/test_api_integration.py`

**Action Items:**
- [ ] Rename test files to be service-specific:
  - `test_api_integration.py` → `test_application_tracker_api.py`
  - `test_api_integration.py` → `test_document_guide_api.py`
  - etc.
- [ ] Clear Python cache: `find . -type d -name __pycache__ -exec rm -rf {} +`
- [ ] Re-run Python test suite

**Estimated Time:** 30 minutes

### 7. Document Guide Import Errors

**Issue:** Module import errors in document-guide tests

**Action Items:**
- [ ] Add `__init__.py` to tests directory if missing
- [ ] Fix import paths in test files
- [ ] Verify PYTHONPATH includes service directory

**Estimated Time:** 30 minutes

### 8. User Profile Import Errors

**Issue:** Cannot import 'storage' from main.py

**Action Items:**
- [ ] Review user-profile main.py exports
- [ ] Fix import statements in test files
- [ ] Ensure all required modules are exported

**Estimated Time:** 30 minutes

## Priority 4: Optional Improvements

### 9. Long-Running Test Timeouts

**Issue:** Load tests and property tests exceed default timeouts

**Action Items:**
- [ ] Increase Jest timeout for load tests: `jest.setTimeout(600000)` (10 min)
- [ ] Add timeout configuration to property tests
- [ ] Consider splitting long-running tests into separate suite
- [ ] Document expected test execution times

**Estimated Time:** 1 hour

### 10. Redis Dependency for Form Generator

**Issue:** Form generator tests skip Redis-dependent tests

**Action Items:**
- [ ] Set up test Redis instance (Docker recommended)
- [ ] Add Redis to test environment setup
- [ ] Enable full form-generator test coverage

**Estimated Time:** 1 hour

### 11. Deprecation Warnings

**Issue:** FastAPI and asyncio deprecation warnings

**Action Items:**
- [ ] Migrate FastAPI `on_event` to lifespan handlers
- [ ] Update asyncio function checks for Python 3.16 compatibility
- [ ] Review all deprecation warnings

**Estimated Time:** 1-2 hours

## Test Execution Commands

### Run All TypeScript Tests
```bash
npm test
```

### Run Specific TypeScript Test Suite
```bash
npm test -- services/api-gateway/src/tests/conversation-orchestrator.test.ts
```

### Run All Python Tests
```bash
python -m pytest services/ -v
```

### Run Specific Python Service Tests
```bash
python -m pytest services/application-tracker/tests/ -v
python -m pytest services/dialect-detector/tests/ -v
python -m pytest services/scheme-matcher/tests/ -v
```

### Run Property Tests Only
```bash
# TypeScript
npm test -- --testNamePattern="property"

# Python
python -m pytest services/ -v -k "property"
```

### Clear Python Cache
```bash
# Windows PowerShell
Get-ChildItem -Path . -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force

# Linux/Mac
find . -type d -name __pycache__ -exec rm -rf {} +
```

## Success Criteria

Task 15 will be considered complete when:

- [ ] All API Gateway integration tests pass
- [ ] All API Gateway conversation orchestrator tests pass
- [ ] All API Gateway distributed tracing tests pass
- [ ] All Python services can import their modules
- [ ] All dialect-detector tests run (after numpy installation)
- [ ] Database performance tests pass OR targets are adjusted with justification
- [ ] No critical test failures remain
- [ ] Test execution completes within reasonable time (<10 minutes for full suite)

## Estimated Total Time to Fix All Issues

- **Priority 1 (Critical):** 2.5-3.5 hours
- **Priority 2 (Performance):** 2-3 hours
- **Priority 3 (Infrastructure):** 1.5-2 hours
- **Priority 4 (Optional):** 3-4 hours

**Total:** 9-12.5 hours for complete resolution

**Minimum for Deployment:** 2.5-3.5 hours (Priority 1 only)
