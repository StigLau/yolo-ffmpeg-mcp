/**
 * Custom Configuration Example - Factory Function Usage Pattern
 * 
 * This example shows how to use the factory function to create a server
 * with custom configuration, which is useful for different environments
 * or specialized use cases.
 */

import { createHaikuServer } from '@kompo/haiku-mcp-server';

async function main() {
  console.log('Creating Haiku MCP Server with custom configuration...');
  
  // Create server with custom configuration
  const server = await createHaikuServer({
    llm: {
      primary: 'anthropic',    // Use Anthropic Haiku as primary
      fallback: 'gemini'       // Gemini Flash as fallback
    },
    ffmpeg: {
      outputDir: '/tmp/kompo/videos',
      maxDuration: 300,        // 5 minutes max
      quality: 'high'
    },
    registry: {
      cacheDir: '/tmp/kompo/registry',
      maxFileSize: '100MB'
    },
    response_limits: {
      max_tokens: 2000,
      strip_metadata: true
    }
  });
  
  console.log('Server created with custom configuration');
  console.log('Starting server...');
  
  // Start server
  await server.run();
}

main().catch(console.error);