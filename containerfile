# Podman Containerfile for FFMPEG MCP Server
# Compatible with Docker but optimized for Podman's rootless containers

FROM python:3.13-slim

# Set environment variables for optimal Python performance
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Core utilities
    bash \
    curl \
    # FFmpeg and multimedia
    ffmpeg \
    mediainfo \
    libsndfile1 \
    # Build tools for Python packages
    gcc \
    g++ \
    # OpenCV dependencies 
    libopencv-dev \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install UV for ultra-fast Python package management
RUN pip install --no-cache-dir uv

# Create working directory
WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml ./

# Install Python dependencies with UV (10x faster than pip)
RUN uv pip install --system --no-cache \
    fastmcp>=2.7.1 \
    mcp>=1.9.3 \
    pydantic>=2.11.5 \
    pytest>=8.4.0 \
    pytest-asyncio>=1.0.0 \
    jsonschema>=4.0.0 \
    psutil>=5.9.0 \
    opencv-python-headless>=4.8.0 \
    pillow>=10.0.0 \
    numpy>=1.24.0

# Create non-root user for security (Podman rootless advantage)
RUN groupadd -g 1000 mcp && useradd -u 1000 -g mcp -s /bin/bash -m mcp

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/
COPY README.md CLAUDE.md ./

# Create directories for file processing
RUN mkdir -p /tmp/music/source /tmp/music/temp /tmp/music/screenshots /tmp/music/metadata /tmp/music/finished \
    && chown -R mcp:mcp /app /tmp/music

# Copy test files if available
COPY tests/files/*.mp4 /tmp/music/source/ 2>/dev/null || true
COPY tests/files/*.jpeg /tmp/music/source/ 2>/dev/null || true
COPY tests/files/*.flac /tmp/music/source/ 2>/dev/null || true
COPY tests/files/*.mp3 /tmp/music/source/ 2>/dev/null || true

# Fix ownership after file copy
RUN chown -R mcp:mcp /tmp/music

# Copy and setup component verification script
COPY scripts/verify_container_components.py /app/verify_components.py
RUN chmod +x /app/verify_components.py && chown mcp:mcp /app/verify_components.py

# Create health check script
RUN echo '#!/bin/bash\npython -c "import src.server; print(\"✅ MCP server OK\")" || exit 1' > /app/healthcheck.sh \
    && chmod +x /app/healthcheck.sh \
    && chown mcp:mcp /app/healthcheck.sh

# Verify components during build
RUN python /app/verify_components.py || (echo "❌ Component verification failed during build" && exit 1)

# Switch to non-root user
USER mcp

# Expose MCP server port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/healthcheck.sh

# Default command
CMD ["python", "-m", "src.server"]

# Labels
LABEL maintainer="Stig Lau" \
      version="1.0.0" \
      description="FFMPEG MCP Server - Podman Build with UV" \
      org.opencontainers.image.source="https://github.com/your-repo/yolo-ffmpeg-mcp"