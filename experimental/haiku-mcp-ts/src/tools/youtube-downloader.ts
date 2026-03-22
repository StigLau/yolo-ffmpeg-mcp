/**
 * YouTube downloading tool using yt-dlp with LLM optimization
 */

import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import { join, extname } from 'path';
import { BaseLLMClient, LLMRequest } from '../llm/types.js';
import { sanitizeResponse, SanitizationConfig } from '../utils/sanitization.js';
import type { YouTubeConfig } from '../config.js';

export interface YouTubeDownloadRequest {
  url: string;
  output_dir: string;
  format?: string;
  audio_only?: boolean;
  max_duration?: number;
}

export interface YouTubeDownloadResult {
  success: boolean;
  downloaded_file?: string;
  title?: string;
  duration?: number;
  format?: string;
  execution_time_ms?: number;
  llm_tokens_used?: number;
  llm_cost?: number;
  sanitized_output?: string;
  error?: string;
}

export class YouTubeDownloader {
  constructor(
    private llmClient: BaseLLMClient,
    private config: YouTubeConfig,
    private sanitizationConfig: SanitizationConfig
  ) {}

  async downloadVideo(request: YouTubeDownloadRequest): Promise<YouTubeDownloadResult> {
    const startTime = Date.now();
    
    try {
      // Use LLM to generate optimal yt-dlp command
      const llmRequest: LLMRequest = {
        prompt: this.buildYTDLPPrompt(request),
        max_tokens: 300,
        temperature: 0.1,
      };

      const llmResponse = await this.llmClient.generate(llmRequest);
      
      if (!llmResponse.success) {
        return {
          success: false,
          error: `LLM command generation failed: ${llmResponse.error}`,
        };
      }

      const command = this.extractYTDLPCommand(llmResponse.content);
      if (!command) {
        return {
          success: false,
          error: 'Failed to extract valid yt-dlp command from LLM response',
        };
      }

      // Execute yt-dlp command
      const executionResult = await this.executeYTDLP(command, request.output_dir);
      
      if (!executionResult.success) {
        return {
          success: false,
          execution_time_ms: Date.now() - startTime,
          llm_tokens_used: llmResponse.tokens_used,
          llm_cost: llmResponse.cost_estimate,
          error: executionResult.error,
        };
      }

      // Sanitize output for token efficiency
      const sanitized = sanitizeResponse(
        executionResult.output || '', 
        'youtube_download', 
        this.sanitizationConfig
      );

      // Extract metadata from output
      const metadata = this.parseDownloadOutput(executionResult.output || '');

      return {
        success: true,
        downloaded_file: executionResult.downloadedFile,
        title: metadata.title,
        duration: metadata.duration,
        format: metadata.format,
        execution_time_ms: Date.now() - startTime,
        llm_tokens_used: llmResponse.tokens_used,
        llm_cost: llmResponse.cost_estimate,
        sanitized_output: sanitized.sanitized_content,
      };

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      return {
        success: false,
        execution_time_ms: Date.now() - startTime,
        error: errorMessage,
      };
    }
  }

  private buildYTDLPPrompt(request: YouTubeDownloadRequest): string {
    let prompt = `Generate a single yt-dlp command for downloading from YouTube:

URL: ${request.url}
Output directory: ${request.output_dir}`;

    if (request.format) {
      prompt += `\nPreferred format: ${request.format}`;
    }

    if (request.audio_only) {
      prompt += `\nAudio only: true`;
    }

    if (request.max_duration) {
      prompt += `\nMax duration: ${request.max_duration} seconds`;
    }

    prompt += `

Requirements:
- Return ONLY the complete yt-dlp command, no explanation
- Use efficient format selection
- Include proper output filename template
- Add progress reporting
- Use quality settings: ${this.config.quality}
- Add timeout protection

yt-dlp command:`;

    return prompt;
  }

  private extractYTDLPCommand(llmResponse: string): string | null {
    const lines = llmResponse.trim().split('\n');
    
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('yt-dlp ')) {
        return trimmed;
      }
    }

    // Try to find any line with yt-dlp
    for (const line of lines) {
      if (line.includes('yt-dlp')) {
        const match = line.match(/yt-dlp[^`"']*/);
        if (match) {
          return match[0].trim();
        }
      }
    }

    return null;
  }

  private async executeYTDLP(command: string, outputDir: string): Promise<{
    success: boolean;
    output?: string;
    downloadedFile?: string;
    error?: string;
  }> {
    return new Promise((resolve) => {
      const args = command.split(' ').slice(1); // Remove 'yt-dlp' from args
      
      const process = spawn('yt-dlp', args, {
        stdio: ['ignore', 'pipe', 'pipe'],
        cwd: outputDir,
      });

      let stdout = '';
      let stderr = '';

      process.stdout?.on('data', (data) => {
        stdout += data.toString();
      });

      process.stderr?.on('data', (data) => {
        stderr += data.toString();
      });

      const timeout = setTimeout(() => {
        process.kill('SIGKILL');
        resolve({
          success: false,
          error: `yt-dlp command timed out after ${this.config.timeout_seconds} seconds`,
        });
      }, this.config.timeout_seconds * 1000);

      process.on('close', async (code) => {
        clearTimeout(timeout);
        
        if (code === 0) {
          // Try to find the downloaded file
          try {
            const files = await fs.readdir(outputDir);
            const videoFiles = files.filter(f => 
              ['.mp4', '.mkv', '.webm', '.mp3', '.m4a'].includes(extname(f).toLowerCase())
            );
            
            // Get the most recently created file
            let newestFile = '';
            let newestTime = 0;
            
            for (const file of videoFiles) {
              const stats = await fs.stat(join(outputDir, file));
              if (stats.mtimeMs > newestTime) {
                newestTime = stats.mtimeMs;
                newestFile = file;
              }
            }

            resolve({
              success: true,
              output: stdout + stderr,
              downloadedFile: newestFile ? join(outputDir, newestFile) : undefined,
            });
          } catch (err) {
            resolve({
              success: true,
              output: stdout + stderr,
            });
          }
        } else {
          resolve({
            success: false,
            error: `yt-dlp exited with code ${code}: ${stderr}`,
          });
        }
      });

      process.on('error', (error) => {
        clearTimeout(timeout);
        resolve({
          success: false,
          error: `Failed to execute yt-dlp: ${error.message}`,
        });
      });
    });
  }

  private parseDownloadOutput(output: string): {
    title?: string;
    duration?: number;
    format?: string;
  } {
    const metadata: any = {};

    // Extract title
    const titleMatch = output.match(/\[download\] Destination: (.+?)\.(?:mp4|mkv|webm|mp3|m4a)/);
    if (titleMatch) {
      metadata.title = titleMatch[1].split('/').pop();
    }

    // Extract duration (if available)
    const durationMatch = output.match(/Duration: (\d{2}):(\d{2}):(\d{2})/);
    if (durationMatch) {
      const hours = parseInt(durationMatch[1]);
      const minutes = parseInt(durationMatch[2]);
      const seconds = parseInt(durationMatch[3]);
      metadata.duration = hours * 3600 + minutes * 60 + seconds;
    }

    // Extract format
    const formatMatch = output.match(/format (\d+) \(([^)]+)\)/);
    if (formatMatch) {
      metadata.format = formatMatch[2];
    }

    return metadata;
  }
}