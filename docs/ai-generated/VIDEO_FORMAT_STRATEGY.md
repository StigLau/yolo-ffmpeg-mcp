# Video Format Output Strategy

## User-Viewable Final Output Requirements

**RULE**: When creating final output for user verification/consumption, ALWAYS use YUV420P format for maximum compatibility.

## Implementation Strategy

- **Internal Processing**: YUV444P format acceptable (higher quality, not user-facing)
- **Draft/Internal Videos**: YUV444P format acceptable for development/testing
- **Export/Final User Output**: MUST be YUV420P format - use `youtube_recommended_encode` operation
- **Verification Step**: Test final videos open in VLC/QuickTime before claiming success

## Encoding Command for Final Output

```bash
# Apply YouTube recommended encoding for user-viewable output
mcp.call_tool('process_file', {
    'input_file_id': draft_video_id,
    'operation': 'youtube_recommended_encode',
    'output_extension': 'mp4'
})
```

## Quality vs Compatibility

- **YUV444P**: Higher quality, limited player support (development use)
- **YUV420P**: Universal compatibility, slight quality loss (user delivery)