/**
 * TypeScript MCP Client for Haiku FFMPEG MCP Server
 * Responds to Gemini LLM's questions about connecting to the MCP server
 */

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { z } from 'zod';

class HaikuMCPClient {
  private client: Client;
  private transport: StdioClientTransport;

  constructor() {
    this.client = new Client(
      {
        name: 'haiku-mcp-client',
        version: '1.0.0',
      },
      {
        capabilities: {},
      }
    );
  }

  /**
   * Answer to Question 1: Connecting to the Server
   * Connect to the Haiku MCP server using StdioClientTransport
   */
  async connect(): Promise<void> {
    // Let SDK manage the server process - provide command and args
    this.transport = new StdioClientTransport({
      command: 'node',
      args: ['dist/server.js'],
      env: { 
        ...process.env,
        ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY 
      }
    });

    // Connect the client
    await this.client.connect(this.transport);
    console.log('✅ Connected to Haiku MCP Server');
  }

  /**
   * Answer to Question 2 & 3: Calling a Tool and Handling Response
   * Call a tool on the MCP server and handle the response
   */
  async callTool(toolName: string, args: any = {}): Promise<any> {
    try {
      // Use built-in callTool method
      const response = await this.client.callTool({
        name: toolName,
        arguments: args,
      });

      console.log(`✅ Tool ${toolName} called successfully`);
      return response;
    } catch (error) {
      console.error(`❌ Error calling tool ${toolName}:`, error);
      throw error;
    }
  }

  /**
   * List available tools
   */
  async listTools(): Promise<any> {
    try {
      const response = await this.client.listTools();
      return response;
    } catch (error) {
      console.error('❌ Error listing tools:', error);
      throw error;
    }
  }

  /**
   * Disconnect from server
   */
  async disconnect(): Promise<void> {
    await this.client.close();
    console.log('✅ Disconnected from server');
  }
}

/**
 * Complete runnable example that demonstrates the client
 */
async function main() {
  console.log('ANTHROPIC_API_KEY:', process.env.ANTHROPIC_API_KEY);

  const client = new HaikuMCPClient();

  try {
    // Connect to server
    await client.connect();

    // Test 1: List available tools first
    console.log('📋 Testing tools list...');
    const toolsList = await client.listTools();
    console.log('Available Tools:', toolsList.tools.map(t => t.name));

    // Test 2: Get LLM stats
    console.log('\n📊 Testing LLM stats...');
    const statsResponse = await client.callTool('get_llm_stats', {});
    console.log('LLM Stats:', JSON.parse(statsResponse.content[0].text));

    // Test 3: Create music video
    console.log('\n🎵 Testing music video creation...');
    const musicVideoResponse = await client.callTool('create_music_video', {
      video_file: '/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4',
      audio_file: '/tmp/music/source/Subnautic Measures.flac',
      output_file: '/tmp/kompo/haiku-ffmpeg/generated-videos/music-video-test.mp4',
      duration: 18
    });
    console.log('Music Video Response:', JSON.parse(musicVideoResponse.content[0].text));

  } catch (error) {
    console.error('❌ Client error:', error);
  } finally {
    // Always disconnect
    await client.disconnect();
  }
}

// Answer to Question 4: Compilation and Running Commands
/*
Compilation and Running Commands:

1. Compile the client.ts file:
   tsc client.ts --target es2020 --module esnext --moduleResolution bundler

2. Run the compiled client:
   node client.js

Or using ts-node directly:
   npx ts-node --esm client.ts

Or add to package.json scripts:
   "scripts": {
     "client": "npx ts-node --esm client.ts"
   }
   
   Then run: npm run client
*/

export { HaikuMCPClient };

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}