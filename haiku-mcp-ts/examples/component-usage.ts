/**
 * Component Usage Example - Individual Components
 * 
 * This example shows how to use individual components from the package
 * for custom implementations or when you need more fine-grained control.
 */

import { 
  VideoProcessor, 
  HaikuClient, 
  FileManager,
  type BaseLLMClient 
} from '@kompo/haiku-mcp-server/lib';

async function main() {
  console.log('Creating individual components...');
  
  // Initialize LLM client
  const llmClient: BaseLLMClient = new HaikuClient({
    provider: 'anthropic',
    model: 'haiku-3',
    apiKey: process.env.ANTHROPIC_API_KEY!,
    maxTokens: 2000
  });
  
  // Initialize file manager
  const fileManager = new FileManager();
  
  // Initialize video processor with custom configuration
  const videoProcessor = new VideoProcessor(
    llmClient,
    {
      outputDir: '/tmp/custom-videos',
      tempDir: '/tmp/custom-temp',
      maxDuration: 600, // 10 minutes
      quality: 'high'
    },
    {
      strip_metadata: true,
      max_output_tokens: 1500,
      preserve_essential_fields: ['success', 'output_file'],
      aggressive_pruning: true
    }
  );
  
  console.log('Components initialized');
  
  // Example: Process a video file
  try {
    const result = await videoProcessor.processVideo({
      input_file: '/path/to/input/video.mp4',
      output_file: '/tmp/custom-videos/output.mp4',
      operation: 'resize',
      parameters: {
        width: 1920,
        height: 1080,
        maintain_aspect: true
      }
    });
    
    console.log('Video processing result:', result);
    
    // Register the output file
    if (result.success && result.output_file) {
      await fileManager.registerFile(result.output_file);
      console.log('File registered in registry');
    }
    
  } catch (error) {
    console.error('Video processing failed:', error);
  }
}

main().catch(console.error);