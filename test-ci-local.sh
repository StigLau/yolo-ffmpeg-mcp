#!/bin/bash
set -e

echo "🐳 Building CI test environment locally..."

# Build the CI test image
docker build -f Dockerfile.ci-test -t ffmpeg-mcp-ci-local:latest .

echo ""
echo "🧪 Running CI tests in Docker container..."
echo "This mimics the exact CI environment and commands"
echo ""

# Run the tests (same commands as CI)
echo "📋 Test 1: Unit Core Tests"
docker run --rm ffmpeg-mcp-ci-local:latest python -m pytest tests/ci/test_unit_core.py -v --tb=short

echo ""
echo "📋 Test 2: Integration Basic Tests"  
docker run --rm ffmpeg-mcp-ci-local:latest python -m pytest tests/ci/test_integration_basic.py -v --tb=short

echo ""
echo "📋 Test 3: MCP Server Tests"
docker run --rm ffmpeg-mcp-ci-local:latest python -m pytest tests/ci/test_mcp_server.py -v --tb=short

echo ""
echo "📋 Test 4: Workflow Minimal Tests"
docker run --rm ffmpeg-mcp-ci-local:latest python -m pytest tests/ci/test_workflow_minimal.py -v --tb=short

echo ""
echo "✅ All CI tests completed in Docker!"
echo "If these pass, the GitHub Actions CI should work too."