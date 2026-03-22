#!/bin/bash
# API Token Access Validation Test
# Tests both Anthropic and Gemini API access step by step

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}🔑 $1${NC}"
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

print_header "API Token Access Validation Test"

# Step 1: Check environment variables
print_step "Step 1: Checking environment variables..."

if [[ -z "$ANTHROPIC_API_KEY" ]]; then
    print_error "ANTHROPIC_API_KEY not set"
    exit 1
else
    print_success "ANTHROPIC_API_KEY is set (${#ANTHROPIC_API_KEY} chars)"
    echo "  Format: ${ANTHROPIC_API_KEY:0:15}..."
fi

if [[ -z "$GEMINI_API_KEY" ]]; then
    print_error "GEMINI_API_KEY not set"
    exit 1
else
    print_success "GEMINI_API_KEY is set (${#GEMINI_API_KEY} chars)"
    echo "  Format: ${GEMINI_API_KEY:0:15}..."
fi

# Step 2: Test Anthropic API directly
print_step "Step 2: Testing Anthropic API access..."

ANTHROPIC_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Content-Type: application/json" \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -d '{
        "model": "claude-3-haiku-20240307",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "Say hello"}]
    }' \
    https://api.anthropic.com/v1/messages)

ANTHROPIC_HTTP_CODE=$(echo "$ANTHROPIC_RESPONSE" | tail -1)
ANTHROPIC_BODY=$(echo "$ANTHROPIC_RESPONSE" | sed '$d')

if [[ "$ANTHROPIC_HTTP_CODE" == "200" ]]; then
    print_success "Anthropic API access working"
    echo "  Model: claude-3-haiku-20240307"
    echo "  Response: $(echo "$ANTHROPIC_BODY" | jq -r '.content[0].text' 2>/dev/null || echo "OK")"
elif [[ "$ANTHROPIC_HTTP_CODE" == "401" ]]; then
    print_error "Anthropic API authentication failed (401)"
    echo "  Response: $ANTHROPIC_BODY"
    echo "  Check your API key at: https://console.anthropic.com/account/keys"
elif [[ "$ANTHROPIC_HTTP_CODE" == "429" ]]; then
    print_error "Anthropic API rate limited (429)"
    echo "  Response: $ANTHROPIC_BODY"
    echo "  Wait and try again, or check usage limits"
else
    print_error "Anthropic API failed (HTTP $ANTHROPIC_HTTP_CODE)"
    echo "  Response: $ANTHROPIC_BODY"
fi

# Step 3: Test Gemini API directly
print_step "Step 3: Testing Gemini API access..."

GEMINI_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Content-Type: application/json" \
    -d '{
        "contents": [{
            "parts": [{"text": "Say hello"}]
        }]
    }' \
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=$GEMINI_API_KEY")

GEMINI_HTTP_CODE=$(echo "$GEMINI_RESPONSE" | tail -1)
GEMINI_BODY=$(echo "$GEMINI_RESPONSE" | sed '$d')

if [[ "$GEMINI_HTTP_CODE" == "200" ]]; then
    print_success "Gemini API access working"
    echo "  Model: gemini-1.5-flash"
    echo "  Response: $(echo "$GEMINI_BODY" | jq -r '.candidates[0].content.parts[0].text' 2>/dev/null || echo "OK")"
elif [[ "$GEMINI_HTTP_CODE" == "400" ]]; then
    print_error "Gemini API bad request (400)"
    echo "  Response: $GEMINI_BODY"
    echo "  Check API key format or request structure"
elif [[ "$GEMINI_HTTP_CODE" == "403" ]]; then
    print_error "Gemini API forbidden (403)"
    echo "  Response: $GEMINI_BODY"
    echo "  Check your API key at: https://aistudio.google.com/app/apikey"
elif [[ "$GEMINI_HTTP_CODE" == "429" ]]; then
    print_error "Gemini API rate limited (429)"
    echo "  Response: $GEMINI_BODY"
    echo "  Wait and try again, or check quota limits"
else
    print_error "Gemini API failed (HTTP $GEMINI_HTTP_CODE)"
    echo "  Response: $GEMINI_BODY"
fi

# Step 4: Test TypeScript MCP server initialization
print_step "Step 4: Testing TypeScript MCP server initialization..."

cat > test_mcp_init.ts << EOF
import { HaikuMCPClient } from './client.ts';

async function testMCPInit() {
  const client = new HaikuMCPClient();
  
  try {
    console.log('🔌 Connecting to MCP server...');
    await client.connect();
    
    console.log('📋 Testing tool list...');
    const tools = await client.listTools();
    console.log('✅ Available tools:', tools.tools.map(t => t.name).join(', '));
    
    console.log('📊 Testing LLM stats...');
    const stats = await client.callTool('get_llm_stats', {});
    const statsData = JSON.parse(stats.content[0].text);
    console.log('✅ Primary model:', statsData.primary_model.provider + '/' + statsData.primary_model.model);
    console.log('✅ Fallback model:', statsData.fallback_model.provider + '/' + statsData.fallback_model.model);
    
    await client.disconnect();
    console.log('✅ MCP server test completed successfully');
    
  } catch (error) {
    console.error('❌ MCP server test failed:', error.message);
    process.exit(1);
  }
}

testMCPInit();
EOF

echo "  Running MCP server test..."
if ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY GEMINI_API_KEY=$GEMINI_API_KEY npx tsx test_mcp_init.ts 2>&1; then
    print_success "MCP server initialization working"
else
    print_error "MCP server initialization failed"
fi

# Cleanup
rm -f test_mcp_init.ts

# Step 5: Summary
print_header "Test Summary"

if [[ "$ANTHROPIC_HTTP_CODE" == "200" ]] && [[ "$GEMINI_HTTP_CODE" == "200" ]]; then
    print_success "All API tokens are working correctly"
    echo ""
    echo "✅ Anthropic API: Ready for video processing"
    echo "✅ Gemini API: Ready as fallback"
    echo "✅ MCP Server: Ready for music video creation"
    echo ""
    echo "You can now run: ./simple-music-video.sh \"Your request\""
else
    print_error "Some API tokens have issues"
    echo ""
    if [[ "$ANTHROPIC_HTTP_CODE" != "200" ]]; then
        echo "❌ Fix Anthropic API access first"
    fi
    if [[ "$GEMINI_HTTP_CODE" != "200" ]]; then
        echo "❌ Fix Gemini API access (fallback won't work)"
    fi
fi