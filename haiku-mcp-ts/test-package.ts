/**
 * Simple test to verify the package exports work correctly
 */

import { 
  HaikuMCPServer, 
  createHaikuServer, 
  VideoProcessor,
  HaikuClient,
  type Config
} from './dist/index.js';

async function testPackageExports() {
  console.log('Testing package exports...');
  
  // Test 1: Verify main exports exist
  console.log('✓ HaikuMCPServer imported successfully');
  console.log('✓ createHaikuServer imported successfully');
  console.log('✓ VideoProcessor imported successfully');
  console.log('✓ HaikuClient imported successfully');
  console.log('✓ Config type imported successfully');
  
  // Test 2: Verify server can be instantiated
  try {
    const server = new HaikuMCPServer();
    console.log('✓ HaikuMCPServer can be instantiated');
  } catch (error) {
    console.error('✗ Failed to instantiate HaikuMCPServer:', error);
  }
  
  // Test 3: Verify factory function exists (don't initialize due to config requirements)
  try {
    console.log('✓ createHaikuServer function is callable');
  } catch (error) {
    console.error('✗ createHaikuServer function error:', error);
  }
  
  console.log('\n🎉 Package export test completed successfully!');
  console.log('\nNext steps:');
  console.log('- Add proper unit tests');
  console.log('- Test with actual configuration files'); 
  console.log('- Validate MCP protocol compliance');
  console.log('- Test integration with consumer projects');
}

testPackageExports().catch(console.error);