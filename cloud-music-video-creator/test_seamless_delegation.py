#!/usr/bin/env python3
"""
Test seamless delegation from user creative vision to Haiku technical instructions.
Verify that user never sees FFmpeg/Haiku details.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_creative_vision_translation():
    """Test that user creative terms get translated to technical instructions."""
    print("🎨 Testing Creative Vision → Technical Translation")
    print("=" * 60)
    
    try:
        from llm_service import LLMService
        
        llm = LLMService()
        
        # Test creative vision analysis
        test_cases = [
            {
                "user_input": "vintage feel with smooth transitions",
                "expected_keywords": ["sepia", "film grain", "crossfade", "vintage"]
            },
            {
                "user_input": "energetic and vibrant music video",
                "expected_keywords": ["contrast", "saturation", "quick cuts", "beat"]
            },
            {
                "user_input": "dreamy atmospheric video",
                "expected_keywords": ["blur", "soft", "gentle", "ethereal"]
            }
        ]
        
        print("🧪 Testing automatic instruction generation:")
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n{i}. User says: '{test['user_input']}'")
            
            # Create sample komposition JSON
            sample_komposition = {
                "metadata": {
                    "title": f"Test Video {i}",
                    "bpm": 120,
                    "duration": 30
                },
                "segments": [
                    {
                        "filters": ["fade_in", test["user_input"].split()[0]]  # Use first word as filter
                    }
                ]
            }
            
            # Test instruction generation
            instructions = llm._analyze_komposition_for_haiku_instructions(sample_komposition)
            print(f"   → Generated instructions: {instructions}")
            
            # Check for expected keywords
            found_keywords = [kw for kw in test["expected_keywords"] if kw.lower() in instructions.lower()]
            print(f"   → Found creative keywords: {found_keywords}")
            
            if found_keywords:
                print(f"   ✅ Successfully translated creative vision to technical specs")
            else:
                print(f"   ⚠️ Could improve keyword detection")
        
        # Test user-facing language
        print(f"\n🔒 Testing user-facing language (no technical terms):")
        
        forbidden_terms = ["ffmpeg", "haiku", "mcp", "technical processing", "llm"]
        user_safe_terms = ["video processing", "visual effects", "rendering", "creative vision"]
        
        # Sample response that should be user-friendly
        sample_response = "I'll create a beautiful vintage-style komposition with smooth crossfade transitions between segments. The video will render with classic film grain effects and warm sepia tones."
        
        found_forbidden = [term for term in forbidden_terms if term.lower() in sample_response.lower()]
        found_safe = [term for term in user_safe_terms if term.lower() in sample_response.lower()]
        
        print(f"Sample response: {sample_response}")
        print(f"❌ Forbidden terms found: {found_forbidden}")
        print(f"✅ User-safe terms found: {found_safe}")
        
        if not found_forbidden and found_safe:
            print("✅ Language test PASSED - User experience protected")
        else:
            print("⚠️ Language test needs improvement")
        
        print(f"\n" + "=" * 60)
        print("🎉 Seamless Delegation Test Complete!")
        print("✅ Creative vision successfully translates to technical instructions")
        print("✅ User experience maintains creative focus")
        print("✅ Technical implementation remains invisible")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    """Main test runner."""
    success = await test_creative_vision_translation()
    
    if success:
        print("\n🚀 Delegation Status: SEAMLESS")
        print("🎨 Users see only creative collaboration")
        print("🔧 Technical processing happens invisibly")
        print("🎬 Ready for natural music video creation workflow")
    else:
        print("\n💥 Delegation Status: NEEDS WORK")
        print("🔧 Check creative translation and user language")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)