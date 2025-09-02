# Bergen Nature Music Video

> **Type**: Komposition  
> **BPM**: 120  
> **Duration**: 32 beats  
> **Created**: Converted from JSON komposition

## 🎬 Video Configuration

- **Resolution**: 1280x720
- **Frame Rate**: 24 fps  
- **Format**: MP4
- **Quality**: High (libx264, medium preset)

## 🎵 Audio Setup

- **Master BPM**: 120
- **Beat Pattern**: 0-32 beats
- **Audio Processing**: Trim to video duration, crossfades

## 🎞️ Segment Sequence

### Segment 1: "Mountain View Clouds" (0-8 beats)
- **Source**: `Bergen_In_Motion`
- **Duration**: 4.0 seconds (8 beats at 120 BPM)
- **Video Effects**: 
  - [Effects to be defined based on segment position/style]
- **Transitions**: [Fade configuration based on position in sequence]

### Segment 2: "Rooftop Sunset" (8-16 beats)
- **Source**: `Bergen_In_Motion`
- **Duration**: 4.0 seconds (8 beats at 120 BPM)
- **Video Effects**: 
  - [Effects to be defined based on segment position/style]
- **Transitions**: [Fade configuration based on position in sequence]

### Segment 3: "Green Waterfall" (16-32 beats)
- **Source**: `Bergen_In_Motion`
- **Duration**: 8.0 seconds (16 beats at 120 BPM)
- **Video Effects**: 
  - [Effects to be defined based on segment position/style]
- **Transitions**: [Fade configuration based on position in sequence]

## 🔄 Processing Workflow

1. **Parse Komposition**: Extract segments, effects, timing
2. **Registry Resolution**: Convert file IDs to actual media paths
3. **FFMPEG Generation**: Create filter_complex command with all effects
4. **Model-Specific Fixes**: Apply LLM-specific syntax corrections
5. **Execution**: Run FFMPEG with proper -map parameters
6. **Quality Check**: Validate output duration, format, and quality

---

*Converted from JSON komposition format*