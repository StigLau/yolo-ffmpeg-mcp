---
name: video-processing
description: FFmpeg video processing patterns, format strategy, and music video creation. Activated when working with video files, FFmpeg commands, or komposition workflows.
---

# Video Processing Patterns

## Music Video Creation Strategy

**Philosophy**: Separate video and audio processing streams for maximum flexibility.

- **Video Processing**: Focus on visual effects, timing, transitions (drop audio with `-an`)
- **Audio Integration**: External high-quality audio sources (MP3, WAV) replace video audio
- **Smart Assembly**: AI-guided combination of processed video + prepared audio

## Video Format Strategy

- **Final User Output**: Always use YUV420P for maximum compatibility (VLC, QuickTime)
- **Intermediate Processing**: YUV444P acceptable for internal workflows (higher quality)
- **Verification**: Test final videos in standard players before delivery

## Beat Timing System

- 120 BPM formula: 16 beats = 8 seconds
- Use FFmpeg setpts/atempo filters for beat synchronization
- Pre-input args: FFmpeg operations requiring arguments before `-i` need special parameter handling

## File Management

- **Source directory**: `/tmp/music/source/`
- **Temp directory**: `/tmp/music/temp/`
- **Screenshots**: `/tmp/music/screenshots/{sourceRef}/`
- **Metadata**: `/tmp/music/metadata/`
- **File IDs**: Format `file_12345678` for secure reference
- All file access restricted to allowed directories only

## Available Operations

convert, extract_audio, trim, resize, normalize_audio, to_mp3, replace_audio,
concatenate_simple, image_to_video, reverse, gradient_wipe, crossfade_transition,
opacity_transition
