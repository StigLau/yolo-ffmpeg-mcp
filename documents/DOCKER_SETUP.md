# Docker Setup Guide for FFMPEG MCP Server

## Overview

This document provides comprehensive instructions for running the FFMPEG MCP Server in Docker containers. The Docker setup includes:

- **Multi-stage optimized build** for production deployment
- **External MCP access** while maintaining containerized processing
- **Volume mounts** for file processing and persistent data
- **Resource limits** and health monitoring
- **Development and production configurations**

## Quick Start

### 1. Build and Run (Production)

```bash
# Build the Docker image
docker build -t ffmpeg-mcp:latest .

# Run with docker-compose (recommended)
docker-compose up -d

# Or run directly
docker run -d \
  --name ffmpeg-mcp-server \
  -p 8000:8000 \
  -v $(pwd)/test-media:/tmp/music/source:ro \
  -v ffmpeg-temp:/tmp/music/temp \
  ffmpeg-mcp:latest
```

### 2. Verify Installation

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f ffmpeg-mcp

# Test MCP server
curl http://localhost:8000/health
```

### 3. Access MCP Server

The MCP server will be accessible at:
- **Host**: `localhost` or your Docker host IP
- **Port**: `8000`
- **Protocol**: Standard MCP over HTTP/WebSocket

**Claude Code Configuration:**
```json
{
  "mcpServers": {
    "ffmpeg-mcp": {
      "command": "nc",
      "args": ["localhost", "8000"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

## Directory Structure

```
ffmpeg-mcp/
├── Dockerfile                 # Multi-stage production build
├── docker-compose.yml         # Complete orchestration setup  
├── .dockerignore             # Build optimization
├── DOCKER_SETUP.md           # This documentation
├── src/                      # Application source code
├── tests/                    # Test suite
├── test-media/               # Source media files (mounted read-only)
└── pyproject.toml           # Python dependencies
```

## Volume Management

### Persistent Volumes

```bash
# List all FFMPEG MCP volumes
docker volume ls | grep ffmpeg

# Inspect volume details
docker volume inspect ffmpeg-metadata
docker volume inspect ffmpeg-screenshots
docker volume inspect ffmpeg-temp

# Backup volumes (important for production)
docker run --rm -v ffmpeg-metadata:/data -v $(pwd):/backup alpine tar czf /backup/metadata-backup.tar.gz -C /data .
```

### Volume Purposes

| Volume | Purpose | Persistence | Size |
|--------|---------|-------------|------|
| `test-media/` | Source files (read-only) | Host directory | Variable |
| `ffmpeg-temp` | Processing output | Docker volume | 10-50GB |
| `ffmpeg-screenshots` | Scene screenshots | Docker volume | 1-5GB |
| `ffmpeg-metadata` | Analysis cache | Docker volume | 100MB-1GB |
| `ffmpeg-logs` | Application logs | Docker volume | 100MB |

## Development Workflow

### 1. Development Mode with Live Reload

```bash
# Start with development profile (includes MCP Inspector)
docker-compose --profile dev up -d

# Access MCP Inspector at http://localhost:6274
```

### 2. Local Development with Container

```bash
# Build development image
docker build --target python-deps -t ffmpeg-mcp:dev .

# Run with local code mounted
docker run -it --rm \
  -v $(pwd)/src:/app/src \
  -v $(pwd)/tests:/app/tests \
  -p 8000:8000 \
  ffmpeg-mcp:dev \
  python -m src.server
```

### 3. Testing in Container

```bash
# Run tests in container
docker-compose exec ffmpeg-mcp python -m pytest tests/ -v

# Run specific test
docker-compose exec ffmpeg-mcp python -m pytest tests/test_ffmpeg_integration.py -v

# Run with coverage
docker-compose exec ffmpeg-mcp python -m pytest --cov=src tests/
```

## Production Deployment

### 1. Build Optimized Production Image

```bash
# Build with specific version tag
docker build -t ffmpeg-mcp:1.0.0 .

# Tag for registry
docker tag ffmpeg-mcp:1.0.0 your-registry/ffmpeg-mcp:1.0.0

# Push to registry
docker push your-registry/ffmpeg-mcp:1.0.0
```

### 2. Production docker-compose.yml

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  ffmpeg-mcp:
    image: your-registry/ffmpeg-mcp:1.0.0
    container_name: ffmpeg-mcp-prod
    ports:
      - "8000:8000"
    volumes:
      - /data/media:/tmp/music/source:ro
      - /data/ffmpeg-temp:/tmp/music/temp
      - /data/ffmpeg-screenshots:/tmp/music/screenshots
      - /data/ffmpeg-metadata:/tmp/music/metadata
    environment:
      - MCP_HOST=0.0.0.0
      - MAX_FILE_SIZE=1073741824  # 1GB for production
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '4.0'
    restart: always
```

### 3. Health Monitoring

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' ffmpeg-mcp-server

# Monitor resource usage
docker stats ffmpeg-mcp-server

# Set up log rotation
docker-compose exec ffmpeg-mcp logrotate /etc/logrotate.conf
```

## Troubleshooting

### Common Issues

**1. Container Won't Start**
```bash
# Check logs
docker-compose logs ffmpeg-mcp

# Common fixes:
# - Verify port 8000 is available
# - Check volume mount permissions
# - Ensure sufficient disk space
```

**2. MCP Server Not Accessible**
```bash
# Test internal connectivity
docker-compose exec ffmpeg-mcp python -c "import src.server; print('Server imports OK')"

# Check network configuration
docker network inspect ffmpeg-mcp-network

# Verify port binding
docker port ffmpeg-mcp-server
```

**3. File Processing Issues**
```bash
# Check FFmpeg installation
docker-compose exec ffmpeg-mcp ffmpeg -version

# Verify volume mounts
docker-compose exec ffmpeg-mcp ls -la /tmp/music/

# Test file permissions
docker-compose exec ffmpeg-mcp id
```

**4. Performance Issues**
```bash
# Monitor resource usage
docker stats --no-stream ffmpeg-mcp-server

# Check cache efficiency
docker-compose exec ffmpeg-mcp ls -la /tmp/music/metadata/

# Optimize container resources
# Edit docker-compose.yml resource limits
```

### Debug Mode

```bash
# Run container in debug mode
docker run -it --rm \
  -v $(pwd)/src:/app/src \
  --entrypoint /bin/bash \
  ffmpeg-mcp:latest

# Inside container, run manual tests
python -c "import src.server; print('Import successful')"
ffmpeg -version
ls -la /tmp/music/
```

## Security Considerations

### 1. Container Security

```bash
# Run security scan
docker scout cves ffmpeg-mcp:latest

# Check for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image ffmpeg-mcp:latest
```

### 2. Network Security

```bash
# Limit network access (production)
docker network create --driver bridge --internal ffmpeg-internal

# Use in docker-compose.yml:
networks:
  default:
    external:
      name: ffmpeg-internal
```

### 3. File System Security

```bash
# Set proper volume permissions
sudo chown -R 1000:1000 ./test-media
sudo chmod -R 755 ./test-media

# Use read-only mounts where possible
-v $(pwd)/test-media:/tmp/music/source:ro
```

## Future Speech Detection Integration

### Prepared Dependencies

The Docker image includes pre-installed libraries for future speech detection features:

```dockerfile
# Already included in Dockerfile:
torch>=2.0.0          # For Whisper and Silero VAD
torchaudio>=2.0.0      # Audio processing
librosa>=0.10.0        # Audio analysis  
pydub>=0.25.0          # Audio manipulation
```

### Adding Speech Detection

When implementing speech detection:

1. **Update pyproject.toml** with specific speech libraries:
```toml
dependencies = [
    # ... existing deps ...
    "openai-whisper>=20231117",
    "silero-vad-fork>=1.0.0",
    "webrtcvad-wheels>=2.0.0",
]
```

2. **Rebuild container**:
```bash
docker build -t ffmpeg-mcp:speech-v1 .
docker-compose down && docker-compose up -d
```

3. **Test new features**:
```bash
docker-compose exec ffmpeg-mcp python -c "import whisper; print('Whisper available')"
```

## Backup and Recovery

### Backup Persistent Data

```bash
#!/bin/bash
# backup-ffmpeg-data.sh

# Create backup directory
mkdir -p ./backups/$(date +%Y%m%d)

# Backup volumes
docker run --rm \
  -v ffmpeg-metadata:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/$(date +%Y%m%d)/metadata.tar.gz -C /data .

docker run --rm \
  -v ffmpeg-screenshots:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/$(date +%Y%m%d)/screenshots.tar.gz -C /data .
```

### Restore from Backup

```bash
#!/bin/bash
# restore-ffmpeg-data.sh

BACKUP_DATE=$1

docker run --rm \
  -v ffmpeg-metadata:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/$BACKUP_DATE/metadata.tar.gz -C /data

docker run --rm \
  -v ffmpeg-screenshots:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/$BACKUP_DATE/screenshots.tar.gz -C /data
```

## Performance Optimization

### Resource Tuning

```yaml
# Adjust in docker-compose.yml based on your hardware
deploy:
  resources:
    limits:
      memory: 8G        # Increase for large video processing
      cpus: '8.0'       # Use more CPUs for parallel processing
    reservations:
      memory: 1G        # Minimum guaranteed memory
      cpus: '1.0'       # Minimum guaranteed CPU
```

### Cache Optimization

```bash
# Monitor cache hit rates
docker-compose exec ffmpeg-mcp \
  find /tmp/music/metadata -name "*.json" | wc -l

# Clear cache if needed
docker-compose exec ffmpeg-mcp \
  rm -rf /tmp/music/metadata/*.json
```

This Docker setup provides a robust, scalable foundation for the FFMPEG MCP Server with room for future speech detection features and production deployment flexibility.