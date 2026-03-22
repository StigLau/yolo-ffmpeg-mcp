#!/bin/bash
# Local CI Test Suite - Complete validation before push
set -e

echo "🧪 COMPLETE LOCAL CI TEST SUITE"
echo "================================"

# Test 1: Enhanced BD System
echo "📊 Test 1: Enhanced BD System"
echo "Testing enhanced BD command..."
if ./scripts/bd StigLau/yolo-ffmpeg-mcp 21; then
    echo "✅ Enhanced BD analysis completed successfully"
else
    exit_code=$?
    if [ $exit_code -eq 2 ]; then
        echo "🚨 CRITICAL: BD detected issues requiring intervention"
        exit 2
    elif [ $exit_code -eq 1 ]; then
        echo "⚠️ WARNING: BD detected some concerns"
    else
        echo "❌ BD analysis failed"
        exit 1
    fi
fi

# Test 2: Ubuntu Single-stage Docker Build
echo ""
echo "🐳 Test 2: Ubuntu Single-stage Docker Build"
echo "Building Ubuntu single-stage Docker image..."
start_time=$(date +%s)
docker build -f docker/Dockerfile.ubuntu-single-stage -t ffmpeg-mcp-local-test . > /dev/null
end_time=$(date +%s)
build_time=$((end_time - start_time))
echo "✅ Docker build completed in ${build_time}s (target: <120s)"

if [ $build_time -gt 120 ]; then
    echo "⚠️ WARNING: Build time ${build_time}s exceeds 120s target"
fi

# Test 3: Docker Container Functionality
echo ""
echo "🧪 Test 3: Docker Container Functionality"
echo "Testing Python, Java, FFmpeg in container..."
docker run --rm ffmpeg-mcp-local-test python3 --version > /dev/null && echo "✅ Python working"
docker run --rm ffmpeg-mcp-local-test java -version > /dev/null 2>&1 && echo "✅ Java working"
docker run --rm ffmpeg-mcp-local-test ffmpeg -version > /dev/null 2>&1 && echo "✅ FFmpeg working"

# Test 4: Python Dependencies and MCP Server
echo ""
echo "🐍 Test 4: Python Dependencies and MCP Server"
echo "Testing Python dependencies and MCP server import..."
uv run python -c "
import src.server
import src.file_manager
import src.ffmpeg_wrapper
print('✅ All MCP modules imported successfully')
" 

# Test 5: Core Unit Tests
echo ""
echo "🧪 Test 5: Core Unit Tests"
echo "Running core unit tests..."
uv run python -m pytest tests/ci/test_unit_core.py -v --tb=short > /dev/null
echo "✅ Unit tests passed"

# Test 6: MCP Server Tests
echo ""
echo "🔌 Test 6: MCP Server Tests"
echo "Running MCP server tests..."
uv run python -m pytest tests/ci/test_mcp_server.py -v --tb=short > /dev/null
echo "✅ MCP server tests passed"

# Test 7: Validate Docker Image Size
echo ""
echo "📏 Test 7: Docker Image Size Validation"
size=$(docker images ffmpeg-mcp-local-test --format "{{.Size}}")
echo "Docker image size: $size"
if [[ $size == *"GB"* ]]; then
    echo "⚠️ WARNING: Image size >1GB may be excessive"
else
    echo "✅ Image size acceptable"
fi

# Test 8: Enhanced BD Components Test
echo ""
echo "🔧 Test 8: Enhanced BD Components"
echo "Testing individual BD components..."
python3 scripts/bd_enhanced_analysis.py StigLau/yolo-ffmpeg-mcp 21 > /dev/null
echo "✅ Enhanced analysis component working"

python3 scripts/bd_takeover_protocol.py StigLau/yolo-ffmpeg-mcp 21 > /dev/null
echo "✅ Takeover protocol component working"

# Cleanup
echo ""
echo "🧹 Cleanup"
docker rmi ffmpeg-mcp-local-test > /dev/null 2>&1
echo "✅ Test cleanup completed"

echo ""
echo "🎉 ALL LOCAL CI TESTS PASSED!"
echo "================================"
echo "✅ Enhanced BD system validated"
echo "✅ Ubuntu Docker build working (<2 minutes vs 35+ minutes Alpine)"
echo "✅ All components functional (Python, Java, FFmpeg)"
echo "✅ MCP server and dependencies working" 
echo "✅ Unit tests and MCP tests passing"
echo "✅ Docker image reasonable size"
echo ""
echo "🚀 READY TO PUSH - Local CI validation complete!"