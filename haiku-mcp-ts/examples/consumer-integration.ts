/**
 * Example integration for consuming LLM project
 * Shows how to integrate haiku-mcp-server into existing HTTP server
 */

import MCPHttpBridge from './http-bridge.js';

// Option 1: Standalone Bridge Server
export function startStandaloneBridge(port: number = 3001) {
  const bridge = new MCPHttpBridge();
  bridge.start(port);
  return bridge;
}

// Option 2: Integrate into existing Express app
export function addMCPRoutes(app: any) {
  const bridge = new MCPHttpBridge();

  // Mount MCP routes on existing app
  app.use('/api/mcp', bridge.app);

  return bridge;
}

// Option 3: Simple fetch-based client for consumer LLM
export class HaikuMCPClient {
  constructor(private baseUrl: string = 'http://localhost:3001') {}

  async callTool(tool: string, arguments: any = {}): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/mcp/call-tool`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool, arguments })
    });

    if (!response.ok) {
      throw new Error(`MCP call failed: ${response.statusText}`);
    }

    return response.json();
  }

  async listTools(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/mcp/list-tools`);

    if (!response.ok) {
      throw new Error(`Failed to list tools: ${response.statusText}`);
    }

    return response.json();
  }

  async health(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/health`);
    return response.json();
  }
}

// Example usage for consuming LLM
export async function exampleUsage() {
  console.log('🚀 Starting MCP HTTP Bridge...');

  // Start bridge
  const bridge = startStandaloneBridge(3001);

  // Wait for startup
  await new Promise(resolve => setTimeout(resolve, 3000));

  // Create client
  const client = new HaikuMCPClient();

  try {
    // Check health
    const health = await client.health();
    console.log('Health:', health);

    // List available tools
    const tools = await client.listTools();
    console.log('Available tools:', tools);

    // Example: Video analysis
    const analysis = await client.callTool('haiku_video_analysis', {
      video_path: '/tmp/sample-video.mp4',
      analysis_type: 'full'
    });
    console.log('Video analysis:', analysis);

    // Example: Create music video
    const musicVideo = await client.callTool('create_music_video', {
      video_file: 'video_001',
      audio_file: 'audio_001',
      output_file: '/tmp/output.mp4',
      duration: 30
    });
    console.log('Music video result:', musicVideo);

  } catch (error) {
    console.error('Error:', error);
  } finally {
    bridge.stop();
  }
}

// For LLM integration in svelte-test project
export const INTEGRATION_INSTRUCTIONS = `
## Quick Integration Steps

1. Install package:
   \`\`\`bash
   bun link @stiglau/komposteur-mcp-server
   \`\`\`

2. Add to your server:
   \`\`\`typescript
   import MCPHttpBridge from '@stiglau/komposteur-mcp-server/examples/http-bridge';

   const bridge = new MCPHttpBridge();
   bridge.start(3001);
   \`\`\`

3. Use in your LLM service:
   \`\`\`typescript
   const response = await fetch('http://localhost:3001/api/mcp/call-tool', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       tool: 'haiku_video_analysis',
       arguments: { video_path: '/path/to/video.mp4' }
     })
   });
   \`\`\`

4. Set environment variables:
   \`\`\`bash
   export ANTHROPIC_API_KEY=your_key_here
   export GEMINI_API_KEY=your_fallback_key  # Optional
   \`\`\`

That's it! All 8 video processing tools are now available via HTTP.
`;

if (import.meta.url === `file://${process.argv[1]}`) {
  exampleUsage().catch(console.error);
}