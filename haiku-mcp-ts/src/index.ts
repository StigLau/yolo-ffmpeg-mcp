/**
 * Haiku MCP Server - Package Entry Point
 * 
 * This is the main entry point for the @kompo/haiku-mcp-server package.
 * It provides multiple export patterns to support different usage scenarios.
 */

// Primary exports - Server classes and factory functions
export { HaikuMCPServer } from './server.js';
export { createHaikuServer, createCustomServer } from './factory.js';

// Individual components for custom implementations
export { VideoProcessor } from './tools/video-processor.js';
export { YouTubeDownloader } from './tools/youtube-downloader.js';
export { FileManager } from './registry/file-manager.js';

// LLM clients
export { HaikuClient } from './llm/haiku-client.js';
export { GeminiFlashClient } from './llm/gemini-client.js';

// Configuration utilities
export { loadConfig } from './config.js';

// Type exports for TypeScript consumers
export type { BaseLLMClient, LLMResponse } from './llm/types.js';

// Re-export config types from config.ts
export type { 
  Config,
  LLMConfig, 
  FFMPEGConfig,
  YouTubeConfig,
  ResponseLimits 
} from './config.js';

// Utility exports
export { sanitizeResponse } from './utils/sanitization.js';