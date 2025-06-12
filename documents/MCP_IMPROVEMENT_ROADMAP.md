# FFMPEG MCP Server - Improvement Roadmap

## Executive Summary

Based on the complex Dagny-Baybay workflow (scene detection → reversal → timeline construction) and komposition database analysis, this document outlines critical improvements needed to elevate the MCP from proof-of-concept to production-ready video editing platform.

## Critical Missing Features

### 1. Proper Reverse Operation
**Current State**: Workaround using `convert` operation with custom filters
```python
# Current workaround
process_file(file_id, "convert", "mp4", "-vf reverse -af areverse")
```

**Needed**: Dedicated reverse operation
```python
# Add to ffmpeg_wrapper.py ALLOWED_OPERATIONS
"reverse": {
    "args": ["-vf", "reverse", "-af", "areverse"],
    "description": "Reverse video and audio playback"
}
```

**Impact**: Makes video reversal a first-class citizen, eliminates workarounds

### 2. Batch Scene Processing
**Current**: Manual scene extraction and processing
```python
# Current workflow (6 steps)
scenes = analyze_video_content(file_id)
clip1 = trim(file_id, start=0, duration=10)
clip1_rev = convert(clip1, "-vf reverse")
clip2 = trim(file_id, start=10, duration=10) 
clip2_rev = convert(clip2, "-vf reverse")
final = concatenate_all([clip1, clip1_rev, clip2, clip2_rev])
```

**Needed**: Automated scene processing
```python
@server.call_tool()
async def process_all_scenes(file_id: str, operation: str) -> dict:
    """Apply operation to all detected scenes automatically"""
    scenes = await analyze_video_content(file_id)
    results = []
    for scene in scenes["scenes"]:
        clip = await extract_scene(file_id, scene)
        processed = await apply_operation(clip, operation)
        results.append(processed)
    return {"processed_scenes": results}

# New workflow (1 step)
result = process_all_scenes(file_id, "reverse_and_concatenate")
```

**Impact**: Reduces 6-step manual workflow to 1-step automated process

### 3. Timeline Builder
**Current**: Sequential concatenation only
```python
# Current: Can only chain A → B → C
concat1 = concatenate_simple(clipA, clipB)
final = concatenate_simple(concat1, clipC)
```

**Needed**: Declarative timeline construction
```python
@server.call_tool()
async def build_timeline(segments: List[dict]) -> dict:
    """Build complex timeline from segment specifications"""
    # segments = [
    #     {"clip_id": "scene1", "start_time": 0, "duration": 10},
    #     {"clip_id": "scene1_rev", "start_time": 10, "duration": 10},
    #     {"clip_id": "scene2", "start_time": 20, "duration": 10}
    # ]
    return await construct_timeline(segments)
```

**Impact**: Enables komposition-style declarative editing

## Workflow Enhancements

### 4. Preset Workflows
```python
WORKFLOW_PRESETS = {
    "scene_mirror": {
        "description": "Each scene followed by its reverse (Dagny-Baybay style)",
        "operations": [
            {"step": "analyze_scenes", "params": {}},
            {"step": "extract_all_scenes", "params": {}},
            {"step": "reverse_each_scene", "params": {}},
            {"step": "build_mirror_timeline", "params": {}},
            {"step": "add_audio", "params": {"audio_file": "user_specified"}}
        ]
    },
    "music_video_auto": {
        "description": "AI-driven music video creation",
        "operations": [
            {"step": "smart_trim_to_beats", "params": {"bpm": "auto_detect"}},
            {"step": "scene_selection", "params": {"criteria": "high_energy"}},
            {"step": "add_transitions", "params": {"type": "beat_sync"}},
            {"step": "audio_replacement", "params": {"normalize": true}}
        ]
    },
    "content_loop": {
        "description": "Create seamless loops with reversal",
        "operations": [
            {"step": "trim_to_duration", "params": {"duration": "user_specified"}},
            {"step": "create_reverse", "params": {}},
            {"step": "seamless_loop", "params": {"fade_duration": 0.5}}
        ]
    }
}

@server.call_tool()
async def execute_preset(preset_name: str, file_id: str, **params) -> dict:
    """Execute predefined workflow preset"""
    preset = WORKFLOW_PRESETS[preset_name]
    results = []
    
    for operation in preset["operations"]:
        result = await execute_operation(operation, file_id, params)
        results.append(result)
        file_id = result.get("output_file_id", file_id)
    
    return {"final_output": file_id, "steps_completed": len(results)}
```

### 5. Advanced Scene Operations
```python
@server.call_tool()
async def smart_scene_workflow(
    file_id: str, 
    pattern: str = "mirror",  # "mirror", "loop", "shuffle", "crescendo"
    audio_sync: bool = True
) -> dict:
    """Intelligent scene-based video construction"""
    
    scenes = await analyze_video_content(file_id)
    
    if pattern == "mirror":
        # Dagny-Baybay style: scene1 → scene1_rev → scene2 → scene2_rev
        timeline = []
        for i, scene in enumerate(scenes["scenes"]):
            timeline.append({"type": "scene", "index": i, "reversed": False})
            timeline.append({"type": "scene", "index": i, "reversed": True})
    
    elif pattern == "loop":
        # Seamless A → B → B_rev → A_rev loop
        timeline = build_loop_timeline(scenes)
    
    elif pattern == "crescendo":
        # Increasing intensity based on content analysis
        timeline = build_crescendo_timeline(scenes)
    
    return await execute_timeline(timeline, file_id, audio_sync)
```

## Production Readiness

### 6. File Lifecycle Management
**Current Issue**: File IDs regenerate between MCP restarts, breaking user references

**Solution**: Persistent file tracking
```python
# Add to file_manager.py
class PersistentFileManager:
    def __init__(self):
        self.db_path = "/tmp/music/metadata/file_registry.json"
        self.load_registry()
    
    def register_file(self, file_path: str) -> str:
        """Generate persistent file ID based on content hash"""
        content_hash = self.compute_file_hash(file_path)
        file_id = f"file_{content_hash[:8]}"
        
        self.registry[file_id] = {
            "path": file_path,
            "created": time.time(),
            "last_accessed": time.time(),
            "content_hash": content_hash
        }
        self.save_registry()
        return file_id
    
    def resolve_file_id(self, file_id: str) -> str:
        """Get actual file path from persistent ID"""
        if file_id in self.registry:
            self.registry[file_id]["last_accessed"] = time.time()
            return self.registry[file_id]["path"]
        raise FileNotFoundError(f"File ID {file_id} not found")
```

### 7. Progress Tracking for Long Operations
```python
@server.call_tool()
async def get_operation_progress(job_id: str) -> dict:
    """Get real-time progress for long-running operations"""
    progress = await get_job_progress(job_id)
    return {
        "job_id": job_id,
        "progress_percent": progress.percent,
        "status": progress.status,  # "running", "completed", "failed"
        "current_step": progress.current_step,
        "total_steps": progress.total_steps,
        "eta_seconds": progress.eta,
        "output_preview": progress.preview_url  # For visual feedback
    }

@server.call_tool()
async def start_async_operation(operation: str, **params) -> dict:
    """Start long operation in background, return job ID"""
    job_id = generate_job_id()
    asyncio.create_task(execute_operation_async(job_id, operation, params))
    return {"job_id": job_id, "status": "started"}
```

### 8. Error Recovery and Cleanup
```python
@server.call_tool()
async def cleanup_failed_operations() -> dict:
    """Clean up orphaned temp files from failed operations"""
    cleaned_files = []
    temp_dir = Path("/tmp/music/temp")
    
    for file_path in temp_dir.glob("temp_*"):
        if is_orphaned_file(file_path):
            file_path.unlink()
            cleaned_files.append(str(file_path))
    
    return {
        "cleaned_count": len(cleaned_files),
        "freed_space_mb": calculate_freed_space(cleaned_files)
    }

async def is_orphaned_file(file_path: Path) -> bool:
    """Check if temp file is from failed operation"""
    # Check if file is older than 1 hour and not referenced
    age_hours = (time.time() - file_path.stat().st_mtime) / 3600
    return age_hours > 1 and not is_file_referenced(file_path)
```

## Integration with Komposition Database

### 9. Komposition Schema Bridge
```python
@server.call_tool()
async def export_to_komposition(file_id: str) -> dict:
    """Export MCP analysis to komposition database format"""
    analysis = await get_video_insights(file_id)
    file_info = await get_file_info(file_id)
    
    komposition = {
        "type": "Video",
        "bpm": -1,  # Not music-based
        "segments": [],
        "sources": [{
            "id": f"{file_info['name']}:main",
            "url": f"file://{file_info['path']}",
            "startingOffset": 0,
            "checksums": compute_checksum(file_info['path']),
            "extension": file_info['extension'],
            "mediatype": "Video"
        }]
    }
    
    # Convert MCP scenes to komposition segments
    for scene in analysis["scenes"]:
        segment = {
            "id": scene.get("description", f"Scene {scene['scene_id']}"),
            "sourceid": "",
            "start": int(scene["start"] * 1000000),  # Convert to microseconds
            "duration": int(scene["duration"] * 1000000),
            "end": int(scene["end"] * 1000000)
        }
        komposition["segments"].append(segment)
    
    return {"komposition_schema": komposition}

@server.call_tool()
async def import_from_komposition(komposition_data: dict) -> dict:
    """Import komposition timeline for MCP processing"""
    # Convert komposition segments to MCP timeline format
    timeline_segments = []
    for segment in komposition_data["segments"]:
        timeline_segments.append({
            "clip_name": segment["id"],
            "start_time": segment["start"] / 1000000,  # Convert from microseconds
            "duration": segment["duration"] / 1000000,
            "source_id": segment.get("sourceid", "main")
        })
    
    return {"mcp_timeline": timeline_segments}
```

### 10. Beat-Aware Processing
```python
@server.call_tool()
async def analyze_audio_rhythm(file_id: str) -> dict:
    """Detect BPM and beat positions for musical alignment"""
    file_path = resolve_file_path(file_id)
    
    # Use librosa or similar for beat detection
    rhythm_data = await detect_beats_and_bpm(file_path)
    
    return {
        "bpm": rhythm_data.bpm,
        "beat_positions": rhythm_data.beat_times,
        "tempo_changes": rhythm_data.tempo_map,
        "confidence": rhythm_data.confidence
    }

@server.call_tool()
async def align_cuts_to_beats(
    file_id: str, 
    target_bpm: float = None,
    snap_threshold: float = 0.1
) -> dict:
    """Suggest cuts aligned to musical beats"""
    rhythm = await analyze_audio_rhythm(file_id)
    scenes = await get_video_insights(file_id)
    
    aligned_cuts = []
    for scene in scenes["scenes"]:
        # Find nearest beat to scene boundaries
        nearest_start_beat = find_nearest_beat(scene["start"], rhythm["beat_positions"])
        nearest_end_beat = find_nearest_beat(scene["end"], rhythm["beat_positions"])
        
        if abs(scene["start"] - nearest_start_beat) < snap_threshold:
            aligned_cuts.append({
                "original_start": scene["start"],
                "beat_aligned_start": nearest_start_beat,
                "confidence": "high"
            })
    
    return {"aligned_cuts": aligned_cuts, "bpm": rhythm["bpm"]}
```

## Documentation Improvements

### 11. Comprehensive Workflow Documentation

**Create**: `/docs/WORKFLOW_EXAMPLES.md`
```markdown
# FFMPEG MCP - Complete Workflow Examples

## Scene-Based Editing Patterns

### 1. Mirror Effect (Dagny-Baybay Style)
Creates mesmerizing back-and-forth effect where each scene plays forward then backward.

**Use Case**: Social media content, artistic videos, hypnotic effects
**Complexity**: Intermediate
**Duration**: Doubles original video length

#### Step-by-Step:
1. `analyze_video_content(file_id)` - Detect natural scene boundaries
2. `process_all_scenes(file_id, "extract")` - Extract each scene as separate clip
3. `process_all_scenes(file_id, "reverse")` - Create reversed version of each scene
4. `build_timeline([scene1, scene1_rev, scene2, scene2_rev, ...])` - Construct final sequence
5. `replace_audio(final_video, backing_track)` - Add professional audio

#### Automated Version:
```python
result = execute_preset("scene_mirror", file_id, audio_file="backing_track.flac")
```

### 2. Music Video Creation
Automatically creates music video from source footage with beat-synchronized cuts.

**Use Case**: Music videos, promotional content, social media
**Complexity**: Advanced
**Duration**: Matches audio track length

#### Manual Process:
1. `analyze_audio_rhythm(audio_file)` - Detect BPM and beat positions
2. `smart_trim_suggestions(video_file, desired_duration=audio_length)` - AI suggests best moments
3. `align_cuts_to_beats(video_file, bpm=detected_bpm)` - Sync cuts to musical beats
4. `build_timeline(beat_aligned_segments)` - Construct music-synchronized sequence
5. `replace_audio(final_video, music_track)` - Replace with music track

#### Automated Version:
```python
result = execute_preset("music_video_auto", video_file, audio_file="song.mp3")
```

### 3. Content Loop Creation
Creates seamless infinite loops perfect for social media or backgrounds.

**Technical Details**:
- Analyzes content for natural loop points
- Applies crossfade transitions for seamless playback
- Optimizes for file size and streaming

#### Process:
1. `smart_trim_suggestions(file_id, desired_duration=10)` - Find best loop segment
2. `create_reverse(trimmed_clip)` - Create backward version
3. `seamless_loop([forward, backward], fade_duration=0.5)` - Blend for seamless transition
```

### 12. API Reference Documentation

**Create**: `/docs/API_REFERENCE.md`
```markdown
# FFMPEG MCP - Complete API Reference

## Core Operations

### process_file(input_file_id, operation, output_extension, params)
Execute single FFMPEG operation on file.

**Parameters**:
- `input_file_id` (string, required): File ID from list_files()
- `operation` (string, required): Operation name from get_available_operations()
- `output_extension` (string, required): Output file extension (mp4, mp3, etc.)
- `params` (string, optional): Operation-specific parameters

**Returns**:
```json
{
  "success": true,
  "output_file_id": "file_abc123",
  "message": "Successfully processed video.mp4"
}
```

**Example - Video Reversal**:
```python
result = process_file(
    input_file_id="file_123",
    operation="reverse",
    output_extension="mp4",
    params=""
)
```

**Example - Audio Replacement**:
```python
result = process_file(
    input_file_id="file_123",
    operation="replace_audio", 
    output_extension="mp4",
    params="audio_file=file_456"
)
```

### Available Operations Reference

#### trim
**Purpose**: Extract portion of video/audio
**Required Parameters**: `start` (seconds), `duration` (seconds)
**Example**: `params="start=10 duration=5"`

#### reverse  
**Purpose**: Reverse video and audio playback
**Parameters**: None
**Technical**: Uses FFMPEG reverse and areverse filters

#### concatenate_simple
**Purpose**: Join two videos with automatic resolution/audio handling
**Required Parameters**: `second_video` (file_id)
**Smart Features**:
- Automatic resolution matching
- Audio stream compatibility
- Orientation normalization (prevents 90° rotation issues)

#### replace_audio
**Purpose**: Replace video audio with different audio track
**Required Parameters**: `audio_file` (file_id)
**Behavior**: Video length determines final duration (audio trimmed if longer)

[... continue for all operations ...]
```

## Performance Optimizations

### 13. Advanced Caching System
```python
class AdvancedCache:
    def __init__(self):
        self.operation_cache = {}  # Cache operation results
        self.scene_cache = {}      # Cache scene detection results
        self.audio_cache = {}      # Cache audio analysis results
    
    async def get_or_execute(self, operation_key: str, operation_func, *args):
        """Get cached result or execute operation and cache result"""
        if operation_key in self.operation_cache:
            return self.operation_cache[operation_key]
        
        result = await operation_func(*args)
        self.operation_cache[operation_key] = result
        return result
    
    def generate_operation_key(self, file_id: str, operation: str, params: dict) -> str:
        """Generate unique key for operation caching"""
        param_hash = hashlib.md5(str(sorted(params.items())).encode()).hexdigest()
        return f"{file_id}:{operation}:{param_hash}"
```

### 14. Background Processing Queue
```python
class OperationQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.active_jobs = {}
        self.completed_jobs = {}
    
    async def add_job(self, operation: str, **params) -> str:
        """Add operation to background queue"""
        job_id = f"job_{int(time.time() * 1000)}"
        job = {
            "id": job_id,
            "operation": operation,
            "params": params,
            "status": "queued",
            "created_at": time.time()
        }
        
        await self.queue.put(job)
        self.active_jobs[job_id] = job
        return job_id
    
    async def process_queue(self):
        """Background worker to process operation queue"""
        while True:
            job = await self.queue.get()
            try:
                job["status"] = "running"
                result = await self.execute_operation(job)
                job["status"] = "completed"
                job["result"] = result
                self.completed_jobs[job["id"]] = job
            except Exception as e:
                job["status"] = "failed"
                job["error"] = str(e)
            finally:
                del self.active_jobs[job["id"]]
```

## Priority Implementation Roadmap

### Phase 1: Core Functionality (Week 1-2)
**Goal**: Fix immediate workflow friction
- [ ] Add proper `reverse` operation to ffmpeg_wrapper.py
- [ ] Implement `process_all_scenes()` for batch processing
- [ ] Create basic `build_timeline()` function
- [ ] Add `scene_mirror` preset workflow

**Success Metric**: Dagny-Baybay style video creation in 1 command instead of 6

### Phase 2: Production Polish (Week 3-6)  
**Goal**: Production-ready reliability
- [ ] Persistent file ID system
- [ ] Progress tracking for long operations
- [ ] Error recovery and cleanup
- [ ] Comprehensive documentation
- [ ] `music_video_auto` preset

**Success Metric**: No more broken file references, full operation visibility

### Phase 3: Advanced Features (Month 2-3)
**Goal**: Professional-grade capabilities
- [ ] Beat-aware audio processing
- [ ] Komposition database integration
- [ ] Background processing queue
- [ ] Advanced caching system
- [ ] Visual operation preview

**Success Metric**: Beat-synchronized music video creation, komposition import/export

### Phase 4: Ecosystem Integration (Month 4+)
**Goal**: Complete video production pipeline
- [ ] Plugin system for custom operations
- [ ] Web interface for visual editing
- [ ] Cloud storage integration
- [ ] Collaboration features
- [ ] Template marketplace

**Success Metric**: Complete alternative to traditional video editing software

## Impact Assessment

### High Impact, Low Effort
1. **Proper reverse operation** - Fixes immediate workflow friction
2. **Preset workflows** - Makes complex operations accessible
3. **Better documentation** - Reduces learning curve

### High Impact, Medium Effort  
1. **Batch scene processing** - Eliminates repetitive manual steps
2. **Timeline builder** - Enables complex video construction
3. **Progress tracking** - Professional user experience

### High Impact, High Effort
1. **Komposition integration** - Bridges to existing ecosystem
2. **Beat-aware processing** - Enables music video workflows
3. **Background processing** - Handles large file operations

## Technical Debt Priorities

### Critical (Fix First)
- File ID persistence across sessions
- Proper error handling and cleanup
- Memory management for large files

### Important (Fix Soon)
- Operation result caching
- Temp file lifecycle management
- Input validation and sanitization

### Nice to Have (Fix Later)
- Performance optimization
- Code organization improvements
- Extended format support

## Conclusion

The FFMPEG MCP Server has proven its core capabilities through complex workflows like the Dagny-Baybay scene reversal project. These improvements would transform it from a powerful proof-of-concept into a production-ready video editing platform that bridges AI-powered automation with professional video production needs.

**Next Steps**: Implement Phase 1 improvements to address immediate workflow friction, then proceed through the roadmap based on user feedback and production requirements.