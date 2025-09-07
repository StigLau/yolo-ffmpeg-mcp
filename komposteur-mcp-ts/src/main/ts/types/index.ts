/**
 * Type definitions for Komposteur MCP Server
 */

import { z } from 'zod';

// Kompost.json schema validation
export const KompostSchema = z.object({
  name: z.string(),
  bpm: z.number().optional(),
  duration: z.number().optional(),
  segments: z.array(z.object({
    source: z.string(),
    start: z.number().optional(),
    duration: z.number().optional(),
    volume: z.number().optional()
  })),
  transitions: z.array(z.object({
    type: z.string(),
    duration: z.number().optional()
  })).optional()
});

export type KompostConfig = z.infer<typeof KompostSchema>;

// YouTube download configuration
export const YouTubeDownloadSchema = z.object({
  url: z.string().url(),
  format: z.enum(['mp4', 'webm', 'best']).default('best'),
  quality: z.enum(['720p', '1080p', 'best', 'worst']).default('best'),
  outputPath: z.string().optional()
});

export type YouTubeDownloadConfig = z.infer<typeof YouTubeDownloadSchema>;

// S3 operation configuration
export const S3ConfigSchema = z.object({
  bucket: z.string(),
  key: z.string(),
  region: z.string().optional(),
  localPath: z.string().optional()
});

export type S3Config = z.infer<typeof S3ConfigSchema>;

// Komposteur JAR execution result
export interface KomposteurResult {
  success: boolean;
  output: string;
  error?: string;
  exitCode: number;
  duration: number;
  outputFiles?: string[];
}

// MCP Tool definitions
export interface MCPToolDefinition {
  name: string;
  description: string;
  inputSchema: {
    type: "object";
    properties: Record<string, unknown>;
    required?: string[];
  };
}

// Processing status
export enum ProcessingStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export interface ProcessingJob {
  id: string;
  status: ProcessingStatus;
  startTime: Date;
  endTime?: Date;
  input: unknown;
  output?: KomposteurResult;
  error?: string;
}