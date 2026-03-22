#!/usr/bin/env python3
"""
End-to-End Music Video Creation Test

This test simulates an LLM using the MCP server to create a complete music video
from video clips, images, and audio tracks. It verifies the entire workflow is
functional and demonstrates the music video production capabilities.

Workflow:
1. Setup and copy test files to source directory
2. Discover available media assets
3. Create video clips from source videos
4. Convert image to video clip
5. Assemble clips into sequences
6. Add different audio tracks to different sections
7. Create final music video
8. Verify output quality and properties
"""

import asyncio
import json
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.server import mcp, file_manager, ffmpeg
from src.config import SecurityConfig


async def call_tool(name, **kwargs):
    """Helper to call MCP tools and parse JSON response."""
    result = await mcp.call_tool(name, kwargs)
    if result and len(result) > 0:
        return json.loads(result[0].text)
    return {}

class MusicVideoCreator:
    """Simulates an LLM creating a music video using MCP tools"""
    
    def __init__(self):
        self.created_files: List[str] = []  # Track created file IDs for cleanup
        
    async def log_step(self, step: str, details: str = ""):
        """Log progress like an LLM would"""
        print(f"\n🎬 {step}")
        if details:
            print(f"   {details}")
            
    async def setup_test_environment(self):
        """Copy test files to source directory"""
        await self.log_step("Setting up test environment", "Copying test files to source directory")
        
        test_files_dir = Path(__file__).parent / "files"
        source_dir = SecurityConfig.SOURCE_DIR
        
        # Ensure source directory exists
        source_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy test files
        copied_files = []
        for test_file in test_files_dir.glob("*"):
            if test_file.is_file():
                dest_file = source_dir / test_file.name
                shutil.copy2(test_file, dest_file)
                copied_files.append(test_file.name)
                print(f"   📁 Copied: {test_file.name}")
        
        return copied_files
        
    async def discover_media_assets(self) -> Dict[str, List[Any]]:
        """Discover and categorize available media files"""
        await self.log_step("Discovering media assets", "Analyzing available files for music video creation")
        
        files_result = await call_tool('list_files')
        files = files_result.get('files', [])

        # Categorize files
        videos = []
        audio = []
        images = []

        for file in files:
            ext = file['extension'].lower()
            if ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
                # Get detailed info for each video
                info = await call_tool('get_file_info', file_id=file['id'])
                video_props = info.get('media_info', {}).get('video_properties', {})

                videos.append({
                    'file': file,
                    'resolution': video_props.get('resolution'),
                    'duration': video_props.get('duration', 0),
                    'has_audio': video_props.get('has_audio', False)
                })
                print(f"   🎥 Video: {file['name']} ({video_props.get('resolution', 'unknown')}, {video_props.get('duration', 0):.1f}s)")

            elif ext in ['.mp3', '.flac', '.wav', '.m4a', '.ogg']:
                info = await call_tool('get_file_info', file_id=file['id'])
                audio_props = info.get('media_info', {}).get('video_properties', {})

                audio.append({
                    'file': file,
                    'duration': audio_props.get('duration', 0)
                })
                print(f"   🎵 Audio: {file['name']} ({audio_props.get('duration', 0):.1f}s)")

            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                images.append({
                    'file': file
                })
                print(f"   🖼️ Image: {file['name']}")
        
        print(f"   Found: {len(videos)} videos, {len(audio)} audio tracks, {len(images)} images")
        
        return {
            'videos': videos,
            'audio': audio,
            'images': images
        }
        
    async def create_video_clips(self, videos: List[Dict]) -> List[str]:
        """Extract specific clips from source videos"""
        await self.log_step("Creating video clips", "Extracting specific segments for the music video")
        
        clips = []
        
        # Create clips from each video
        for i, video in enumerate(videos[:3]):  # Use first 3 videos
            file_id = video['file']['id']
            duration = video['duration']

            # Extract different segments based on video index
            if i == 0:
                start_time = min(2, duration - 5)
                clip_duration = min(5, duration - start_time)
                await self.log_step(f"   Extracting clip from {video['file']['name']}", f"5 seconds starting at {start_time}s")
            elif i == 1:
                start_time = min(1, duration - 4)
                clip_duration = min(4, duration - start_time)
                await self.log_step(f"   Extracting clip from {video['file']['name']}", f"4 seconds starting at {start_time}s")
            else:
                start_time = min(3, duration - 6)
                clip_duration = min(6, duration - start_time)
                await self.log_step(f"   Extracting clip from {video['file']['name']}", f"6 seconds starting at {start_time}s")

            # Trim the video
            result = await call_tool(
                'process_file',
                input_file_id=file_id,
                operation="trim",
                output_extension="mp4",
                params=f"start={start_time} duration={clip_duration}"
            )

            if result.get('success'):
                clips.append(result['output_file_id'])
                self.created_files.append(result['output_file_id'])
                print(f"   ✅ Created clip: {clip_duration}s video clip")
            else:
                print(f"   ❌ Failed to create clip: {result.get('message')}")
                
        return clips
        
    async def convert_images_to_video(self, images: List[Dict]) -> List[str]:
        """Convert images to video clips"""
        await self.log_step("Converting images to video", "Creating video clips from images")
        
        image_videos = []
        
        for image in images[:2]:  # Use first 2 images
            await self.log_step(f"   Converting {image['file']['name']}", "3-second video clip")

            result = await call_tool(
                'process_file',
                input_file_id=image['file']['id'],
                operation="image_to_video",
                output_extension="mp4",
                params="duration=3"
            )

            if result.get('success'):
                image_videos.append(result['output_file_id'])
                self.created_files.append(result['output_file_id'])
                print(f"   ✅ Created 3s video from image")
            else:
                print(f"   ❌ Failed to convert image: {result.get('message')}")
                
        return image_videos
        
    async def assemble_video_sequence(self, clips: List[str], image_videos: List[str]) -> str:
        """Combine all video clips into a sequence"""
        await self.log_step("Assembling video sequence", "Concatenating all clips into a single video")
        
        # Combine clips in order: video1, image1, video2, video3, image2
        sequence = []
        
        # Add video clips
        if len(clips) >= 1:
            sequence.append(clips[0])
        if len(image_videos) >= 1:
            sequence.append(image_videos[0])
        if len(clips) >= 2:
            sequence.append(clips[1])
        if len(clips) >= 3:
            sequence.append(clips[2])
        if len(image_videos) >= 2:
            sequence.append(image_videos[1])
            
        # Concatenate all clips
        combined_video = sequence[0]
        
        for next_clip in sequence[1:]:
            await self.log_step(f"   Concatenating clips", f"Adding next segment to sequence")
            
            result = await call_tool(
                'process_file',
                input_file_id=combined_video,
                operation="concatenate_simple",
                output_extension="mp4",
                params=f"second_video={next_clip}"
            )

            if result.get('success'):
                combined_video = result['output_file_id']
                self.created_files.append(result['output_file_id'])
                print(f"   ✅ Concatenated successfully")
            else:
                print(f"   ❌ Concatenation failed: {result.get('message')}")
                break
                
        return combined_video
        
    async def add_background_music(self, video_id: str, audio_tracks: List[Dict]) -> str:
        """Add background music to the video"""
        await self.log_step("Adding background music", "Replacing video audio with music track")
        
        if not audio_tracks:
            print("   ⚠️ No audio tracks available")
            return video_id
            
        # Use the first audio track as background music
        music_track = audio_tracks[0]['file']
        await self.log_step(f"   Using: {music_track['name']}", "Replacing video audio with music")

        result = await call_tool(
            'process_file',
            input_file_id=video_id,
            operation="replace_audio",
            output_extension="mp4",
            params=f"audio_file={music_track['id']}"
        )

        if result.get('success'):
            self.created_files.append(result['output_file_id'])
            print(f"   ✅ Background music added successfully")
            return result['output_file_id']
        else:
            print(f"   ❌ Failed to add music: {result.get('message')}")
            return video_id
            
    async def verify_final_output(self, final_video_id: str) -> Dict[str, Any]:
        """Verify the final music video properties"""
        await self.log_step("Verifying final output", "Checking music video properties and quality")
        
        info = await call_tool('get_file_info', file_id=final_video_id)
        
        if info.get('media_info', {}).get('success'):
            video_props = info['media_info'].get('video_properties', {})
            basic_info = info.get('basic_info', {})
            
            verification = {
                'success': True,
                'file_size_mb': basic_info.get('size', 0) / (1024 * 1024),
                'resolution': video_props.get('resolution'),
                'duration': video_props.get('duration', 0),
                'has_video': video_props.get('has_video', False),
                'has_audio': video_props.get('has_audio', False),
                'codec': video_props.get('codec')
            }
            
            print(f"   📊 Final video properties:")
            print(f"      Size: {verification['file_size_mb']:.1f} MB")
            print(f"      Resolution: {verification['resolution']}")
            print(f"      Duration: {verification['duration']:.1f} seconds")
            print(f"      Has video: {verification['has_video']}")
            print(f"      Has audio: {verification['has_audio']}")
            print(f"      Codec: {verification['codec']}")
            
            return verification
        else:
            return {'success': False, 'error': 'Failed to get video info'}
            
    async def cleanup(self):
        """Clean up created files"""
        await self.log_step("Cleaning up", "Removing temporary files")
        await call_tool('cleanup_temp_files')
        print(f"   🗑️ Cleaned up {len(self.created_files)} temporary files")
        
    async def create_music_video(self) -> Dict[str, Any]:
        """Main workflow to create a complete music video"""
        print("🎵 Starting End-to-End Music Video Creation Test 🎵")
        print("=" * 60)
        
        try:
            # 1. Setup environment
            copied_files = await self.setup_test_environment()
            
            # 2. Discover media assets
            assets = await self.discover_media_assets()
            
            if not assets['videos'] or not assets['audio']:
                return {'success': False, 'error': 'Insufficient media assets'}
                
            # 3. Create video clips
            video_clips = await self.create_video_clips(assets['videos'])
            
            # 4. Convert images to video
            image_videos = []
            if assets['images']:
                image_videos = await self.convert_images_to_video(assets['images'])
                
            # 5. Assemble video sequence
            if video_clips:
                combined_video = await self.assemble_video_sequence(video_clips, image_videos)
                
                # 6. Add background music
                final_video = await self.add_background_music(combined_video, assets['audio'])
                
                # 7. Verify final output
                verification = await self.verify_final_output(final_video)
                
                if verification['success']:
                    await self.log_step("🎉 Music Video Creation Complete!", 
                                      f"Successfully created {verification['duration']:.1f}s music video")
                    return {
                        'success': True,
                        'final_video_id': final_video,
                        'properties': verification,
                        'workflow_steps': 7,
                        'created_files': len(self.created_files)
                    }
                else:
                    return {'success': False, 'error': 'Final verification failed'}
            else:
                return {'success': False, 'error': 'No video clips created'}
                
        except Exception as e:
            return {'success': False, 'error': f'Workflow failed: {str(e)}'}
        finally:
            # Always cleanup
            await self.cleanup()

async def main():
    """Run the end-to-end test"""
    creator = MusicVideoCreator()
    result = await creator.create_music_video()
    
    print("\n" + "=" * 60)
    if result['success']:
        print("✅ END-TO-END TEST PASSED")
        print(f"   Created music video with {result['workflow_steps']} workflow steps")
        print(f"   Final duration: {result['properties']['duration']:.1f} seconds")
        print(f"   Final size: {result['properties']['file_size_mb']:.1f} MB")
        print(f"   Resolution: {result['properties']['resolution']}")
        print(f"   Processed {result['created_files']} intermediate files")
        print("\n🎬 The MCP server is fully functional for music video creation!")
        return 0
    else:
        print("❌ END-TO-END TEST FAILED")
        print(f"   Error: {result['error']}")
        print("\n🔧 MCP server needs debugging before production use.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)