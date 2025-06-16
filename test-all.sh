#!/bin/bash
set -e

echo "🚀 FFMPEG MCP Server - Complete Test Suite"
echo "=========================================="
echo ""

# Check if Docker is available and running
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo "🐳 Running tests in Docker (clean environment)..."
    
    # Build Docker image
    echo "   Building test environment..."
    docker build -f docker/Dockerfile.ci-test -t ffmpeg-mcp-test:latest . > /dev/null
    
    echo ""
    echo "📋 Test Results:"
    echo "----------------"
    
    # Run each test suite
    echo "🧪 Unit Core Tests:"
    docker run --rm ffmpeg-mcp-test:latest python -m pytest tests/ci/test_unit_core.py -v --tb=short | grep -E "(PASSED|FAILED|ERROR|test_)"
    
    echo ""
    echo "🧪 Integration Tests:"
    docker run --rm ffmpeg-mcp-test:latest python -m pytest tests/ci/test_integration_basic.py -v --tb=short | grep -E "(PASSED|FAILED|ERROR|SKIPPED|test_)"
    
    echo ""
    echo "🧪 MCP Server Tests:"
    docker run --rm ffmpeg-mcp-test:latest python -m pytest tests/ci/test_mcp_server.py -v --tb=short | grep -E "(PASSED|FAILED|ERROR|SKIPPED|test_)"
    
    echo ""
    echo "🧪 Workflow Tests:"
    docker run --rm ffmpeg-mcp-test:latest python -m pytest tests/ci/test_workflow_minimal.py -v --tb=short | grep -E "(PASSED|FAILED|ERROR|SKIPPED|test_)"
    
    echo ""
    echo "✅ All tests completed!"
    echo ""
    echo "💡 For detailed output, run: ./test-ci-local.sh"
    echo "💡 For specific tests, run: docker run --rm ffmpeg-mcp-test:latest python -m pytest [test-file] -v"
    
elif command -v uv >/dev/null 2>&1; then
    echo "⚡ Running tests with UV (ultra-fast Python package manager)..."
    
    echo ""
    echo "📋 Test Results:"
    echo "----------------"
    
    # Run tests with UV
    uv run pytest tests/ci/ -v --tb=short
    
    echo ""
    echo "✅ UV tests completed!"

elif command -v python3 >/dev/null 2>&1 && command -v pytest >/dev/null 2>&1; then
    echo "🐍 Running tests locally (using system Python)..."
    
    # Check if we're in UV environment
    if [[ -d ".venv" ]]; then
        echo "   Activating UV environment..."
        source .venv/bin/activate
    fi
    
    echo ""
    echo "📋 Test Results:"
    echo "----------------"
    
    # Run tests locally
    python -m pytest tests/ci/ -v --tb=short
    
    echo ""
    echo "✅ Local tests completed!"
    
else
    echo "❌ Error: Neither Docker nor Python3/pytest available"
    echo ""
    echo "Install options:"
    echo "  1. Install Docker (recommended for clean testing)"
    echo "  2. Install Python 3 + pytest: pip install pytest pytest-asyncio"
    echo "  3. Use UV: uv sync --group dev"
    exit 1
fi

echo ""
echo "📚 Next steps:"
echo "   - View documentation: cat README.md"
echo "   - Start MCP server: uv run python -m src.server"
echo "   - Development guide: cat CLAUDE.md"