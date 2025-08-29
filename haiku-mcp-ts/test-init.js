
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
