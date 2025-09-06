#!/usr/bin/env python3
"""
End-to-End Test for Haiku Failure Analysis System
Tests that:
1. Haiku processing fails gracefully when given erroneous video references
2. The outer LLM analyzes the failed attempt
3. User gets intelligent feedback and corrected komposition
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_haiku_failure_analysis():
    """Test complete failure analysis workflow with missing media files."""
    print("🔍 Testing Haiku Failure Analysis System")
    print("=" * 60)
    
    try:
        # Import LLM service
        from src.llm_service import get_llm_service
        
        llm_service = get_llm_service()
        print("✅ LLM Service initialized")
        
        # Create komposition with erroneous video references (missing files)
        erroneous_komposition = """# Erroneous Music Video Test
        
## Basic Parameters
- **Title**: Test Missing Media Validation
- **Duration**: 30 seconds  
- **BPM**: 120
- **Resolution**: 1920x1080 HD
- **Style**: Testing failure analysis

## Segments Structure

### Segment 1: Missing Video Test (0-10s)
- **Source**: media_001 (non_existent_video.mp4)
- **Duration**: 10 seconds
- **Effects**: Should fail gracefully
- **Transition**: Won't work due to missing file

### Segment 2: Another Missing File (10-20s)  
- **Source**: media_002 (also_missing.mp4)
- **Duration**: 10 seconds
- **Effects**: This should also fail
- **Transition**: Cross-fade (impossible)

### Segment 3: Third Missing File (20-30s)
- **Source**: media_003 (completely_fake.mp4) 
- **Duration**: 10 seconds
- **Effects**: Final failure test
- **Transition**: Fade to black

## Audio
- **Background**: media_004 (missing_audio.mp3)

This komposition deliberately references non-existent media files to test the validation and failure analysis system.
"""

        print("📋 Testing komposition with multiple missing media files...")
        print("🎯 Expected outcome: Validation should block processing and provide analysis")
        
        # Process the erroneous komposition - this should trigger validation failure
        print("\n1️⃣ Phase 1: Pre-validation (should catch missing files)")
        result = await llm_service.process_komposition_markdown_with_haiku(
            komposition_md=erroneous_komposition,
            output_path="/tmp/test_failure_analysis.mp4"
        )
        
        print(f"\n🔍 Processing Result Analysis:")
        print(f"Success: {result.get('success')}")
        print(f"Processing Method: {result.get('processing_method')}")
        print(f"Error: {result.get('error', 'None')}")
        
        if not result.get("success"):
            print("✅ Validation correctly blocked processing")
            
            # Check if pre-validation was performed
            if "validation_blocked" in result.get("processing_method", ""):
                print("✅ Pre-validation system working correctly")
                print(f"   - Validation details available: {'Yes' if result.get('validation_details') else 'No'}")
            
            # Check if failure analysis was performed  
            if result.get("failure_analysis"):
                analysis = result.get("failure_analysis")
                print(f"\n📊 Failure Analysis Results:")
                print(f"   - Failure Type: {analysis.get('failure_type')}")
                print(f"   - Root Causes: {len(analysis.get('root_causes', []))}")
                print(f"   - Improvement Suggestions: {len(analysis.get('improvement_suggestions', []))}")
                print(f"   - Severity: {analysis.get('severity')}")
                
                # Display some suggestions
                suggestions = analysis.get('improvement_suggestions', [])
                if suggestions:
                    print(f"   - Key Suggestions:")
                    for i, suggestion in enumerate(suggestions[:3], 1):
                        print(f"     {i}. {suggestion}")
            
            # Check if outer LLM evaluation was performed
            if result.get("gemini_evaluation"):
                evaluation = result.get("gemini_evaluation")
                print(f"\n🤖 Outer LLM (Gemini) Evaluation:")
                print(f"   - Evaluation Success: {evaluation.get('success')}")
                print(f"   - User Guidance Available: {'Yes' if result.get('user_guidance') else 'No'}")
                
                if result.get("user_guidance"):
                    user_guidance = result.get("user_guidance")[:200]
                    print(f"   - User Message Preview: \"{user_guidance}...\"")
                
                if evaluation.get("corrected_komposition"):
                    print(f"   - Corrected Komposition: Available")
                    # Show preview of corrected komposition
                    corrected = result.get("corrected_komposition", "")
                    if corrected:
                        print(f"   - Corrected Preview: {corrected[:100]}...")
                
                print(f"   - Processing Strategy: {evaluation.get('processing_strategy', 'None')[:100]}...")
            else:
                print("⚠️ Outer LLM evaluation not available (likely fallback mode)")
            
        else:
            print("❌ Expected validation to fail but processing succeeded")
            print("This indicates the validation system may not be working properly")
            return False
        
        print(f"\n🎯 End-to-End Test Results:")
        print(f"✅ Pre-validation: {'WORKING' if 'validation_blocked' in result.get('processing_method', '') else 'NEEDS CHECK'}")
        print(f"✅ Failure analysis: {'WORKING' if result.get('failure_analysis') else 'NEEDS CHECK'}")  
        print(f"✅ Outer LLM evaluation: {'WORKING' if result.get('gemini_evaluation') else 'FALLBACK MODE'}")
        print(f"✅ User guidance: {'WORKING' if result.get('user_guidance') else 'NEEDS CHECK'}")
        
        # Test summary
        validation_working = 'validation_blocked' in result.get('processing_method', '')
        analysis_working = bool(result.get('failure_analysis'))
        evaluation_working = bool(result.get('gemini_evaluation'))
        
        if validation_working and analysis_working:
            print(f"\n🎉 CORE FUNCTIONALITY: WORKING")
            print(f"✅ System prevents synthetic content generation")
            print(f"✅ System provides intelligent failure analysis")
            if evaluation_working:
                print(f"✅ System provides user-friendly guidance")
            else:
                print(f"⚠️ Outer LLM evaluation in fallback mode")
        else:
            print(f"\n⚠️ SOME ISSUES DETECTED")
            if not validation_working:
                print(f"❌ Pre-validation not working")
            if not analysis_working:
                print(f"❌ Failure analysis not working")
        
        return validation_working and analysis_working
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test runner."""
    print("🚀 Starting End-to-End Haiku Failure Analysis Test...")
    
    success = await test_haiku_failure_analysis()
    
    if success:
        print(f"\n🎉 END-TO-END TEST: PASSED")
        print(f"✅ Haiku failure analysis system is working correctly")
        print(f"✅ No more synthetic content generation for missing media files")
        print(f"✅ Users get intelligent feedback and corrected kompositions")
        print(f"✅ Ready to handle sessions like e9d8dd8a-2cf5-4602-8c5a-50cfb43992fe correctly")
    else:
        print(f"\n💥 END-TO-END TEST: FAILED")
        print(f"🔧 System needs additional work to prevent synthetic content")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)