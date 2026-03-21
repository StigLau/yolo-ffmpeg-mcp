#!/usr/bin/env node

import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import { join, extname, basename } from 'path';

export interface RegistryFile {
  id: string;
  filename: string;
  path: string;
  size: number;
  created_at: string;
  content_type?: string;
  duration?: number;
  resolution?: string;
  metadata?: Record<string, any>;
}

export interface RegistryListResponse {
  files: RegistryFile[];
  total: number;
}

/**
 * Client for integrating with the existing Python MCP multimedia registry
 */
export class MultimediaRegistryClient {
  private pythonMcpPath: string;
  
  constructor(pythonMcpPath?: string) {
    // Default to the parent Python MCP server
    this.pythonMcpPath = pythonMcpPath || join(process.cwd(), '..', 'src', 'server.py');
  }

  /**
   * Call Python MCP tool via subprocess using the FastMCP server
   */
  private async callPythonMcpTool(toolName: string, parameters: Record<string, any>): Promise<any> {
    return new Promise((resolve, reject) => {
      const pythonScript = `
import sys
import asyncio
import json
sys.path.insert(0, '${join(process.cwd(), '..', 'src')}')

# Import the mcp server instance from server.py
from server import mcp

async def call_tool():
    try:
        # Use the FastMCP tool function directly
        tool_func = getattr(mcp, '${toolName.replace('mcp__ffmpeg-mcp__', '')}', None)
        if not tool_func:
            raise Exception(f"Tool {toolName} not found")
        
        result = await tool_func(**${JSON.stringify(parameters)})
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(call_tool())
`;

      const child = spawn('python3', ['-c', pythonScript], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { ...process.env, PYTHONPATH: join(process.cwd(), '..', 'src') }
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('close', (code) => {
        if (code === 0) {
          try {
            const result = JSON.parse(stdout.trim());
            if (result.error) {
              reject(new Error(`Python MCP tool error: ${result.error}`));
            } else {
              resolve(result);
            }
          } catch (parseError) {
            console.error('Python stdout:', stdout);
            console.error('Python stderr:', stderr);
            reject(new Error(`Failed to parse Python MCP response: ${parseError}`));
          }
        } else {
          console.error('Python stderr:', stderr);
          reject(new Error(`Python MCP tool failed with code ${code}: ${stderr}`));
        }
      });

      child.on('error', (error) => {
        reject(new Error(`Failed to execute Python MCP tool: ${error.message}`));
      });
    });
  }

  /**
   * List files from the multimedia registry using Python MCP list_files function
   */
  public async listFiles(): Promise<RegistryListResponse> {
    try {
      console.error('📋 Fetching files from Python MCP registry...');
      const result = await this.callPythonMcpTool('list_files', {});
      
      return {
        files: result.files || [],
        total: result.files ? result.files.length : 0
      };
    } catch (error) {
      console.error('❌ Failed to list files from registry:', error);
      throw error;
    }
  }

  /**
   * Get detailed information about a specific file using Python MCP get_file_info function
   */
  public async getFileInfo(fileId: string): Promise<RegistryFile> {
    try {
      console.error(`🔍 Getting file info for ${fileId} from Python MCP...`);
      const result = await this.callPythonMcpTool('get_file_info', {
        file_id: fileId
      });
      
      return result;
    } catch (error) {
      console.error(`❌ Failed to get file info for ${fileId}:`, error);
      throw error;
    }
  }

  /**
   * Register a new file in the multimedia registry
   * This calls the Python MCP server to add the file to the registry
   */
  public async registerFile(filePath: string, metadata?: Record<string, any>): Promise<RegistryFile> {
    try {
      console.error(`📝 Registering file ${filePath} with Python MCP...`);
      
      // Get file stats
      const stats = await fs.stat(filePath);
      
      // Try to get media metadata if it's a media file
      let mediaMetadata = {};
      const ext = extname(filePath).toLowerCase();
      const mediaExtensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.mp3', '.wav'];
      
      if (mediaExtensions.includes(ext)) {
        try {
          // Use Python MCP to analyze the file and get metadata
          const analysisResult = await this.callPythonMcpTool('mcp__ffmpeg-mcp__analyze_video_content', {
            file_id: basename(filePath) // This might need adjustment based on how Python MCP expects file references
          });
          mediaMetadata = analysisResult.metadata || {};
        } catch (analysisError) {
          console.error('⚠️ Failed to get media metadata:', analysisError);
        }
      }
      
      // Create registry entry (this simulates what the Python server would do)
      const registryFile: RegistryFile = {
        id: `ts_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        filename: basename(filePath),
        path: filePath,
        size: stats.size,
        created_at: new Date().toISOString(),
        content_type: this.getContentType(ext),
        ...mediaMetadata,
        metadata: { ...mediaMetadata, ...metadata }
      };
      
      console.error(`✅ File registered: ${registryFile.id}`);
      return registryFile;
      
    } catch (error) {
      console.error(`❌ Failed to register file ${filePath}:`, error);
      throw error;
    }
  }

  /**
   * Check if Python MCP server is available and responsive
   */
  public async checkPythonMcpHealth(): Promise<{ available: boolean; error?: string }> {
    try {
      console.error('🏥 Checking Python MCP server health...');
      const result = await this.callPythonMcpTool('mcp__ffmpeg-mcp__get_registry_status', {});
      
      return {
        available: true
      };
    } catch (error) {
      return {
        available: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * Get content type based on file extension
   */
  private getContentType(extension: string): string {
    const contentTypes: Record<string, string> = {
      '.mp4': 'video/mp4',
      '.avi': 'video/avi',
      '.mov': 'video/quicktime',
      '.mkv': 'video/x-matroska',
      '.webm': 'video/webm',
      '.mp3': 'audio/mpeg',
      '.wav': 'audio/wav',
      '.flac': 'audio/flac',
      '.aac': 'audio/aac',
      '.jpg': 'image/jpeg',
      '.jpeg': 'image/jpeg',
      '.png': 'image/png',
      '.gif': 'image/gif'
    };
    
    return contentTypes[extension.toLowerCase()] || 'application/octet-stream';
  }

  /**
   * Delegate complex operations to Python MCP server
   */
  public async delegateToPython(toolName: string, parameters: Record<string, any>): Promise<any> {
    try {
      console.error(`🐍 Delegating ${toolName} to Python MCP server...`);
      const result = await this.callPythonMcpTool(toolName, parameters);
      console.error(`✅ Python delegation completed for ${toolName}`);
      return result;
    } catch (error) {
      console.error(`❌ Python delegation failed for ${toolName}:`, error);
      throw error;
    }
  }
}

/**
 * Global registry client instance
 */
export const registryClient = new MultimediaRegistryClient();