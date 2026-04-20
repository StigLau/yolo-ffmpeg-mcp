/**
 * Simple HTTP Bridge for Haiku MCP Server
 * Provides REST API wrapper around MCP stdio transport
 */

import express from 'express';
import { spawn, ChildProcess } from 'child_process';
import { randomUUID } from 'crypto';

interface MCPRequest {
  jsonrpc: '2.0';
  id: string | number;
  method: string;
  params?: any;
}

interface MCPResponse {
  jsonrpc: '2.0';
  id: string | number;
  result?: any;
  error?: any;
}

class MCPHttpBridge {
  private app: express.Application;
  private mcpProcess: ChildProcess | null = null;
  private pendingRequests = new Map<string | number, express.Response>();

  constructor() {
    this.app = express();
    this.app.use(express.json());
    this.setupRoutes();
  }

  private setupRoutes() {
    // Generic tool call endpoint
    this.app.post('/api/mcp/call-tool', async (req, res) => {
      const { tool, arguments: args } = req.body;

      if (!tool) {
        return res.status(400).json({ error: 'Missing tool parameter' });
      }

      try {
        await this.ensureMCPProcess();
        const response = await this.callMCPTool(tool, args || {});
        res.json(response);
      } catch (error) {
        res.status(500).json({
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    });

    // List available tools
    this.app.get('/api/mcp/list-tools', async (req, res) => {
      try {
        await this.ensureMCPProcess();
        const response = await this.listMCPTools();
        res.json(response);
      } catch (error) {
        res.status(500).json({
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    });

    // Health check
    this.app.get('/api/health', (req, res) => {
      res.json({
        status: 'ok',
        mcpProcess: this.mcpProcess ? 'running' : 'stopped',
        timestamp: new Date().toISOString()
      });
    });
  }

  private async ensureMCPProcess(): Promise<void> {
    if (this.mcpProcess && !this.mcpProcess.killed) {
      return;
    }

    return new Promise((resolve, reject) => {
      // Spawn MCP server process
      this.mcpProcess = spawn('bun', ['run', 'dist/server.js'], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: {
          ...process.env,
          ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY,
          GEMINI_API_KEY: process.env.GEMINI_API_KEY
        }
      });

      if (!this.mcpProcess.stdout || !this.mcpProcess.stdin) {
        reject(new Error('Failed to create MCP process stdio'));
        return;
      }

      // Handle stdout responses
      this.mcpProcess.stdout.on('data', (data) => {
        const lines = data.toString().split('\n').filter(Boolean);

        for (const line of lines) {
          try {
            const response: MCPResponse = JSON.parse(line);
            const res = this.pendingRequests.get(response.id);

            if (res) {
              this.pendingRequests.delete(response.id);

              if (response.error) {
                res.status(500).json({ error: response.error });
              } else {
                res.json(response.result);
              }
            }
          } catch (parseError) {
            console.error('Failed to parse MCP response:', line);
          }
        }
      });

      // Handle process errors
      this.mcpProcess.on('error', (error) => {
        console.error('MCP process error:', error);
        reject(error);
      });

      this.mcpProcess.stderr?.on('data', (data) => {
        console.error('MCP stderr:', data.toString());
      });

      // Wait for initialization
      setTimeout(() => {
        if (this.mcpProcess && !this.mcpProcess.killed) {
          resolve();
        } else {
          reject(new Error('MCP process failed to start'));
        }
      }, 2000);
    });
  }

  private async callMCPTool(toolName: string, args: any): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!this.mcpProcess?.stdin) {
        reject(new Error('MCP process not available'));
        return;
      }

      const id = randomUUID();
      const request: MCPRequest = {
        jsonrpc: '2.0',
        id,
        method: 'tools/call',
        params: {
          name: toolName,
          arguments: args
        }
      };

      // Store resolver for response handling
      this.pendingRequests.set(id, {
        json: resolve,
        status: () => ({ json: reject })
      } as any);

      // Send request
      this.mcpProcess.stdin.write(JSON.stringify(request) + '\n');

      // Timeout after 30 seconds
      setTimeout(() => {
        if (this.pendingRequests.has(id)) {
          this.pendingRequests.delete(id);
          reject(new Error('MCP tool call timeout'));
        }
      }, 30000);
    });
  }

  private async listMCPTools(): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!this.mcpProcess?.stdin) {
        reject(new Error('MCP process not available'));
        return;
      }

      const id = randomUUID();
      const request: MCPRequest = {
        jsonrpc: '2.0',
        id,
        method: 'tools/list'
      };

      // Store resolver for response handling
      this.pendingRequests.set(id, {
        json: resolve,
        status: () => ({ json: reject })
      } as any);

      // Send request
      this.mcpProcess.stdin.write(JSON.stringify(request) + '\n');

      // Timeout after 10 seconds
      setTimeout(() => {
        if (this.pendingRequests.has(id)) {
          this.pendingRequests.delete(id);
          reject(new Error('MCP tools list timeout'));
        }
      }, 10000);
    });
  }

  public start(port: number = 3001): void {
    this.app.listen(port, () => {
      console.log(`🚀 MCP HTTP Bridge running on port ${port}`);
      console.log(`📋 List tools: GET http://localhost:${port}/api/mcp/list-tools`);
      console.log(`🔧 Call tool: POST http://localhost:${port}/api/mcp/call-tool`);
      console.log(`❤️  Health check: GET http://localhost:${port}/api/health`);
    });
  }

  public stop(): void {
    if (this.mcpProcess) {
      this.mcpProcess.kill();
      this.mcpProcess = null;
    }
  }
}

// Example usage
if (import.meta.url === `file://${process.argv[1]}`) {
  const bridge = new MCPHttpBridge();
  bridge.start(3001);

  // Graceful shutdown
  process.on('SIGINT', () => {
    console.log('Shutting down HTTP bridge...');
    bridge.stop();
    process.exit(0);
  });
}

export default MCPHttpBridge;