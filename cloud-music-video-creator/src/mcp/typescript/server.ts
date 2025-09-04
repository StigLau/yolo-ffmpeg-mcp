#!/usr/bin/env node

/**
 * Cloud Music Video Creator - TypeScript MCP Server
 * Simple, direct implementation
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

interface KompositionSpec {
  title: string;
  description: string;
  bpm: number;
  duration_seconds: number;
  user_id: string;
  audio_file_path?: string;
  visual_concept?: string;
}

interface Komposition {
  id: string;
  title: string;
  description?: string;
  user_id: string;
  bpm: number;
  duration_seconds: number;
  status: string;
  created_at: string;
  segments: any[];
  generated_videos: any[];
}

// Simple in-memory storage
const kompositions: Map<string, Komposition> = new Map();
const mediaFiles: Map<string, any> = new Map();

function generateId(): string {
  return Math.random().toString(36).substring(2, 15);
}

const server = new Server(
  {
    name: 'cloud-music-video-creator',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'create_komposition',
        description: 'Create a new komposition from basic parameters',
        inputSchema: {
          type: 'object',
          properties: {
            title: { type: 'string' },
            description: { type: 'string' },
            user_id: { type: 'string' },
            bpm: { type: 'number' },
            duration_seconds: { type: 'number' },
            audio_file_path: { type: 'string' },
            visual_concept: { type: 'string' },
          },
          required: ['title', 'description', 'user_id', 'bpm', 'duration_seconds'],
        },
      },
      {
        name: 'get_komposition',
        description: 'Retrieve komposition by ID',
        inputSchema: {
          type: 'object',
          properties: {
            komposition_id: { type: 'string' },
          },
          required: ['komposition_id'],
        },
      },
      {
        name: 'update_komposition',
        description: 'Update existing komposition',
        inputSchema: {
          type: 'object',
          properties: {
            komposition_id: { type: 'string' },
            updates: { type: 'object' },
          },
          required: ['komposition_id', 'updates'],
        },
      },
      {
        name: 'list_user_kompositions',
        description: 'List all kompositions for a user',
        inputSchema: {
          type: 'object',
          properties: {
            user_id: { type: 'string' },
          },
          required: ['user_id'],
        },
      },
      {
        name: 'register_media_file',
        description: 'Register a media file',
        inputSchema: {
          type: 'object',
          properties: {
            file_path: { type: 'string' },
            media_type: { type: 'string' },
            metadata: { type: 'object' },
          },
          required: ['file_path', 'media_type'],
        },
      },
      {
        name: 'process_komposition_video',
        description: 'Generate video for komposition',
        inputSchema: {
          type: 'object',
          properties: {
            komposition_id: { type: 'string' },
            processing_options: { type: 'object' },
          },
          required: ['komposition_id'],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'create_komposition': {
        const spec = args as any as KompositionSpec;
        const id = generateId();
        const komposition: Komposition = {
          id,
          title: spec.title,
          description: spec.description,
          user_id: spec.user_id,
          bpm: spec.bpm,
          duration_seconds: spec.duration_seconds,
          status: 'draft',
          created_at: new Date().toISOString(),
          segments: [],
          generated_videos: [],
        };
        
        kompositions.set(id, komposition);
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(komposition, null, 2),
            },
          ],
        };
      }

      case 'get_komposition': {
        const { komposition_id } = args as { komposition_id: string };
        const komposition = kompositions.get(komposition_id);
        
        if (!komposition) {
          throw new Error(`Komposition ${komposition_id} not found`);
        }
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(komposition, null, 2),
            },
          ],
        };
      }

      case 'update_komposition': {
        const { komposition_id, updates } = args as { 
          komposition_id: string; 
          updates: Record<string, any> 
        };
        
        const komposition = kompositions.get(komposition_id);
        if (!komposition) {
          throw new Error(`Komposition ${komposition_id} not found`);
        }
        
        // Update komposition
        Object.assign(komposition, updates);
        kompositions.set(komposition_id, komposition);
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(komposition, null, 2),
            },
          ],
        };
      }

      case 'list_user_kompositions': {
        const { user_id } = args as { user_id: string };
        const userKompositions = Array.from(kompositions.values())
          .filter(k => k.user_id === user_id);
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(userKompositions, null, 2),
            },
          ],
        };
      }

      case 'register_media_file': {
        const { file_path, media_type, metadata } = args as {
          file_path: string;
          media_type: string;
          metadata?: Record<string, any>;
        };
        
        const mediaId = generateId();
        const mediaRef = {
          id: mediaId,
          file_path,
          media_type,
          metadata: metadata || {},
          created_at: new Date().toISOString(),
        };
        
        mediaFiles.set(mediaId, mediaRef);
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(mediaRef, null, 2),
            },
          ],
        };
      }

      case 'process_komposition_video': {
        const { komposition_id, processing_options } = args as {
          komposition_id: string;
          processing_options?: Record<string, any>;
        };
        
        const komposition = kompositions.get(komposition_id);
        if (!komposition) {
          throw new Error(`Komposition ${komposition_id} not found`);
        }
        
        // Simulate video processing
        const videoOutput = {
          id: generateId(),
          komposition_id,
          file_path: `/tmp/music-video-creator/generated-videos/${komposition_id}_${Date.now()}.mp4`,
          generation_timestamp: new Date().toISOString(),
          processing_cost: 0.15,
          quality_score: 0.85,
          processing_duration: 45.2,
          status: 'completed',
        };
        
        // Add to komposition
        komposition.generated_videos.push(videoOutput);
        komposition.status = 'completed';
        kompositions.set(komposition_id, komposition);
        
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(videoOutput, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error instanceof Error ? error.message : String(error)}`,
        },
      ],
      isError: true,
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Cloud Music Video Creator MCP server running on stdio');
}

main().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});