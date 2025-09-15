/**
 * Factory Functions for Haiku MCP Server
 * 
 * Provides convenient factory functions to create and configure
 * Haiku MCP Server instances with different configuration patterns.
 */

import { HaikuMCPServer } from './server.js';
import type { Config } from './config.js';

/**
 * Partial configuration interface for factory functions
 */
export interface HaikuServerConfig {
  llm?: {
    primary?: 'anthropic' | 'gemini';
    fallback?: 'anthropic' | 'gemini';
  };
  ffmpeg?: {
    outputDir?: string;
    tempDir?: string;
    quality?: string;
    maxDuration?: number;
  };
  youtube?: {
    outputDir?: string;
    maxDuration?: number;
    quality?: string;
  };
  registry?: {
    cacheDir?: string;
    maxFileSize?: string;
  };
  response_limits?: {
    max_tokens?: number;
    strip_metadata?: boolean;
  };
}

/**
 * Create a Haiku MCP Server with custom configuration
 * 
 * This is the recommended way to create a server instance when you need
 * custom configuration that differs from the default config.yaml setup.
 * 
 * @param config Partial configuration to override defaults
 * @returns Initialized HaikuMCPServer instance
 */
export async function createHaikuServer(config?: HaikuServerConfig): Promise<HaikuMCPServer> {
  const server = new HaikuMCPServer();
  
  if (config) {
    // Apply custom configuration
    server.setCustomConfig(config);
  }
  
  await server.initialize();
  return server;
}

/**
 * Create a Haiku MCP Server with completely custom configuration
 * 
 * This function allows you to provide a complete configuration object,
 * bypassing the default config loading mechanism entirely.
 * 
 * @param fullConfig Complete configuration object
 * @returns Initialized HaikuMCPServer instance
 */
export async function createCustomServer(fullConfig: Config): Promise<HaikuMCPServer> {
  const server = new HaikuMCPServer();
  server.setFullConfig(fullConfig);
  await server.initialize();
  return server;
}

/**
 * Create a minimal Haiku MCP Server for development/testing
 * 
 * Creates a server with minimal configuration suitable for development
 * and testing environments. Uses fallback modes when API keys are missing.
 * 
 * @returns Initialized HaikuMCPServer instance
 */
export async function createDevServer(): Promise<HaikuMCPServer> {
  const devConfig: HaikuServerConfig = {
    llm: {
      primary: 'anthropic',
      fallback: 'gemini'
    },
    ffmpeg: {
      outputDir: '/tmp/haiku-dev',
      tempDir: '/tmp/haiku-dev/temp',
      quality: 'medium',
      maxDuration: 60 // 1 minute for dev
    },
    registry: {
      cacheDir: '/tmp/haiku-dev/registry'
    },
    response_limits: {
      max_tokens: 1000,
      strip_metadata: true
    }
  };
  
  return createHaikuServer(devConfig);
}

/**
 * Create a production-optimized Haiku MCP Server
 * 
 * Creates a server with production-ready configuration including
 * proper error handling, logging, and resource limits.
 * 
 * @param outputDir Production output directory
 * @returns Initialized HaikuMCPServer instance
 */
export async function createProductionServer(outputDir: string): Promise<HaikuMCPServer> {
  const prodConfig: HaikuServerConfig = {
    llm: {
      primary: 'anthropic',
      fallback: 'gemini'
    },
    ffmpeg: {
      outputDir,
      tempDir: `${outputDir}/temp`,
      quality: 'high',
      maxDuration: 600 // 10 minutes max
    },
    registry: {
      cacheDir: `${outputDir}/registry`,
      maxFileSize: '500MB'
    },
    response_limits: {
      max_tokens: 2000,
      strip_metadata: false // Keep full metadata in production
    }
  };
  
  return createHaikuServer(prodConfig);
}