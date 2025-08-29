
import { sanitizeResponse, sanitizeFFMPEGOutput, sanitizeYouTubeOutput } from './dist/utils/sanitization.js';

try {
  // Test FFMPEG output sanitization
  const ffmpegOutput = `ffmpeg version 4.4.0-0ubuntu1
built with gcc 9 (Ubuntu 9.4.0-1ubuntu1~20.04.2)
configuration: --prefix=/usr --extra-version=0ubuntu1
libavutil      56. 70.100 / 56. 70.100
Stream #0:0: Video: h264 (High), yuv420p, 1920x1080 [SAR 1:1 DAR 16:9], 25 fps
size=    1024kB time=00:00:10.00 bitrate= 838.9kbits/s fps=25.0 q=28.0 size=    2048kB time=00:00:20.00`;

  const config = { strip_metadata: true, max_output_tokens: 100, preserve_essential_fields: [], aggressive_pruning: true };
  const result = sanitizeFFMPEGOutput(ffmpegOutput, config);
  
  if (result.reduction_percentage < 50) {
    console.log('❌ FFMPEG sanitization not effective enough:', result.reduction_percentage);
    process.exit(1);
  }
  
  console.log(`✅ FFMPEG sanitization: ${result.reduction_percentage}% reduction`);
  
  // Test YouTube output sanitization  
  const youtubeOutput = `format code  extension  resolution note
140          m4a        audio only tiny  130k , m4a_dash container, mp4a.40.2@128k (44100Hz), 4.26MiB
298          mp4        1280x720   720p  2998k , mp4_dash container, avc1.4d401f@2998k, 30fps, video only, 98.84MiB
[download] Downloading video 1 of 1
[download] Destination: /tmp/test.mp4`;

  const ytResult = sanitizeYouTubeOutput(youtubeOutput, config);
  
  if (ytResult.reduction_percentage < 60) {
    console.log('❌ YouTube sanitization not effective enough:', ytResult.reduction_percentage);  
    process.exit(1);
  }
  
  console.log(`✅ YouTube sanitization: ${ytResult.reduction_percentage}% reduction`);
  
  console.log('✅ All sanitization tests passed');
  process.exit(0);
} catch (error) {
  console.log('❌ Sanitization test failed:', error.message);
  process.exit(1);
}
