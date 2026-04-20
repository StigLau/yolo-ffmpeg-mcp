/**
 * Basic Usage Example - Direct Server Usage Pattern
 * 
 * This is the most common usage pattern for the Haiku MCP Server.
 * The server runs on stdio transport and communicates via MCP protocol.
 */

import { HaikuMCPServer } from '@kompo/haiku-mcp-server';

async function main() {
  console.log('Initializing Haiku MCP Server...');
  
  // Create server instance
  const server = new HaikuMCPServer();
  
  // Initialize with default configuration
  await server.initialize();
  
  console.log('Server initialized successfully');
  console.log('Starting server on stdio transport...');
  
  // Start server (this will run indefinitely)
  await server.run();
}

main().catch(console.error);