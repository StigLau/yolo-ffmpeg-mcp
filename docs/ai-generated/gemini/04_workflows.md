# Workflows

This document describes some of the key workflows that the FFMPEG MCP Server supports.

## Basic Video Editing

This workflow shows how to perform basic video editing operations, such as trimming, resizing, and converting a video.

1.  **List the available files**: Use the `list_files()` tool to get a list of the available source files.
2.  **Get file information**: Use the `get_file_info()` tool to get detailed metadata for the video you want to edit.
3.  **Process the file**: Use the `process_file()` tool to perform the desired editing operation. For example, to trim a video, you would use the `trim` operation and specify the start time and duration of the trim.
4.  **List the generated files**: Use the `list_generated_files()` tool to see the new video that you created.

## Intelligent Video Editing

This workflow shows how to use the content analysis features of the server to perform intelligent video editing.

1.  **Analyze the video content**: Use the `analyze_video_content()` tool to analyze the content of the video. This will identify the scenes in the video and the objects that appear in each scene.
2.  **Get smart trim suggestions**: Use the `get_smart_trim_suggestions()` tool to get intelligent trim suggestions based on the content analysis. The server will suggest the best scenes to include in a highlight reel.
3.  **Process the file**: Use the `process_file()` tool to trim the video based on the suggestions from the previous step.

## Music Video Creation

This workflow shows how to create a beat-synchronized music video from a set of video clips and a music track.

1.  **Create a `komposition` file**: Create a JSON file that defines the structure of the music video. The `komposition` file should specify the video clips to use, their timing, and the background music.
2.  **Process the `komposition` file**: Use the `process_komposition_file()` tool to create the music video. The server will automatically synchronize the video clips to the beat of the music.
