#!/usr/bin/env python3
"""
Test speech komposition processing
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

async def test_speech_komposition():
    print("🎬 Testing Speech Komposition Processing")
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
        komposition_file = Path("speech_music_video_komposition.json")
        print(f"📁 Komposition file: {komposition_file}")
        print(f"📏 File exists: {komposition_file.exists()}")
        
        if not komposition_file.exists():
            print("❌ Komposition file not found!")
            return
        
        # Test the processor
        print(f"\n🎵 Processing speech komposition...")
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
            print(f"🎤 Speech segments: {summary.get('speech_segments_found', 0)}")
            
            # Show output file path
            if output_id:
                output_path = file_manager.resolve_id(output_id)
                if output_path:
                    print(f"📂 Output path: {output_path}")
                    if output_path.exists():
                        file_size = output_path.stat().st_size
                        print(f"📏 Output size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
        else:
            error = result.get('error', 'Unknown error')
            print(f"❌ Processing failed: {error}")
        
        print(f"\n{'='*50}")
        print("🎉 Speech komposition test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   This is expected without MCP dependencies installed")
    except Exception as e:
        print(f"❌ Test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_speech_komposition())