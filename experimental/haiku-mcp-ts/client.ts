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

    // Test 1: Registry system
    console.log('📋 Testing registry system...');
    
    const registryStatus = await client.callTool('get_registry_status', {});
    console.log('Registry Status:', JSON.parse(registryStatus.content[0].text));

    const filesList = await client.callTool('list_files', {});
    const files = JSON.parse(filesList.content[0].text).files;
    console.log(`Found ${files.length} files in registry:`);
    
    if (files.length > 0) {
      console.log('File IDs:', files.map(f => `${f.id} (${f.extension})`));
      
      // Test file info for first file
      const fileInfo = await client.callTool('get_file_info', { file_id: files[0].id });
      console.log('First File Info:', JSON.parse(fileInfo.content[0].text));
      
      // Test music video with file IDs
      const videoFile = files.find(f => f.mediaType === 'video');
      const audioFile = files.find(f => f.mediaType === 'audio');
      
      if (videoFile && audioFile) {
        console.log('\n🎵 Testing music video with file IDs...');
        const musicVideoResponse = await client.callTool('create_music_video', {
          video_file: videoFile.id,
          audio_file: audioFile.id,
          output_file: '/tmp/kompo/haiku-ffmpeg/generated-videos/registry-music-video.mp4',
          duration: 18
        });
        console.log('Music Video Response:', JSON.parse(musicVideoResponse.content[0].text));
      } else {
        console.log('⚠️  No video/audio files found for music video test');
      }
    }

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