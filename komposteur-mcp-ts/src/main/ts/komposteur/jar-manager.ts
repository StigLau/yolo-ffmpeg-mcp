/**
 * Manages Komposteur JAR file location and execution
 */

import { execFile } from 'child_process';
import { promisify } from 'util';
import { existsSync } from 'fs';
import { resolve } from 'path';
import { homedir } from 'os';
import type { KomposteurResult } from '../types/index.js';

const execFileAsync = promisify(execFile);

export class KomposteurJarManager {
  private jarPath: string | null = null;

  constructor() {
    this.findJarPath();
  }

  /**
   * Locate Komposteur JAR file using the strategy from CLAUDE.md:
   * 1. Local development JAR (~/.m2/repository/)
   * 2. Fallback to lib/ directory
   * 3. Error if not found
   */
  private findJarPath(): void {
    // Local development path (fastest iteration)
    const localDevPath = resolve(
      homedir(), 
      '.m2/repository/no/lau/kompost/mcp/uber-kompost-1.0.0-shaded.jar'
    );
    
    if (existsSync(localDevPath)) {
      console.log('🔧 Using local development JAR:', localDevPath);
      this.jarPath = localDevPath;
      return;
    }

    // Fallback to lib directory
    const fallbackPath = resolve('./lib/komposteur-uber.jar');
    if (existsSync(fallbackPath)) {
      console.log('📦 Using fallback JAR:', fallbackPath);
      this.jarPath = fallbackPath;
      return;
    }

    console.warn('⚠️ No Komposteur JAR found. Please run: npm run komposteur:download');
    this.jarPath = null;
  }

  /**
   * Check if JAR is available
   */
  isAvailable(): boolean {
    return this.jarPath !== null && existsSync(this.jarPath);
  }

  /**
   * Get current JAR path
   */
  getJarPath(): string | null {
    return this.jarPath;
  }

  /**
   * Execute Komposteur JAR with given arguments (main entry point)
   */
  async execute(args: string[], timeoutMs: number = 30000): Promise<KomposteurResult> {
    if (!this.isAvailable()) {
      return {
        success: false,
        output: '',
        error: 'Komposteur JAR not available. Run: npm run komposteur:download',
        exitCode: -1,
        duration: 0
      };
    }

    const startTime = Date.now();

    try {
      const { stdout, stderr } = await execFileAsync(
        'java',
        ['-jar', this.jarPath!, ...args],
        { 
          timeout: timeoutMs,
          maxBuffer: 10 * 1024 * 1024 // 10MB buffer
        }
      );

      const duration = Date.now() - startTime;

      return {
        success: true,
        output: stdout,
        error: stderr || undefined,
        exitCode: 0,
        duration
      };

    } catch (error: any) {
      const duration = Date.now() - startTime;

      return {
        success: false,
        output: error.stdout || '',
        error: error.message || 'Unknown error',
        exitCode: error.code || -1,
        duration
      };
    }
  }

  /**
   * Execute with classpath (for McpDownloadServiceCli)
   */
  async executeWithClasspath(args: string[], timeoutMs: number = 600000): Promise<KomposteurResult> {
    if (!this.isAvailable()) {
      return {
        success: false,
        output: '',
        error: 'Komposteur JAR not available. Run: npm run komposteur:download',
        exitCode: -1,
        duration: 0
      };
    }

    const startTime = Date.now();

    try {
      const { stdout, stderr } = await execFileAsync(
        'java',
        args, // args already include -cp and JAR path
        { 
          timeout: timeoutMs, // 10 minutes for downloads
          maxBuffer: 10 * 1024 * 1024 // 10MB buffer
        }
      );

      const duration = Date.now() - startTime;

      return {
        success: true,
        output: stdout,
        error: stderr || undefined,
        exitCode: 0,
        duration
      };

    } catch (error: any) {
      const duration = Date.now() - startTime;

      return {
        success: false,
        output: error.stdout || '',
        error: error.message || 'Unknown error',
        exitCode: error.code || -1,
        duration
      };
    }
  }

  /**
   * Test JAR functionality
   */
  async testJar(): Promise<boolean> {
    const result = await this.execute(['--help'], 5000);
    return result.success && result.exitCode === 0;
  }

  /**
   * Get JAR version info
   */
  async getVersion(): Promise<string | null> {
    // Try running with no args to get usage/version info
    const result = await this.execute([], 5000);
    if (result.success || result.output) {
      // Parse version from output like "Version: 0.12.0-SNAPSHOT"
      const versionMatch = result.output.match(/Version:\s*([\d\.\-A-Z]+)/);
      return versionMatch ? versionMatch[1] : 'Unknown';
    }
    return null;
  }
}