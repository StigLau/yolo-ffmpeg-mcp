# FFMPEG MCP Server - Alpine-based for smaller size and stability
FROM python:3.11-alpine

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apk add --no-cache \
    # Core utilities
    bash \
    curl \
    netcat-openbsd \
    # FFmpeg and multimedia
    ffmpeg \
    # Build tools and development libraries
    gcc \
    g++ \
    musl-dev \
    linux-headers \
    # OpenCV dependencies 
    glib-dev \
    # Audio processing
    libsndfile-dev \
    # Python development
    python3-dev \
    # For some pip packages
    build-base

# Install UV for fast Python package management
RUN pip install --no-cache-dir uv

# Create working directory
WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml ./

# Install core Python dependencies (lightweight versions for Alpine)
RUN uv pip install --system --no-cache \
    fastmcp>=2.7.1 \
    mcp>=1.9.3 \
    pydantic>=2.11.5 \
    # Testing dependencies
    pytest>=8.4.0 \
    pytest-asyncio>=1.0.0 \
    # Minimal dependencies for Alpine
    jsonschema>=4.0.0 \
    psutil>=5.9.0 \
    # Video effects dependencies
    opencv-python-headless>=4.8.0 \
    pillow>=10.0.0 \
    numpy>=1.24.0

# Create non-root user
RUN addgroup -g 1000 mcp && adduser -u 1000 -G mcp -s /bin/bash -D mcp

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/
COPY README.md ./

# Create directories for file processing
RUN mkdir -p /tmp/music/source /tmp/music/temp /tmp/music/screenshots /tmp/music/metadata /tmp/music/finished \
    && chown -R mcp:mcp /app /tmp/music

# Create health check script
RUN echo '#!/bin/bash\npython -c "import src.server; print(\"✅ MCP server OK\")" || exit 1' > /app/healthcheck.sh \
    && chmod +x /app/healthcheck.sh \
    && chown mcp:mcp /app/healthcheck.sh

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
      description="FFMPEG MCP Server - Alpine Build"