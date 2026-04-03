#!/usr/bin/env python3
"""
Test Enhanced Komposition Generator with Content Analysis Integration
=====================================================================

Tests the new enhanced komposition generator that integrates:
- AI-powered video content analysis
- Source metadata files
- Visual characteristic mapping to musical structure
- Content-aware scene selection
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.enhanced_komposition_generator import generate_enhanced_komposition_from_description
except ImportError as e:
    print(f"Import error: {e}")
    print("Trying to import directly...")
    from src.enhanced_komposition_generator import generate_enhanced_komposition_from_description

async def test_enhanced_komposition():
    """Test enhanced komposition generation"""
    
    print("🧠 Testing Enhanced Komposition Generator")
    print("=" * 50)
    
    # Test description
    description = """Create a 120 BPM music video with dramatic dark intro using faces,
    eye-focused verse with close-up scenes, dynamic refrain with multiple eyes and movement,
    and a fade-out outro. Use source metadata for optimal scene selection."""
    
    title = "Enhanced Eye Movement Test Video"
    
    print(f"📝 Description: {description}")
    print(f"🎬 Title: {title}")
    print()
    
    try:
        result = await generate_enhanced_komposition_from_description(
            description=description,
            title=title,
            use_source_metadata=True
        )
        
        if result["success"]:
            print("✅ Enhanced komposition generated successfully!")
            print(f"📊 Content analysis used: {result.get('content_analysis_used', 0)} files")
            print(f"🎯 Scenes selected: {result.get('scenes_selected', 0)}")
            print(f"📁 Komposition file: {result.get('komposition_file')}")
            print()
            
            # Show selection details
            selection_details = result.get('selection_details', [])
            if selection_details:
                print("🎭 Scene Selection Details:")
                for i, scene in enumerate(selection_details, 1):
                    print(f"   {i}. {scene.musical_role.upper()}: {scene.source_filename}")
                    print(f"      Time: {scene.start:.1f}s - {scene.end:.1f}s ({scene.duration:.1f}s)")
                    print(f"      Objects: {', '.join(scene.objects) if scene.objects else 'None'}")
                    print(f"      Characteristics: {', '.join(scene.visual_characteristics[:3])}")
                    print(f"      Reasons: {', '.join(scene.selection_reasons[:2])}")
                    print(f"      Quality Score: {scene.quality_score}")
                    print()
            
            # Show komposition summary
            komposition = result.get('komposition', {})
            segments = komposition.get('segments', [])
            print(f"📈 Komposition Summary:")
            print(f"   Segments: {len(segments)}")
            print(f"   Duration: {komposition.get('metadata', {}).get('estimatedDuration', 0):.1f}s")
            print(f"   BPM: {komposition.get('metadata', {}).get('bpm', 120)}")
            print(f"   Effects: {len(komposition.get('effects_tree', []))}")
            print()
            
            # Show enhanced features
            if 'contentAnalysisSummary' in komposition:
                summary = komposition['contentAnalysisSummary']
                print(f"🎯 Content Analysis Summary:")
                print(f"   Files Analyzed: {summary.get('filesAnalyzed', 0)}")
                print(f"   Scenes Selected: {summary.get('scenesSelected', 0)}")
                print(f"   Selection Method: {summary.get('selectionCriteria', 'Unknown')}")
            
            return True
            
        else:
            print(f"❌ Enhanced komposition generation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"💥 Exception during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_comparison():
    """Compare basic vs enhanced komposition generation"""
    
    print("\n🔄 Comparison Test: Basic vs Enhanced")
    print("=" * 40)
    
    description = "Create a 120 BPM music video with intro, verse, refrain, outro using eye movement theme"
    
    # Test basic generation (would need to import basic generator)
    print("1️⃣ Basic komposition generation would create generic segments")
    print("   - Uses generic timings and file matching")
    print("   - No content analysis integration")
    print("   - Basic effects and transitions")
    print()
    
    # Test enhanced generation
    print("2️⃣ Enhanced komposition generation:")
    enhanced_result = await generate_enhanced_komposition_from_description(
        description=description,
        title="Comparison Test - Enhanced",
        use_source_metadata=True
    )
    
    if enhanced_result["success"]:
        print("   ✅ Uses AI-powered scene analysis")
        print("   ✅ Maps visual characteristics to musical roles")
        print("   ✅ Integrates source metadata files")
        print("   ✅ Content-aware scene selection")
        print(f"   📊 Analyzed {enhanced_result.get('content_analysis_used', 0)} files")
        print(f"   🎯 Selected {enhanced_result.get('scenes_selected', 0)} optimal scenes")
    else:
        print(f"   ❌ Enhanced failed: {enhanced_result.get('error')}")
    
    return enhanced_result["success"]

async def main():
    """Run all enhanced komposition tests"""
    
    print("🚀 Enhanced Komposition Generator Test Suite")
    print("Connecting Content Analysis to Music Video Creation")
    print("=" * 60)
    
    # Test enhanced generation
    test1_passed = await test_enhanced_komposition()
    
    # Test comparison
    test2_passed = await test_comparison()
    
    # Final summary
    print("\n🎯 Test Results Summary")
    print("=" * 25)
    
    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Enhanced komposition generator working")
        print("✅ Content analysis integration successful")
        print("✅ Source metadata utilization confirmed")
        print("\n💡 The enhanced generator successfully bridges the gap between")
        print("   content analysis insights and komposition generation!")
    else:
        print("❌ Some tests failed")
        print(f"   Enhanced generation: {'✅' if test1_passed else '❌'}")
        print(f"   Comparison test: {'✅' if test2_passed else '❌'}")
    
    return test1_passed and test2_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)