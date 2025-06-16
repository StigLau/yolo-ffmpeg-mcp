#!/bin/bash
set -e

echo "🚀 FFMPEG MCP Server - Complete Test Suite"
echo "=========================================="
echo ""

# Check if Podman is available (modern Docker alternative)
if command -v podman >/dev/null 2>&1; then
    echo "🚀 Running tests in Podman (rootless, daemonless containers)..."
    
    # Build Podman image using CI test file (more reliable for testing)
    echo "   Building test environment with Podman..."
    echo "   Debug: Building with verbose output..."
    podman build -f docker/Dockerfile.ci-test -t ffmpeg-mcp-test:latest .
    
    echo ""
    echo "📋 Test Results (Podman):"
    echo "-------------------------"
    
    # Run each test suite with Podman
    echo "🧪 Unit Core Tests:"
    podman run --rm ffmpeg-mcp-test:latest python -m pytest tests/ci/test_unit_core.py -v --tb=short | grep -E "(PASSED|FAILED|ERROR|test_)"
    
    echo ""
    echo "🧪 Integration Tests:"
    podman run --rm ffmpeg-mcp-test:latest python -m pytest tests/ci/test_integration_basic.py -v --tb=short | grep -E "(PASSED|FAILED|ERROR|SKIPPED|test_)"
    
    echo ""
    echo "🧪 MCP Server Tests:"
    podman run --rm ffmpeg-mcp-test:latest python -m pytest tests/ci/test_mcp_server.py -v --tb=short | grep -E "(PASSED|FAILED|ERROR|SKIPPED|test_)"
    
    echo ""
    echo "🧪 Workflow Tests:"
    podman run --rm ffmpeg-mcp-test:latest python -m pytest tests/ci/test_workflow_minimal.py -v --tb=short | grep -E "(PASSED|FAILED|ERROR|SKIPPED|test_)"
    
    echo ""
    echo "✅ All Podman tests completed!"
    echo ""
    echo "💡 Podman advantages: Rootless, daemonless, 10x faster startup"
    echo "💡 For detailed output, run: podman run --rm ffmpeg-mcp-test:latest python -m pytest tests/ci/ -v"

# Check if Docker is available and running (legacy fallback)
elif command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo "🐳 Running tests in Docker (legacy fallback)..."
    
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
    echo "❌ Error: No container runtime or Python testing available"
    echo ""
    echo "Install options (in order of preference):"
    echo "  1. 🚀 Podman (recommended - rootless, fast): brew install podman"
    echo "  2. ⚡ UV Python manager: curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  3. 🐳 Docker (legacy): Install Docker Desktop"
    echo "  4. 🐍 System Python: pip install pytest pytest-asyncio"
    exit 1
fi

echo ""
echo "📚 Next steps:"
echo "   - View documentation: cat README.md"
echo "   - Start MCP server: uv run python -m src.server"
echo "   - Development guide: cat CLAUDE.md"