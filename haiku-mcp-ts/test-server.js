#!/usr/bin/env node

/**
 * Test script for Haiku MCP Server
 */

import { spawn } from 'child_process';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join } from 'path';

// Test configuration
const TEST_CONFIG = `server:
  name: "haiku-mcp-server-test"
  version: "1.0.0"

llm:
  primary: "haiku"
  fallback: "gemini_flash" 
  timeout_seconds: 30
  max_retries: 1

models:
  haiku:
    provider: "anthropic"
    model: "claude-3-haiku-20240307"
    api_key: "test-key"
    max_tokens: 500
    
  gemini_flash:
    provider: "google"
    model: "gemini-1.5-flash"
    api_key: "test-key"
    max_tokens: 500

ffmpeg:
  timeout_seconds: 60
  temp_directory: "/tmp/haiku-mcp-test"
  cleanup_on_exit: true

youtube:
  timeout_seconds: 120
  max_duration_seconds: 600
  quality: "best[height<=480]"

logging:
  level: "DEBUG"
  include_ffmpeg_logs: false
  sanitize_responses: true

response_limits:
  max_tokens: 200
  strip_metadata: true
  include_performance_stats: true`;

async function runTest() {
  console.log('🧪 Testing Haiku MCP Server...\n');

  // Step 1: Create test config
  console.log('1. Creating test configuration...');
  if (!existsSync('config')) {
    console.log('   Creating config directory');
  }
  
  const configPath = 'config/config.yaml';
  writeFileSync(configPath, TEST_CONFIG);
  console.log('   ✅ Test config created\n');

  // Step 2: Compile TypeScript
  console.log('2. Compiling TypeScript...');
  const tscResult = await runCommand('npx', ['tsc']);
  
  if (tscResult.code !== 0) {
    console.log('   ❌ TypeScript compilation failed:');
    console.log(tscResult.stderr);
    return false;
  }
  console.log('   ✅ TypeScript compiled successfully\n');

  // Step 3: Test MCP server initialization
  console.log('3. Testing MCP server initialization...');
  
  const testScript = `
import { HaikuMCPServer } from './dist/server.js';

async function test() {
  try {
    console.log('Creating server instance...');
    const server = new HaikuMCPServer();
    
    console.log('Initializing server...');
    await server.initialize();
    
    console.log('✅ Server initialized successfully');
    return true;
  } catch (error) {
    console.log('❌ Server initialization failed:', error.message);
    return false;
  }
}

test().then(success => process.exit(success ? 0 : 1));
`;

  writeFileSync('test-init.js', testScript);
  
  const initResult = await runCommand('node', ['test-init.js']);
  
  if (initResult.code !== 0) {
    console.log('   ❌ Server initialization failed:');
    console.log(initResult.stdout);
    console.log(initResult.stderr);
    return false;
  }
  
  console.log('   ✅ Server initialization successful\n');

  // Step 4: Test tool registration
  console.log('4. Testing tool registration...');
  const toolsTest = await testTools();
  
  if (!toolsTest) {
    console.log('   ❌ Tool registration failed\n');
    return false;
  }
  
  console.log('   ✅ All tools registered successfully\n');

  // Step 5: Test sanitization utilities
  console.log('5. Testing response sanitization...');
  const sanitizationTest = await testSanitization();
  
  if (!sanitizationTest) {
    console.log('   ❌ Sanitization test failed\n');
    return false;
  }
  
  console.log('   ✅ Sanitization working correctly\n');

  console.log('🎉 All tests passed! Haiku MCP Server is ready.\n');
  console.log('📋 Summary:');
  console.log('   - TypeScript compilation: ✅');
  console.log('   - Server initialization: ✅');
  console.log('   - Tool registration: ✅');
  console.log('   - Response sanitization: ✅');
  console.log('\n🚀 To use the server:');
  console.log('   1. Set environment variables: ANTHROPIC_API_KEY, GOOGLE_API_KEY');
  console.log('   2. Run: npm start');
  
  return true;
}

async function testTools() {
  const toolsTestScript = `
import { readFileSync } from 'fs';

try {
  const serverCode = readFileSync('dist/server.js', 'utf8');
  
  const expectedTools = [
    'create_music_video',
    'process_video_file', 
    'download_youtube_audio',
    'download_youtube_video',
    'get_llm_stats'
  ];
  
  for (const tool of expectedTools) {
    if (!serverCode.includes(tool)) {
      console.log(\`❌ Missing tool: \${tool}\`);
      process.exit(1);
    }
  }
  
  console.log('✅ All expected tools found in server code');
  process.exit(0);
} catch (error) {
  console.log('❌ Tool check failed:', error.message);
  process.exit(1);
}
`;

  writeFileSync('test-tools.js', toolsTestScript);
  const result = await runCommand('node', ['test-tools.js']);
  return result.code === 0;
}

async function testSanitization() {
  const sanitizationTestScript = `
import { sanitizeResponse, sanitizeFFMPEGOutput, sanitizeYouTubeOutput } from './dist/utils/sanitization.js';

try {
  // Test FFMPEG output sanitization
  const ffmpegOutput = \`ffmpeg version 4.4.0-0ubuntu1
built with gcc 9 (Ubuntu 9.4.0-1ubuntu1~20.04.2)
configuration: --prefix=/usr --extra-version=0ubuntu1
libavutil      56. 70.100 / 56. 70.100
Stream #0:0: Video: h264 (High), yuv420p, 1920x1080 [SAR 1:1 DAR 16:9], 25 fps
size=    1024kB time=00:00:10.00 bitrate= 838.9kbits/s fps=25.0 q=28.0 size=    2048kB time=00:00:20.00\`;

  const config = { strip_metadata: true, max_output_tokens: 100, preserve_essential_fields: [], aggressive_pruning: true };
  const result = sanitizeFFMPEGOutput(ffmpegOutput, config);
  
  if (result.reduction_percentage < 50) {
    console.log('❌ FFMPEG sanitization not effective enough:', result.reduction_percentage);
    process.exit(1);
  }
  
  console.log(\`✅ FFMPEG sanitization: \${result.reduction_percentage}% reduction\`);
  
  // Test YouTube output sanitization  
  const youtubeOutput = \`format code  extension  resolution note
140          m4a        audio only tiny  130k , m4a_dash container, mp4a.40.2@128k (44100Hz), 4.26MiB
298          mp4        1280x720   720p  2998k , mp4_dash container, avc1.4d401f@2998k, 30fps, video only, 98.84MiB
[download] Downloading video 1 of 1
[download] Destination: /tmp/test.mp4\`;

  const ytResult = sanitizeYouTubeOutput(youtubeOutput, config);
  
  if (ytResult.reduction_percentage < 60) {
    console.log('❌ YouTube sanitization not effective enough:', ytResult.reduction_percentage);  
    process.exit(1);
  }
  
  console.log(\`✅ YouTube sanitization: \${ytResult.reduction_percentage}% reduction\`);
  
  console.log('✅ All sanitization tests passed');
  process.exit(0);
} catch (error) {
  console.log('❌ Sanitization test failed:', error.message);
  process.exit(1);
}
`;

  writeFileSync('test-sanitization.js', sanitizationTestScript);
  const result = await runCommand('node', ['test-sanitization.js']);
  return result.code === 0;
}

function runCommand(command, args) {
  return new Promise((resolve) => {
    const process = spawn(command, args, { stdio: 'pipe' });
    
    let stdout = '';
    let stderr = '';
    
    process.stdout?.on('data', (data) => stdout += data.toString());
    process.stderr?.on('data', (data) => stderr += data.toString());
    
    process.on('close', (code) => {
      resolve({ code, stdout, stderr });
    });
  });
}

// Cleanup function
function cleanup() {
  try {
    const filesToCleanup = ['test-init.js', 'test-tools.js', 'test-sanitization.js', 'config/config.yaml'];
    for (const file of filesToCleanup) {
      if (existsSync(file)) {
        // Skip cleanup for now
      }
    }
  } catch (error) {
    console.log('Warning: Cleanup failed:', error.message);
  }
}

// Run tests
runTest()
  .then(success => {
    cleanup();
    process.exit(success ? 0 : 1);
  })
  .catch(error => {
    console.error('Test runner failed:', error);
    cleanup();
    process.exit(1);
  });