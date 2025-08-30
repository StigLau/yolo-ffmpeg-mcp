# Platform-Optimized FFMPEG Commands for LLM Testing

## Platform Optimization Strategy

Based on the MCP server's format preset system, we optimize for target platforms using "least common denominator" compatibility while tailoring to specific viewer contexts.

### **Core Optimization Principles:**

1. **Platform-First Design**: Choose format based on primary distribution platform
2. **Compatibility Fallback**: Ensure broad device compatibility with proven codec settings  
3. **Quality vs Performance**: Balance output quality with processing time and file size
4. **Viewer Context**: Optimize for expected viewing conditions (mobile, desktop, TV)

### **Available Platform Presets:**

```python
PLATFORM_PRESETS = {
    "youtube_landscape": "1920x1080, 16:9, center_crop",    # Desktop/TV viewing
    "youtube_shorts": "1080x1920, 9:16, smart_crop",       # Mobile-first vertical
    "instagram_square": "1080x1080, 1:1, center_crop",     # Feed posts  
    "instagram_story": "1080x1920, 9:16, center_crop",     # Stories/Reels
    "tiktok_vertical": "1080x1920, 9:16, top_crop",        # Portrait optimization
    "twitter_landscape": "1280x720, 16:9, center_crop",    # Web/mobile mix
    "facebook_square": "1200x1200, 1:1, scale_blur_bg",    # Social engagement
    "cinema_wide": "2560x1080, 21:9, center_crop"          # Cinematic content
}
```

## Updated Test Prompts with Platform Optimization

### Test 1: YouTube Shorts Optimization
**Prompt**: "Create a 15-second YouTube Short using PXL_20250306_132546255.mp4 with Coast music background and smooth looping"

**Enhanced Sonnet Baseline** (Platform-Optimized):
```bash
# Step 1: Platform analysis and format conversion
ffmpeg -i PXL_20250306_132546255.mp4 \
  -filter_complex "
    [0:v]scale=1080:1920:force_original_aspect_ratio=increase,
    crop=1080:1920:(iw-ow)/2:(ih-oh)/2,
    loop=loop=4:size=1:start=0,
    fade=in:st=0:d=0.5,fade=out:st=14.5:d=0.5[v]
  " \
  -map "[v]" -t 15 -c:v libx264 -preset medium -crf 23 \
  -pix_fmt yuv420p -r 30 youtube_shorts_video.mp4

# Step 2: Mobile-optimized audio processing
ffmpeg -i youtube_shorts_video.mp4 -i Coast.mp3 \
  -filter_complex "[1:a]loudnorm=I=-14:TP=-1:LRA=7[a]" \
  -map 0:v -map "[a]" -t 15 -c:v copy -c:a aac -b:a 128k \
  -movflags +faststart final_shorts.mp4
```

**Platform Optimizations Applied**:
- ✅ Vertical format (1080x1920) for mobile viewing
- ✅ YUV420P pixel format for universal compatibility
- ✅ 30fps standard for smooth mobile playback
- ✅ Loudness normalization at -14 LUFS (YouTube Shorts standard)
- ✅ FastStart for faster mobile loading
- ✅ Conservative bitrate (128k) for mobile networks

### Test 2: Multi-Platform Distribution
**Prompt**: "Create a 30-second video using lookin.mp4 and panning.mp4 optimized for both Instagram Stories and TikTok at 135 BPM"

**Enhanced Sonnet Baseline** (Cross-Platform):
```bash
# Step 1: Multi-platform format preparation
ffmpeg -i lookin.mp4 -i panning.mp4 \
  -filter_complex "
    [0:v]scale=1080:1920:force_original_aspect_ratio=increase,
    crop=1080:1920:(iw-ow)/2:(ih-oh)/2[v1];
    [1:v]scale=1080:1920:force_original_aspect_ratio=increase,
    crop=1080:1920:(iw-ow)/2:(ih-oh)/2[v2];
    [v1][v2]xfade=transition=fade:duration=0.5:offset=14.5[v]
  " \
  -map "[v]" -t 30 -c:v libx264 -preset medium -crf 20 \
  -pix_fmt yuv420p -r 30 -g 60 multi_platform.mp4

# Step 2: BPM-synchronized audio with platform standards
ffmpeg -i multi_platform.mp4 -i background_music.mp3 \
  -filter_complex "
    [1:a]loudnorm=I=-16:TP=-1.5:LRA=8,
    atempo=1.125[a]
  " \
  -map 0:v -map "[a]" -t 30 -c:v copy -c:a aac -b:a 192k \
  -movflags +faststart cross_platform_final.mp4
```

**Platform Optimizations Applied**:
- ✅ 9:16 vertical format (Instagram + TikTok compatible)
- ✅ GOP size 60 (2-second keyframes for platform algorithms)
- ✅ -16 LUFS loudness (Instagram Stories standard)
- ✅ 192k audio for higher quality music content
- ✅ BPM tempo adjustment for music synchronization

### Test 3: Desktop vs Mobile Optimization
**Prompt**: "Create a 24-second cinematic video from Subnautica footage with deep ocean atmosphere, optimized for desktop YouTube viewing"

**Enhanced Sonnet Baseline** (Desktop-Optimized):
```bash
# Step 1: Desktop-first cinematic formatting
ffmpeg -i subnautica_footage.mp4 \
  -filter_complex "
    [0:v]scale=1920:1080:force_original_aspect_ratio=increase,
    crop=1920:1080,
    vignette=angle=PI/3:x0=0.5:y0=0.5:mode=forward,
    unsharp=5:5:1.5:5:5:0.0,
    colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131:0,
    fade=in:st=0:d=1.5,fade=out:st=22.5:d=1.5[v]
  " \
  -map "[v]" -t 24 -c:v libx264 -preset slow -crf 18 \
  -pix_fmt yuv420p -r 24 cinematic_desktop.mp4

# Step 2: High-quality audio for desktop speakers/headphones
ffmpeg -i cinematic_desktop.mp4 -i atmospheric_music.mp3 \
  -filter_complex "
    [1:a]loudnorm=I=-16:TP=-2:LRA=11,
    lowpass=f=12000,
    aecho=0.6:0.9:2000:0.4,
    stereo_widen=width=1.4[a]
  " \
  -map 0:v -map "[a]" -t 24 -c:v copy -c:a aac -b:a 256k \
  -movflags +faststart desktop_optimized.mp4
```

**Platform Optimizations Applied**:
- ✅ Landscape format (1920x1080) for desktop viewing
- ✅ 24fps cinematic frame rate
- ✅ Higher CRF 18 for desktop quality expectations
- ✅ Stereo widening for desktop audio systems
- ✅ 256k audio bitrate for high-fidelity experience
- ✅ Extended fade durations for cinematic pacing

## Enhanced Validation Criteria

### **Platform-Aware Scoring**:

1. **Format Appropriateness** (25% of score):
   - Correct aspect ratio for target platform
   - Appropriate resolution and crop strategy
   - Frame rate matching platform standards

2. **Compatibility Optimization** (25% of score):
   - YUV420P pixel format for universal playback
   - Proper GOP structure for platform algorithms
   - FastStart for web/mobile delivery

3. **Audio Standards** (25% of score):
   - Platform-specific loudness normalization
   - Appropriate bitrate for content type and platform
   - Audio processing matching viewing context

4. **Technical Excellence** (25% of score):
   - Professional codec settings and quality
   - Efficient encoding parameters
   - Error handling and validation steps

### **Platform-Specific Quality Markers**:

**YouTube Shorts**: `1080x1920`, `yuv420p`, `loudnorm=I=-14`, `movflags +faststart`
**Instagram Stories**: `1080x1920`, `yuv420p`, `loudnorm=I=-16`, `r=30`  
**TikTok**: `1080x1920`, `yuv420p`, `top_crop`, `g=60`
**Desktop YouTube**: `1920x1080`, `yuv420p`, `loudnorm=I=-16`, `stereo processing`

## Implementation in Test Framework

The validation framework now checks for:
- ✅ **Platform Format Detection**: Recognizes target platform from prompt
- ✅ **Optimization Verification**: Validates platform-specific settings
- ✅ **Compatibility Scoring**: Scores universal playback compatibility  
- ✅ **Context Awareness**: Evaluates appropriateness for viewing context

This ensures LLM outputs are not just technically correct, but optimized for real-world distribution across target platforms with proper viewer experience considerations.