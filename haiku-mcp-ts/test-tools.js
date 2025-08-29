
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
      console.log(`❌ Missing tool: ${tool}`);
      process.exit(1);
    }
  }
  
  console.log('✅ All expected tools found in server code');
  process.exit(0);
} catch (error) {
  console.log('❌ Tool check failed:', error.message);
  process.exit(1);
}
