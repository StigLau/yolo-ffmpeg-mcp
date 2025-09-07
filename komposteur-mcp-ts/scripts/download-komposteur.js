#!/usr/bin/env node

/**
 * Downloads Komposteur JAR from GitHub Packages
 * Fallback script when local development JAR is not available
 */

import { createWriteStream, mkdirSync, existsSync } from 'fs';
import { resolve } from 'path';
import { pipeline } from 'stream/promises';

const GITHUB_PACKAGE_URL = 'https://github.com/StigLau/komposteur/packages/2597233';
const LIB_DIR = './lib';
const JAR_PATH = resolve(LIB_DIR, 'komposteur-uber.jar');

async function downloadKomposteur() {
  console.log('📦 Downloading Komposteur JAR...');
  
  // Create lib directory if it doesn't exist
  if (!existsSync(LIB_DIR)) {
    mkdirSync(LIB_DIR, { recursive: true });
  }

  try {
    // Note: This is a placeholder - actual GitHub Packages download requires authentication
    // In practice, you would need to:
    // 1. Authenticate with GitHub Packages
    // 2. Use the actual JAR download URL
    // 3. Handle authentication tokens
    
    console.log('⚠️  Manual download required:');
    console.log(`1. Visit: ${GITHUB_PACKAGE_URL}`);
    console.log(`2. Download the uber-kompost-1.0.0-shaded.jar file`);
    console.log(`3. Place it at: ${JAR_PATH}`);
    console.log('');
    console.log('Alternatively, build Komposteur locally and it will be auto-detected in ~/.m2/repository/');
    
  } catch (error) {
    console.error('❌ Download failed:', error.message);
    process.exit(1);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  downloadKomposteur().catch(console.error);
}