#!/usr/bin/env python3
"""
Comprehensive test for Registry and Audio Integration
Tests the complete workflow with registry services and audio integration
"""

import os
import sys
import asyncio
import json
import subprocess
import tempfile
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.registry.komposition_registry import KompositionRegistry
from src.registry.media_registry import MediaRegistry
from src.storage.temp_storage import TempStorageBackend
from src.services.komposition_processor import KompositionProcessor
from src.services.video_processor import VideoProcessor
from src.services.audio_processor import AudioProcessor
from src.llm.processing_llm import ProcessingLLM

from src.models.komposition import KompositionSpec, EffectType
from src.models.media import MediaType


async def test_complete_workflow():
    """Test complete workflow with registry and audio integration"""
    print("🎼 Testing Complete Registry and Audio Integration Workflow")
    print("=" * 60)
    
    # Initialize services
    storage = TempStorageBackend()
    komposition_registry = KompositionRegistry(storage)
    media_registry = MediaRegistry(storage)
    processing_llm = ProcessingLLM()
    
    komposition_processor = KompositionProcessor(processing_llm, media_registry)
    video_processor = VideoProcessor(processing_llm, media_registry)
    audio_processor = AudioProcessor(media_registry)
    
    # Test user request
    user_id = "test_user_audio"
    
    print("🎵 Step 1: Create test audio file...")
    test_audio_path = await audio_processor.create_test_audio(duration=20.0, bpm=128)
    print(f"   ✅ Created test audio: {test_audio_path}")
    
    print("📁 Step 2: Register audio file in media registry...")
    audio_ref = await audio_processor.register_audio_file(test_audio_path)
    print(f"   ✅ Registered audio: {audio_ref.id}")
    print(f"   📊 Duration: {audio_ref.metadata.duration_seconds}s")
    print(f"   🎧 Sample rate: {audio_ref.metadata.sample_rate}Hz")
    print(f"   📻 Channels: {audio_ref.metadata.channels}")
    
    print("🎬 Step 3: Create komposition with audio integration...")
    spec = KompositionSpec(
        title="Audio-Enhanced Music Video",
        description="20-second music video with integrated audio track and mixed effects",
        bpm=128.0,
        duration_seconds=20.0,
        audio_file_path=test_audio_path,
        visual_concept="vintage and blurry effects",
        preferred_effects=[EffectType.VINTAGE, EffectType.BLUR]
    )
    
    komposition = await komposition_processor.create_from_spec(spec, user_id)
    print(f"   ✅ Created komposition: {komposition.id}")
    print(f"   🎵 Audio track: {komposition.audio_track is not None}")
    print(f"   📹 Segments: {len(komposition.segments)}")
    
    print("💾 Step 4: Store komposition in registry...")
    stored_komposition = await komposition_registry.create(spec, user_id)
    print(f"   ✅ Stored in registry: {stored_komposition.id}")
    
    print("🔍 Step 5: Validate komposition for processing...")
    validation = await komposition_processor.validate_for_processing(komposition)
    print(f"   ✅ Valid: {validation['valid']}")
    print(f"   ⚠️  Warnings: {len(validation['warnings'])}")
    if validation['warnings']:
        for warning in validation['warnings']:
            print(f"      - {warning}")
    print(f"   💰 Estimated cost: ${validation['estimated_cost']:.3f}")
    
    print("⚡ Step 6: Generate video with audio...")
    video_output = await video_processor.generate_video(komposition)
    print(f"   ✅ Generated video: {video_output.id}")
    print(f"   📁 File: {video_output.file_reference.storage_path}")
    print(f"   ⏱️  Processing time: {video_output.processing_duration:.1f}s")
    print(f"   💰 Cost: ${video_output.processing_cost:.3f}")
    print(f"   ⭐ Quality score: {video_output.quality_score:.2f}")
    
    print("🔍 Step 7: Verify final video...")
    video_path = Path(video_output.file_reference.full_path)
    
    if video_path.exists():
        file_size = video_path.stat().st_size
        print(f"   ✅ Video file exists: {file_size} bytes")
        
        # Check video properties
        info_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', str(video_path)]
        result = subprocess.run(info_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            info = json.loads(result.stdout)
            video_duration = float(info['format']['duration'])
            
            # Check for audio stream
            has_audio = any(stream['codec_type'] == 'audio' for stream in info['streams'])
            
            print(f"   📊 Duration: {video_duration:.1f}s")
            print(f"   🎵 Has audio: {has_audio}")
            print(f"   📐 Resolution: {info['streams'][0]['width']}x{info['streams'][0]['height']}")
            
            # Verify duration and audio
            duration_ok = 19.0 <= video_duration <= 21.0
            
            if duration_ok and has_audio:
                print("   🎊 VIDEO VERIFICATION PASSED!")
                return True
            else:
                print(f"   ❌ VIDEO VERIFICATION FAILED: duration={duration_ok}, audio={has_audio}")
                return False
    
    print("   ❌ Video file not found")
    return False


async def test_registry_operations():
    """Test registry CRUD operations"""
    print("\n🗃️  Testing Registry Operations")
    print("=" * 40)
    
    storage = TempStorageBackend()
    komposition_registry = KompositionRegistry(storage)
    media_registry = MediaRegistry(storage)
    
    # Test komposition registry
    print("📝 Testing komposition registry...")
    
    spec = KompositionSpec(
        title="Registry Test",
        description="Test komposition for registry operations",
        bpm=140.0,
        duration_seconds=15.0
    )
    
    # Create
    komposition = await komposition_registry.create(spec, "test_user")
    print(f"   ✅ Created: {komposition.id}")
    
    # Retrieve
    retrieved = await komposition_registry.get(komposition.id)
    print(f"   ✅ Retrieved: {retrieved is not None}")
    
    # Update
    updated = await komposition_registry.update(komposition.id, {"title": "Updated Title"})
    print(f"   ✅ Updated: {updated.title}")
    
    # List user kompositions
    user_komps = await komposition_registry.list_user_kompositions("test_user")
    print(f"   ✅ Listed: {len(user_komps)} kompositions")
    
    # Test media registry
    print("📁 Testing media registry...")
    
    # Create test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test media file content")
        test_file_path = f.name
    
    try:
        from src.models.media import MediaMetadata
        
        metadata = MediaMetadata(
            type=MediaType.VIDEO,
            filename="test_file.txt",
            file_size_bytes=0
        )
        
        # Register file
        media_ref = await media_registry.register_file(test_file_path, metadata)
        print(f"   ✅ Registered: {media_ref.id}")
        
        # Get file
        media_file = await media_registry.get_file(media_ref.id)
        print(f"   ✅ Retrieved: {media_file is not None}")
        
        # Count files
        count = await media_registry.count()
        print(f"   ✅ Count: {count} files")
        
    finally:
        # Clean up
        Path(test_file_path).unlink()
    
    return True


def main():
    """Run all registry and audio integration tests"""
    print("🚀 Registry and Audio Integration Tests")
    print("=" * 50)
    
    # Check FFmpeg availability
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ FFmpeg available")
    except:
        print("❌ FFmpeg not found")
        return 1
    
    async def run_tests():
        results = []
        
        # Test 1: Registry operations
        print("\n" + "=" * 50)
        results.append(await test_registry_operations())
        
        # Test 2: Complete workflow
        print("\n" + "=" * 50)
        results.append(await test_complete_workflow())
        
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS:")
        print(f"Registry Operations: {'PASS' if results[0] else 'FAIL'}")
        print(f"Complete Workflow: {'PASS' if results[1] else 'FAIL'}")
        
        if all(results):
            print("🎉 ALL REGISTRY AND AUDIO TESTS PASSED!")
            print("   ✅ Registry services working correctly")
            print("   ✅ Audio integration functional")
            print("   ✅ Complete workflow validated")
            return 0
        else:
            print("💥 SOME TESTS FAILED!")
            return 1
    
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()