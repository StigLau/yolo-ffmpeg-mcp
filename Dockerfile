# FFMPEG MCP Server - Production Docker Image
# Multi-stage build for optimized container size

# Stage 1: Base system with FFmpeg and Python
FROM python:3.13-slim-bookworm AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    # FFmpeg and multimedia libraries
    ffmpeg \
    # OpenCV dependencies
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # Audio processing dependencies
    libsndfile1 \
    # Network and security
    ca-certificates \
    # Build tools (needed for some Python packages)
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Stage 2: Python dependencies
FROM base AS python-deps

# Install UV for fast Python package management
RUN pip install uv

# Create working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies using UV
RUN uv pip install --system \
    fastmcp>=2.7.1 \
    mcp>=1.9.3 \
    opencv-python>=4.11.0.86 \
    pydantic>=2.11.5 \
    scenedetect>=0.6.6 \
    # Testing dependencies
    pytest>=8.4.0 \
    pytest-asyncio>=1.0.0

# Install additional dependencies for future speech detection features
# (Prepared but not required for current functionality)
RUN uv pip install --system \
    # Audio processing libraries
    librosa>=0.10.0 \
    pydub>=0.25.0 \
    # Speech processing (prepared for future features)
    torch>=2.0.0 \
    torchaudio>=2.0.0 \
    # JSON schema validation
    jsonschema>=4.0.0 \
    # Performance monitoring
    psutil>=5.9.0

# Stage 3: Final production image
FROM base AS production

# Create non-root user for security
RUN groupadd -r mcp && useradd -r -g mcp -s /bin/bash mcp

# Copy Python dependencies from previous stage
COPY --from=python-deps /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

# Create application directory
WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/
COPY pyproject.toml ./
COPY README.md ./

# Create directories for file processing
RUN mkdir -p /tmp/music/source /tmp/music/temp /tmp/music/screenshots /tmp/music/metadata \
    && chown -R mcp:mcp /app /tmp/music

# Create health check script
RUN echo '#!/bin/bash\npython -c "import src.server; print(\"MCP server imports successfully\")" || exit 1' > /app/healthcheck.sh \
    && chmod +x /app/healthcheck.sh \
    && chown mcp:mcp /app/healthcheck.sh

# Switch to non-root user
USER mcp

# Expose MCP server port (standard MCP protocol)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/healthcheck.sh

# Default command - start MCP server
CMD ["python", "-m", "src.server"]

# Labels for container metadata
LABEL maintainer="Stig Lau" \
      version="1.0.0" \
      description="FFMPEG MCP Server with Intelligent Video Processing" \
      org.opencontainers.image.source="https://github.com/stiglau/yolo-ffmpeg-mcp" \
      org.opencontainers.image.title="FFMPEG MCP Server" \
      org.opencontainers.image.description="Intelligent video processing with AI-powered content analysis"