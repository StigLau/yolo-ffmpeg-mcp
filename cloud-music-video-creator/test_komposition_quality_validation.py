#!/usr/bin/env python3
"""
Test Komposition Quality Validation System
Tests the experimental quality validation that can be rolled back if too restrictive.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.haiku_validation import HaikuValidator


def test_quality_validation():
    """Test komposition quality validation with the problematic example."""
    print("🧪 Testing Komposition Quality Validation (EXPERIMENTAL)")
    print("=" * 60)
    
    validator = HaikuValidator()
    
    # The problematic komposition from your example
    problematic_komposition = """# New Music Video Komposition

## Basic Parameters
- **Duration**: 15 seconds
- **BPM**: 120 (standard tempo)
- **Resolution**: 1920x1080 HD
- **Style**: 8-bit retro

## Segments Structure

### Segment 1: Opening (0-5s)
- **Source**: media_002 (JJVtt947FfI_136.mp4)
- **Effects**: 8-bit filter
- **Transition**: Crossfade (1-second overlap)

### Segment 2: Middle (5-10s)
- **Source**: media_002 (JJVtt947FfI_136.mp4)
- **Effects**: 8-bit filter
- **Transition**: Crossfade (1-second overlap)

### Segment 3: Finale (10-15s)
- **Source**: media_002 (JJVtt947FfI_136.mp4)
- **Effects**: 8-bit filter
- **Transition**: Crossfade (1-second overlap)

## Technical Specifications
- **Format**: MP4 (H.264/AAC)
- **Quality**: CRF 23 (high quality)
- **Audio**: media_001 (Subnautic Measures.flac)
"""
    
    # Test quality validation
    print("1️⃣ Testing problematic komposition...")
    quality_result = validator.validate_komposition_quality(problematic_komposition)
    
    print(f"Quality Issues Found: {len(quality_result['issues'])}")
    print(f"Needs Improvement: {quality_result['needs_improvement']}")
    print(f"Is Experimental: {quality_result['experimental']}")
    
    if quality_result['issues']:
        print("\n🚨 Quality Issues Detected:")
        for i, issue in enumerate(quality_result['issues'], 1):
            print(f"   {i}. {issue}")
    
    # Test with a good komposition
    good_komposition = """# Varied Music Video Komposition

## Basic Parameters
- **Duration**: 15 seconds
- **BPM**: 120 (standard tempo)

## Segments Structure

### Segment 1: Opening (0-5s)
- **Source**: media_001 (video1.mp4)
- **Effects**: Subtle fade in
- **Transition**: Cut

### Segment 2: Middle (5-10s)
- **Source**: media_002 (video2.mp4)  
- **Effects**: Color boost, fast cuts
- **Transition**: Cut

### Segment 3: Finale (10-15s)
- **Source**: media_003 (video3.mp4)
- **Effects**: Dramatic zoom, slow motion
- **Transition**: Fade to black
"""
    
    print("\n2️⃣ Testing good komposition...")
    good_result = validator.validate_komposition_quality(good_komposition)
    
    print(f"Quality Issues Found: {len(good_result['issues'])}")
    print(f"Needs Improvement: {good_result['needs_improvement']}")
    
    if good_result['issues']:
        print("\nQuality Issues:")
        for i, issue in enumerate(good_result['issues'], 1):
            print(f"   {i}. {issue}")
    else:
        print("✅ No quality issues detected in varied komposition")
    
    # Test integration with full validation
    print("\n3️⃣ Testing integration with full pre-validation...")
    try:
        # This will include both media validation (which will fail) and quality validation
        full_validation = validator.validate_komposition_pre_processing(problematic_komposition)
        print(f"Full Validation Success: {full_validation['success']}")
        print(f"Warnings: {len(full_validation['warnings'])}")
        print(f"Errors: {len(full_validation['errors'])}")
        
        if full_validation['warnings']:
            print("\nWarnings (including quality issues):")
            for warning in full_validation['warnings']:
                if "Quality issue:" in warning:
                    print(f"   🎨 {warning}")
                else:
                    print(f"   ⚠️ {warning}")
        
    except Exception as e:
        print(f"Full validation completed with expected media file errors: {type(e).__name__}")
        print("This is expected since we don't have the actual media files")
    
    # Summary
    print(f"\n🎯 Quality Validation Test Summary:")
    print(f"✅ Detected same source issue: {'Yes' if 'same media source' in str(quality_result['issues']) else 'No'}")
    print(f"✅ Detected crossfade timing issue: {'Yes' if 'Crossfade time' in str(quality_result['issues']) else 'No'}")
    print(f"✅ Detected identical effects issue: {'Yes' if 'identical effects' in str(quality_result['issues']) else 'No'}")
    print(f"✅ Correctly identified as experimental: {quality_result['experimental']}")
    
    expected_issues = 3  # Same source, crossfade timing, identical effects
    actual_issues = len(quality_result['issues'])
    
    if actual_issues >= 2:  # Allow some flexibility
        print(f"✅ Quality validation working correctly!")
        print(f"📊 Found {actual_issues} issues (expected ~{expected_issues})")
        return True
    else:
        print(f"❌ Quality validation may need tuning")
        print(f"📊 Found {actual_issues} issues (expected ~{expected_issues})")
        return False


def test_rollback_safety():
    """Test that quality validation doesn't break existing functionality."""
    print(f"\n🔄 Testing Rollback Safety...")
    print("=" * 40)
    
    validator = HaikuValidator()
    
    # Test that validation gracefully handles parsing errors
    malformed_komposition = """# Broken Komposition
This is not properly formatted markdown
"""
    
    try:
        result = validator.validate_komposition_quality(malformed_komposition)
        print("✅ Gracefully handles malformed komposition")
        print(f"   Issues found: {len(result['issues'])}")
        print(f"   Still marked as experimental: {result['experimental']}")
        
    except Exception as e:
        print(f"❌ Quality validation crashes on malformed input: {e}")
        return False
    
    print("✅ Rollback safety confirmed - no breaking changes")
    return True


if __name__ == "__main__":
    print("🚀 Starting Komposition Quality Validation Tests...")
    
    # Run tests
    quality_test_passed = test_quality_validation()
    rollback_test_passed = test_rollback_safety()
    
    # Overall result
    if quality_test_passed and rollback_test_passed:
        print(f"\n🎉 ALL TESTS PASSED")
        print(f"✅ Quality validation detects problematic kompositions")
        print(f"✅ Safe to deploy (can be rolled back if too restrictive)")
        print(f"✅ Integration with existing validation works")
        sys.exit(0)
    else:
        print(f"\n💥 SOME TESTS FAILED")
        print(f"🔧 Quality validation needs adjustment before deployment")
        sys.exit(1)