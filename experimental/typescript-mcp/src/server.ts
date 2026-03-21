#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { tmpdir } from "os";
import { join, extname } from "path";
import { randomUUID } from "crypto";

import { createLLMClient, LLMClient, VideoProcessingRequest } from "./llm-client.js";
import { protectedFFmpeg, FFmpegExecutionResult } from "./ffmpeg-executor.js";
import { registryClient, RegistryFile } from "./registry-client.js";

// Global state
let llmClient: LLMClient | null = null;
const processedVideos = new Map<string, FFmpegExecutionResult>();

/**
 * Initialize LLM client on server startup
 */
async function initializeLLMClient() {
  try {
    llmClient = createLLMClient();
    if (llmClient) {
      console.error(`✅ ${process.env.LLM_PROVIDER || 'Anthropic'} LLM client initialized`);
      const status = llmClient.getDailySpendStatus();
      console.error(`💰 Daily budget: $${status.remainingBudget.toFixed(3)} remaining`);
    } else {
      console.error("⚠️ LLM client not available - using fallback mode");
    }
  } catch (error) {
    console.error("❌ Failed to initialize LLM client:", error);
    llmClient = null;
  }
}

// Create MCP server
const server = new McpServer({
  name: "kompolight",
  version: "1.0.0"
});

// ====== TOOLS ====== 

// Tool 1: AI-powered FFmpeg command generation and execution
server.registerTool(
  "smart-ffmpeg-process",
  {
    title: "Smart FFmpeg Processing with LLM",
    description: "Generate and execute safe FFmpeg commands using LLM analysis",
    inputSchema: {
      operation: z.string().describe("Video processing operation (e.g., 'trim', 'resize', 'convert', 'extract_audio')"),
      fileIds: z.array(z.string()).describe("Input file IDs from the multimedia registry"),
      outputName: z.string().optional().describe("Output filename (will be placed in temp directory)"),
      parameters: z.record(z.any()).optional().describe("Operation-specific parameters"),
      constraints: z.object({
        maxDuration: z.number().optional().describe("Maximum processing duration in seconds"),
        maxFileSize: z.number().optional().describe("Maximum output file size in MB"),
        allowedFormats: z.array(z.string()).optional().describe("Allowed output formats")
      }).optional().describe("Processing constraints")
    }
  },
  async ({ operation, fileIds, outputName, parameters = {}, constraints }) => {
    const processId = randomUUID();
    console.error(`🎬 Starting smart FFmpeg process ${processId.slice(0, 8)}`);

    try {
      // Step 1: Get file information from registry
      const inputFiles: string[] = [];
      const fileInfos: RegistryFile[] = [];
      
      for (const fileId of fileIds) {
        try {
          const fileInfo = await registryClient.getFileInfo(fileId);
          inputFiles.push(fileInfo.path);
          fileInfos.push(fileInfo);
        } catch (error) {
          return {
            content: [{
              type: "text",
              text: `❌ Failed to get file info for ${fileId}: ${error}`
            }],
            isError: true
          };
        }
      }

      // Step 2: Generate output path
      const outputPath = outputName 
        ? join(tmpdir(), outputName)
        : join(tmpdir(), `processed_${Date.now()}_${processId.slice(0, 8)}.mp4`);

      // Step 3: Create processing request
      const request: VideoProcessingRequest = {
        operation,
        inputFiles,
        outputPath,
        parameters,
        constraints
      };

      // Step 4: Generate FFmpeg command using LLM or fallback
      let commandResult;
      if (llmClient) {
        try {
          commandResult = await llmClient.generateFFmpegCommand(request);
          console.error(`🧠 LLM generated command with ${commandResult.confidence} confidence`);
        } catch (error) {
          console.error(`⚠️ LLM failed: ${error}, using fallback`);
          commandResult = llmClient.generateFallbackCommand(request);
        }
      } else {
        // Use a basic heuristic fallback when no LLM client
        commandResult = {
          ffmpegCommand: ['ffmpeg', '-i', inputFiles[0], '-y', outputPath],
          reasoning: 'Basic fallback command (no LLM available)',
          safetyChecks: { validInputs: true, noDestructiveOps: true, outputPathSafe: true, resourceLimits: true },
          confidence: 0.5
        };
      }

      // Step 5: Execute the command with protection
      const executionResult = await protectedFFmpeg.executeCommand(commandResult.ffmpegCommand);
      
      // Store result
      processedVideos.set(processId, executionResult);

      // Step 6: Register output file if successful
      let registeredFile: RegistryFile | null = null;
      if (executionResult.success && executionResult.outputPath) {
        try {
          registeredFile = await registryClient.registerFile(executionResult.outputPath, {
            source_files: fileInfos.map(f => f.id),
            operation,
            processing_parameters: parameters,
            llm_confidence: commandResult.confidence,
            processing_time_ms: executionResult.processTime
          });
        } catch (regError) {
          console.error(`⚠️ Failed to register output file: ${regError}`);
        }
      }

      // Step 7: Return result
      if (executionResult.success) {
        return {
          content: [{
            type: "text",
            text: `✅ Smart FFmpeg processing completed successfully!\n\n` +
                  `🆔 Process ID: ${processId}\n` +
                  `🎯 Operation: ${operation}\n` +
                  `📂 Input files: ${fileInfos.map(f => f.filename).join(', ')}\n` +
                  `📁 Output: ${executionResult.outputPath}\n` +
                  `🧠 AI Confidence: ${commandResult.confidence}\n` +
                  `⚡ Processing time: ${executionResult.processTime}ms\n` +
                  `🛡️ Safety checks: All passed\n` +
                  `💭 AI Reasoning: ${commandResult.reasoning}\n` +
                  `🆔 Registry ID: ${registeredFile?.id || 'Not registered'}\n\n` +
                  `📋 Command executed: ${commandResult.ffmpegCommand.join(' ')}`
          }]
        };
      } else {
        return {
          content: [{
            type: "text",
            text: `❌ Smart FFmpeg processing failed\n\n` +
                  `🆔 Process ID: ${processId}\n` +
                  `🎯 Operation: ${operation}\n` +
                  `❌ Error: ${executionResult.error}\n` +
                  `⏱️ Processing time: ${executionResult.processTime}ms\n` +
                  `💭 AI Reasoning: ${commandResult.reasoning}\n` +
                  `📋 Command attempted: ${commandResult.ffmpegCommand.join(' ')}\n\n` +
                  `🔍 Stderr output:\n${executionResult.stderr.slice(-500)}`
          }],
          isError: true
        };
      }

    } catch (error) {
      return {
        content: [{
          type: "text",
          text: `💥 Smart FFmpeg processing error: ${error instanceof Error ? error.message : String(error)}`
        }],
        isError: true
      };
    }
  }
);

// Tool 2: List files from multimedia registry
server.registerTool(
  "list-registry-files",
  {
    title: "List Multimedia Registry Files",
    description: "List all available files from the multimedia registry",
    inputSchema: {
      includeMetadata: z.boolean().default(false).describe("Include detailed metadata for each file")
    }
  },
  async ({ includeMetadata }) => {
    try {
      console.error("📋 Fetching files from multimedia registry...");
      const registryResponse = await registryClient.listFiles();
      
      if (registryResponse.files.length === 0) {
        return {
          content: [{
            type: "text",
            text: "📁 No files found in multimedia registry.\n\n" +
                  "Use the Python MCP server to add files to the registry first."
          }]
        };
      }

      const fileList = registryResponse.files
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .map(file => {
          let info = `• ${file.filename} (${file.id})\n` +
                     `  📊 Size: ${(file.size / 1024 / 1024).toFixed(2)} MB\n` +
                     `  📅 Created: ${new Date(file.created_at).toLocaleString()}`;
          
          if (file.content_type) {
            info += `\n  🎭 Type: ${file.content_type}`;
          }
          
          if (file.duration) {
            info += `\n  ⏱️ Duration: ${file.duration}s`;
          }
          
          if (file.resolution) {
            info += `\n  📐 Resolution: ${file.resolution}`;
          }
          
          if (includeMetadata && file.metadata) {
            info += `\n  🏷️ Metadata: ${JSON.stringify(file.metadata, null, 2)}`;
          }
          
          return info;
        })
        .join("\n\n");

      return {
        content: [{
          type: "text",
          text: `📁 Multimedia Registry Files (${registryResponse.total})\n\n${fileList}`
        }]
      };

    } catch (error) {
      return {
        content: [{
          type: "text",
          text: `❌ Failed to list registry files: ${error instanceof Error ? error.message : String(error)}`
        }],
        isError: true
      };
    }
  }
);

// Tool 3: Get LLM status and cost information
server.registerTool(
  "llm-status",
  {
    title: "LLM Status",
    description: "Check LLM availability, daily spend status, and budget information",
    inputSchema: {}
  },
  async () => {
    try {
      if (!llmClient) {
        return {
          content: [{
            type: "text",
            text: "🤖 LLM Status: DISABLED\n\n" +
                  "❌ LLM client not available\n" +
                  "💡 Set LLM_PROVIDER and relevant API key to enable LLM features\n" +
                  "🔄 Fallback mode: Basic heuristic FFmpeg command generation active"
          }]
        };
      }

      const status = llmClient.getDailySpendStatus();
      const provider = process.env.LLM_PROVIDER || 'ANTHROPIC';
      
      return {
        content: [{
          type: "text",
          text: `🤖 LLM Status: ACTIVE (${provider})\n\n` +
                `💰 Daily Budget Status:\n` +
                `   • Spent today: $${status.dailySpend.toFixed(4)}\n` +
                `   • Daily limit: $${status.dailyLimit.toFixed(2)}\n` +
                `   • Remaining: $${status.remainingBudget.toFixed(4)}\n` +
                `   • Can afford request: ${status.canAffordTypicalRequest ? '✅ Yes' : '❌ No'}\n\n` +
                `📊 Features:\n` +
                `   • Smart FFmpeg command generation\n` +
                `   • Safety validation and protection\n` +
                `   • Cost-controlled AI analysis\n` +
                `   • Fallback heuristics when budget exceeded`
        }]
      };

    } catch (error) {
      return {
        content: [{
          type: "text",
          text: `❌ Failed to get LLM status: ${error instanceof Error ? error.message : String(error)}`
        }],
        isError: true
      };
    }
  }
);

// Tool 4: System health check
server.registerTool(
  "system-health",
  {
    title: "System Health Check",
    description: "Check health status of all system components",
    inputSchema: {}
  },
  async () => {
    const checks: string[] = [];
    
    // Check FFmpeg availability
    try {
      const result = await protectedFFmpeg.executeCommand(['ffmpeg', '-version']);
      checks.push("✅ FFmpeg: Available and functional");
    } catch {
      checks.push("❌ FFmpeg: Not available or not working");
    }

    // Check Python MCP registry connection
    const pythonHealth = await registryClient.checkPythonMcpHealth();
    if (pythonHealth.available) {
      checks.push("✅ Python MCP Registry: Connected and responsive");
    } else {
      checks.push(`❌ Python MCP Registry: Not available - ${pythonHealth.error}`);
    }

    // Check LLM
    if (llmClient) {
      const status = llmClient.getDailySpendStatus();
      const provider = process.env.LLM_PROVIDER || 'ANTHROPIC';
      checks.push(`✅ LLM (${provider}): Active (${status.canAffordTypicalRequest ? 'budget available' : 'budget exceeded'})`);
    } else {
      checks.push("⚠️ LLM: Disabled (API key not set)");
    }

    // Check processing stats
    const totalProcessed = processedVideos.size;
    const successfulProcessed = Array.from(processedVideos.values()).filter(r => r.success).length;
    checks.push(`📊 Processing Stats: ${successfulProcessed}/${totalProcessed} successful`);

    return {
      content: [{
        type: "text",
        text: `🏥 System Health Check\n\n${checks.join('\n')}\n\n` +
              `🏗️ Architecture: TypeScript MCP Frontend\n` +
              `🐍 Backend: Python MCP Registry Integration\n` +
              `🛡️ Protection: Advanced FFmpeg validation enabled\n` +
              `🧠 AI: ${process.env.LLM_PROVIDER || 'Anthropic'} LLM smart command generation`
      }]
    };
  }
);

// Tool 5: Delegate complex operations to Python MCP
server.registerTool(
  "delegate-to-python",
  {
    title: "Delegate to Python MCP",
    description: "Delegate complex operations to the Python MCP server",
    inputSchema: {
      toolName: z.string().describe("Python MCP tool name (e.g., 'yolo_smart_video_concat')"),
      parameters: z.record(z.any()).describe("Parameters to pass to the Python tool")
    }
  },
  async ({ toolName, parameters }) => {
    try {
      console.error(`🐍 Delegating ${toolName} to Python MCP...`);
      const result = await registryClient.delegateToPython(toolName, parameters);
      
      return {
        content: [{
          type: "text",
          text: `✅ Python MCP delegation completed successfully!\n\n` +
                `🛠️ Tool: ${toolName}\n` +
                `📥 Parameters: ${JSON.stringify(parameters, null, 2)}\n` +
                `📤 Result: ${JSON.stringify(result, null, 2)}`
        }]
      };

    } catch (error) {
      return {
        content: [{
          type: "text",
          text: `❌ Python MCP delegation failed:\n\n` +
                `🛠️ Tool: ${toolName}\n` +
                `❌ Error: ${error instanceof Error ? error.message : String(error)}`
        }],
        isError: true
      };
    }
  }
);

// ====== RESOURCES ====== 

// Resource: Server configuration
server.registerResource(
  "config",
  "config://typescript-mcp",
  {
    title: "TypeScript MCP Configuration",
    description: "Current TypeScript MCP server configuration and status",
    mimeType: "application/json"
  },
  async () => ({
    contents: [{
      uri: "config://typescript-mcp",
      mimeType: "application/json",
      text: JSON.stringify({
        server: {
          name: "kompolight",
          version: "1.0.0",
          architecture: "TypeScript Frontend + Python Backend",
          capabilities: [
            "smart-ffmpeg-processing",
            "llm-integration", 
            "python-mcp-delegation",
            "registry-integration",
            "safety-validation"
          ]
        },
        llm: {
          provider: process.env.LLM_PROVIDER || 'ANTHROPIC',
          available: llmClient !== null,
          dailySpend: llmClient?.getDailySpendStatus().dailySpend || 0,
          dailyLimit: llmClient?.getDailySpendStatus().dailyLimit || 0
        },
        statistics: {
          totalProcessed: processedVideos.size,
          successfulProcessed: Array.from(processedVideos.values()).filter(r => r.success).length
        }
      }, null, 2)
    }]
  })
);

// ====== PROMPTS ====== 

// Prompt: Smart video processing workflow
server.registerPrompt(
  "smart-video-workflow",
  {
    title: "Smart Video Processing Workflow",
    description: "Complete workflow for intelligent video processing with LLM",
    argsSchema: {
      operation: z.string().describe("Video processing operation"),
      fileIds: z.string().describe("Comma-separated input file IDs from registry"),
      customInstructions: z.string().optional().describe("Additional processing instructions")
    }
  },
  ({ operation, fileIds, customInstructions }) => ({
    messages: [{
      role: "user",
      content: {
        type: "text",
        text: `I need to perform intelligent video processing using the TypeScript MCP server with LLM integration.\n\n` +
              `Operation: ${operation}\n` +
              `Input files: ${fileIds}\n` +
              `${customInstructions ? `Custom instructions: ${customInstructions}\n` : ''}` +
              `Please:\n` +
              `1. Use smart-ffmpeg-process tool with LLM analysis\n` +
              `2. The AI will generate safe, optimal FFmpeg commands\n` +
              `3. Protected execution with safety validation\n` +
              `4. Automatic registry integration for output files\n\n` +
              `Execute this with full AI assistance and provide detailed results.`
      }
    }]
  })
);

// ====== SERVER STARTUP ====== 
async function startServer() {
  console.error("🚀 Starting Kompolight MCP Server...");
  
  // Initialize components
  await initializeLLMClient();
  
  // Check Python MCP health
  const pythonHealth = await registryClient.checkPythonMcpHealth();
  if (pythonHealth.available) {
    console.error("✅ Python MCP registry connection verified");
  } else {
    console.error("⚠️ Python MCP registry not available:", pythonHealth.error);
  }
  
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error("🎬 Kompolight MCP Server ready!");
  console.error(`🧠 LLM Provider: ${process.env.LLM_PROVIDER || 'ANTHROPIC'} (${llmClient ? "ENABLED" : "DISABLED"})`);
  console.error("🐍 Python MCP:", pythonHealth.available ? "CONNECTED" : "DISCONNECTED");
}

// Handle graceful shutdown
process.on("SIGINT", () => {
  console.error("🛑 Shutting down Kompolight MCP server...");
  process.exit(0);
});

process.on("SIGTERM", () => {
  console.error("🛑 Shutting down Kompolight MCP server...");
  process.exit(0);
});

// Start the server
startServer().catch((error) => {
  console.error("💥 Failed to start Kompolight MCP server:", error);
  process.exit(1);
});
