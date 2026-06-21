#!/bin/bash

echo "🎬 YOLO FFMPEG MCP - 128-Beat Music Video Creation"
echo "=================================================="

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Please install uv first: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if source video files exist
if [ ! -f "tests/files/JJVtt947FfI_136.mp4" ] || [ ! -f "tests/files/_wZ5Hof5tXY_136.mp4" ]; then
    echo "❌ Source video files not found in tests/files/"
    echo "   Expected: JJVtt947FfI_136.mp4 and _wZ5Hof5tXY_136.mp4"
    exit 1
fi

echo "✅ Source video files found"

# Copy source files to temp location for processing (MCP server expects files in /tmp/music/source/)
echo "📁 Setting up source files..."
mkdir -p /tmp/music/source/
cp tests/files/JJVtt947FfI_136.mp4 /tmp/music/source/
cp tests/files/_wZ5Hof5tXY_136.mp4 /tmp/music/source/

echo "📹 Video files copied to /tmp/music/source/"

# Install dependencies if needed
echo "📦 Installing dependencies..."
uv sync

# Run our music video creation script directly (no MCP server needed - we import directly)
echo "🚀 Starting 128-beat music video creation..."
echo ""

uv run python claude-yolo.py

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS! Music video creation completed"
    echo "📁 Check the generated files:"
    echo "   - 128_beat_music_video_komposition.json"
    echo "   - audio_timing_manifest.json"
    echo "   - Various processed video segments"
    echo ""
    echo "🎬 Ready for final assembly in your video editor!"
else
    echo ""
    echo "❌ FAILED! Check error messages above"
    exit 1
fi