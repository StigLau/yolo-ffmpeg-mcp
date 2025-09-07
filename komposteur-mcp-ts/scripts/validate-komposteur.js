#!/usr/bin/env node

/**
 * Validates Komposteur JAR availability and functionality
 */

import { existsSync } from 'fs';
import { resolve } from 'path';
import { homedir } from 'os';
import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);

async function validateKomposteur() {
  console.log('🔍 Validating Komposteur JAR availability...\n');
  
  // Check local development JAR
  const localDevPath = resolve(
    homedir(), 
    '.m2/repository/no/lau/kompost/mcp/uber-kompost-1.0.0-shaded.jar'
  );
  
  if (existsSync(localDevPath)) {
    console.log('✅ Local development JAR found:', localDevPath);
    await testJar(localDevPath);
    return;
  }

  // Check fallback JAR
  const fallbackPath = resolve('./lib/komposteur-uber.jar');
  if (existsSync(fallbackPath)) {
    console.log('✅ Fallback JAR found:', fallbackPath);
    await testJar(fallbackPath);
    return;
  }

  console.log('❌ No Komposteur JAR found');
  console.log('Run: npm run komposteur:download');
  process.exit(1);
}

async function testJar(jarPath) {
  try {
    console.log('🧪 Testing JAR functionality...');
    
    const { stdout, stderr } = await execFileAsync('java', ['-jar', jarPath, '--version'], {
      timeout: 10000
    });
    
    console.log('✅ JAR test successful');
    console.log('Version output:', stdout.trim());
    
    if (stderr) {
      console.log('Warnings:', stderr.trim());
    }
    
  } catch (error) {
    console.log('❌ JAR test failed:', error.message);
    
    if (error.code === 'ENOENT') {
      console.log('💡 Java not found. Please install Java Runtime Environment.');
    }
    
    process.exit(1);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  validateKomposteur().catch(console.error);
}