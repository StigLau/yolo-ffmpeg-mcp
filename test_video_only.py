#!/usr/bin/env python3
"""
Test video-only composition without global audio
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

async def test_video_only():
    print("🎬 Testing Video-Only Composition")
    print("=" * 50)
    
    try:
        # Import components 
        from file_manager import FileManager
        from ffmpeg_wrapper import FFMPEGWrapper
        from config import SecurityConfig
        from speech_komposition_processor import SpeechKompositionProcessor
        
        # Initialize components
        file_manager = FileManager()
        ffmpeg_wrapper = FFMPEGWrapper(SecurityConfig.FFMPEG_PATH)
        processor = SpeechKompositionProcessor(file_manager, ffmpeg_wrapper)
        
        # Check the komposition file
        komposition_file = Path("video_only_komposition.json")
        print(f"📁 Komposition file: {komposition_file}")
        print(f"📏 File exists: {komposition_file.exists()}")
        
        if not komposition_file.exists():
            print("❌ Komposition file not found!")
            return
        
        # Test the processor
        print(f"\n🎵 Processing video-only composition...")
        result = await processor.process_speech_komposition(str(komposition_file))
        
        print(f"\n📊 PROCESSING RESULTS:")
        print(f"✅ Success: {result.get('success', False)}")
        
        if result.get('success'):
            output_id = result.get('output_file_id')
            metadata = result.get('metadata', {})
            summary = result.get('processing_summary', {})
            
            print(f"🎬 Output File ID: {output_id}")
            print(f"🎵 Title: {metadata.get('title', 'Unknown')}")
            print(f"⏱️  Duration: {metadata.get('estimatedDuration', 0)}s")
            print(f"📈 Segments processed: {summary.get('segments_processed', 0)}")
            
            # Show output file path
            if output_id:
                output_path = file_manager.resolve_id(output_id)
                if output_path:
                    print(f"📂 Output path: {output_path}")
                    if output_path.exists():
                        file_size = output_path.stat().st_size
                        print(f"📏 Output size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
                        
                        if file_size > 0:
                            print(f"🎉 SUCCESS! Video composition created!")
                            print(f"🔧 Next step: Add speech overlay functionality")
                            return True
                        else:
                            print(f"❌ Output file is empty - processing issue detected")
                    else:
                        print(f"❌ Output file doesn't exist")
                else:
                    print(f"❌ Could not resolve output file path")
        else:
            error = result.get('error', 'Unknown error')
            print(f"❌ Processing failed: {error}")
        
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_video_only())
    if success:
        print(f"\n🎉 Video composition pipeline working!")
        print(f"✅ Ready to add speech overlay")
    else:
        print(f"\n❌ Video composition failed")