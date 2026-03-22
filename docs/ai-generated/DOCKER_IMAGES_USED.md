# Docker Images Used in CI/CD Pipeline

## 📋 Overview

This document details all Docker images and build strategies used across our CI/CD workflows.

## 🏗️ Build Workflows and Docker Images

### 1. **Main Application Dockerfile** (`Dockerfile`)
- **Base Image**: `python:3.13-alpine`
- **Usage**: Production MCP server container
- **Built By**: MCP Server Docker Tests workflow
- **Dependencies**: FFMPEG + Java + Python + minimal MCP packages
- **Tag**: `ffmpeg-mcp:ci` (CI testing)
- **Strategy**: Self-contained minimal Alpine build

### 2. **Base Image Workflows**

#### A. `build-base-images-fast.yml`
**Test Matrix Build**:
- **Dockerfile.base** → Tag: `test-base-alpine`
  - Base: `python:3.13-alpine`
  - Includes: OpenCV, NumPy, full dependencies
- **Dockerfile.base.optimized** → Tag: `test-base-alpine-minimal` 
  - Base: `python:3.13-alpine`
  - Includes: Only FFMPEG + Java + Python + psutil

**Production Build** (main branch only):
- **Output**: `ghcr.io/stiglau/yolo-ffmpeg-mcp:base-optimized-latest`
- **From**: `Dockerfile.base.optimized`
- **Platform**: linux/amd64

#### B. `build-base-images.yml`
- **Output**: `ghcr.io/stiglau/yolo-ffmpeg-mcp:base-latest`
- **From**: `Dockerfile.base`
- **Includes**: Full dependencies (OpenCV, NumPy, UV)

#### C. `build-manual-base-images.yml` (Manual Trigger)
**Alpine Base**:
- **Output**: `ghcr.io/stiglau/yolo-ffmpeg-mcp:base-alpine-latest`
- **From**: `Dockerfile.base`
- **Platform**: linux/amd64, linux/arm64

**Alpine Optimized**:
- **Output**: `ghcr.io/stiglau/yolo-ffmpeg-mcp:base-alpine-optimized-latest`
- **From**: `Dockerfile.base.optimized`
- **Platform**: linux/amd64, linux/arm64

### 3. **CI Test Images**

#### MCP Server Tests (`mcp-server-tests.yml`)
- **Main Build**: Uses main `Dockerfile` (self-contained Alpine)
- **Tag**: `ffmpeg-mcp:ci`
- **Test Container**: `mcp-test-container`
- **Strategy**: Build + test in same workflow

#### Podman Alternative (`ci-podman.yml`)
- **Dynamic Dockerfile**: `python:3.13-alpine` (generated in workflow)
- **Purpose**: Podman vs Docker comparison testing

## 🎯 Current Strategy

### **Production Approach**: Self-Contained Alpine
- **Main Dockerfile**: Builds everything from `python:3.13-alpine`
- **Advantages**: Simple, reliable, no external dependencies
- **Build Time**: ~3-5 minutes
- **Dependencies**: Only essential packages (FFMPEG + Java + Python + MCP)

### **Base Image Strategy**: Available but Unused
- **Status**: Base images defined but not referenced by main Dockerfile
- **Purpose**: Future optimization potential
- **Manual Trigger**: Available via `build-manual-base-images.yml`

## 📊 Image Registry Locations

### GitHub Container Registry (GHCR)
- **Registry**: `ghcr.io/stiglau/yolo-ffmpeg-mcp`
- **Tags**:
  - `base-latest` - Full Alpine base with all dependencies
  - `base-optimized-latest` - Minimal Alpine base
  - `base-alpine-latest` - Manual Alpine build (multi-platform)
  - `base-alpine-optimized-latest` - Manual minimal build (multi-platform)

### Local/CI Tags
- `ffmpeg-mcp:ci` - Main application for testing
- `test-base-alpine` - Test build of full base
- `test-base-alpine-minimal` - Test build of minimal base

## 🔧 Dockerfile Mapping

| Dockerfile | Purpose | Base Image | Used By | Registry Tag |
|------------|---------|------------|---------|--------------|
| `Dockerfile` | **Main App** | `python:3.13-alpine` | **Production** | Built locally in CI |
| `Dockerfile.base` | Full Base | `python:3.13-alpine` | Manual/Test | `base-latest` |
| `Dockerfile.base.optimized` | **Minimal Base** | `python:3.13-alpine` | Manual/Test | `base-optimized-latest` |

## 🚀 Optimization Opportunities

### Current State: ✅ Working
- Main Dockerfile builds everything (3-5 minutes)
- No external base image dependencies
- Simple and reliable

### Future Optimization: 📦 Available
1. **Build base images** via manual workflow
2. **Switch main Dockerfile** to use pre-built base
3. **Reduce build time** from 3-5 minutes to ~30 seconds

### Implementation Path
```bash
# 1. Build base image (manual)
gh workflow run "Manual Base Image Build" --ref main

# 2. Update main Dockerfile FROM line
FROM ghcr.io/stiglau/yolo-ffmpeg-mcp:base-alpine-optimized-latest

# 3. Remove dependency installation from main Dockerfile
```

## 🎭 Testing Strategy

### Matrix Testing
- **Full Alpine** vs **Minimal Alpine** performance comparison
- **Build time tracking** and **image size comparison**
- **Dependency validation** for each variant

### Docker Health Checks
- **FFMPEG functionality**: `ffmpeg -version`
- **Python imports**: MCP modules + dependencies
- **File operations**: Video creation and processing

## 📈 Performance Metrics

### Build Times (Current)
- **Main Dockerfile**: 3-5 minutes (self-contained)
- **Base Images**: 5-10 minutes (full dependencies)
- **Optimized Base**: 2-3 minutes (minimal dependencies)

### Image Sizes
- **Full Base**: ~800MB-1GB (with OpenCV/NumPy)
- **Minimal Base**: ~300-400MB (FFMPEG + Java + Python only)
- **Final App**: Depends on base + ~50MB app code

## 🔄 Workflow Triggers

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `build-base-images-fast.yml` | Push to `main`/`feature/docker-*` | Performance testing |
| `build-base-images.yml` | Push to `main` | Production base builds |
| `build-manual-base-images.yml` | **Manual only** | On-demand base caching |
| `mcp-server-tests.yml` | All PRs | Main application testing |

---

**Last Updated**: 2025-01-17  
**Status**: Self-contained Alpine approach working ✅  
**Next Step**: Consider base image optimization for faster builds 📦