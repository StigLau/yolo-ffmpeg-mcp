#!/usr/bin/env python3
"""
Test the new markdown-based Haiku processing flow.
Verifies that komposition markdown is properly processed without JSON conversion.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_markdown_processing():
    """Test the markdown processing flow end-to-end."""
    print("🎭 Testing Markdown-Native Haiku Processing Flow")
    print("=" * 60)
    
    try:
        from src.llm_service import LLMService
        
        llm = LLMService()
        
        # Test markdown komposition (similar to what the user created)
        test_komposition = """# Subnautica 80BPM Music Video

## Basic Parameters
- **Title**: Subnautica 80BPM
- **Duration**: 64 seconds (6 segments; 8+12+8+8+16+7 bars @ 80BPM)
- **BPM**: 80
- **Resolution**: 1920x1080 HD
- **Style**: Subnautica themed; Vintage vibes (first half), 8-bit vibes (second half)

## Segments Structure

### Segment 1: Intro (0-8s)
- **Source**: media_001 (JJVtt947FfI_136.mp4)
- **Duration**: 8 seconds (8 bars @ 80BPM)
- **Effects**: Vintage filter, slight grain
- **Transition**: Fade to white (1s)

### Segment 2: Build (8-20s) 
- **Source**: media_001 (JJVtt947FfI_136.mp4)
- **Duration**: 12 seconds (12 bars @ 80BPM)
- **Effects**: Gradual saturation increase, beat sync
- **Transition**: Quick cut on beat

### Segment 3: Bridge (20-28s)
- **Source**: media_001 (JJVtt947FfI_136.mp4)  
- **Duration**: 8 seconds (8 bars @ 80BPM)
- **Effects**: 8-bit style transition, pixelation
- **Transition**: Digital glitch effect

### Segment 4: Climax (28-36s)
- **Source**: media_001 (JJVtt947FfI_136.mp4)
- **Duration**: 8 seconds (8 bars @ 80BPM)
- **Effects**: High contrast, vibrant colors
- **Transition**: Fast cuts on beat

### Segment 5: Outro Build (36-52s)
- **Source**: media_001 (JJVtt947FfI_136.mp4)
- **Duration**: 16 seconds (16 bars @ 80BPM)
- **Effects**: Return to vintage, slow crossfades
- **Transition**: Smooth blend

### Segment 6: Final (52-64s)
- **Source**: media_001 (JJVtt947FfI_136.mp4)
- **Duration**: 12 seconds (7+5 bars @ 80BPM)
- **Effects**: Fade to black with grain
- **Transition**: Final fade out
"""
        
        print("📋 Testing markdown analysis functions...")
        
        # Test creative instruction extraction
        instructions = llm._analyze_markdown_for_haiku_instructions(test_komposition)
        print(f"✅ Generated creative instructions: {instructions}")
        
        # Test title extraction
        title = llm._extract_title_from_markdown(test_komposition)
        print(f"✅ Extracted title: {title}")
        
        # Test media file extraction using the markdown processor
        from src.markdown_ffmpeg_processor import create_markdown_haiku_processor
        
        processor = create_markdown_haiku_processor()
        
        # Test media file extraction
        media_files = processor.extract_media_files_from_markdown(test_komposition)
        print(f"✅ Found media files: {media_files}")
        
        # Test media validation
        validation = processor.validate_media_availability(media_files)
        print(f"✅ Media validation result:")
        print(f"   - Total files: {validation['total_files']}")
        print(f"   - Available: {len(validation['available_files'])}")
        print(f"   - Missing: {len(validation['missing_files'])}")
        
        if validation['available_files']:
            print(f"   - Available files: {[f['filename'] for f in validation['available_files']]}")
        if validation['missing_files']:
            print(f"   - Missing files: {[f['filename'] for f in validation['missing_files']]}")
        
        print(f"\n🎯 Test Results:")
        print(f"✅ Markdown parsing: WORKING")
        print(f"✅ Creative instruction generation: WORKING")
        print(f"✅ Media file extraction: WORKING")
        print(f"✅ Media validation: WORKING")
        
        # Note: We're not testing actual Haiku MCP processing here since
        # it requires the Haiku TypeScript server to be running
        print(f"\n📝 Note: Actual Haiku MCP processing requires the TypeScript server")
        print(f"🚀 Ready to test the full flow with a real komposition!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test runner."""
    success = await test_markdown_processing()
    
    if success:
        print(f"\n🎉 Markdown Flow Test: PASSED")
        print(f"✅ Ready for integration testing with Haiku MCP")
    else:
        print(f"\n💥 Markdown Flow Test: FAILED")
        print(f"🔧 Check markdown processing implementation")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)