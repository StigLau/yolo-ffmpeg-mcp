# Komposition Format Reference

**CRITICAL**: This document defines the correct komposition formats for the Cloud Music Video Creator system. Always refer to this when working with kompositions.

## Overview

The system uses two complementary formats:
1. **Markdown Specification (.md)** - Human-readable, LLM-parseable specification format
2. **JSON Komposition (.json)** - Machine-executable format with actual FFmpeg filters and beat timing

## Markdown Specification Format (.md)

**Purpose**: Natural language → structured specification that Haiku-style LLMs can parse into JSON komposition

### Template Structure

```markdown
# [Title]

**User Request**: "[Original natural language request]"

## Music Video Specification

### Basic Parameters
- **Duration**: [X] seconds
- **BPM**: [X] (tempo description)
- **Resolution**: [WIDTHxHEIGHT]
- **Style**: [Style description]

### Visual Concept
[Paragraph describing the overall visual flow and transitions]

### Segments

#### Segment [N]: [Name] (Beats [start]-[end])
- **Duration**: [X] seconds (beats [start]-[end])
- **Source**: [Source description]
- **Effects**:
  - [Effect description (maps to FFmpeg filter)]
  - [Effect description (maps to FFmpeg filter)]
- **Look**: [Visual description]

### Audio
- **Track**: [Description]
- **Volume**: [X]% 
- **Fade in**: [X] second[s]
- **Fade out**: [X] second[s]
- **Sync**: [Synchronization description]

### Technical Specs
- **Format**: [Container/codecs]
- **Frame rate**: [X]fps
- **Quality**: [Preset and CRF]
- **Audio**: [Sample rate and codec]
- **Beat precision**: [Timing accuracy]

### Expected Mood
[Mood and atmosphere description]

---

**Processing Notes**: [Additional context for komposition generation]
```

### Example (vintage_dreamy_30s.md)
```markdown
# Vintage Dreams with Dreamy Blur

**User Request**: "Make me a 30-second vintage music video with dreamy blur effects"

## Music Video Specification

### Basic Parameters
- **Duration**: 30 seconds
- **BPM**: 120 (moderate tempo for smooth transitions)
- **Resolution**: 1920x1080 HD
- **Style**: Vintage → Dreamy transition

### Visual Concept
Create a smooth transition from warm vintage aesthetics to soft dreamy atmosphere:
1. **First half (0-15s)**: Warm vintage sepia tones with film grain texture and subtle vignette
2. **Second half (15-30s)**: Soft blur effects with ethereal glow and gentle fade out
3. **Transition**: 2-second crossfade at 13s mark for seamless flow

### Segments

#### Segment 1: Vintage Opening (Beats 0-30)
- **Duration**: 15 seconds (beats 0-30)
- **Source**: Primary video content
- **Effects**:
  - Vintage color grading (sepia warmth, reduced saturation)
  - Film grain texture (medium intensity)
  - Subtle vignette (dark edges)
- **Look**: Classic film aesthetic with warm golden tones

#### Segment 2: Dreamy Outro (Beats 30-60)  
- **Duration**: 15 seconds (beats 30-60)
- **Source**: Same video content, different section
- **Effects**:
  - Soft blur (medium gaussian blur)
  - Ethereal glow (slight brightness boost)
  - Additional subtle blur accent
  - Fade to black over last 2 seconds
- **Look**: Dreamy, soft-focus atmosphere

### Audio
- **Track**: Vintage ambient atmosphere
- **Volume**: 70% (allows dialogue if present)
- **Fade in**: 1 second gentle entry
- **Fade out**: 1.5 seconds gradual exit
- **Sync**: Beat-perfect synchronization with visual cuts

### Technical Specs
- **Format**: MP4 (H.264/AAC)
- **Frame rate**: 25fps (cinematic feel)
- **Quality**: Medium preset, CRF 23 (good quality/size balance)
- **Audio**: 44.1kHz AAC
- **Beat precision**: Microsecond-accurate timing

### Expected Mood
Nostalgic vintage warmth flowing into dreamy ethereal softness, perfect for contemplative or artistic content.

---

**Processing Notes**: This specification should generate a komposition with beat-synchronized segments, real FFmpeg filters, and proper crossfade transitions suitable for Komposteur processing.
```

## JSON Komposition Format (.json)

**Purpose**: Machine-executable komposition with actual FFmpeg filters, beat timing, and Komposteur configuration

### Template Structure

```json
{
  "metadata": {
    "title": "[Title]",
    "description": "[Description]",
    "bpm": 120,
    "beatsPerMeasure": 4,
    "totalBeats": 60,
    "estimatedDuration": 30.0
  },
  "segments": [
    {
      "id": "[segment_id]",
      "startBeat": 0,
      "endBeat": 30,
      "duration": 15.0,
      "sourceType": "video",
      "sourceRef": "[source_file]",
      "operation": "trim",
      "params": {
        "start": 0,
        "duration": 15.0
      },
      "effects": [
        {
          "type": "[effect_type]",
          "name": "curated_ffmpeg",
          "intensity": 0.8,
          "ffmpeg_filter": "[actual_ffmpeg_filter]"
        }
      ],
      "description": "[Segment description]"
    }
  ],
  "transitions": [
    {
      "from_segment": "[segment_id_1]",
      "to_segment": "[segment_id_2]", 
      "type": "crossfade",
      "duration": 2.0,
      "ffmpeg_filter": "xfade=transition=fade:duration=2:offset=13"
    }
  ],
  "globalAudio": {
    "backgroundMusic": "[audio_file]",
    "musicStartOffset": 0.0,
    "musicVolume": 0.7,
    "fadeIn": 1.0,
    "fadeOut": 1.5
  },
  "outputSettings": {
    "resolution": "1920x1080",
    "fps": 25,
    "videoCodec": "libx264",
    "audioCodec": "aac",
    "audioSampleRate": 44100,
    "preset": "medium",
    "crf": 23
  },
  "komposteur_config": {
    "use_microsecond_precision": true,
    "cache_strategy": "intelligent",
    "validation_level": "comprehensive",
    "sync_accuracy": "beat_perfect"
  }
}
```

### Real Example (vintage_dreamy_30s.json)
```json
{
  "metadata": {
    "title": "Vintage Dreams with Dreamy Blur",
    "description": "30-second vintage music video transitioning to dreamy blur effects",
    "bpm": 120,
    "beatsPerMeasure": 4,
    "totalBeats": 60,
    "estimatedDuration": 30.0
  },
  "segments": [
    {
      "id": "vintage_segment",
      "startBeat": 0,
      "endBeat": 30,
      "duration": 15.0,
      "sourceType": "video",
      "sourceRef": "test_source_video.mp4",
      "operation": "trim",
      "params": {
        "start": 0,
        "duration": 15.0
      },
      "effects": [
        {
          "type": "vintage_grade",
          "name": "curated_ffmpeg",
          "intensity": 0.8,
          "ffmpeg_filter": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,hue=s=0.6,curves=vintage"
        },
        {
          "type": "film_grain",
          "intensity": 0.5,
          "ffmpeg_filter": "noise=alls=20:allf=t"
        },
        {
          "type": "vignette",
          "intensity": 0.6,
          "ffmpeg_filter": "vignette=PI/6"
        }
      ],
      "description": "Vintage sepia segment with film grain and vignette"
    },
    {
      "id": "dreamy_blur_segment", 
      "startBeat": 30,
      "endBeat": 60,
      "duration": 15.0,
      "sourceType": "video",
      "sourceRef": "test_source_video.mp4",
      "operation": "trim",
      "params": {
        "start": 15.0,
        "duration": 15.0
      },
      "effects": [
        {
          "type": "dreamy_blur",
          "intensity": 0.7,
          "ffmpeg_filter": "gblur=sigma=3:steps=1"
        },
        {
          "type": "soft_glow",
          "intensity": 0.5,
          "ffmpeg_filter": "eq=brightness=0.1:contrast=0.9"
        },
        {
          "type": "box_blur_accent",
          "intensity": 0.3,
          "ffmpeg_filter": "boxblur=luma_radius=1:luma_power=0.5"
        },
        {
          "type": "fade_out",
          "intensity": 1.0,
          "ffmpeg_filter": "fade=t=out:st=13:d=2"
        }
      ],
      "description": "Dreamy blur segment with soft glow and fade out"
    }
  ],
  "transitions": [
    {
      "from_segment": "vintage_segment",
      "to_segment": "dreamy_blur_segment", 
      "type": "crossfade",
      "duration": 2.0,
      "ffmpeg_filter": "xfade=transition=fade:duration=2:offset=13"
    }
  ],
  "globalAudio": {
    "backgroundMusic": "vintage_ambient_track.mp3",
    "musicStartOffset": 0.0,
    "musicVolume": 0.7,
    "fadeIn": 1.0,
    "fadeOut": 1.5
  },
  "outputSettings": {
    "resolution": "1920x1080",
    "fps": 25,
    "videoCodec": "libx264",
    "audioCodec": "aac",
    "audioSampleRate": 44100,
    "preset": "medium",
    "crf": 23
  },
  "komposteur_config": {
    "use_microsecond_precision": true,
    "cache_strategy": "intelligent",
    "validation_level": "comprehensive",
    "sync_accuracy": "beat_perfect"
  }
}
```

## Key Format Requirements

### Critical Elements for JSON Komposition:
1. **Beat Timing**: `startBeat`/`endBeat` must be calculated from BPM and duration
2. **Real FFmpeg Filters**: Each effect must have actual `ffmpeg_filter` commands
3. **Source References**: `sourceRef` must point to actual media files
4. **Komposteur Config**: Required for Java integration and microsecond precision
5. **Transitions**: Must have actual FFmpeg crossfade filters with timing

### Mapping MD → JSON:
- **"Vintage color grading"** → `"ffmpeg_filter": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,hue=s=0.6,curves=vintage"`
- **"Soft blur"** → `"ffmpeg_filter": "gblur=sigma=3:steps=1"`
- **"2-second crossfade at 13s"** → `"ffmpeg_filter": "xfade=transition=fade:duration=2:offset=13"`

### Integration Requirements:
- MCP server must accept/generate YOLO-format JSON kompositions
- Process komposition video tool must work with actual FFmpeg filters
- Beat synchronization requires Komposteur Java integration

## Example Files
- **Markdown**: `/tmp/music-video-creator/kompositions/vintage_dreamy_30s.md`
- **JSON**: `/tmp/music-video-creator/kompositions/vintage_dreamy_30s.json`

---

**REMEMBER**: Always use these formats, never create generic Python class structures for kompositions!