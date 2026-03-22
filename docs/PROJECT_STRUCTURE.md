# FFMPEG MCP Server - Project Structure Guide

## 📁 Organized Project Layout for LLMs and Humans

This document provides a comprehensive overview of the project structure, optimized for both LLM navigation and human understanding.

## 🎯 Core System (`src/`)

### MCP Server Core
- **`server.py`** - Main MCP server with 15+ production tools
- **`file_manager.py`** - Secure file ID mapping and validation
- **`config.py`** - Security configuration and settings

### Video Processing Engine
- **`ffmpeg_wrapper.py`** - Safe FFMPEG command building and execution
- **`content_analyzer.py`** - AI-powered video content analysis
- **`video_normalizer.py`** - Video format standardization

### Intelligent Composition System
- **`komposition_generator.py`** - Generate komposition from text descriptions
- **`komposition_processor.py`** - Beat-synchronized music video processing
- **`komposition_build_planner.py`** - Build plan creation with dependency resolution
- **`composition_planner.py`** - High-level composition planning
- **`music_video_builder.py`** - Complete music video workflow orchestration

### Speech Detection & Audio Processing
- **`speech_detector.py`** - AI-powered speech detection using Silero VAD
- **`speech_komposition_processor.py`** - Speech-aware video composition
- **`enhanced_speech_analyzer.py`** - Advanced speech analysis capabilities

### Resource Management
- **`resource_manager.py`** - Resource registry and cache management
- **`deterministic_id_generator.py`** - Consistent file ID generation
- **`transition_processor.py`** - Video transition effects processing

## 🧪 Testing Infrastructure (`tests/`)

### CI/CD Tests
- **`ci/`** - Automated CI/CD pipeline tests
  - `test_unit_core.py` - Core component unit tests
  - `test_integration_basic.py` - Basic integration tests
  - `test_mcp_server.py` - MCP server functionality tests
  - `test_workflow_minimal.py` - Minimal workflow validation

### Development Tests
- **`dev/`** - Development and feature tests
  - `test_speech_features.py` - Speech detection testing
  - `test_resource_system.py` - Resource management tests

### Production Tests
- **`test_ffmpeg_integration.py`** - FFMPEG integration tests
- **`test_end_to_end_music_video.py`** - Complete workflow validation
- **`test_intelligent_content_analysis.py`** - Content analysis tests
- **`test_komposition_music_video.py`** - Komposition system tests

### Test Data & Media
- **`files/`** - Test videos, audio, and images
- **`data/`** - Test komposition JSON files and configurations

## 📚 Documentation (`documents/`)

### Human-Authored Specifications
- **`WORKFLOW_EXAMPLES.md`** - Complete production workflows
- **`DOCKER_SETUP.md`** - Production deployment guide
- **`SPEECH_DETECTION_FEATURE_SPEC.md`** - Speech feature specifications

### AI-Generated Documentation (`ai-generated/`)
- **`mcp-config/`** - MCP server configuration documentation
- **`workflow-analysis/`** - Workflow efficiency analysis
- **`komposition/`** - Beat-synchronized video system docs
- **`speech-detection/`** - Speech detection implementation docs
- **`feature-requests/`** - Feature requests and continuation guides

## 🛠️ Tools & Utilities

### Scripts (`scripts/`)
- **`run_ci_tests.sh`** - CI/CD test execution
- **`video_validator.py`** - Automated video validation
- **`main.py`** - Main entry point (moved from root)
- **`run_tests.py`** - Test runner utility (moved from root)

### Analysis Tools (`tools/analysis/`)
- **`analyze_transition_artifacts.py`** - Transition artifact analysis
- **`fix_transition_artifacts.py`** - Artifact correction utilities
- **`rebuild_frame_accurate_video.py`** - Frame-accurate video rebuilding

## 📖 Examples & Workflows

### Video Workflow Examples (`examples/video-workflows/`)
- **`create_beat_synchronized_video.py`** - Beat synchronization examples
- **`create_final_production.py`** - Production workflow examples
- **`build_your_video.py`** - Interactive video building
- **`working_demo_production.py`** - Demo production workflows

### Komposition Examples (`examples/komposition-examples/`)
- **`music_video_komposition.json`** - Complete music video komposition
- **`simple_music_video_komposition.json`** - Basic komposition example
- **`final_speech_music_video.json`** - Speech-synchronized video example
- **`correct_multi_video_komposition.json`** - Multi-source video composition

## 🗄️ Archive (`archive/`)

### Legacy Tests (`legacy-tests/`)
- Historical test files moved from root for reference
- Contains `test_*.py` files from earlier development phases

## 🐳 Deployment & Configuration

### Docker Infrastructure
- **`Dockerfile.ci`** - CI/CD optimized container
- **`Dockerfile`** - Production container
- **`docker-compose.yml`** - Multi-service deployment
- **`build-docker.sh`** - Automated Docker build script

### CI/CD Pipeline
- **`.github/workflows/ci.yml`** - GitHub Actions workflow
- **`pyproject.toml`** - Python project configuration
- **`uv.lock`** - Dependency lock file

## 🧭 LLM Navigation Guide

### Quick File Access by Function Area

**Core Video Processing**: `src/ffmpeg_wrapper.py`, `src/content_analyzer.py`

**Music Video Creation**: `src/komposition_*.py`, `src/music_video_builder.py`

**Speech Detection**: `src/speech_*.py`, `src/enhanced_speech_analyzer.py`

**Testing**: `tests/ci/`, `tests/test_*.py`

**Examples**: `examples/video-workflows/`, `examples/komposition-examples/`

**Documentation**: `documents/WORKFLOW_EXAMPLES.md`, `documents/ai-generated/`

### Problem Area Transitions

1. **Video Processing Issues** → Check `src/ffmpeg_wrapper.py`, `src/content_analyzer.py`
2. **Music Video Problems** → Navigate to `src/komposition_processor.py`, `examples/komposition-examples/`
3. **Speech Detection** → Focus on `src/speech_detector.py`, `documents/ai-generated/speech-detection/`
4. **Testing Issues** → Reference `tests/ci/`, `scripts/video_validator.py`
5. **Configuration** → Check `src/config.py`, `documents/ai-generated/mcp-config/`

This structure enables rapid context switching between problem domains while maintaining logical organization for human developers.