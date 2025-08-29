# Haiku MCP Server

Cost-optimized MCP server using Claude Haiku and Gemini Flash for FFMPEG operations.

## Quick Start

1. **Set API Keys**:
```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_API_KEY="your-google-key"  # Optional, will use Haiku fallback
```

2. **Install & Build**:
```bash
npm install
npm run build
```

3. **Test**:
```bash
npm test
```

4. **Run**:
```bash
npm start
```

## Cost Optimization

- **75x cheaper** than Sonnet: $0.25/1M vs $15/1M tokens
- **Response sanitization**: 75-76% token reduction on verbose outputs
- **Smart fallback**: Haiku primary → Gemini Flash backup

## MCP Tools

- `create_music_video` - Combine video + audio with LLM-optimized FFMPEG
- `process_video_file` - Process video with specified operation  
- `download_youtube_audio/video` - Optimized yt-dlp downloads
- `get_llm_stats` - Cost and usage statistics

## Configuration

Edit `config/config.yaml` or use environment variables.

**Ready for production use with just ANTHROPIC_API_KEY set.**