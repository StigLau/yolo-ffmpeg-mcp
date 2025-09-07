/**
 * Komposteur operations wrapper
 */

import { writeFileSync, readFileSync } from 'fs';
import { resolve } from 'path';
import { v4 as uuidv4 } from 'uuid';
import { KomposteurJarManager } from './jar-manager.js';
import type { 
  KompostConfig, 
  YouTubeDownloadConfig, 
  S3Config, 
  KomposteurResult 
} from '../types/index.js';

export class KomposteurOperations {
  private jarManager: KomposteurJarManager;

  constructor() {
    this.jarManager = new KomposteurJarManager();
  }

  /**
   * Download video from YouTube using McpDownloadServiceCli
   */
  async downloadFromYouTube(config: YouTubeDownloadConfig): Promise<KomposteurResult> {
    const outputPath = config.outputPath || `./generated/media/youtube-${Date.now()}.mp4`;
    
    const args = [
      '-cp', this.jarManager.getJarPath()!,
      'no.lau.download.service.McpDownloadServiceCli',
      'download_youtube',
      config.url,
      config.quality,
      outputPath
    ];

    const result = await this.jarManager.executeWithClasspath(args);
    
    // Parse JSON response from download service
    if (result.success && result.output) {
      try {
        const response = JSON.parse(result.output);
        if (!response.success) {
          return {
            ...result,
            success: false,
            error: response.error
          };
        }
        result.outputFiles = [response.file_path];
      } catch (e) {
        // Non-JSON output, keep as-is
      }
    }
    
    return result;
  }

  /**
   * Process kompost.json composition using main Komposteur entry point
   */
  async processKomposition(kompost: KompostConfig, outputPath?: string): Promise<KomposteurResult> {
    // Create temporary kompost.json file
    const tempId = uuidv4();
    const tempKompostFile = `./generated/kompost-files/kompost-${tempId}.json`;
    const finalOutputPath = outputPath || `./generated/media/composition-${Date.now()}.mp4`;

    try {
      // Write kompost config to temporary file
      writeFileSync(tempKompostFile, JSON.stringify(kompost, null, 2));

      // Use main JAR entry point: java -jar uber-kompost.jar <kompost.json> [output.mp4]
      const args = [tempKompostFile, finalOutputPath];

      const result = await this.jarManager.execute(args);

      // Add output file path to result
      if (result.success) {
        result.outputFiles = [finalOutputPath];
      }

      return result;

    } catch (error: any) {
      return {
        success: false,
        output: '',
        error: `Failed to process komposition: ${error.message}`,
        exitCode: -1,
        duration: 0
      };
    }
  }

  /**
   * Download file from S3 using McpDownloadServiceCli
   */
  async downloadFromS3(config: S3Config): Promise<KomposteurResult> {
    const localPath = config.localPath || `./generated/media/s3-${Date.now()}`;
    const s3Url = `s3://${config.bucket}/${config.key}`;
    const awsProfile = process.env.AWS_PROFILE || 'default';
    
    const args = [
      '-cp', this.jarManager.getJarPath()!,
      'no.lau.download.service.McpDownloadServiceCli',
      'download_s3',
      s3Url,
      awsProfile,
      localPath
    ];

    const result = await this.jarManager.executeWithClasspath(args);
    
    // Parse JSON response from download service
    if (result.success && result.output) {
      try {
        const response = JSON.parse(result.output);
        if (!response.success) {
          return {
            ...result,
            success: false,
            error: response.error
          };
        }
        result.outputFiles = [response.file_path];
      } catch (e) {
        // Non-JSON output, keep as-is
      }
    }

    return result;
  }

  /**
   * Upload file to S3 - Note: Upload functionality not found in CLI analysis
   * This is a placeholder that returns an error message
   */
  async uploadToS3(config: S3Config): Promise<KomposteurResult> {
    return {
      success: false,
      output: '',
      error: 'S3 upload not currently supported by Komposteur CLI. Use AWS CLI or SDK directly.',
      exitCode: -1,
      duration: 0
    };
  }

  /**
   * Get Komposteur status and version
   */
  async getStatus(): Promise<{
    available: boolean;
    version: string | null;
    jarPath: string | null;
  }> {
    return {
      available: this.jarManager.isAvailable(),
      version: await this.jarManager.getVersion(),
      jarPath: this.jarManager.getJarPath()
    };
  }

  /**
   * Validate kompost.json file
   */
  validateKompostFile(filePath: string): { valid: boolean; errors: string[] } {
    try {
      const content = readFileSync(filePath, 'utf-8');
      const parsed = JSON.parse(content);
      
      // Basic validation - could be enhanced with Zod schema
      const errors: string[] = [];
      
      if (!parsed.name) errors.push('Missing required field: name');
      if (!Array.isArray(parsed.segments)) errors.push('Missing or invalid segments array');
      if (parsed.segments && parsed.segments.length === 0) errors.push('Segments array is empty');

      return {
        valid: errors.length === 0,
        errors
      };
    } catch (error: any) {
      return {
        valid: false,
        errors: [`Invalid JSON file: ${error.message}`]
      };
    }
  }
}