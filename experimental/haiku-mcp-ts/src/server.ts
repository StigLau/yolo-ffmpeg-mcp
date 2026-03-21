/**
 * Haiku MCP Server - Cost-optimized video processing server
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
  McpError,
  ErrorCode,
} from '@modelcontextprotocol/sdk/types.js';
import { loadConfig } from './config.js';
import { HaikuClient } from './llm/haiku-client.js';
import { GeminiFlashClient } from './llm/gemini-client.js';
import { VideoProcessor } from './tools/video-processor.js';
import { YouTubeDownloader } from './tools/youtube-downloader.js';
import { BaseLLMClient } from './llm/types.js';
import { FileManager } from './registry/file-manager.js';

class HaikuMCPServer {
  private server: Server;
  private llmClient!: BaseLLMClient;
  private fallbackClient!: BaseLLMClient;
  private videoProcessor!: VideoProcessor;
  private youtubeDownloader!: YouTubeDownloader;
  private fileManager!: FileManager;

  constructor() {
    this.server = new Server({
      name: 'haiku-mcp-server',
      version: '1.0.0',
    }, {
      capabilities: {
        tools: {},
      },
    });

    this.setupToolHandlers();
  }

  async initialize() {
    const config = await loadConfig();
    
    // Initialize LLM clients
    const primaryModel = config.models[config.llm.primary];
    const fallbackModel = config.models[config.llm.fallback];

    if (primaryModel.provider === 'anthropic') {
      this.llmClient = new HaikuClient(primaryModel);
    } else {
      this.llmClient = new GeminiFlashClient(primaryModel);
    }

    if (fallbackModel.provider === 'anthropic') {
      this.fallbackClient = new HaikuClient(fallbackModel);
    } else {
      this.fallbackClient = new GeminiFlashClient(fallbackModel);
    }

    // Initialize tools
    const sanitizationConfig = {
      strip_metadata: config.response_limits.strip_metadata,
      max_output_tokens: config.response_limits.max_tokens,
      preserve_essential_fields: ['success', 'error', 'output_file', 'downloaded_file'],
      aggressive_pruning: true,
    };

    this.videoProcessor = new VideoProcessor(
      this.llmClient, 
      config.ffmpeg, 
      sanitizationConfig
    );

    this.youtubeDownloader = new YouTubeDownloader(
      this.llmClient, 
      config.youtube, 
      sanitizationConfig
    );

    // Initialize file registry
    this.fileManager = new FileManager();

    console.error('Haiku MCP Server initialized');
  }

  private setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'create_music_video',
          description: 'Create a music video by combining video and audio files using LLM-generated FFMPEG commands',
          inputSchema: {
            type: 'object',
            properties: {
              video_file: {
                type: 'string',
                description: 'Path to the input video file',
              },
              audio_file: {
                type: 'string',
                description: 'Path to the input audio file',
              },
              output_file: {
                type: 'string',
                description: 'Path for the output music video file',
              },
              duration: {
                type: 'number',
                description: 'Duration in seconds (optional)',
              },
              start_time: {
                type: 'number',
                description: 'Start time in seconds (optional)',
              },
            },
            required: ['video_file', 'audio_file', 'output_file'],
          },
        },
        {
          name: 'process_video_file',
          description: 'Process a video file with specified operation using LLM-optimized FFMPEG commands',
          inputSchema: {
            type: 'object',
            properties: {
              input_file: {
                type: 'string',
                description: 'Path to the input video file',
              },
              output_file: {
                type: 'string',
                description: 'Path for the output file',
              },
              operation: {
                type: 'string',
                description: 'Video processing operation (e.g., "resize", "trim", "convert", "extract_audio")',
              },
              parameters: {
                type: 'object',
                description: 'Additional parameters for the operation',
              },
            },
            required: ['input_file', 'output_file', 'operation'],
          },
        },
        {
          name: 'download_youtube_audio',
          description: 'Download audio from YouTube video using optimized yt-dlp commands',
          inputSchema: {
            type: 'object',
            properties: {
              url: {
                type: 'string',
                description: 'YouTube video URL',
              },
              output_dir: {
                type: 'string',
                description: 'Directory to save the downloaded audio',
              },
              format: {
                type: 'string',
                description: 'Audio format preference (mp3, m4a, etc.)',
              },
              max_duration: {
                type: 'number',
                description: 'Maximum duration in seconds',
              },
            },
            required: ['url', 'output_dir'],
          },
        },
        {
          name: 'download_youtube_video',
          description: 'Download video from YouTube using optimized yt-dlp commands',
          inputSchema: {
            type: 'object',
            properties: {
              url: {
                type: 'string',
                description: 'YouTube video URL',
              },
              output_dir: {
                type: 'string',
                description: 'Directory to save the downloaded video',
              },
              format: {
                type: 'string',
                description: 'Video format/quality preference',
              },
              max_duration: {
                type: 'number',
                description: 'Maximum duration in seconds',
              },
            },
            required: ['url', 'output_dir'],
          },
        },
        {
          name: 'get_llm_stats',
          description: 'Get current LLM usage statistics and cost estimates',
          inputSchema: {
            type: 'object',
            properties: {},
          },
        },
        {
          name: 'list_files',
          description: 'List all files in the registry with their IDs and metadata',
          inputSchema: {
            type: 'object',
            properties: {},
          },
        },
        {
          name: 'get_file_info',
          description: 'Get detailed information about a file by its ID',
          inputSchema: {
            type: 'object',
            properties: {
              file_id: {
                type: 'string',
                description: 'File ID from the registry (e.g., file_14af0abf)',
              },
            },
            required: ['file_id'],
          },
        },
        {
          name: 'get_registry_status',
          description: 'Get current registry status and statistics',
          inputSchema: {
            type: 'object',
            properties: {},
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      try {
        switch (request.params.name) {
          case 'create_music_video':
            return await this.handleCreateMusicVideo(request.params.arguments);

          case 'process_video_file':
            return await this.handleProcessVideoFile(request.params.arguments);

          case 'download_youtube_audio':
            return await this.handleDownloadYouTubeAudio(request.params.arguments);

          case 'download_youtube_video':
            return await this.handleDownloadYouTubeVideo(request.params.arguments);

          case 'get_llm_stats':
            return await this.handleGetLLMStats();

          case 'list_files':
            return await this.handleListFiles();

          case 'get_file_info':
            return await this.handleGetFileInfo(request.params.arguments);

          case 'get_registry_status':
            return await this.handleGetRegistryStatus();

          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Unknown tool: ${request.params.name}`
            );
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        throw new McpError(ErrorCode.InternalError, errorMessage);
      }
    });
  }

  private async handleCreateMusicVideo(args: any) {
    // Resolve file IDs to actual paths
    const videoPath = this.fileManager.resolveFileId(args.video_file) || args.video_file;
    const audioPath = this.fileManager.resolveFileId(args.audio_file) || args.audio_file;

    const result = await this.videoProcessor.processVideo({
      input_file: videoPath,
      output_file: args.output_file,
      operation: 'create_music_video',
      parameters: {
        audio_file: audioPath,
        duration: args.duration,
        start_time: args.start_time,
      },
    });

    return {
      content: [{
        type: 'text',
        text: JSON.stringify(result, null, 2),
      }],
    };
  }

  private async handleProcessVideoFile(args: any) {
    // Resolve file ID to actual path
    const inputPath = this.fileManager.resolveFileId(args.input_file) || args.input_file;

    const result = await this.videoProcessor.processVideo({
      input_file: inputPath,
      output_file: args.output_file,
      operation: args.operation,
      parameters: args.parameters || {},
    });

    return {
      content: [{
        type: 'text',
        text: JSON.stringify(result, null, 2),
      }],
    };
  }

  private async handleDownloadYouTubeAudio(args: any) {
    const result = await this.youtubeDownloader.downloadVideo({
      url: args.url,
      output_dir: args.output_dir,
      format: args.format,
      audio_only: true,
      max_duration: args.max_duration,
    });

    return {
      content: [{
        type: 'text',
        text: JSON.stringify(result, null, 2),
      }],
    };
  }

  private async handleDownloadYouTubeVideo(args: any) {
    const result = await this.youtubeDownloader.downloadVideo({
      url: args.url,
      output_dir: args.output_dir,
      format: args.format,
      audio_only: false,
      max_duration: args.max_duration,
    });

    return {
      content: [{
        type: 'text',
        text: JSON.stringify(result, null, 2),
      }],
    };
  }

  private async handleGetLLMStats() {
    const stats = {
      primary_model: {
        provider: this.llmClient.provider,
        model: this.llmClient.model,
      },
      fallback_model: {
        provider: this.fallbackClient.provider,
        model: this.fallbackClient.model,
      },
      estimated_costs: {
        primary_per_1k_tokens: this.llmClient.estimateCost(1000),
        fallback_per_1k_tokens: this.fallbackClient.estimateCost(1000),
      },
    };

    return {
      content: [{
        type: 'text',
        text: JSON.stringify(stats, null, 2),
      }],
    };
  }

  private async handleListFiles() {
    const files = await this.fileManager.listFiles();

    return {
      content: [{
        type: 'text',
        text: JSON.stringify({ files }, null, 2),
      }],
    };
  }

  private async handleGetFileInfo(args: any) {
    const fileInfo = await this.fileManager.getFileInfo(args.file_id);

    if (!fileInfo) {
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({ error: `File not found: ${args.file_id}` }, null, 2),
        }],
      };
    }

    return {
      content: [{
        type: 'text',
        text: JSON.stringify({ file: fileInfo }, null, 2),
      }],
    };
  }

  private async handleGetRegistryStatus() {
    const status = this.fileManager.getRegistryStatus();

    return {
      content: [{
        type: 'text',
        text: JSON.stringify({ registry: status }, null, 2),
      }],
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
  }
}

async function main() {
  const server = new HaikuMCPServer();
  await server.initialize();
  await server.run();
}

// Export for testing
export { HaikuMCPServer };

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}