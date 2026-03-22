# Frame Loss Detection and Prevention in Video Processing

**Date**: 2025-08-08  
**Context**: MCP FFMPEG Server - YouTube Shorts Music Video Creation  
**Issue**: H.264 decoder frame loss during video concatenation

## Problem Discovery

### How Frame Loss Was Detected

1. **FFmpeg Error Messages Analysis**
   ```
   [h264 @ 0x7fe044f1be00] No start code is found.
   [h264 @ 0x7fe044f1be00] Error splitting the input into NAL units.
   [vist#0:0/h264] Error submitting packet to decoder: Invalid data found
   [concat] DTS 100079 < 358148 out of order
   ```

2. **Frame Count Verification**
   - Expected: 48 frames per 2-second segment at 24fps
   - Actual results:
     - seg02_Oa8iS1W3OCM.mp4: 26 frames (46% loss)
     - seg03_Oa8iS1W3OCM.mp4: 2 frames (96% loss)
     - seg04_Oa8iS1W3OCM.mp4: 0 frames (100% loss)

3. **H.264 Profile Inconsistencies**
   - Oa8iS1W3OCM.mp4: Main profile
   - 3xEMCU1fyl8.mp4: Constrained Baseline profile
   - PLnPZVqiyjA.mp4: Constrained Baseline profile

## Root Cause Analysis

**Primary Issue**: H.264 profile mismatches cause concatenation decoder failures
- NAL unit boundary detection fails when profiles differ
- Timestamp discontinuities (DTS out of order) indicate temporal inconsistencies
- YouTube videos use different encoding parameters from Google's encoder

## Solution Framework

### Solution 4: Two-Pass Approach (Recommended for Komposteur)

**Phase 1: Normalization Pass**
```bash
ffmpeg -i input.mp4 \
  -c:v libx264 -profile:v baseline -pix_fmt yuv420p -r 24 \
  -c:a aac -ar 48000 -ac 2 \
  normalized.mp4
```

**Phase 2: Processing Pass**
```bash
ffmpeg -f concat -safe 0 -i list.txt -c copy output.mp4
```

**Benefits:**
- Eliminates profile compatibility issues
- Ensures consistent frame rates and timing
- Maintains quality while preventing decoder errors
- Clear separation between normalization and creative processing

### Post-Processing Quality Assessment

**Frame Count Verification**
```bash
expected_frames=$((duration_seconds * fps))
actual_frames=$(ffprobe -select_streams v:0 -count_packets -show_entries stream=nb_read_packets -of csv=p=0 output.mp4)

if [ "$actual_frames" -ne "$expected_frames" ]; then
    echo "⚠️  Frame loss detected: $actual_frames/$expected_frames frames"
    echo "💡 Recommendation: Re-process with normalization pass"
fi
```

**Quality Metrics Detection**
```bash
# Check for decoder errors in processing log
if grep -q "No start code\|Error splitting\|DTS.*out of order" process.log; then
    echo "🚨 Decoder issues detected - consider re-encoding inputs"
fi
```

## Komposteur Integration Strategy

### Current MCP Context (Experimental)
- **Goal**: Identify and document issues for upstream fixes
- **Approach**: Test multiple solutions, gather data
- **Outcome**: Provide recommendations to Komposteur team

### Komposteur Production Integration
- **Pre-Processing**: Implement Two-Pass approach for mixed-source projects
- **Post-Processing**: Automatic quality validation
- **User Feedback**: Clear recommendations when re-processing would improve quality
- **Iteration Strategy**: Fewer, more reliable processing cycles vs. multiple trial-and-error attempts

### Implementation Recommendations

1. **Profile Detection**: Analyze input sources before processing
2. **Smart Normalization**: Only normalize when profile mismatches detected  
3. **Quality Gates**: Post-processing validation with clear user feedback
4. **Graceful Degradation**: Inform users of quality issues with improvement suggestions

## Technical Validation

### Test Results
- **Original segments**: 46-100% frame loss on mixed profiles
- **Two-Pass Normalized segments**: FAILED - Same H.264 decoder errors persist
- **Finding**: Frame corruption occurs at temporal segment boundaries, not codec level
- **Root Cause**: Segments cut at non-keyframe positions create undecodable P/B-frames

### Error Patterns to Monitor
```bash
# Critical error patterns indicating frame loss risk
grep -E "(No start code|Error splitting|DTS.*out of order|packets to decoder.*Invalid)" ffmpeg.log
```

## Conclusion

**CRITICAL FINDING**: The frame loss issue is not codec compatibility but temporal segment extraction methodology.

**New Recommended Approach for Komposteur**:
1. **Keyframe-Aligned Segments**: Extract segments only at keyframe boundaries using `-ss` with `-avoid_negative_ts make_zero`
2. **Scene-Change Detection**: Use FFmpeg scene detection to find natural cut points
3. **I-frame Forcing**: Re-encode segments with keyframes at exact cut points if necessary

**Implementation Status**: Two-Pass approach failed. Further investigation required for keyframe-aligned extraction methodology.

**Key Takeaway**: Video segment extraction must respect H.264 frame dependencies to avoid undecodable fragments.