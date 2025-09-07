#!/usr/bin/env node

/**
 * Komposteur MCP Server - TypeScript Implementation
 * Wraps Komposteur JAR functionality for LLM access
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { 
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { KomposteurOperations } from './komposteur/operations.js';
import { 
  KompostSchema, 
  YouTubeDownloadSchema, 
  S3ConfigSchema,
  type MCPToolDefinition 
} from './types/index.js';

class KomposteurMCPServer {
  private server: Server;
  private operations: KomposteurOperations;

  constructor() {
    this.server = new Server(
      {
        name: 'komposteur-mcp-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.operations = new KomposteurOperations();
    this.setupToolHandlers();
  }

  private setupToolHandlers(): void {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: this.getToolDefinitions(),
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'komposteur_youtube_download':
            return await this.handleYouTubeDownload(args);
          
          case 'komposteur_process_composition':
            return await this.handleProcessComposition(args);
          
          case 'komposteur_s3_upload':
            return await this.handleS3Upload(args);
          
          case 'komposteur_s3_download':
            return await this.handleS3Download(args);
          
          case 'komposteur_status':
            return await this.handleStatus();
          
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error: any) {
        return {
          content: [
            {
              type: 'text',
              text: `Error executing ${name}: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  private getToolDefinitions(): MCPToolDefinition[] {
    return [
      {
        name: 'komposteur_youtube_download',
        description: 'Download video from YouTube using Komposteur',
        inputSchema: {
          type: 'object',
          properties: {
            url: { type: 'string', description: 'YouTube video URL' },
            format: { type: 'string', enum: ['mp4', 'webm', 'best'], default: 'best' },
            quality: { type: 'string', enum: ['720p', '1080p', 'best', 'worst'], default: 'best' },
            outputPath: { type: 'string', description: 'Optional output file path' }
          },
          required: ['url']
        }
      },
      {
        name: 'komposteur_process_composition',
        description: 'Process a kompost.json music video composition',
        inputSchema: {
          type: 'object',
          properties: {
            kompost: {
              type: 'object',
              description: 'Kompost composition configuration',
              properties: {
                name: { type: 'string' },
                bpm: { type: 'number' },
                duration: { type: 'number' },
                segments: {
                  type: 'array',
                  items: {
                    type: 'object',
                    properties: {
                      source: { type: 'string' },
                      start: { type: 'number' },
                      duration: { type: 'number' },
                      volume: { type: 'number' }
                    },
                    required: ['source']
                  }
                }
              },
              required: ['name', 'segments']
            },
            outputPath: { type: 'string', description: 'Optional output file path' }
          },
          required: ['kompost']
        }
      },
      {
        name: 'komposteur_s3_upload',
        description: 'Upload file to S3 using Komposteur',
        inputSchema: {
          type: 'object',
          properties: {
            bucket: { type: 'string', description: 'S3 bucket name' },
            key: { type: 'string', description: 'S3 object key' },
            localPath: { type: 'string', description: 'Local file path to upload' },
            region: { type: 'string', description: 'AWS region (optional)' }
          },
          required: ['bucket', 'key', 'localPath']
        }
      },
      {
        name: 'komposteur_s3_download',
        description: 'Download file from S3 using Komposteur',
        inputSchema: {
          type: 'object',
          properties: {
            bucket: { type: 'string', description: 'S3 bucket name' },
            key: { type: 'string', description: 'S3 object key' },
            localPath: { type: 'string', description: 'Local path to save file (optional)' },
            region: { type: 'string', description: 'AWS region (optional)' }
          },
          required: ['bucket', 'key']
        }
      },
      {
        name: 'komposteur_status',
        description: 'Get Komposteur system status and version information',
        inputSchema: {
          type: 'object',
          properties: {},
          required: []
        }
      }
    ];
  }

  private async handleYouTubeDownload(args: any) {
    const config = YouTubeDownloadSchema.parse(args);
    const result = await this.operations.downloadFromYouTube(config);

    return {
      content: [
        {
          type: 'text',
          text: result.success 
            ? `✅ YouTube download completed\\nOutput: ${result.output}\\nDuration: ${result.duration}ms`
            : `❌ YouTube download failed\\nError: ${result.error}\\nExit code: ${result.exitCode}`,
        },
      ],
    };
  }

  private async handleProcessComposition(args: any) {
    const { kompost, outputPath } = args;
    const validatedKompost = KompostSchema.parse(kompost);
    const result = await this.operations.processKomposition(validatedKompost, outputPath);

    return {
      content: [
        {
          type: 'text',
          text: result.success 
            ? `✅ Komposition processed successfully\\nOutput files: ${result.outputFiles?.join(', ') || 'Unknown'}\\nDuration: ${result.duration}ms`
            : `❌ Komposition processing failed\\nError: ${result.error}\\nExit code: ${result.exitCode}`,
        },
      ],
    };
  }

  private async handleS3Upload(args: any) {
    const config = S3ConfigSchema.parse(args);
    const result = await this.operations.uploadToS3(config);

    return {
      content: [
        {
          type: 'text',
          text: result.success 
            ? `✅ S3 upload completed\\nBucket: ${config.bucket}\\nKey: ${config.key}\\nDuration: ${result.duration}ms`
            : `❌ S3 upload failed\\nError: ${result.error}\\nExit code: ${result.exitCode}`,
        },
      ],
    };
  }

  private async handleS3Download(args: any) {
    const config = S3ConfigSchema.parse(args);
    const result = await this.operations.downloadFromS3(config);

    return {
      content: [
        {
          type: 'text',
          text: result.success 
            ? `✅ S3 download completed\\nFiles: ${result.outputFiles?.join(', ') || 'Unknown'}\\nDuration: ${result.duration}ms`
            : `❌ S3 download failed\\nError: ${result.error}\\nExit code: ${result.exitCode}`,
        },
      ],
    };
  }

  private async handleStatus() {
    const status = await this.operations.getStatus();

    return {
      content: [
        {
          type: 'text',
          text: `🔍 Komposteur Status:
Available: ${status.available ? '✅' : '❌'}
Version: ${status.version || 'Unknown'}
JAR Path: ${status.jarPath || 'Not found'}

${!status.available ? 'Run: npm run komposteur:download to set up Komposteur JAR' : 'Ready for operations'}`,
        },
      ],
    };
  }

  async run(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('🎵 Komposteur MCP Server running on stdio');
  }
}

// Start the server
if (import.meta.url === `file://${process.argv[1]}`) {
  const server = new KomposteurMCPServer();
  server.run().catch(console.error);
}