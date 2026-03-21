/**
 * File Registry Manager for TypeScript MCP Server
 * Provides file abstraction through IDs instead of direct paths
 */

import { promises as fs } from 'fs';
import { join } from 'path';
import * as crypto from 'crypto';

export interface FileInfo {
  id: string;
  path: string;
  size: number;
  modified: Date;
  extension: string;
  mediaType: 'video' | 'audio' | 'image' | 'unknown';
}

export class FileManager {
  private fileMap: Map<string, string> = new Map(); // id -> path
  private propertyCache: Map<string, FileInfo> = new Map();
  private cacheTimestamps: Map<string, number> = new Map();
  private readonly cacheTTL = 300000; // 5 minutes in ms

  private readonly sourceDir = '/tmp/music/source';
  private readonly tempDir = '/tmp/music/temp';
  private readonly finishedDir = '/tmp/music/finished';

  constructor() {
    this.ensureDirectories();
    this.discoverFiles();
  }

  private async ensureDirectories(): Promise<void> {
    const dirs = [this.sourceDir, this.tempDir, this.finishedDir];
    
    for (const dir of dirs) {
      try {
        await fs.mkdir(dir, { recursive: true });
      } catch (error) {
        // Directory might already exist
      }
    }
  }

  /**
   * Discover and register all files in source directory
   */
  private async discoverFiles(): Promise<void> {
    try {
      const files = await fs.readdir(this.sourceDir);
      
      for (const file of files) {
        const fullPath = join(this.sourceDir, file);
        try {
          const stats = await fs.stat(fullPath);
          if (stats.isFile()) {
            this.registerFile(fullPath);
          }
        } catch (error) {
          // Skip files we can't access
        }
      }
    } catch (error) {
      console.error('Error discovering files:', error);
    }
  }

  /**
   * Register a file and return its ID reference
   */
  registerFile(filePath: string): string {
    // Generate consistent ID based on file path
    const fileId = this.generateFileId(filePath);
    
    this.fileMap.set(fileId, filePath);
    
    // Cache file info
    this.cacheFileInfo(fileId, filePath);
    
    return fileId;
  }

  /**
   * Resolve file ID to actual file path
   */
  resolveFileId(fileId: string): string | null {
    return this.fileMap.get(fileId) || null;
  }

  /**
   * Get file information by ID
   */
  async getFileInfo(fileId: string): Promise<FileInfo | null> {
    const cachedInfo = this.propertyCache.get(fileId);
    const cacheTime = this.cacheTimestamps.get(fileId);
    
    // Return cached info if still valid
    if (cachedInfo && cacheTime && (Date.now() - cacheTime) < this.cacheTTL) {
      return cachedInfo;
    }

    // Refresh cache
    const filePath = this.resolveFileId(fileId);
    if (!filePath) return null;

    return this.cacheFileInfo(fileId, filePath);
  }

  /**
   * List all registered files
   */
  async listFiles(): Promise<FileInfo[]> {
    const files: FileInfo[] = [];
    
    for (const fileId of this.fileMap.keys()) {
      const info = await this.getFileInfo(fileId);
      if (info) {
        files.push(info);
      }
    }
    
    return files;
  }

  /**
   * Get registry status
   */
  getRegistryStatus(): { total_files: number; cache_entries: number } {
    return {
      total_files: this.fileMap.size,
      cache_entries: this.propertyCache.size
    };
  }

  private generateFileId(filePath: string): string {
    // Create consistent ID based on filename (not full path for stability)
    const fileName = filePath.split('/').pop() || filePath;
    const hash = crypto.createHash('md5').update(fileName).digest('hex');
    return `file_${hash.substring(0, 8)}`;
  }

  private async cacheFileInfo(fileId: string, filePath: string): Promise<FileInfo | null> {
    try {
      const stats = await fs.stat(filePath);
      const fileName = filePath.split('/').pop() || '';
      const extension = fileName.split('.').pop()?.toLowerCase() || '';
      
      const fileInfo: FileInfo = {
        id: fileId,
        path: filePath,
        size: stats.size,
        modified: stats.mtime,
        extension: extension,
        mediaType: this.getMediaType(extension)
      };

      this.propertyCache.set(fileId, fileInfo);
      this.cacheTimestamps.set(fileId, Date.now());
      
      return fileInfo;
    } catch (error) {
      console.error(`Error caching file info for ${filePath}:`, error);
      return null;
    }
  }

  private getMediaType(extension: string): 'video' | 'audio' | 'image' | 'unknown' {
    const videoExts = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'm4v'];
    const audioExts = ['mp3', 'flac', 'wav', 'aac', 'm4a', 'ogg', 'wma'];
    const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'];
    
    if (videoExts.includes(extension)) return 'video';
    if (audioExts.includes(extension)) return 'audio';
    if (imageExts.includes(extension)) return 'image';
    
    return 'unknown';
  }
}