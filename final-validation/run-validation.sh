#!/bin/bash

# Final System Validation Runner
# Task 14.3 - Gram Sahayak Final Validation

set -e

echo "=========================================="
echo "Gram Sahayak - Final System Validation"
echo "Task 14.3"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Track results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run test suite
run_test_suite() {
    local suite_name=$1
    local test_command=$2
    
    echo ""
    echo "=========================================="
    echo "Running: $suite_name"
    echo "=========================================="
    
    if eval "$test_command"; then
        echo -e "${GREEN}✓ $suite_name PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ $suite_name FAILED${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Set environment variables
export FC_NUM_RUNS=100
export HYPOTHESIS_MAX_EXAMPLES=100
export API_BASE_URL=${API_BASE_URL:-http://localhost:3000}

echo "Configuration:"
echo "  - Property test iterations: 100+"
echo "  - API Base URL: $API_BASE_URL"
echo ""

# 1. Property-Based Tests Validation
run_test_suite \
    "Property-Based Tests (100+ iterations)" \
    "npm run test:validation:property"

# 2. Multi-Language End-to-End Tests
run_test_suite \
    "Multi-Language E2E Tests (22 languages)" \
    "npm run test:validation:languages"

# 3. Government Portal Integration Tests
run_test_suite \
    "Government Portal Integration Tests" \
    "npm run test:validation:integration"

# 4. Offline Capabilities and Synchronization Tests
run_test_suite \
    "Offline Capabilities and Sync Tests" \
    "npm run test:validation:offline"

# Summary
echo ""
echo "=========================================="
echo "VALIDATION SUMMARY"
echo "=========================================="
echo "Total Test Suites: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED_TESTS${NC}"
else
    echo "Failed: 0"
fi
echo ""

# Final result
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}=========================================="
    echo "✓ ALL VALIDATION TESTS PASSED"
    echo "System is ready for deployment"
    echo "==========================================${NC}"
    exit 0
else
    echo -e "${RED}=========================================="
    echo "✗ VALIDATION FAILED"
    echo "Please fix failing tests before deployment"
    echo "==========================================${NC}"
    exit 1
fi
