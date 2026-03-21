/**
 * Video processing tools using LLM-generated FFMPEG commands
 */

import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import { join } from 'path';
import { BaseLLMClient, LLMRequest } from '../llm/types.js';
import { sanitizeResponse, SanitizationConfig } from '../utils/sanitization.js';
import type { FFMPEGConfig } from '../config.js';

export interface VideoProcessRequest {
  input_file: string;
  output_file: string;
  operation: string;
  parameters?: Record<string, any>;
}

export interface VideoProcessResult {
  success: boolean;
  output_file?: string;
  command_used?: string;
  execution_time_ms?: number;
  llm_tokens_used?: number;
  llm_cost?: number;
  sanitized_output?: string;
  error?: string;
}

export class VideoProcessor {
  constructor(
    private llmClient: BaseLLMClient,
    private config: FFMPEGConfig,
    private sanitizationConfig: SanitizationConfig
  ) {}

  async processVideo(request: VideoProcessRequest): Promise<VideoProcessResult> {
    const startTime = Date.now();
    
    try {
      // Generate FFMPEG command using LLM
      const llmRequest: LLMRequest = {
        prompt: this.buildFFMPEGPrompt(request),
        max_tokens: 500,
        temperature: 0.1,
      };

      const llmResponse = await this.llmClient.generate(llmRequest);
      
      if (!llmResponse.success) {
        return {
          success: false,
          error: `LLM (${this.llmClient.provider}/${this.llmClient.model}) command generation failed: ${llmResponse.error}`,
        };
      }

      const command = this.extractFFMPEGCommand(llmResponse.content);
      if (!command) {
        return {
          success: false,
          error: 'Failed to extract valid FFMPEG command from LLM response',
        };
      }

      // Execute FFMPEG command
      const executionResult = await this.executeFFMPEG(command);
      
      if (!executionResult.success) {
        return {
          success: false,
          command_used: command,
          llm_tokens_used: llmResponse.tokens_used,
          llm_cost: llmResponse.cost_estimate,
          error: executionResult.error,
        };
      }

      // Sanitize output for token efficiency
      const sanitized = sanitizeResponse(
        executionResult.output || '', 
        request.operation, 
        this.sanitizationConfig
      );

      return {
        success: true,
        output_file: request.output_file,
        command_used: command,
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

  private buildFFMPEGPrompt(request: VideoProcessRequest): string {
    let prompt = `Generate a single FFMPEG command for this video processing task:

Operation: ${request.operation}
Input file: ${request.input_file}
Output file: ${request.output_file}`;

    if (request.parameters && Object.keys(request.parameters).length > 0) {
      prompt += `\nParameters: ${JSON.stringify(request.parameters)}`;
    }

    prompt += `

Requirements:
- Return ONLY the complete ffmpeg command, no explanation
- Use appropriate codecs and quality settings
- Handle audio/video sync properly
- Use efficient processing flags
- CRITICAL: Always wrap file paths in double quotes to handle spaces
- Example: ffmpeg -i "input file.mp4" -i "audio file.mp3" "output.mp4"
- Command should be ready to execute directly

FFMPEG Command:`;

    return prompt;
  }

  private extractFFMPEGCommand(llmResponse: string): string | null {
    // Extract command from LLM response
    const lines = llmResponse.trim().split('\n');
    
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('ffmpeg ')) {
        return trimmed;
      }
    }

    // Try to find any line with ffmpeg
    for (const line of lines) {
      if (line.includes('ffmpeg')) {
        const match = line.match(/ffmpeg[^`"']*/);
        if (match) {
          return match[0].trim();
        }
      }
    }

    return null;
  }

  private parseShellCommand(command: string): string[] {
    const args: string[] = [];
    let current = '';
    let inQuotes = false;
    let quoteChar = '';
    
    for (let i = 0; i < command.length; i++) {
      const char = command[i];
      
      if (!inQuotes && (char === '"' || char === "'")) {
        inQuotes = true;
        quoteChar = char;
      } else if (inQuotes && char === quoteChar) {
        inQuotes = false;
        quoteChar = '';
      } else if (!inQuotes && char === ' ') {
        if (current.trim()) {
          args.push(current.trim());
          current = '';
        }
      } else {
        current += char;
      }
    }
    
    if (current.trim()) {
      args.push(current.trim());
    }
    
    return args;
  }

  private async executeFFMPEG(command: string): Promise<{
    success: boolean;
    output?: string;
    error?: string;
  }> {
    return new Promise((resolve) => {
      // Proper shell parsing to handle quoted arguments
      const args = this.parseShellCommand(command).slice(1); // Remove 'ffmpeg' from args
      
      const process = spawn('ffmpeg', args, {
        stdio: ['ignore', 'pipe', 'pipe'],
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
          error: `FFMPEG command timed out after ${this.config.timeout_seconds} seconds`,
        });
      }, this.config.timeout_seconds * 1000);

      process.on('close', (code) => {
        clearTimeout(timeout);
        
        if (code === 0) {
          resolve({
            success: true,
            output: stderr, // FFMPEG logs to stderr
          });
        } else {
          resolve({
            success: false,
            error: `FFMPEG exited with code ${code}: ${stderr}`,
          });
        }
      });

      process.on('error', (error) => {
        clearTimeout(timeout);
        resolve({
          success: false,
          error: `Failed to execute FFMPEG: ${error.message}`,
        });
      });
    });
  }
}