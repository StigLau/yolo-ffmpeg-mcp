#!/bin/bash

# CI/CD Test Runner for FFMPEG MCP Server
# Runs comprehensive test suite in containerized environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 FFMPEG MCP Server CI/CD Test Suite${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Environment validation
echo -e "${YELLOW}📋 Environment Validation${NC}"
echo "Python version: $(python3 --version)"

# Check FFmpeg availability
if command -v ffmpeg >/dev/null 2>&1; then
    echo "FFMPEG version: $(ffmpeg -version | head -1)"
elif [ -f "/opt/homebrew/bin/ffmpeg" ]; then
    echo "FFMPEG found at: /opt/homebrew/bin/ffmpeg"
    echo "FFMPEG version: $(/opt/homebrew/bin/ffmpeg -version | head -1)"
elif [ -f "/usr/local/bin/ffmpeg" ]; then
    echo "FFMPEG found at: /usr/local/bin/ffmpeg"
    echo "FFMPEG version: $(/usr/local/bin/ffmpeg -version | head -1)"
else
    echo "⚠️  FFMPEG not found in PATH - tests may fail"
fi

echo "Test data directory: $(ls /tmp/music/source 2>/dev/null | wc -l) files"
if [ -d "/tmp/music/source" ]; then
    echo "Test files available:"
    ls -la /tmp/music/source/
else
    echo "❌ Test source directory not found"
fi
echo ""

# Test categories to run
test_categories=(
    "tests/ci/test_unit_core.py"
    "tests/ci/test_integration_basic.py" 
    "tests/ci/test_mcp_server.py"
    "tests/ci/test_workflow_minimal.py"
)

# Track test results
total_tests=0
passed_tests=0
failed_tests=0

# Function to run test category
run_test_category() {
    local test_file="$1"
    local category_name=$(basename "$test_file" .py)
    
    echo -e "${BLUE}🧪 Running $category_name${NC}"
    echo "   File: $test_file"
    
    if python3 -m pytest "$test_file" -v --tb=short; then
        echo -e "${GREEN}✅ $category_name PASSED${NC}"
        ((passed_tests++))
    else
        echo -e "${RED}❌ $category_name FAILED${NC}"
        ((failed_tests++))
    fi
    
    ((total_tests++))
    echo ""
}

# Run each test category
for test_file in "${test_categories[@]}"; do
    if [ -f "$test_file" ]; then
        run_test_category "$test_file"
    else
        echo -e "${YELLOW}⚠️  Test file not found: $test_file${NC}"
    fi
done

# Video validation test (if video files are available)
echo -e "${BLUE}🎬 Video Processing & Validation Test${NC}"
if [ -f "scripts/video_validator.py" ]; then
    if python3 scripts/video_validator.py; then
        echo -e "${GREEN}✅ Video validation PASSED${NC}"
        ((passed_tests++))
    else
        echo -e "${RED}❌ Video validation FAILED${NC}"
        ((failed_tests++))
    fi
    ((total_tests++))
else
    echo -e "${YELLOW}⚠️  Video validator not found${NC}"
fi
echo ""

# MCP server integration test
echo -e "${BLUE}🔧 MCP Server Integration Test${NC}"
if [ -f "tests/ci/test_mcp_server.sh" ]; then
    if bash tests/ci/test_mcp_server.sh; then
        echo -e "${GREEN}✅ MCP server integration PASSED${NC}"
        ((passed_tests++))
    else
        echo -e "${RED}❌ MCP server integration FAILED${NC}"
        ((failed_tests++))
    fi
    ((total_tests++))
else
    echo -e "${YELLOW}⚠️  MCP server integration test not found${NC}"
fi
echo ""

# Performance benchmarks (optional)
echo -e "${BLUE}⚡ Performance Benchmarks${NC}"
if [ -f "scripts/benchmark_performance.py" ]; then
    python3 scripts/benchmark_performance.py || echo -e "${YELLOW}⚠️  Benchmarks failed but continuing${NC}"
else
    echo -e "${YELLOW}⚠️  Performance benchmarks not available${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}📊 Test Results Summary${NC}"
echo -e "${BLUE}======================${NC}"
echo "Total tests: $total_tests"
echo -e "Passed: ${GREEN}$passed_tests${NC}"
echo -e "Failed: ${RED}$failed_tests${NC}"

if [ $failed_tests -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 ALL TESTS PASSED! 🎉${NC}"
    echo -e "${GREEN}CI/CD pipeline validation successful${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}💥 TESTS FAILED: $failed_tests/${total_tests}${NC}"
    echo -e "${RED}CI/CD pipeline validation failed${NC}"
    exit 1
fi