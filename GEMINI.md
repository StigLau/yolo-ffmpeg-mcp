# Gemini Integration Guide for FFMPEG MCP Server

This document outlines the key principles and workflows for interacting with the FFMPEG MCP server. It is intended to be a concise guide for AI assistants.

## 🎬 Music Video Creation

**Objective**: Combine video and audio to create music videos.

**Workflow**:
1.  **Video Processing**: Process video files (trim, effects, etc.), ignoring the original audio (`-an` flag in FFmpeg).
2.  **Audio Integration**: Use a separate audio track for the final video.
3.  **Assembly**: Combine the processed video with the new audio.

## 🗂️ File System Hygiene

**Core Rule**: No AI-generated files in the project root.

**Storage Locations**:
*   **Generated Content**: `/tmp/kompo/haiku-ffmpeg/` (e.g., `generated-videos/`, `youtube-downloads/`)
*   **Large Files (>10MB)**: Must be in `/tmp/kompo/haiku-ffmpeg/` unless approved as source files.
*   **Source Code**: `src/`
*   **Documentation**: `docs/`
*   **Archives**: `archive/`

**File Classification**:
*   **High Value (Keep)**: Source code, essential documentation, configuration.
*   **Medium Value (Archive)**: Historical analysis, old experiments.
*   **Low Value (Delete)**: AI-generated reports, build artifacts, large temporary files.

**File Creation Logging**: All file and folder creations must be logged in `FILE_CREATION_LOG.md`.

## 🏛️ Architectural Principles

*   **No Git Submodules**: Integrate with external projects (Komposteur, VideoRenderer) via APIs or managed dependencies, not git submodules.
*   **Hierarchical Agents**: The system is a multi-agent hierarchy with YOLO as the master orchestrator and specialized subagents (FastTrack, Komposteur, etc.).
*   **No Unauthorized Architectural Changes**: Do not change core dependencies, tech stacks, or base images without explicit permission.

## 🛠️ Development Workflow

*   **Build Detective (BD)**: Use the Build Detective tool for CI/build analysis before resorting to LLM analysis.
*   **Local CI**: Run the local CI validation (`uv run python test_basic_ci.py`) before pushing changes.
*   **Development vs. Production JARs**: Use local `~/.m2` JARs for development and GitHub Packages JARs for production.

## 🧠 LLM Integration & AI Restraint

*   **Haiku LLM / FastTrack**: Use the Haiku subagent for cost-effective video analysis and strategy selection.
*   **Avoid Over-Engineering**: 
    *   **The 3-Line Rule**: If a fix is likely small, spend more time analyzing than implementing.
    *   **Root Cause First**: Always identify the root cause before attempting a fix. Do not treat symptoms.
    *   **Incremental Changes**: Prefer small, verifiable changes over large, complex ones.
    *   **Consult Experts**: Ask for guidance on established patterns and conventions.
*   **Progressive Debugging**: A good debugging process reveals new, specific error messages with each fix. A bad pattern is when the same error persists after multiple, increasingly complex fixes.

## 🎥 Video Output

*   **Final Output**: Must be in `YUV420P` format for maximum compatibility. Use the `youtube_recommended_encode` operation.
*   **Intermediate Files**: Can be in `YUV444P` format.
