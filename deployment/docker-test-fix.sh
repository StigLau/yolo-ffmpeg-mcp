#!/bin/bash
# Quick test script to verify Docker fixes

set -e

echo "🐳 Testing Docker fixes..."

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down --remove-orphans || true

# Force rebuild with no cache
echo "🔨 Force rebuilding Docker image..."
docker-compose build --no-cache ffmpeg-mcp

# Start the container
echo "🚀 Starting container..."
docker-compose up -d ffmpeg-mcp

# Wait for startup
echo "⏳ Waiting for container startup..."
sleep 15

# Test pytest availability
echo "🧪 Testing pytest availability..."
docker-compose exec ffmpeg-mcp python -c "import pytest; print('✅ pytest available')"

# Test basic imports
echo "🔧 Testing basic imports..."
docker-compose exec ffmpeg-mcp python -c "import src.server; print('✅ MCP server imports OK')"

# Run a quick test
echo "🧪 Running quick test..."
docker-compose exec ffmpeg-mcp python -m pytest tests/test_ffmpeg_integration.py::TestFFMPEGIntegration::test_get_available_operations -v

echo "✅ Docker fixes verified!"

# Show container status
echo "📊 Container status:"
docker-compose ps

echo ""
echo "🎉 All tests passed! Docker environment is working correctly."
echo "You can now run: ./build-docker.sh test"