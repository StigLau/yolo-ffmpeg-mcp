# Core Components

This document provides a more detailed description of the core components of the FFMPEG MCP Server.

## `server.py`

This is the main entry point of the application. It uses the `FastMCP` framework to expose a set of tools that can be called remotely. The server is responsible for handling incoming requests, calling the appropriate tools, and returning the results.

The server defines a wide range of tools, including:

*   `list_files()`: Lists the available source files.
*   `get_file_info()`: Gets detailed metadata for a file.
*   `process_file()`: Processes a file using a specified FFMPEG operation.
*   `analyze_video_content()`: Analyzes the content of a video to identify scenes and objects.
*   `process_komposition_file()`: Creates a beat-synchronized music video from a `komposition` JSON file.

## `ffmpeg_wrapper.py`

This module provides a safe and convenient way to interact with the `ffmpeg` command-line tool. It defines a set of allowed operations and their corresponding command-line arguments, which helps to prevent command injection vulnerabilities.

The `FFMPEGWrapper` class provides the following methods:

*   `build_command()`: Builds a safe FFMPEG command.
*   `execute_command()`: Executes an FFMPEG command with a timeout.
*   `get_file_info()`: Gets file information using `ffprobe`.

## `file_manager.py`

This module is responsible for managing files and their IDs. It provides a secure way to access files by using randomly generated IDs instead of direct file paths. This helps to prevent unauthorized access to the filesystem.

The `FileManager` class provides the following methods:

*   `register_file()`: Registers a file and returns its ID.
*   `resolve_id()`: Converts a file ID to its actual path.
*   `create_temp_file()`: Creates a temporary file and returns its ID and path.
*   `cleanup_temp_files()`: Removes all temporary files.

## `content_analyzer.py`

This module uses `PySceneDetect` and `OpenCV` to analyze video content. It can detect scene changes, identify objects within scenes, and provide a summary of the video's content.

The `VideoContentAnalyzer` class provides the following methods:

*   `analyze_video_content()`: Analyzes the content of a video to identify scenes and objects.
*   `get_cached_analysis()`: Gets the cached analysis for a file.
*   `get_smart_trim_suggestions()`: Gets intelligent trim suggestions based on the content analysis.
*   `get_scene_screenshots()`: Gets screenshots for each scene in a video.
