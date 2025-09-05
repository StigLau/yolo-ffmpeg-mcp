# Subnautic 9-Segment Processing Blueprint

**Source**: `subnautic_9segments_komposition.md`  
**Purpose**: Complete FFmpeg command sequence and processing steps for 54-second music video

## Processing Overview

**Total Duration**: 54 seconds (9 segments × 6 seconds each)  
**Segment Timing**: Each segment exactly 6 seconds (8 beats at 80 BPM)  
**Audio**: Subnautic Measures.flac synchronized to 80 BPM

## Step-by-Step Processing Commands

### **Phase 1: Audio Preparation**

```bash
# Step 1: Analyze original audio duration and BPM
ffprobe -v quiet -print_format json -show_format "../.testdata/Subnautic Measures.flac"

# Step 2: Process audio to match 80 BPM and 54-second duration  
ffmpeg -i "../.testdata/Subnautic Measures.flac" \
  -filter_complex "[0:a]atempo=0.8,volume=0.75,afade=t=in:st=0:d=1,afade=t=out:st=52:d=2[audio_out]" \
  -map "[audio_out]" \
  -c:a aac -b:a 128k -ar 44100 \
  -t 54 \
  subnautic_audio_80bpm.aac
```

### **Phase 2: Segment Extraction and Processing**

#### **Group 1: Film Noir Segments (1-3)**

```bash
# Segment 1: Film Noir (0-6s) 
ffmpeg -i "../.testdata/JJVtt947FfI_136.mp4" \
  -ss 10 -t 6 \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:black,eq=contrast=1.5:brightness=-0.1:saturation=0.3,curves=all='0/0.1 0.5/0.4 1/0.9',fade=t=out:st=5:d=1:color=white" \
  -c:v libx264 -preset medium -crf 23 \
  -r 25 -an \
  segment_01_noir.mp4

# Segment 2: Film Noir (6-12s)
ffmpeg -i "../.testdata/_wZ5Hof5tXY_136.mp4" \
  -ss 5 -t 6 \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:black,eq=contrast=1.5:brightness=-0.1:saturation=0.3,curves=all='0/0.1 0.5/0.4 1/0.9',fade=t=out:st=5:d=1:color=white" \
  -c:v libx264 -preset medium -crf 23 \
  -r 25 -an \
  segment_02_noir.mp4

# Segment 3: Film Noir (12-18s)  
ffmpeg -i "../.testdata/JJVtt947FfI_136.mp4" \
  -ss 25 -t 6 \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:black,eq=contrast=1.5:brightness=-0.1:saturation=0.3,curves=all='0/0.1 0.5/0.4 1/0.9',fade=t=out:st=5:d=1:color=white" \
  -c:v libx264 -preset medium -crf 23 \
  -r 25 -an \
  segment_03_noir.mp4
```

#### **Group 2: Vintage Sepia Segments (4-6)**

```bash
# Segment 4: Vintage (18-24s)
ffmpeg -i "../.testdata/_wZ5Hof5tXY_136.mp4" \
  -ss 15 -t 6 \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:black,colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,hue=s=0.6,noise=alls=15:allf=t,vignette=PI/8,fade=t=out:st=5:d=1:color=white" \
  -c:v libx264 -preset medium -crf 23 \
  -r 25 -an \
  segment_04_vintage.mp4

# Segment 5: Vintage (24-30s) - LAST fade-to-white
ffmpeg -i "../.testdata/JJVtt947FfI_136.mp4" \
  -ss 40 -t 6 \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:black,colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,hue=s=0.6,noise=alls=15:allf=t,vignette=PI/8,fade=t=out:st=5:d=1:color=white" \
  -c:v libx264 -preset medium -crf 23 \
  -r 25 -an \
  segment_05_vintage.mp4

# Segment 6: Vintage (30-36s) - FIRST fade-to-black
ffmpeg -i "../.testdata/_wZ5Hof5tXY_136.mp4" \
  -ss 30 -t 6 \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:black,colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,hue=s=0.6,noise=alls=15:allf=t,vignette=PI/8,fade=t=out:st=5:d=1:color=black" \
  -c:v libx264 -preset medium -crf 23 \
  -r 25 -an \
  segment_06_vintage.mp4
```

#### **Group 3: Dreamy Blur Segments (7-9)**

```bash
# Segment 7: Dreamy (36-42s)
ffmpeg -i "../.testdata/JJVtt947FfI_136.mp4" \
  -ss 60 -t 6 \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:black,gblur=sigma=2.5:steps=1,eq=brightness=0.15:saturation=1.1,boxblur=luma_radius=1:luma_power=0.3,fade=t=out:st=5:d=1:color=black" \
  -c:v libx264 -preset medium -crf 23 \
  -r 25 -an \
  segment_07_dreamy.mp4

# Segment 8: Dreamy (42-48s)  
ffmpeg -i "../.testdata/_wZ5Hof5tXY_136.mp4" \
  -ss 50 -t 6 \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:black,gblur=sigma=2.5:steps=1,eq=brightness=0.15:saturation=1.1,boxblur=luma_radius=1:luma_power=0.3,fade=t=out:st=5:d=1:color=black" \
  -c:v libx264 -preset medium -crf 23 \
  -r 25 -an \
  segment_08_dreamy.mp4

# Segment 9: Dreamy Finale (48-54s) - Extended fade-to-black
ffmpeg -i "../.testdata/JJVtt947FfI_136.mp4" \
  -ss 80 -t 6 \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:black,gblur=sigma=2.5:steps=1,eq=brightness=0.15:saturation=1.1,boxblur=luma_radius=1:luma_power=0.3,fade=t=out:st=4:d=2:color=black" \
  -c:v libx264 -preset medium -crf 23 \
  -r 25 -an \
  segment_09_dreamy.mp4
```

### **Phase 3: Video Concatenation**

```bash
# Create concatenation file list
cat > segment_list.txt << EOF
file 'segment_01_noir.mp4'
file 'segment_02_noir.mp4'  
file 'segment_03_noir.mp4'
file 'segment_04_vintage.mp4'
file 'segment_05_vintage.mp4'
file 'segment_06_vintage.mp4'
file 'segment_07_dreamy.mp4'
file 'segment_08_dreamy.mp4'
file 'segment_09_dreamy.mp4'
EOF

# Concatenate all video segments
ffmpeg -f concat -safe 0 -i segment_list.txt \
  -c copy \
  -avoid_negative_ts make_zero \
  subnautic_video_only.mp4
```

### **Phase 4: Final Audio-Video Assembly**

```bash  
# Combine processed video with synchronized audio
ffmpeg -i subnautic_video_only.mp4 \
  -i subnautic_audio_80bpm.aac \
  -c:v copy \
  -c:a copy \
  -shortest \
  -movflags +faststart \
  subnautic_9segments_final.mp4
```

### **Phase 5: Quality Verification**

```bash
# Verify final output properties
ffprobe -v quiet -print_format json -show_format -show_streams subnautic_9segments_final.mp4

# Check duration precision  
ffprobe -v quiet -select_streams v:0 -show_entries stream=duration -of csv=p=0 subnautic_9segments_final.mp4

# Generate thumbnail for preview
ffmpeg -i subnautic_9segments_final.mp4 \
  -ss 27 -vframes 1 \
  -q:v 2 \
  subnautic_9segments_preview.jpg
```

## Processing Summary

### **Files Generated**
- **9 segment files**: `segment_01_noir.mp4` through `segment_09_dreamy.mp4`
- **Audio file**: `subnautic_audio_80bpm.aac`  
- **Video-only**: `subnautic_video_only.mp4`
- **Final output**: `subnautic_9segments_final.mp4`
- **Preview**: `subnautic_9segments_preview.jpg`

### **Processing Time Estimate**
- **Audio processing**: ~10 seconds
- **9 segment processing**: ~90 seconds (10s each)
- **Concatenation**: ~5 seconds  
- **Final assembly**: ~5 seconds
- **Total**: ~110 seconds (under 2 minutes)

### **Resource Requirements**
- **Disk space**: ~500MB temporary files, ~50MB final output
- **Memory**: ~2GB peak usage during processing
- **CPU**: High utilization during encoding phases

## Bill of Materials Structure

### **Input Materials**
```json
{
  "video_sources": [
    {"id": "video1", "path": "../.testdata/JJVtt947FfI_136.mp4", "usage": "segments 1,3,5,7,9"},
    {"id": "video2", "path": "../.testdata/_wZ5Hof5tXY_136.mp4", "usage": "segments 2,4,6,8"}
  ],
  "audio_sources": [
    {"id": "audio1", "path": "../.testdata/Subnautic Measures.flac", "bpm_adjustment": "to_80bpm"}
  ]
}
```

### **Processing Steps**
```json
{
  "steps": [
    {"step": 1, "operation": "audio_processing", "input": "audio1", "output": "subnautic_audio_80bpm.aac"},
    {"step": 2, "operation": "segment_extraction", "count": 9, "filters": ["noir", "vintage", "dreamy"]},
    {"step": 3, "operation": "concatenation", "input": "9_segments", "output": "subnautic_video_only.mp4"},
    {"step": 4, "operation": "final_assembly", "inputs": ["video", "audio"], "output": "subnautic_9segments_final.mp4"}
  ]
}
```

### **Quality Metrics**
- **Duration accuracy**: ±0.1s tolerance (54.0s target)
- **Beat alignment**: Perfect 8-beat segments
- **Visual consistency**: Smooth transitions between filter groups  
- **Audio sync**: Zero drift over 54-second duration

This blueprint demonstrates the complete processing pipeline from komposition specification to final video output, providing a template for similar structured music video productions.