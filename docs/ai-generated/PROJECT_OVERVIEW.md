# Project Overview: YOLO FFMPEG MCP Server

This project is an advanced FFMPEG-based Media Context Protocol (MCP) server designed for intelligent video processing, analysis, and "komposition" (composition). It offers a comprehensive suite of tools
for automated video editing, with a strong focus on content-aware operations, speech analysis, and beat-synchronized music video creation.

## Core Components and Functionality

### 1. Server and Configuration
*   **MCP Server (`src/server.py`):** The central FastMCP server exposing all functionalities as tools. It orchestrates the various backend modules.
*   **Configuration (`src/config.py`):** The `SecurityConfig` class manages critical settings like allowed file extensions, maximum file sizes, process timeouts, resource limits, FFMPEG binary path, and
    directory paths for source, temporary, and screenshot files.
*   **File Management (`src/file_manager.py`):** The `FileManager` class handles media file registration, unique ID generation, path resolution (from ID to actual path), temporary file creation, and     
    caching of file properties. It operates with configured source (`/tmp/music/source`) and temporary (`/tmp/music/temp`) directories.

### 2. Media Processing
*   **FFMPEG Abstraction (`src/ffmpeg_wrapper.py`):** The `FFMPEGWrapper` provides a Pythonic interface to FFMPEG. It defines a dictionary of `ALLOWED_OPERATIONS` (e.g., convert, extract_audio, trim,    
    resize, various transitions, image_to_video, smart concatenation), builds FFMPEG command lines safely, and executes them. It can also retrieve media file information using `ffprobe` and includes file    
    property caching via `FileManager`.
*   **Video Normalization (`src/video_normalizer.py`):** The `VideoNormalizer` standardizes video files to consistent formats (orientation, resolution) by analyzing a set of videos to determine an       
    optimal common format and then applying rotation, scaling, and padding.

### 3. Content Analysis
*   **Video Content Analysis (`src/content_analyzer.py`):** The `VideoContentAnalyzer` uses PySceneDetect for scene boundary detection and OpenCV for basic object recognition (faces, eyes) and frame     
    characteristic analysis (brightness, color, detail). It generates scene-specific screenshots and compiles analysis reports with editing suggestions and highlight identification.
*   **Speech Detection (`src/speech_detector.py`):** The `SpeechDetector` uses Silero VAD (with WebRTC VAD as a fallback) to identify speech segments in audio/video files. It provides timestamps,        
    confidence scores, and basic quality assessment for each segment, featuring a pluggable backend system and caching.
*   **Enhanced Speech Analysis (`src/enhanced_speech_analyzer.py`):** The `EnhancedSpeechAnalyzer` builds upon basic speech detection. It refines speech segments with details like natural pause          
    detection, pitch range, and quality scoring. It identifies optimal cut points and generates cut strategies for fitting speech into target durations.

### 4. "Komposition" System (Automated Video Assembly)
*   **Komposition Generator (`src/komposition_generator.py`):** The `KompositionGenerator` parses natural language descriptions to create `komposition.json` files (structured blueprints for videos). It  
    interprets intent regarding BPM, resolution, content keywords, musical structure, and aesthetic styles (e.g., "leica-like", "cinematic").
*   **Komposition Build Planner (`src/komposition_build_planner.py`):** The `KompositionBuildPlanner` transforms a `komposition.json` into a detailed, step-by-step build plan. It performs precise beat   
    timing calculations for any BPM, maps file dependencies, plans snippet extractions with exact timestamps, and orders effect operations.
*   **Komposition Processor (`src/komposition_processor.py`):** The `KompositionProcessor` takes a `komposition.json` and processes its segments according to beat timing. It handles different media types
    (image to video, video extraction/stretching) and concatenates segments, optionally adding a global audio track.
*   **Speech-Aware Komposition Processor (`src/speech_komposition_processor.py`):** An extension of `KompositionProcessor`, this class specifically handles segments with `speechOverlay` configurations.  
    It intelligently mixes original speech (extracted from video segments) with background music, adjusting volumes based on speech presence.
*   **Transition Processor (`src/transition_processor.py`):** This processor handles `komposition.json` files that define an `effects_tree` for advanced visual transitions (e.g., gradient wipe,          
    crossfade, opacity), applying them recursively based on the tree structure.                                                                                                                                

### 5. Intelligent Composition Planning
*   **Composition Planner (`src/composition_planner.py`):** An advanced engine for creating `komposition-plan.json` files. It analyzes multiple video sources, performs speech-aware time allocation based
    on BPM, optimizes source-to-slot assignments, generates cutting strategies, plans audio handling (including background music and speech overlays), and creates an effects chain.

## Key Workflows (Exposed via MCP Server)

1.  **File Management & Info:** `list_files`, `get_file_info`, `list_generated_files`.
2.  **Basic Processing:** `process_file` for individual FFMPEG operations (trim, convert, resize, extract_audio, replace_audio, concatenate_simple, image_to_video, etc.).
3.  **Content Analysis:** `analyze_video_content`, `get_video_insights`, `smart_trim_suggestions`, `get_scene_screenshots`.
4.  **Speech Analysis:** `detect_speech_segments`, `get_speech_insights`, `analyze_composition_sources` (uses `EnhancedSpeechAnalyzer`).
5.  **Komposition Workflow:**
    *   `generate_komposition_from_description` (NLP to `komposition.json`).
    *   `create_build_plan_from_komposition` (`komposition.json` to detailed build plan).
    *   `validate_build_plan_for_bpms` (tests build plan timing).
    *   `process_komposition_file` (basic komposition execution).
    *   `process_transition_effects_komposition` (executes kompositions with advanced transitions).
    *   `process_speech_komposition` (executes kompositions with speech overlays).
6.  **Intelligent Composition Workflow:**
    *   `generate_composition_plan` (creates a high-level intelligent plan).
    *   `process_composition_plan` (executes the intelligent plan).
    *   `preview_composition_timing` (quick timing preview without full processing).
7.  **Atomic Workflow:** `create_video_from_description` (combines generation, planning, and optional building from a single text prompt).
8.  **Audio Manifest Workflow:** `build_video_from_audio_manifest` (builds video based on detailed audio timing).
9.  **Utility:** `cleanup_temp_files`, `get_available_operations`.
10. **Batch Processing:** `batch_process` for sequential execution of multiple operations.

## Development and Build Environment

### Dependencies (`pyproject.toml`)
*   Core: `fastmcp`, `mcp`, `opencv-python`, `pydantic`, `scenedetect`.
*   Speech: `librosa`, `pydub`, `torch`, `torchaudio`, `silero-vad`, `jsonschema`, `psutil`.
*   Development: `pytest`, `pytest-asyncio`.

### Dockerfiles
*   **`Dockerfile` (Production):** A multi-stage build (`python:3.13-slim-bookworm` base) for an optimized production image. Installs system dependencies (FFMPEG, OpenCV libs, audio libs), Python        
    dependencies via `uv`, creates a non-root user `mcp`, sets up necessary directories, includes a health check, and defaults to running `python -m src.server`.
*   **`Dockerfile.simple` (Testing/Development):** A simpler Docker build (`python:3.11-slim` base) primarily for speech detection testing. Also uses `uv` and installs similar dependencies, with         
    fallbacks for PyTorch/Silero VAD. Defaults to running `python test_lookin_docker.py`.                                                                                                                      

### Makefile
Provides convenience commands for:
*   `install`: Install dependencies using `uv sync`.
*   `start`: Start the MCP server.
*   `test`: Run integration tests (`tests/test_ffmpeg_integration.py`).
*   `clean`: Remove temporary files and `uv` cache.
*   `setup-dirs`: Create necessary `/tmp/music/` subdirectories.
*   `dev`: Full development setup (setup-dirs + install).
*   `config`: Generate MCP configuration for Claude Code.
*   `add-mcp`: Add MCP server to Claude Code project scope.
*   `inspector`: Start MCP Inspector.

### Testing
*   Integration tests for FFMPEG operations are in `tests/test_ffmpeg_integration.py`.
*   A Docker-specific test script `test_lookin_docker.py` is used by `Dockerfile.simple` to verify speech detection capabilities within the container.                                                     


I want you to interact with the MCP server and use it only. With it I want you to build a music video with the speed of 120 BPM and have the video last for 128 beats. You should use the snippets you fiWe 
nd from the scenes we have from the video metadata and compose a nice history based on the snippets being played for 8 beats each. Choose one of the songs for backing music. If possible, I want the video to have a rough Leica look. Report back if you see issues or improvement proposals with the MCP Server API                                                                                            

                                   