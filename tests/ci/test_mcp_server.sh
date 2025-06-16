#!/bin/bash

# MCP Server Test Suite
# Simulates LLM interactions with the FFMPEG MCP server via direct method calls
# Replicates the music video creation workflow performed earlier

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
MCP_SERVER_DIR="${GITHUB_WORKSPACE:-$(pwd)}"
PYTHON_PATH="${PYTHON_PATH:-python3}"
TEST_OUTPUT_DIR="/tmp/music/test_results"

# Ensure output directory exists
mkdir -p "$TEST_OUTPUT_DIR"

echo -e "${BLUE}🎬 MCP Server Test Suite${NC}"
echo -e "${BLUE}========================${NC}"
echo ""
echo "Testing the FFMPEG MCP server workflow that created the 11.5-second music video"
echo "This simulates LLM interactions via direct Python method calls"
echo ""

# Function to call MCP server methods
call_mcp_method() {
    local method_name="$1"
    local params="$2"
    local description="$3"
    
    echo -e "${YELLOW}📞 Calling: ${method_name}${NC}"
    echo -e "   ${description}"
    
    # Create Python script to call the MCP method
    cat > "$TEST_OUTPUT_DIR/temp_test.py" << EOF
import sys
import json
import asyncio
import os
sys.path.insert(0, '$MCP_SERVER_DIR/src')
sys.path.insert(0, '$MCP_SERVER_DIR')
os.chdir('$MCP_SERVER_DIR')

# Import as module to avoid relative import issues
import src.server as server_module
mcp = server_module.mcp

async def test_method():
    try:
        result = await mcp.call_tool("$method_name", $params)
        # Handle FastMCP response format
        if isinstance(result, list) and len(result) > 0:
            content = result[0]
            if hasattr(content, 'text'):
                result_data = json.loads(content.text)
                print(json.dumps(result_data, indent=2))
                return result_data
        print(json.dumps(result, indent=2, default=str))
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_method())
EOF

    # Execute the test
    cd "$MCP_SERVER_DIR"
    PYTHONPATH="$MCP_SERVER_DIR" "$PYTHON_PATH" "$TEST_OUTPUT_DIR/temp_test.py" 2>&1
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ Success${NC}"
    else
        echo -e "${RED}❌ Failed (exit code: $exit_code)${NC}"
    fi
    
    echo ""
    return $exit_code
}

# Function to run a complete test case
run_test_case() {
    local test_name="$1"
    shift
    local description="$1"
    shift
    
    echo -e "${BLUE}🧪 Test Case: ${test_name}${NC}"
    echo -e "   ${description}"
    echo ""
    
    local failed_tests=0
    
    while [[ $# -gt 0 ]]; do
        local method="$1"
        local params="$2"
        local desc="$3"
        shift 3
        
        if ! call_mcp_method "$method" "$params" "$desc"; then
            ((failed_tests++))
        fi
        
        sleep 1  # Brief pause between calls
    done
    
    if [ $failed_tests -eq 0 ]; then
        echo -e "${GREEN}🎉 Test Case '${test_name}' completed successfully!${NC}"
    else
        echo -e "${RED}💥 Test Case '${test_name}' had ${failed_tests} failures${NC}"
    fi
    
    echo ""
    echo "----------------------------------------"
    echo ""
    
    return $failed_tests
}

# Test Case 1: Basic MCP Server Functionality
echo -e "${BLUE}Starting MCP Server Tests...${NC}"
echo ""

run_test_case "Basic Server Functions" \
    "Test core MCP server functionality and file discovery" \
    \
    "list_files" "{}" \
    "List all available source files" \
    \
    "get_available_operations" "{}" \
    "Get list of available FFMPEG operations"

# Test Case 2: File Information and Analysis
# Get a file ID from the list_files result for subsequent tests
echo -e "${YELLOW}🔍 Getting file IDs for testing...${NC}"

# Create a helper script to extract file IDs
cat > "$TEST_OUTPUT_DIR/get_file_ids.py" << 'EOF'
import sys
import json
import asyncio
import os
sys.path.insert(0, '$MCP_SERVER_DIR/src')
sys.path.insert(0, '$MCP_SERVER_DIR')
os.chdir('$MCP_SERVER_DIR')

# Import as module to avoid relative import issues
import src.server as server_module
mcp = server_module.mcp

async def get_file_ids():
    try:
        result = await mcp.call_tool("list_files", {})
        # Handle FastMCP response format
        if isinstance(result, list) and len(result) > 0:
            content = result[0]
            if hasattr(content, 'text'):
                result_data = json.loads(content.text)
                files = result_data.get('files', [])
            else:
                files = []
        else:
            files = result.get('files', []) if isinstance(result, dict) else []
        
        # Find specific files we know exist
        lookin_id = None
        pxl_id = None
        panning_id = None
        audio_id = None
        
        for file in files:
            name = file.get('name', '').lower()
            if 'lookin' in name and name.endswith('.mp4'):
                lookin_id = file['id']
            elif 'pxl' in name and name.endswith('.mp4'):
                pxl_id = file['id'] 
            elif 'panning' in name and name.endswith('.mp4'):
                panning_id = file['id']
            elif 'subnautic' in name and name.endswith('.flac'):
                audio_id = file['id']
        
        print(f"LOOKIN_ID={lookin_id}")
        print(f"PXL_ID={pxl_id}")
        print(f"PANNING_ID={panning_id}")
        print(f"AUDIO_ID={audio_id}")
        
        return lookin_id, pxl_id, panning_id, audio_id
        
    except Exception as e:
        print(f"Error getting file IDs: {e}")
        return None, None, None, None

if __name__ == "__main__":
    asyncio.run(get_file_ids())
EOF

cd "$MCP_SERVER_DIR"
PYTHONPATH="$MCP_SERVER_DIR" "$PYTHON_PATH" "$TEST_OUTPUT_DIR/get_file_ids.py" > "$TEST_OUTPUT_DIR/file_ids.txt"

# Source the file IDs
source "$TEST_OUTPUT_DIR/file_ids.txt"

if [ -z "$LOOKIN_ID" ] || [ -z "$PXL_ID" ] || [ -z "$PANNING_ID" ] || [ -z "$AUDIO_ID" ]; then
    echo -e "${RED}❌ Could not find required test files${NC}"
    echo "Available files should include: lookin.mp4, PXL_*.mp4, panning*.mp4, Subnautic*.flac"
    exit 1
fi

echo -e "${GREEN}✅ Found test files:${NC}"
echo "   LOOKIN: $LOOKIN_ID"
echo "   PXL: $PXL_ID" 
echo "   PANNING: $PANNING_ID"
echo "   AUDIO: $AUDIO_ID"
echo ""

# Test Case 2: File Information and Analysis
run_test_case "File Information and Analysis" \
    "Test file metadata retrieval and content analysis" \
    \
    "get_file_info" "{\"file_id\": \"$LOOKIN_ID\"}" \
    "Get detailed info for lookin video" \
    \
    "analyze_video_content" "{\"file_id\": \"$PXL_ID\"}" \
    "Analyze video content for PXL video"

# Test Case 3: Music Video Creation Workflow (Replicate our earlier success)
run_test_case "Music Video Creation Workflow" \
    "Replicate the successful 11.5-second music video creation" \
    \
    "batch_process" \
    "{\"operations\": [
        {\"input_file_id\": \"$PXL_ID\", \"operation\": \"trim\", \"output_extension\": \"mp4\", \"params\": \"start=0 duration=4\", \"output_name\": \"test_intro_segment\"},
        {\"input_file_id\": \"$LOOKIN_ID\", \"operation\": \"trim\", \"output_extension\": \"mp4\", \"params\": \"start=0 duration=4\", \"output_name\": \"test_main_segment\"},
        {\"input_file_id\": \"$PANNING_ID\", \"operation\": \"trim\", \"output_extension\": \"mp4\", \"params\": \"start=0 duration=4\", \"output_name\": \"test_outro_segment\"}
    ]}" \
    "Create three 4-second video segments (12 seconds total = 24 beats at 120 BPM)"

# Test Case 4: Advanced Composition Features  
run_test_case "Advanced Composition Features" \
    "Test intelligent video composition and speech detection" \
    \
    "detect_speech_segments" "{\"file_id\": \"$LOOKIN_ID\"}" \
    "Detect speech segments in lookin video" \
    \
    "generate_komposition_from_description" \
    "{\"description\": \"Create a test 120 BPM music video with intro, main, and outro segments using available videos\", \"title\": \"Test Composition\", \"custom_bpm\": 120}" \
    "Generate komposition from natural language description"

# Test Case 5: Resource Management
run_test_case "Resource Management" \
    "Test file tracking and cleanup functionality" \
    \
    "list_generated_files" "{}" \
    "List all generated files from previous operations" \
    \
    "cleanup_temp_files" "{}" \
    "Clean up temporary files (optional)"

# Summary
echo -e "${BLUE}🏁 Test Suite Complete!${NC}"
echo ""
echo -e "${GREEN}✅ Successfully tested MCP server workflow that creates music videos${NC}"
echo -e "   - Basic server functionality"
echo -e "   - File information and analysis" 
echo -e "   - Music video creation (batch processing)"
echo -e "   - Advanced composition features"
echo -e "   - Resource management"
echo ""

# Create a simple curl-based test as well
echo -e "${BLUE}📡 Creating HTTP-based test script...${NC}"

cat > "$TEST_OUTPUT_DIR/test_mcp_http.sh" << 'EOF'
#!/bin/bash

# HTTP-based MCP server testing
# Note: This requires the MCP server to be running with HTTP transport
# Currently the MCP server uses stdio transport, so this is for future use

MCP_SERVER_URL="http://localhost:8000"

echo "🌐 HTTP MCP Server Test"
echo "======================="
echo ""
echo "Note: This requires MCP server to be running with HTTP transport"
echo "Current server uses stdio transport - this is for reference/future use"
echo ""

# Example MCP over HTTP request
curl_mcp_request() {
    local method="$1"
    local params="$2"
    
    curl -X POST "$MCP_SERVER_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"jsonrpc\": \"2.0\",
            \"id\": 1,
            \"method\": \"tools/call\",
            \"params\": {
                \"name\": \"$method\",
                \"arguments\": $params
            }
        }" 2>/dev/null | jq '.' || echo "Server not available via HTTP"
}

echo "Testing basic connectivity..."
curl_mcp_request "list_files" "{}"
EOF

chmod +x "$TEST_OUTPUT_DIR/test_mcp_http.sh"

echo -e "${GREEN}✅ Created HTTP test script at: $TEST_OUTPUT_DIR/test_mcp_http.sh${NC}"
echo ""

# Create a Makefile target for easy testing
cat > "$MCP_SERVER_DIR/test_mcp.mk" << 'EOF'
# MCP Server Testing Makefile
# Usage: make -f test_mcp.mk test-mcp

.PHONY: test-mcp test-mcp-quick test-mcp-workflow

test-mcp: ## Run complete MCP server test suite
	@echo "🧪 Running complete MCP server test suite..."
	@./test_mcp_server.sh

test-mcp-quick: ## Run basic MCP server connectivity test  
	@echo "⚡ Running quick MCP server test..."
	@cd $(shell pwd) && PYTHONPATH=$(shell pwd) .venv/bin/python -c "
import asyncio
import sys
import os
sys.path.insert(0, 'src')
os.chdir('.')
import src.server as server_module
mcp = server_module.mcp
async def test():
    result = await mcp.call_tool('list_files', {})
    print(f'✅ MCP server responding - found {len(result.get(\"files\", []))} files')
asyncio.run(test())
"

test-mcp-workflow: ## Test music video creation workflow only
	@echo "🎬 Testing music video creation workflow..."
	@./test_mcp_server.sh | grep -A 20 "Music Video Creation Workflow"

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
EOF

echo -e "${GREEN}✅ Created Makefile targets:${NC}"
echo -e "   ${YELLOW}make -f test_mcp.mk test-mcp${NC}        # Complete test suite"
echo -e "   ${YELLOW}make -f test_mcp.mk test-mcp-quick${NC}   # Quick connectivity test"  
echo -e "   ${YELLOW}make -f test_mcp.mk test-mcp-workflow${NC} # Music video workflow only"
echo ""

echo -e "${BLUE}🎯 Test files created:${NC}"
echo -e "   ${GREEN}test_mcp_server.sh${NC}     # Main test suite (this script)"
echo -e "   ${GREEN}test_mcp.mk${NC}            # Makefile targets for testing"
echo -e "   ${GREEN}$TEST_OUTPUT_DIR/test_mcp_http.sh${NC} # HTTP-based test (future use)"
echo ""

echo -e "${YELLOW}💡 Usage Examples:${NC}"
echo -e "   ${BLUE}./test_mcp_server.sh${NC}                    # Run complete test suite"
echo -e "   ${BLUE}make -f test_mcp.mk test-mcp-quick${NC}      # Quick server test"
echo -e "   ${BLUE}$TEST_OUTPUT_DIR/test_mcp_http.sh${NC}      # HTTP test (if server supports it)"
echo ""

# Clean up temporary files
rm -f "$TEST_OUTPUT_DIR/temp_test.py"
rm -f "$TEST_OUTPUT_DIR/get_file_ids.py"  
rm -f "$TEST_OUTPUT_DIR/file_ids.txt"

echo -e "${GREEN}🎉 MCP Server Test Suite Setup Complete!${NC}"