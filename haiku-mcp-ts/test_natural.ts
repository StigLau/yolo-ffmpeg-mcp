import { HaikuMCPClient } from './client.ts';

async function createNaturalLanguageVideo() {
  const client = new HaikuMCPClient();
  
  try {
    await client.connect();
    
    // Get available files
    const filesList = await client.callTool('list_files', {});
    const files = JSON.parse(filesList.content[0].text).files;
    
    const videoFile = files.find(f => f.mediaType === 'video');
    const audioFile = files.find(f => f.mediaType === 'audio');
    
    if (!videoFile || !audioFile) {
      throw new Error('No video or audio files found');
    }
    
    console.log('📹 Using video:', videoFile.id);
    console.log('🎵 Using audio:', audioFile.id);
    console.log('');
    
    // Create music video
    const response = await client.callTool('create_music_video', {
      video_file: videoFile.id,
      audio_file: audioFile.id,
      output_file: '/tmp/kompo/haiku-ffmpeg/generated-videos/natural_20250901_094056.mp4',
      duration: 18
    });
    
    const result = JSON.parse(response.content[0].text);
    
    if (result.success) {
      console.log('✅ Success!');
      console.log('📁 Output:', '/tmp/kompo/haiku-ffmpeg/generated-videos/natural_20250901_094056.mp4');
      console.log('💰 Cost: $' + (result.llm_cost || 0).toFixed(6));
      console.log('⏱️  Time:', (result.execution_time_ms || 0) + 'ms');
    } else {
      console.log('❌ Failed:', result.error);
      console.log('🛠️  Command:', result.command_used);
    }
    
    await client.disconnect();
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

createNaturalLanguageVideo();
