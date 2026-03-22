# Answers for Gemini LLM - TypeScript MCP Client

## 1. Connecting to the Server

```typescript
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { spawn } from 'child_process';

// Spawn the server process
const serverProcess = spawn('node', ['dist/server.js'], {
  cwd: '/path/to/haiku-mcp-ts',
  env: { 
    ...process.env,
    ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY 
  }
});

// Create stdio transport
const transport = new StdioClientTransport({
  readable: serverProcess.stdout!,
  writable: serverProcess.stdin!,
});

// Create and connect client
const client = new Client({
  name: 'haiku-mcp-client',
  version: '1.0.0',
}, { capabilities: {} });

await client.connect(transport);
```

## 2. Calling a Tool

Our server doesn't have `system-health` but has `get_llm_stats` which serves similar purpose:

```typescript
// Call get_llm_stats tool (our equivalent to system-health)
const response = await client.request({
  method: 'tools/call',
  params: {
    name: 'get_llm_stats',
    arguments: {}
  }
}, {}); // Empty options object
```

## 3. Handling the Response

```typescript
try {
  const response = await client.request({
    method: 'tools/call',
    params: {
      name: 'get_llm_stats',
      arguments: {}
    }
  }, {}); // Empty options object
  
  // Response is already parsed JSON
  console.log('Tool response:', response);
  
  // Access the content
  if (response.content && response.content[0]) {
    const result = JSON.parse(response.content[0].text);
    console.log('LLM Stats:', result);
  }
} catch (error) {
  console.error('Error:', error);
}
```

## 4. Compiling and Running

### Method 1: Using tsc directly
```bash
# Compile
tsc client.ts --target es2020 --module esnext --moduleResolution bundler

# Run
node client.js
```

### Method 2: Using ts-node (recommended)
```bash
# Install ts-node if not installed
npm install --save-dev ts-node

# Run directly
npx ts-node --esm client.ts
```

### Method 3: Add to package.json
```json
{
  "scripts": {
    "client": "npx ts-node --esm client.ts"
  }
}
```

Then run: `npm run client`

## Complete Example

I've created a complete `client.ts` file that demonstrates all of this. The key differences from your questions:

- Our server has different tools: `get_llm_stats`, `process_video_file`, `create_music_video`, etc.
- The server runs as a stdio process, so we spawn it and connect via stdio transport
- Responses come back as structured content with `text` fields that may need JSON parsing

## Available Tools in Our Server

- `create_music_video` - Combine video and audio
- `process_video_file` - Process video with various operations  
- `download_youtube_audio` - Download audio from YouTube
- `download_youtube_video` - Download video from YouTube
- `get_llm_stats` - Get LLM usage statistics (your system-health equivalent)

You can test any of these tools using the client pattern shown above.