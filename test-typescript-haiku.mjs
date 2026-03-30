#!/usr/bin/env node

/**
 * Direct test of TypeScript Haiku MCP Server
 * Tests video processing capabilities and Haiku effectiveness
 */

import { HaikuMCPServer } from './haiku-mcp-ts/dist/server.js';
import fs from 'fs/promises';
import path from 'path';

async function ensureDirectoryExists(dirPath) {
  try {
    await fs.mkdir(dirPath, { recursive: true });
  } catch (error) {
    // Directory might already exist
  }
}

async function testHaikuMCP() {
  console.log("🧠 TESTING TYPESCRIPT HAIKU MCP SERVER");
  console.log("=" + "=".repeat(50));
  
  // Initialize server
  const server = new HaikuMCPServer();
  await server.initialize();
  
  // Ensure output directory exists
  await ensureDirectoryExists('/tmp/kompo/haiku-ffmpeg/generated-videos');
  
  const results = [];
  
  // Test 1: Music video creation
  console.log("\n🎬 Test 1: Music Video Creation");
  console.log("Description: 15-second PXL Coast music video with smooth looping");
  
  const startTime1 = Date.now();
  
  try {
    // Check if input files exist first
    const videoPath = '/tmp/kompo/haiku-ffmpeg/youtube-downloads/PXL_20250306_132546255.mp4';
    const audioPath = '/tmp/kompo/haiku-ffmpeg/youtube-downloads/Coast.mp3';
    
    let videoExists = false, audioExists = false;
    
    try {
      await fs.stat(videoPath);
      videoExists = true;
    } catch {} 
    
    try {
      await fs.stat(audioPath);
      audioExists = true;
    } catch {}
    
    console.log(`📹 Video file exists: ${videoExists ? '✅' : '❌'}`);
    console.log(`🎵 Audio file exists: ${audioExists ? '✅' : '❌'}`);
    
    if (videoExists && audioExists) {
      const result = await server.handleCreateMusicVideo({
        video_file: videoPath,
        audio_file: audioPath,
        output_file: '/tmp/kompo/haiku-ffmpeg/generated-videos/typescript-haiku-test.mp4',
        duration: 15
      });
      
      const processingTime1 = Date.now() - startTime1;
      
      console.log(`⏱️ Processing time: ${processingTime1}ms`);
      console.log(`📊 Result:`, JSON.stringify(result, null, 2));
      
      results.push({
        test: "Music Video Creation",
        success: true,
        processingTime: processingTime1,
        result: result
      });
    } else {
      console.log("❌ Skipping - input files not found");
      results.push({
        test: "Music Video Creation", 
        success: false,
        error: "Input files not found",
        processingTime: Date.now() - startTime1
      });
    }
    
  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
    results.push({
      test: "Music Video Creation",
      success: false,
      error: error.message,
      processingTime: Date.now() - startTime1
    });
  }
  
  // Test 2: LLM Stats
  console.log("\n📊 Test 2: LLM Statistics");
  
  const startTime2 = Date.now();
  
  try {
    const statsResult = await server.handleGetLLMStats();
    const processingTime2 = Date.now() - startTime2;
    
    console.log(`⏱️ Processing time: ${processingTime2}ms`);
    console.log(`📊 Stats:`, JSON.stringify(statsResult, null, 2));
    
    results.push({
      test: "LLM Statistics",
      success: true,
      processingTime: processingTime2,
      result: statsResult
    });
    
  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
    results.push({
      test: "LLM Statistics",
      success: false,
      error: error.message,
      processingTime: Date.now() - startTime2
    });
  }
  
  // Summary
  console.log("\n📋 RESULTS SUMMARY");
  console.log("=" + "=".repeat(30));
  
  const successfulTests = results.filter(r => r.success).length;
  const totalTests = results.length;
  
  console.log(`✅ Successful tests: ${successfulTests}/${totalTests}`);
  console.log(`⏱️ Total processing time: ${results.reduce((sum, r) => sum + r.processingTime, 0)}ms`);
  
  for (const result of results) {
    console.log(`\n🧪 ${result.test}: ${result.success ? '✅' : '❌'}`);
    console.log(`   Time: ${result.processingTime}ms`);
    if (result.error) {
      console.log(`   Error: ${result.error}`);
    }
  }
  
  // Save detailed results
  const reportPath = '/tmp/kompo/haiku-ffmpeg/typescript-haiku-test-results.json';
  await fs.writeFile(reportPath, JSON.stringify({
    timestamp: new Date().toISOString(),
    server: "TypeScript Haiku MCP",
    results: results,
    summary: {
      successful_tests: successfulTests,
      total_tests: totalTests,
      success_rate: (successfulTests / totalTests * 100).toFixed(1) + '%'
    }
  }, null, 2));
  
  console.log(`\n📄 Detailed results saved to: ${reportPath}`);
  
  return results;
}

// Run test
testHaikuMCP().catch(console.error);