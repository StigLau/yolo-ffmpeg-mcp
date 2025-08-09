# FFMPEG MCP Server - Production image using pre-built base
FROM ghcr.io/stiglau/yolo-ffmpeg-mcp:base-latest

# Copy dependency files first for better layer caching
COPY pyproject.toml ./

# Install core Python dependencies (fast - heavy packages pre-installed in base)
RUN uv pip install --system --no-cache \
    fastmcp>=2.7.1 \
    mcp>=1.9.3 \
    pydantic>=2.11.5 \
    pytest>=8.4.0 \
    pytest-asyncio>=1.0.0 \
    jsonschema>=4.0.0 \
    PyYAML>=6.0
# Note: opencv-python-headless, pillow, numpy, psutil pre-installed in base image

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/
COPY README.md ./

# Set Python path for module imports  
ENV PYTHONPATH=/app
# Also add to shell profile for interactive sessions
RUN echo 'export PYTHONPATH=/app' >> /etc/profile

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