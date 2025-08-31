# 80 BPM Music Video - CI Test Specification

## Test Purpose
Validate LLM command generation capabilities (Sonnet, Haiku, Gemini) for music video creation with standardized requirements.

## Success Criteria
✅ **WORKING BASELINE**: Python FFMPEG MCP implementation successful
- File: `80bpm_subnautic_3sec_segments.mp4` 
- Size: 1,710,700 bytes
- Duration: 18.00s (exact)
- Processing time: 5.80s

## Test Requirements

### Input Files
- **Video**: `/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4`
- **Audio**: `/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/Subnautic Measures.flac`
- **BPM**: 80 BPM (corrected from original 120 BPM assumption)

### Video Specifications
- **Segments**: 6 segments × 3.0 seconds each = 18.0s total
- **Timing**: 80 BPM = 1.33 beats/second = 4 beats = 3.0 seconds per segment
- **Segment Times**: 
  1. 84.82s-87.82s (3.0s duration)
  2. 180.33s-183.33s (3.0s duration) 
  3. 167.33s-170.33s (3.0s duration)
  4. 42.98s-45.98s (3.0s duration)
  5. 17.95s-20.95s (3.0s duration)
  6. 13.11s-16.11s (3.0s duration)

### Visual Effects
- **Segments 1-3**: 8-bit retro effect for better transition visibility
  - `scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10`
- **Segments 4-6**: Leica cinematic look  
  - `colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4`

### Transition Effects
- **Type**: Smooth fade in/out transitions (0.3s duration)
- **Implementation**: 
  - Segment 1: fade out only at end
  - Segments 2-5: fade in at start, fade out at end  
  - Segment 6: fade in only at start
- **NO harsh cuts or white flashes** (previous issue resolved)

### Output Format
- **Codec**: H.264 (`-c:v libx264 -preset medium`)
- **Audio**: AAC (`-c:a aac -b:a 128k`)
- **Pixel Format**: `yuv420p` (user-compatible)
- **Resolution**: 1280x720

## Working FFMPEG Command (Reference)
```bash
ffmpeg -y -i /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4 -i /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/Subnautic\ Measures.flac -filter_complex [0:v]trim=start=84.82:duration=3.0,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=out:st=2.7:d=0.3[seg0];[0:v]trim=start=180.33:duration=3.0,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg1];[0:v]trim=start=167.33:duration=3.0,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg2];[0:v]trim=start=42.98:duration=3.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg3];[0:v]trim=start=17.95:duration=3.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg4];[0:v]trim=start=13.11:duration=3.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3[seg5];[seg0][seg1][seg2][seg3][seg4][seg5]concat=n=6:v=1:a=0[finalvideo];[1:a]atrim=duration=18.0[finalaudio] -map [finalvideo] -map [finalaudio] -c:v libx264 -preset medium -c:a aac -b:a 128k -pix_fmt yuv420p /tmp/kompo/haiku-ffmpeg/120bpm-music-videos/80bpm_subnautic_3sec_segments.mp4
```

**Command Length**: 1761 characters

## Test Prompts for LLM Comparison

### Standardized Prompt
```
Create an 80 BPM music video using FFMPEG with these exact specifications:

REQUIREMENTS:
- Input video: /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4
- Input audio: /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/Subnautic Measures.flac
- Tempo: 80 BPM (4 beats = 3.0 seconds per segment)
- Total duration: exactly 18.0 seconds
- Output: /tmp/kompo/haiku-ffmpeg/120bpm-music-videos/output.mp4

VIDEO SEGMENTS (use these exact timestamps):
1. Segment 1: 84.82s - 87.82s (3.0s duration)
2. Segment 2: 180.33s - 183.33s (3.0s duration) 
3. Segment 3: 167.33s - 170.33s (3.0s duration)
4. Segment 4: 42.98s - 45.98s (3.0s duration)
5. Segment 5: 17.95s - 20.95s (3.0s duration)
6. Segment 6: 13.11s - 16.11s (3.0s duration)

TRANSITIONS:
- 0.3 second fade in/out transitions between segments
- NO harsh cuts or white flashes

VIDEO EFFECTS:
- Segments 1-3: 8-bit retro effect (scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10)
- Segments 4-6: Leica cinematic look (colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4)

OUTPUT FORMAT:
- Codec: H.264 (-c:v libx264 -preset medium)
- Audio: AAC (-c:a aac -b:a 128k)
- Pixel format: yuv420p (user-compatible)

TASK: Generate the complete FFMPEG command that implements all these requirements in a single command.
```

### Simplified Prompt (for smaller models)
```
Create a music video using FFMPEG with these requirements:

- Extract 6 segments (3 seconds each) from video at specific timestamps
- Apply visual effects: 8-bit effect on first 3 segments, cinematic look on last 3 segments  
- Add smooth fade transitions (0.3 second) between segments
- Combine with audio track, trim to 18 seconds total
- Output as H.264 MP4 with YUV420P format

Input files:
- Video: /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4
- Audio: /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/Subnautic Measures.flac

Segment times: 84.82s, 180.33s, 167.33s, 42.98s, 17.95s, 13.11s (3s each)

Generate the FFMPEG command.
```

## Quality Validation Criteria

### Command Quality
- [ ] Correct segment extraction with exact timestamps
- [ ] Proper fade transitions (no harsh cuts)
- [ ] Correct visual effects application
- [ ] Audio synchronization maintained
- [ ] Output format specifications met

### Output Quality  
- [ ] Duration: 18.00s ± 0.1s
- [ ] File size: ~1.7MB (similar to baseline)
- [ ] Visual continuity and flow
- [ ] Audio quality maintained
- [ ] No encoding errors

## Previous Issues Resolved

### ❌ Original Issues (120 BPM version)
- Harsh white transitions instead of smooth fades
- 2.0s segments felt too rushed  
- Complex xfade transitions failed with frame rate issues

### ✅ Solutions Applied (80 BPM version)
- Simple fade in/out transitions (0.3s)
- 3.0s segments for proper 80 BPM feel
- 8-bit effects on first half for better transition visibility
- No tempo stretching (avoided encoding issues)

## Test Execution

### Manual Test Command
```bash
# Execute the working baseline
uv run python create_120bpm_fade_transitions.py

# Expected output file
ls -la /tmp/kompo/haiku-ffmpeg/120bpm-music-videos/80bpm_subnautic_3sec_segments.mp4
```

### Automated Test Framework
1. **Haiku MCP Test**: Execute with TypeScript MCP server
2. **Command Comparison**: Compare generated vs reference command
3. **Output Validation**: Check duration, file size, visual quality
4. **Performance Metrics**: Processing time, token usage, cost

## Notes
- This specification represents a **proven working solution**
- Can be used as CI test baseline for LLM command generation
- All parameters have been validated through actual execution
- Ready for Haiku/Gemini comparison testing