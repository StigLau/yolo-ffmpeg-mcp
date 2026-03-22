# Music Video Creation Test System

## Overview
Comprehensive testing system for the LLM-MCP music video creation pipeline. Tests Natural Language input → video generation → verification → playback.

## Test Scripts

### 1. `test_music_video_creation.sh` - Core Verification Script
**Purpose**: Verifies generated music videos meet quality standards

**Usage**:
```bash
./test_music_video_creation.sh [description] [komposition_file] [test_mode]
```

**Features**:
- ✅ File existence verification
- ✅ Duration validation (configurable range)
- ✅ Video codec verification (H.264, resolution, framerate)
- ✅ Audio codec verification (AAC, sample rate, channels)
- ✅ Automatic video playback (cross-platform)
- ✅ Colored output with timestamps

**Test Modes**:
- `natural_language` - Tests natural language → MCP server → video
- `komposition` - Tests komposition file processing
- `batch` - Tests batch operation results

### 2. `run_full_test.sh` - Complete Pipeline Test
**Purpose**: End-to-end test with MCP server integration

**Usage**:
```bash
./run_full_test.sh [test_scenario]
```

**Test Scenarios**:
- `1` or `quick` - Quick test with available files
- `2` or `transitions` - Test with smooth transitions
- `3` or `beat` - Beat-synchronized test at 120 BPM
- `4` or `example1` - Full example description
- Custom description as argument

### 3. `test_examples.conf` - Configuration File
**Purpose**: Stores test scenarios and expected values

**Contents**:
- Example natural language descriptions
- Komposition file references
- Expected duration ranges
- File path configurations

## Quick Start

### Basic Test
```bash
# Test with latest generated video
./test_music_video_creation.sh

# Test specific scenario
./run_full_test.sh quick
```

### Custom Test
```bash
# Custom natural language description
./test_music_video_creation.sh "Create a 15 second video with smooth transitions"

# Test specific komposition
./test_music_video_creation.sh "" "my_composition.json" "komposition"
```

## Verification Criteria

### File Verification
- ✅ File exists in `/tmp/music/temp/`
- ✅ File size > 1MB (reasonable for video)
- ✅ Duration within expected range (±2 seconds)

### Video Quality
- ✅ Codec: H.264
- ✅ Resolution: 1920x1080 (or source resolution)
- ✅ Frame rate: 25-30 FPS
- ✅ Progressive scan

### Audio Quality
- ✅ Codec: AAC
- ✅ Sample rate: 44.1kHz or 48kHz
- ✅ Channels: Stereo (2ch)
- ✅ Audio stream present

### Playback Test
- ✅ Opens with system default player
- ✅ Cross-platform support (macOS/Linux)
- ✅ Fallback players (VLC, mpv)

## Example Test Outputs

### Successful Test
```
🎬 Music Video Creation Test
==================================================
✅ File exists (2.7M)
✅ Duration: 11.6s
✅ Duration within expected range (10s - 20s)
✅ Video: h264 1920x1080 @ 30/1 fps
✅ Audio: aac 48000Hz 2ch
✅ Video opened with default player
==================================================
✅ Music video creation test completed successfully!
```

### Failed Test
```
❌ Video file does not exist: /tmp/music/temp/expected_file.mp4
❌ Duration outside expected range (10s - 20s)
⚠️  No audio stream found
```

## Integration with Development Workflow

### During Development
```bash
# Quick verification after changes
./test_music_video_creation.sh

# Full pipeline test
./run_full_test.sh
```

### Continuous Integration
```bash
# Automated testing in CI/CD
./run_full_test.sh quick && echo "Tests passed"
```

### Manual Verification
1. Run test script
2. Verify video opens and plays correctly
3. Check audio synchronization
4. Validate visual quality

## Dependencies

### Required
- `ffprobe` - Video analysis
- `bc` - Duration calculations
- `jq` - JSON parsing (optional, for komposition files)

### Video Players (Auto-detected)
- macOS: `open` (default)
- Linux: `xdg-open`, `vlc`, `mpv`

### Installation
```bash
# macOS
brew install ffmpeg jq

# Ubuntu/Debian
sudo apt install ffmpeg bc jq vlc

# Make scripts executable
chmod +x *.sh
```

## Customization

### Adding New Test Scenarios
Edit `test_examples.conf`:
```bash
EXAMPLE_DESCRIPTIONS+=(
    "Your new test description here"
)
```

### Adjusting Verification Criteria
Edit duration ranges in test scripts:
```bash
EXPECTED_MIN_DURATION=8
EXPECTED_MAX_DURATION=25
```

### Custom Komposition Tests
```bash
./test_music_video_creation.sh "" "path/to/your/komposition.json" "komposition"
```

## Troubleshooting

### Video Won't Play
- Check video player availability
- Try different player: `vlc /path/to/video.mp4`
- Verify file permissions

### Test Fails
- Check MCP server is running
- Verify source media files exist
- Check temp directory permissions
- Ensure ffprobe is installed

### Duration Mismatches
- Adjust expected ranges in config
- Check komposition file timing
- Verify source video lengths

## Test Results Interpretation

### Green ✅ - Success
All checks passed, video meets quality standards

### Yellow ⚠️ - Warning
Non-critical issues detected, video likely playable

### Red ❌ - Error
Critical failure, video may not be playable

## Future Enhancements

- [ ] Frame-by-frame quality analysis
- [ ] Audio synchronization testing
- [ ] Transition effect verification
- [ ] Performance benchmarking
- [ ] Automated CI/CD integration
- [ ] Visual regression testing