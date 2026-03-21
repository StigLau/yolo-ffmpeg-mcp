# Rusty YouTube Shorts Music Video Project

**Project Status:** 🚧 **IN PROGRESS - PAUSED (Download Issues)**  
**Target:** YouTube Shorts with rusty/old aesthetic and Subnautica music  
**Created:** 2025-08-07  

## Project Requirements

### **🎯 Creative Vision**
- **Format:** YouTube Shorts (9:16 portrait, 1080x1920)
- **Aesthetic:** Rusty/old looking filter applied to all video segments
- **Transitions:** 1-second fade-to-white between segments
- **Music:** Subnautica background track
- **Structure:** 10 segments × 4 beats each at 120 BPM
- **Duration:** ~20 seconds total (40 beats ÷ 120 BPM × 60 = 20s)

### **📹 Source Materials**

#### **Target YouTube Videos:**
- https://www.youtube.com/shorts/PLnPZVqiyjA
- https://www.youtube.com/shorts/3xEMCU1fyl8
- https://www.youtube.com/shorts/Oa8iS1W3OCM

#### **✅ Available Audio (.testdata/):**
- **`Subnautic Measures.flac`** (28MB) - Primary background music
- `16BL - Deep In My Soul (Original Mix).mp3` (19MB) - Alternative
- `Torn on TDF.flac` (44MB) - Alternative
- `ZeroSoul.flac` (24MB) - Alternative

#### **✅ Available Video (.testdata/):**
- **`JJVtt947FfI_136.mp4`** (17MB) - Can be used as source material
- **`_wZ5Hof5tXY_136.mp4`** (10MB) - Can be used as source material
- `Boat having a sad day.jpeg` - Can convert to video if needed

## Technical Specifications

### **Music Video Structure**
```
Master BPM: 120
Total Duration: 20 seconds (40 beats)
Segment Structure: 10 segments × 4 beats each

Beat Timeline:
Segment 1:  Beats 0-4   (0.0s - 2.0s)
Segment 2:  Beats 4-8   (2.0s - 4.0s)  
Segment 3:  Beats 8-12  (4.0s - 6.0s)
[...continuing pattern...]
Segment 10: Beats 36-40 (18.0s - 20.0s)
```

### **Video Processing Requirements**
1. **Source Analysis** - Analyze each video for optimal segment extraction points
2. **Segment Extraction** - Extract 2-second clips from different parts of each video
3. **Aspect Ratio** - Convert to 1080x1920 portrait format
4. **Visual Effects** - Apply rusty/old filter to each segment
5. **Transitions** - 1-second fade-to-white between segments
6. **Audio Sync** - Sync all segments to 120 BPM Subnautica music

## Workflow Plan

### **Phase 1: Content Acquisition** ❌ **(BLOCKED)**
- [x] ~~Download 3 YouTube Shorts videos~~ - **DOWNLOAD SYSTEM BROKEN**
- [x] Locate Subnautica music - **FOUND: `Subnautic Measures.flac`**
- [ ] Manual download of YouTube videos as workaround

### **Phase 2: Content Analysis** (Ready when videos available)
- [ ] Analyze each video with `analyze_video_content(file_id)`
- [ ] Identify optimal segment extraction points (every 2-4 seconds)
- [ ] Create "tagging" metadata for segment selection
- [ ] Document video characteristics (motion, color, content type)

### **Phase 3: Komposition Creation**
- [ ] Generate komposition JSON with 10 segments at 4 beats each
- [ ] Configure rusty/old visual effects for each segment
- [ ] Set up fade-to-white transitions (1s duration)
- [ ] Configure Subnautica music background sync

### **Phase 4: Video Processing**
- [ ] Build video using `process_komposition_file()`
- [ ] Verify YouTube Shorts format compliance
- [ ] Apply final quality optimization

### **Phase 5: Quality Assurance & Documentation**
- [ ] Test final video playback and loop behavior  
- [ ] Document issues encountered and improvements needed
- [ ] Create TODO items for future enhancements

## Current Status & Blockers

### **🚫 Primary Blocker: Download System**
- **Issue:** Java `MultiSourceDownloadBridge` class not found
- **Impact:** Cannot acquire target YouTube videos
- **Report:** See `DOWNLOAD_SYSTEM_FAILURE_REPORT.md`
- **Assigned:** Komposteur Claude for Java classpath repair

### **🎯 Immediate Workaround Options:**

#### **Option A: Use Available Content**
```bash
# Work with existing .testdata videos
Source Videos: JJVtt947FfI_136.mp4, _wZ5Hof5tXY_136.mp4  
Audio: Subnautic Measures.flac
Workflow: Proceed with available content to prototype the system
```

#### **Option B: Manual Download**
```bash
# External download, then import
yt-dlp https://www.youtube.com/shorts/PLnPZVqiyjA -o "source_video_1.mp4"
yt-dlp https://www.youtube.com/shorts/3xEMCU1fyl8 -o "source_video_2.mp4"  
yt-dlp https://www.youtube.com/shorts/Oa8iS1W3OCM -o "source_video_3.mp4"
```

## Komposition JSON Template

### **Planned Structure:**
```json
{
  "metadata": {
    "title": "Rusty Subnautica YouTube Shorts",
    "bpm": 120,
    "totalBeats": 40,
    "estimatedDuration": 20.0,
    "outputFormat": {
      "resolution": "1080x1920",
      "fps": 30,
      "format": "mp4"
    }
  },
  "segments": [
    {
      "id": "seg_1", "startBeat": 0, "endBeat": 4,
      "sourceRef": "video_1", "extractionParams": {...},
      "effects": [
        {"type": "rusty_filter", "intensity": 0.8},
        {"type": "resize", "width": 1080, "height": 1920}
      ]
    },
    // ... 9 more segments
  ],
  "transitions": [
    {"type": "fade_to_white", "duration": 1.0, "between": ["seg_1", "seg_2"]},
    // ... 9 more transitions
  ],
  "audioConfiguration": {
    "backgroundMusic": "Subnautic Measures.flac",
    "volume": 0.8,
    "fadeIn": 0.5, "fadeOut": 0.5
  }
}
```

## Future Enhancements (TODO Items)

### **🎵 Audio Extraction & Speech Clipping**
- [ ] **Tool: `extract_audio_from_video(file_id, format)`**
  - Extract audio tracks from video sources
  - Support multiple formats (WAV, MP3, FLAC)
  - Maintain audio quality and metadata

- [ ] **Tool: `clip_audio_segment(file_id, start_time, duration)`**
  - Extract specific audio segments with precise timing
  - Support millisecond precision for speech extraction
  - Automatic gain normalization

- [ ] **Caching System for Extracted Content**
  - Cache extracted audio segments by content hash
  - Reuse previously extracted speech/music clips
  - Metadata indexing for content discovery

- [ ] **Speech Detection & Extraction**
  - Integrate with existing `detect_speech_segments()` 
  - Auto-extract speech portions for reuse in compositions
  - Generate searchable speech content library

### **📊 Video Tagging & Metadata Process**
- [ ] **Automated Video Tagging System**
  - Analyze visual content (motion, color, objects)
  - Generate semantic tags for segment selection
  - Create searchable content database

- [ ] **Smart Segment Selection**
  - AI-powered optimal cut point detection
  - Beat-synchronized segment boundaries
  - Content-aware segment matching to music

### **🎨 Enhanced Visual Effects**
- [ ] **Expanded Filter Library**
  - More vintage/retro filter options
  - Customizable aging effects (scratches, dust, grain)
  - Period-specific looks (70s, 80s, 90s aesthetics)

- [ ] **Advanced Transition System**
  - More transition types (dissolve, wipe, zoom)
  - Beat-synchronized transition timing
  - Content-aware transition selection

## Resumption Instructions

### **When Download System is Fixed:**
1. **Test download functionality:**
   ```python
   result = await get_download_info("https://www.youtube.com/shorts/PLnPZVqiyjA")
   ```

2. **Download target videos:**
   ```python
   videos = await batch_download_urls([
       "https://www.youtube.com/shorts/PLnPZVqiyjA",
       "https://www.youtube.com/shorts/3xEMCU1fyl8", 
       "https://www.youtube.com/shorts/Oa8iS1W3OCM"
   ])
   ```

3. **Resume workflow from Phase 2: Content Analysis**

### **Alternative: Immediate Prototype**
1. **Use available .testdata videos:**
   ```python
   # Import existing videos and create prototype
   available_videos = ["JJVtt947FfI_136.mp4", "_wZ5Hof5tXY_136.mp4"]
   audio_track = "Subnautic Measures.flac"
   ```

2. **Create prototype komposition and test workflow**
3. **Document lessons learned for when target videos are available**

---

**Next Action:** Choose approach (fix downloads or prototype with available content) and proceed with music video creation workflow.