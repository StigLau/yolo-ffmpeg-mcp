#!/bin/bash
# Natural Language Music Video Creation with TypeScript MCP Server
# Interactive CLI for creating music videos with natural language prompts

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}🎬 $1${NC}"
    echo "$(printf '=%.0s' {1..60})"
}

print_step() {
    echo -e "${PURPLE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
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
echo "Using TypeScript MCP Server with Haiku LLM"
echo ""

# Show available files from registry
print_step "Discovering available files..."
REGISTRY_OUTPUT=$(ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY npx tsx -e "
import { HaikuMCPClient } from './client.js';

async function listFiles() {
  const client = new HaikuMCPClient();
  try {
    await client.connect();
    const filesList = await client.callTool('list_files', {});
    const files = JSON.parse(filesList.content[0].text).files;
    console.log(JSON.stringify(files, null, 2));
    await client.disconnect();
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}
listFiles();
" 2>/dev/null)

if [[ $? -eq 0 ]]; then
    echo "$REGISTRY_OUTPUT" | jq -r '.[] | select(.mediaType=="video") | "📹 \(.id) - \(.path | split("/") | last) (\(.size/1024/1024 | floor)MB)"'
    echo ""
    echo "$REGISTRY_OUTPUT" | jq -r '.[] | select(.mediaType=="audio") | "🎵 \(.id) - \(.path | split("/") | last) (\(.size/1024/1024 | floor)MB)"'
    echo ""
else
    print_error "Failed to connect to MCP server"
    echo "Make sure to run: npm run build"
    exit 1
fi

# Get video files for selection
VIDEO_FILES=$(echo "$REGISTRY_OUTPUT" | jq -r '.[] | select(.mediaType=="video") | .id')
AUDIO_FILES=$(echo "$REGISTRY_OUTPUT" | jq -r '.[] | select(.mediaType=="audio") | .id')

if [[ -z "$VIDEO_FILES" ]] || [[ -z "$AUDIO_FILES" ]]; then
    print_error "No video or audio files found in registry"
    exit 1
fi

# Interactive mode or direct prompt
if [[ $# -eq 0 ]]; then
    print_step "Interactive Mode - Enter your natural language request"
    echo "Examples:"
    echo "  'Create an 18-second music video with fade effects'"
    echo "  'Make a dramatic video with crossfades and vintage look'"
    echo "  'Generate a beat-synced video at 120 BPM with smooth transitions'"
    echo ""
    read -p "🎬 Your request: " USER_REQUEST
else
    USER_REQUEST="$*"
fi

print_info "Processing request: \"$USER_REQUEST\""

# Create output directory
mkdir -p /tmp/kompo/haiku-ffmpeg/generated-videos

# Select first video and audio file automatically (user can modify script for selection)
VIDEO_ID=$(echo "$VIDEO_FILES" | head -n1)
AUDIO_ID=$(echo "$AUDIO_FILES" | head -n1)

print_step "Selected files:"
echo "📹 Video: $VIDEO_ID"
echo "🎵 Audio: $AUDIO_ID"
echo ""

# Generate timestamp for unique output
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="/tmp/kompo/haiku-ffmpeg/generated-videos/natural_language_${TIMESTAMP}.mp4"

print_step "Creating music video with TypeScript MCP Server..."

# Call the TypeScript MCP server with the natural language request
RESULT=$(ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY npx tsx -e "
import { HaikuMCPClient } from './client.js';

async function createMusicVideo() {
  const client = new HaikuMCPClient();
  try {
    await client.connect();
    
    // Add natural language context to the request
    const response = await client.callTool('create_music_video', {
      video_file: '$VIDEO_ID',
      audio_file: '$AUDIO_ID', 
      output_file: '$OUTPUT_FILE',
      duration: 18,
      user_request: '$USER_REQUEST'
    });
    
    const result = JSON.parse(response.content[0].text);
    console.log(JSON.stringify(result, null, 2));
    
    await client.disconnect();
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}
createMusicVideo();
" 2>/dev/null)

if [[ $? -eq 0 ]]; then
    SUCCESS=$(echo "$RESULT" | jq -r '.success')
    
    if [[ "$SUCCESS" == "true" ]]; then
        print_success "Music video created successfully!"
        echo ""
        print_info "Output file: $OUTPUT_FILE"
        
        # Get video info
        if [[ -f "$OUTPUT_FILE" ]]; then
            FILE_SIZE=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE" 2>/dev/null)
            SIZE_MB=$((FILE_SIZE / 1024 / 1024))
            print_info "File size: ${SIZE_MB}MB"
            
            # Try to get duration
            if command -v ffprobe >/dev/null 2>&1; then
                DURATION=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$OUTPUT_FILE" 2>/dev/null)
                if [[ -n "$DURATION" ]]; then
                    print_info "Duration: ${DURATION}s"
                fi
            fi
            
            # Try to open video on macOS
            if [[ "$OSTYPE" == "darwin"* ]] && command -v open >/dev/null 2>&1; then
                echo ""
                read -p "🎬 Open video in default player? (y/n): " -n 1 -r
                echo ""
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    open "$OUTPUT_FILE"
                fi
            fi
        fi
        
        # Show processing stats
        COMMAND_USED=$(echo "$RESULT" | jq -r '.command_used // "N/A"')
        LLM_COST=$(echo "$RESULT" | jq -r '.llm_cost // 0')
        PROCESSING_TIME=$(echo "$RESULT" | jq -r '.execution_time_ms // 0')
        
        echo ""
        print_header "Processing Statistics"
        echo "💰 LLM Cost: \$$(printf '%.6f' $LLM_COST)"
        echo "⏱️  Processing Time: ${PROCESSING_TIME}ms"
        echo "🛠️  FFMPEG Command:"
        echo "   $COMMAND_USED"
        
    else
        print_error "Music video creation failed"
        ERROR_MSG=$(echo "$RESULT" | jq -r '.error // "Unknown error"')
        echo "$ERROR_MSG"
        
        # Show the attempted command for debugging
        COMMAND_USED=$(echo "$RESULT" | jq -r '.command_used // "N/A"')
        if [[ "$COMMAND_USED" != "N/A" ]]; then
            echo ""
            print_info "Attempted FFMPEG command:"
            echo "$COMMAND_USED"
        fi
    fi
else
    print_error "Failed to connect to TypeScript MCP server"
    echo "Make sure the server is built: npm run build"
fi

print_header "Session Complete"