#!/usr/bin/env node

import { spawn, ChildProcess } from 'child_process';
import { promises as fs } from 'fs';
import { join, extname, dirname } from 'path';
import { randomUUID } from 'crypto';

export interface FFmpegExecutionResult {
  success: boolean;
  outputPath?: string;
  duration?: number;
  error?: string;
  processTime: number;
  command: string[];
  stdout: string;
  stderr: string;
}

export interface FFmpegValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  sanitizedCommand: string[];
}

export class ProtectedFFmpegExecutor {
  private readonly maxExecutionTime: number = 300000; // 5 minutes
  private readonly allowedInputExtensions: Set<string> = new Set([
    '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv',
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'
  ]);
  
  private readonly allowedOutputExtensions: Set<string> = new Set([
    '.mp4', '.webm', '.avi', '.mov', '.mp3', '.wav', '.aac', '.jpg', '.png'
  ]);

  private readonly dangerousFlags: Set<string> = new Set([
    '-f', 'rawvideo', '-f', 'null', '-f', 'pipe', 
    '-protocol_whitelist', '-safe', '-pattern_type'
  ]);

  /**
   * Validate FFmpeg command for safety and correctness
   */
  public validateCommand(command: string[]): FFmpegValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    let sanitizedCommand = [...command];

    // Basic structure validation
    if (!Array.isArray(command) || command.length < 3) {
      errors.push('Command must be an array with at least 3 elements');
      return { valid: false, errors, warnings, sanitizedCommand: [] };
    }

    if (command[0] !== 'ffmpeg') {
      errors.push('Command must start with "ffmpeg"');
      return { valid: false, errors, warnings, sanitizedCommand: [] };
    }

    // Check for dangerous flags
    for (let i = 0; i < command.length; i++) {
      if (this.dangerousFlags.has(command[i])) {
        errors.push(`Dangerous flag detected: ${command[i]}`);
      }
    }

    // Validate input files
    let inputCount = 0;
    for (let i = 1; i < command.length - 1; i++) {
      if (command[i] === '-i' && i + 1 < command.length) {
        const inputPath = command[i + 1];
        inputCount++;
        
        // Check file extension
        const ext = extname(inputPath).toLowerCase();
        if (!this.allowedInputExtensions.has(ext)) {
          warnings.push(`Uncommon input extension: ${ext} for file ${inputPath}`);
        }

        // Basic path safety
        if (inputPath.includes('..') || inputPath.includes('~')) {
          errors.push(`Potentially unsafe input path: ${inputPath}`);
        }
        
        i++; // Skip the input path
      }
    }

    if (inputCount === 0) {
      errors.push('No input files specified with -i flag');
    }

    // Validate output path (should be last argument)
    const outputPath = command[command.length - 1];
    if (!outputPath || outputPath.startsWith('-')) {
      errors.push('Invalid or missing output path');
    } else {
      const outputExt = extname(outputPath).toLowerCase();
      if (!this.allowedOutputExtensions.has(outputExt)) {
        warnings.push(`Uncommon output extension: ${outputExt}`);
      }

      // Ensure output path is safe
      if (outputPath.includes('..') || outputPath.includes('~')) {
        errors.push(`Potentially unsafe output path: ${outputPath}`);
      }
    }

    // Check for overwrite flag
    if (!command.includes('-y') && !command.includes('-n')) {
      sanitizedCommand.splice(-1, 0, '-y'); // Add -y before output path
      warnings.push('Added -y flag to prevent interactive prompts');
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings,
      sanitizedCommand
    };
  }

  /**
   * Verify input files exist and are accessible
   */
  private async verifyInputFiles(command: string[]): Promise<string[]> {
    const errors: string[] = [];
    
    for (let i = 1; i < command.length - 1; i++) {
      if (command[i] === '-i' && i + 1 < command.length) {
        const inputPath = command[i + 1];
        
        try {
          const stats = await fs.stat(inputPath);
          if (!stats.isFile()) {
            errors.push(`Input path is not a file: ${inputPath}`);
          }
          
          // Check file size (warn for very large files)
          const sizeGB = stats.size / (1024 * 1024 * 1024);
          if (sizeGB > 10) {
            console.error(`⚠️ Large input file detected: ${inputPath} (${sizeGB.toFixed(1)}GB)`);
          }
          
        } catch (error) {
          errors.push(`Cannot access input file: ${inputPath} - ${error}`);
        }
        
        i++; // Skip the input path
      }
    }
    
    return errors;
  }

  /**
   * Ensure output directory exists
   */
  private async ensureOutputDirectory(outputPath: string): Promise<void> {
    const dir = dirname(outputPath);
    
    try {
      await fs.mkdir(dir, { recursive: true });
    } catch (error) {
      throw new Error(`Failed to create output directory: ${dir} - ${error}`);
    }
  }

  /**
   * Execute FFmpeg command with protection and monitoring
   */
  public async executeCommand(command: string[]): Promise<FFmpegExecutionResult> {
    const startTime = Date.now();
    const executionId = randomUUID();
    
    console.error(`🎬 Starting FFmpeg execution ${executionId.slice(0, 8)}`);
    console.error(`📝 Command: ${command.join(' ')}`);

    // Step 1: Validate command structure
    const validation = this.validateCommand(command);
    if (!validation.valid) {
      return {
        success: false,
        error: `Command validation failed: ${validation.errors.join(', ')}`,
        processTime: Date.now() - startTime,
        command,
        stdout: '',
        stderr: validation.errors.join('\n')
      };
    }

    // Use sanitized command
    const sanitizedCommand = validation.sanitizedCommand;
    
    // Print warnings
    if (validation.warnings.length > 0) {
      console.error(`⚠️ Warnings: ${validation.warnings.join(', ')}`);
    }

    // Step 2: Verify input files exist
    const inputErrors = await this.verifyInputFiles(sanitizedCommand);
    if (inputErrors.length > 0) {
      return {
        success: false,
        error: `Input file validation failed: ${inputErrors.join(', ')}`,
        processTime: Date.now() - startTime,
        command: sanitizedCommand,
        stdout: '',
        stderr: inputErrors.join('\n')
      };
    }

    // Step 3: Ensure output directory exists
    const outputPath = sanitizedCommand[sanitizedCommand.length - 1];
    try {
      await this.ensureOutputDirectory(outputPath);
    } catch (error) {
      return {
        success: false,
        error: `Output directory creation failed: ${error}`,
        processTime: Date.now() - startTime,
        command: sanitizedCommand,
        stdout: '',
        stderr: String(error)
      };
    }

    // Step 4: Execute FFmpeg with monitoring
    return new Promise((resolve) => {
      const child: ChildProcess = spawn('ffmpeg', sanitizedCommand.slice(1), {
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';
      let resolved = false;

      // Collect output
      child.stdout?.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr?.on('data', (data) => {
        const chunk = data.toString();
        stderr += chunk;
        
        // Log progress for long operations
        if (chunk.includes('time=') || chunk.includes('frame=')) {
          // Extract progress info without flooding logs
          const timeMatch = chunk.match(/time=(\d+:\d+:\d+\.\d+)/);
          if (timeMatch && Math.random() < 0.1) { // Only log 10% of progress updates
            console.error(`⏱️ Progress: ${timeMatch[1]}`);
          }
        }
      });

      // Set timeout
      const timeout = setTimeout(() => {
        if (!resolved) {
          console.error(`⏰ FFmpeg execution timed out after ${this.maxExecutionTime}ms`);
          child.kill('SIGTERM');
          
          // Force kill after 5 seconds if SIGTERM doesn't work
          setTimeout(() => {
            if (!resolved) {
              child.kill('SIGKILL');
            }
          }, 5000);
        }
      }, this.maxExecutionTime);

      // Handle completion
      child.on('close', (code) => {
        if (resolved) return;
        resolved = true;
        
        clearTimeout(timeout);
        const processTime = Date.now() - startTime;
        
        console.error(`🏁 FFmpeg completed in ${processTime}ms with code ${code}`);

        if (code === 0) {
          resolve({
            success: true,
            outputPath,
            processTime,
            command: sanitizedCommand,
            stdout,
            stderr
          });
        } else {
          resolve({
            success: false,
            error: `FFmpeg exited with code ${code}`,
            processTime,
            command: sanitizedCommand,
            stdout,
            stderr
          });
        }
      });

      // Handle process errors
      child.on('error', (error) => {
        if (resolved) return;
        resolved = true;
        
        clearTimeout(timeout);
        const processTime = Date.now() - startTime;
        
        console.error(`❌ FFmpeg process error: ${error}`);
        
        resolve({
          success: false,
          error: `Process error: ${error.message}`,
          processTime,
          command: sanitizedCommand,
          stdout,
          stderr: stderr + `\nProcess error: ${error.message}`
        });
      });
    });
  }

  /**
   * Get metadata about a media file using ffprobe
   */
  public async getMediaInfo(filePath: string): Promise<any> {
    return new Promise((resolve, reject) => {
      const child = spawn('ffprobe', [
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        filePath
      ]);

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
            const info = JSON.parse(stdout);
            resolve(info);
          } catch (parseError) {
            reject(new Error(`Failed to parse ffprobe output: ${parseError}`));
          }
        } else {
          reject(new Error(`ffprobe failed with code ${code}: ${stderr}`));
        }
      });

      child.on('error', (error) => {
        reject(new Error(`ffprobe process error: ${error.message}`));
      });
    });
  }
}

/**
 * Global protected FFmpeg executor instance
 */
export const protectedFFmpeg = new ProtectedFFmpegExecutor();