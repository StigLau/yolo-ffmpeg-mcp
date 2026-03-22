/**
 * Configuration management for Haiku MCP Server
 */

import { readFile } from 'fs/promises';
import { parse } from 'yaml';
import { z } from 'zod';

// Configuration schemas
const ServerConfigSchema = z.object({
  name: z.string(),
  version: z.string(),
  port: z.number().optional(),
});

const LLMConfigSchema = z.object({
  primary: z.string(),
  fallback: z.string(),
  timeout_seconds: z.number(),
  max_retries: z.number(),
});

const ModelConfigSchema = z.object({
  provider: z.enum(['anthropic', 'google']),
  model: z.string(),
  api_key: z.string(),
  max_tokens: z.number(),
});

const FFMPEGConfigSchema = z.object({
  timeout_seconds: z.number(),
  temp_directory: z.string(),
  cleanup_on_exit: z.boolean(),
});

const YouTubeConfigSchema = z.object({
  timeout_seconds: z.number(),
  max_duration_seconds: z.number(),
  quality: z.string(),
});

const LoggingConfigSchema = z.object({
  level: z.enum(['DEBUG', 'INFO', 'WARN', 'ERROR']),
  include_ffmpeg_logs: z.boolean(),
  sanitize_responses: z.boolean(),
});

const ResponseLimitsSchema = z.object({
  max_tokens: z.number(),
  strip_metadata: z.boolean(),
  include_performance_stats: z.boolean(),
});

const ConfigSchema = z.object({
  server: ServerConfigSchema,
  llm: LLMConfigSchema,
  models: z.record(ModelConfigSchema),
  ffmpeg: FFMPEGConfigSchema,
  youtube: YouTubeConfigSchema,
  logging: LoggingConfigSchema,
  response_limits: ResponseLimitsSchema,
});

// Types
export type ServerConfig = z.infer<typeof ServerConfigSchema>;
export type LLMConfig = z.infer<typeof LLMConfigSchema>;
export type ModelConfig = z.infer<typeof ModelConfigSchema>;
export type FFMPEGConfig = z.infer<typeof FFMPEGConfigSchema>;
export type YouTubeConfig = z.infer<typeof YouTubeConfigSchema>;
export type LoggingConfig = z.infer<typeof LoggingConfigSchema>;
export type ResponseLimits = z.infer<typeof ResponseLimitsSchema>;
export type Config = z.infer<typeof ConfigSchema>;

/**
 * Expand environment variables in string values
 */
function expandEnvVars(value: unknown): unknown {
  if (typeof value === 'string') {
    return value.replace(/\$\{([^}]+)\}/g, (_, varName) => {
      return process.env[varName] || '';
    });
  }
  
  if (Array.isArray(value)) {
    return value.map(expandEnvVars);
  }
  
  if (value && typeof value === 'object') {
    const expanded: Record<string, unknown> = {};
    for (const [key, val] of Object.entries(value)) {
      expanded[key] = expandEnvVars(val);
    }
    return expanded;
  }
  
  return value;
}

/**
 * Load configuration from YAML file
 */
export async function loadConfig(configPath?: string): Promise<Config> {
  const defaultPath = configPath || './config/config.yaml';
  
  try {
    const configFile = await readFile(defaultPath, 'utf-8');
    const rawConfig = parse(configFile);
    
    // Expand environment variables
    const expandedConfig = expandEnvVars(rawConfig);
    
    // Validate and parse
    const config = ConfigSchema.parse(expandedConfig);
    
    return config;
  } catch (error) {
    if (error instanceof Error && 'code' in error && error.code === 'ENOENT') {
      // Try example config as fallback
      try {
        const examplePath = './config/config.example.yaml';
        const configFile = await readFile(examplePath, 'utf-8');
        const rawConfig = parse(configFile);
        const expandedConfig = expandEnvVars(rawConfig);
        const config = ConfigSchema.parse(expandedConfig);
        
        console.warn(`Using example config from ${examplePath}`);
        return config;
      } catch (exampleError) {
        throw new Error(`Failed to load config: ${error.message}`);
      }
    }
    
    throw error;
  }
}