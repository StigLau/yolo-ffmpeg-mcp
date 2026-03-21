#!/bin/bash
# Simple Natural Language Music Video Creator
# Direct command-line interface for TypeScript MCP Server

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}🎬 $1${NC}"
    echo "================================"
}

print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check API keys
print_step "Checking API keys..."

if [[ -z "$ANTHROPIC_API_KEY" ]]; then
    print_error "ANTHROPIC_API_KEY not set"
    echo "Run: export ANTHROPIC_API_KEY='your-anthropic-key'"
    echo ""
    echo "To get an API key:"
    echo "1. Go to: https://console.anthropic.com/account/keys"
    echo "2. Create a new API key"
    echo "3. Export it: export ANTHROPIC_API_KEY='sk-ant-api03-...'"
    exit 1
else
    print_success "ANTHROPIC_API_KEY is set (${#ANTHROPIC_API_KEY} chars)"
fi

if [[ -z "$GEMINI_API_KEY" ]]; then
    print_error "GEMINI_API_KEY not set (fallback LLM)"
    echo "Run: export GEMINI_API_KEY='your-google-api-key'"
    echo ""
    echo "To get a Google API key:"
    echo "1. Go to: https://aistudio.google.com/app/apikey"
    echo "2. Create a new API key"
    echo "3. Export it: export GEMINI_API_KEY='your-key-here'"
    echo ""
    echo "⚠️  Continuing with only Anthropic API key (may cause fallback failures)"
else
    print_success "GEMINI_API_KEY is set (${#GEMINI_API_KEY} chars)"
fi

# Test API key validity
print_step "Testing API key validity..."

print_header "Natural Language Music Video Creator"

# Get user request
if [[ $# -eq 0 ]]; then
    echo "Examples:"
    echo "  './simple-music-video.sh \"Create a 20-second dramatic video with fade effects\"'"
    echo "  './simple-music-video.sh \"Make a beat-synced music video at 130 BPM\"'"
    echo ""
    read -p "🎬 Your request: " USER_REQUEST
else
    USER_REQUEST="$*"
fi

echo "Processing: \"$USER_REQUEST\""
echo ""

# Create output file with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="/tmp/kompo/haiku-ffmpeg/generated-videos/natural_${TIMESTAMP}.mp4"

mkdir -p "$(dirname "$OUTPUT_FILE")"

print_step "Testing TypeScript MCP Server..."

# Test with a simple music video creation
cat > test_natural.ts << EOF
import { HaikuMCPClient } from './client.ts';

async function createNaturalLanguageVideo() {
  const client = new HaikuMCPClient();
  
  try {
    await client.connect();
    
    // Get available files
    const filesList = await client.callTool('list_files', {});
    const files = JSON.parse(filesList.content[0].text).files;
    
    const videoFile = files.find(f => f.mediaType === 'video');
    const audioFile = files.find(f => f.mediaType === 'audio');
    
    if (!videoFile || !audioFile) {
      throw new Error('No video or audio files found');
    }
    
    console.log('📹 Using video:', videoFile.id);
    console.log('🎵 Using audio:', audioFile.id);
    console.log('');
    
    // Create music video
    const response = await client.callTool('create_music_video', {
      video_file: videoFile.id,
      audio_file: audioFile.id,
      output_file: '$OUTPUT_FILE',
      duration: 18
    });
    
    const result = JSON.parse(response.content[0].text);
    
    if (result.success) {
      console.log('✅ Success!');
      console.log('📁 Output:', '$OUTPUT_FILE');
      console.log('💰 Cost: $' + (result.llm_cost || 0).toFixed(6));
      console.log('⏱️  Time:', (result.execution_time_ms || 0) + 'ms');
    } else {
      console.log('❌ Failed:', result.error);
      console.log('🛠️  Command:', result.command_used);
    }
    
    await client.disconnect();
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

createNaturalLanguageVideo();
EOF

# Run the test
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY npx tsx test_natural.ts

# Check if file was created
if [[ -f "$OUTPUT_FILE" ]]; then
    FILE_SIZE=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE" 2>/dev/null || echo "0")
    SIZE_MB=$((FILE_SIZE / 1024 / 1024))
    
    print_success "Video created: $OUTPUT_FILE (${SIZE_MB}MB)"
    
    # Try to open on macOS
    if [[ "$OSTYPE" == "darwin"* ]] && command -v open >/dev/null 2>&1; then
        echo ""
        read -p "🎬 Open video? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            open "$OUTPUT_FILE"
        fi
    fi
else
    print_error "Video file was not created"
fi

# Cleanup
rm -f test_natural.ts

print_header "Done"