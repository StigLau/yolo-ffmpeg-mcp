#!/usr/bin/env python3
"""
Example: Form-Factor Control System Usage
Demonstrates how to use the new aspect ratio and cropping management
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from format_manager import FormatManager, COMMON_PRESETS, CropMode

def demonstrate_format_control():
    """Demonstrate the form-factor control system"""
    
    print("🎬 Form-Factor Control System Demo")
    print("=" * 50)
    
    # Initialize format manager
    format_manager = FormatManager()
    
    # 1. Show available presets
    print("\n📋 Available Format Presets:")
    for name, preset in COMMON_PRESETS.items():
        print(f"  • {name}: {preset.aspect_ratio.display_name} ({preset.width}x{preset.height}) - {preset.orientation}")
    
    # 2. Show cropping options
    print(f"\n✂️ Available Cropping Modes:")
    for crop_mode in CropMode:
        descriptions = {
            CropMode.CENTER_CROP: "Crop from center, losing edges (good for symmetric content)",
            CropMode.SMART_CROP: "AI-detected focal point cropping (best quality, slower)",
            CropMode.SCALE_LETTERBOX: "Fit with black bars (preserves all content)",
            CropMode.SCALE_BLUR_BG: "Fit with blurred background (popular for social media)",
            CropMode.SCALE_STRETCH: "Stretch to fit (may distort, not recommended)",
            CropMode.TOP_CROP: "Crop from top (good for portraits with people)",
            CropMode.BOTTOM_CROP: "Crop from bottom"
        }
        print(f"  • {crop_mode.value}: {descriptions.get(crop_mode, 'Custom crop mode')}")
    
    # 3. Simulate format analysis
    print(f"\n🔍 Example Format Analysis:")
    
    # Simulate mixed orientation videos (common real-world scenario)
    mock_videos = [
        ("Portrait phone video", 1080, 1920, "portrait"),
        ("Landscape phone video", 1920, 1080, "landscape"), 
        ("Old 4:3 video", 1024, 768, "landscape"),
        ("Square Instagram post", 1080, 1080, "square")
    ]
    
    for name, width, height, orientation in mock_videos:
        aspect_ratio = width / height
        suggested_crop = format_manager._suggest_crop_mode(width, height, aspect_ratio)
        ratings = format_manager._rate_crop_compatibility(width, height, aspect_ratio)
        
        print(f"\n  📹 {name} ({width}x{height})")
        print(f"     Aspect ratio: {aspect_ratio:.2f}")
        print(f"     Orientation: {orientation}")
        print(f"     Suggested crop: {suggested_crop.value}")
        print(f"     Best crop modes: {[mode.value for mode, rating in ratings.items() if rating == 'excellent']}")
    
    # 4. Show conversion planning
    print(f"\n📐 Format Conversion Planning:")
    
    print("\nScenario: Converting portrait phone videos to YouTube landscape")
    print("Source: 1080x1920 (9:16 portrait)")
    print("Target: 1920x1080 (16:9 landscape)")
    print("\nCropping options:")
    print("  • Center Crop: ❌ Will cut off top/bottom of people")
    print("  • Scale Letterbox: ✅ Black bars on sides, preserves all content")
    print("  • Scale Blur BG: ✅ RECOMMENDED - Blurred background, modern look")
    print("  • Stretch: ❌ Will make people look wide")
    
    print("\nScenario: Converting landscape videos to TikTok vertical")
    print("Source: 1920x1080 (16:9 landscape)")
    print("Target: 1080x1920 (9:16 portrait)")
    print("\nCropping options:")
    print("  • Center Crop: ✅ Good for centered subjects")
    print("  • Smart Crop: ✅ RECOMMENDED - AI finds best crop area")
    print("  • Scale Letterbox: ⚠️ Black bars on top/bottom")
    print("  • Scale Blur BG: ✅ Alternative - fills vertical space")
    
    # 5. MCP Tool Usage Examples
    print(f"\n🔧 MCP Tool Usage Examples:")
    
    print("\n1. Analyze video formats:")
    print("   analyze_video_formats(['file_12345', 'file_67890'])")
    print("   → Returns aspect ratios and suggests optimal target format")
    
    print("\n2. Preview format conversion:")
    print("   preview_format_conversion('file_12345', 'instagram_square', 'center_crop')")
    print("   → Generates preview image showing crop result")
    
    print("\n3. Create conversion plan:")
    print("   create_format_conversion_plan(['file1', 'file2'], 'tiktok_vertical', 'smart_crop')")
    print("   → Returns detailed FFmpeg commands and quality estimates")
    
    print("\n4. Get available presets:")
    print("   get_format_presets()")
    print("   → Lists all platform-specific format options")
    
    # 6. Best Practices
    print(f"\n💡 Best Practices:")
    print("• Choose target format BEFORE starting video editing")
    print("• Use 'auto' mode to let AI pick optimal format based on source videos")
    print("• Preview conversions with different crop modes before committing")
    print("• For mixed orientations, use 'scale_blur_bg' for professional results")
    print("• For social media, match platform specs exactly (TikTok 9:16, YouTube 16:9)")
    print("• Avoid 'scale_stretch' unless aspect ratios are very close")
    
    print(f"\n✨ Form-Factor Control System Ready!")
    print("Users can now specify format upfront and see exactly how videos will be cropped.")

if __name__ == "__main__":
    demonstrate_format_control()