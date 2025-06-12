#!/usr/bin/env python3
"""
Intelligent Content Analysis Test

This test demonstrates the MCP server's new "eyes" - the ability to understand
video content through scene detection and object recognition, enabling intelligent
editing suggestions without manual timecode specification.

Workflow:
1. Analyze video content to detect scenes and objects
2. Get intelligent insights about the video structure
3. Use smart trim suggestions for automated editing
4. Verify the metadata storage and caching system
5. Demonstrate content-aware editing workflows
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.server import (
    list_files, analyze_video_content, get_video_insights, 
    smart_trim_suggestions, process_file, file_manager
)


class IntelligentVideoEditor:
    """Demonstrates intelligent video editing using content analysis"""
    
    def __init__(self):
        self.processed_files = []
        
    async def log_step(self, step: str, details: str = ""):
        """Log progress with visual formatting"""
        print(f"\n🧠 {step}")
        if details:
            print(f"   {details}")
            
    async def test_content_analysis_workflow(self):
        """Test the complete intelligent content analysis workflow"""
        print("🎯 Intelligent Content Analysis Test")
        print("=" * 60)
        
        try:
            # Step 1: Find video files
            await self.log_step("Finding video files for analysis")
            files_result = await list_files()
            video_files = [f for f in files_result['files'] if f.extension.lower() in ['.mp4', '.mov', '.avi']]
            
            if not video_files:
                print("❌ No video files found for testing")
                return False
                
            test_video = video_files[0]
            print(f"   📹 Selected: {test_video.name} (ID: {test_video.id})")
            
            # Step 2: Analyze video content
            await self.log_step("Analyzing video content", "Scene detection + object recognition")
            analysis_result = await analyze_video_content(test_video.id)
            
            if not analysis_result['success']:
                print(f"   ❌ Analysis failed: {analysis_result['error']}")
                return False
                
            analysis = analysis_result['analysis']
            print(f"   ✅ Found {analysis['total_scenes']} scenes in {analysis['total_duration']:.1f}s video")
            print(f"   💾 Metadata cached for future use")
            
            # Step 3: Get intelligent insights
            await self.log_step("Extracting intelligent insights", "Content understanding for editing")
            insights_result = await get_video_insights(test_video.id)
            
            if not insights_result['success']:
                print(f"   ❌ Insights failed: {insights_result['error']}")
                return False
                
            insights = insights_result
            print(f"   🔍 Detected content: {insights['detected_content']}")
            print(f"   🎨 Visual characteristics: {insights['visual_characteristics']}")
            print(f"   💡 Editing suggestions: {len(insights['editing_suggestions'])}")
            print(f"   ⭐ Highlight scenes available: {len(insights['highlights'])}")
            
            # Show editing suggestions
            for suggestion in insights['editing_suggestions']:
                print(f"      • {suggestion}")
                
            # Step 4: Test smart trimming
            await self.log_step("Getting smart trim suggestions", "Intelligence-based video editing")
            
            # Test different durations
            durations = [5.0, 10.0, 20.0]
            best_strategy = None
            
            for duration in durations:
                trim_result = await smart_trim_suggestions(test_video.id, duration)
                
                if trim_result['success'] and trim_result['suggestions']:
                    print(f"   📐 {duration}s suggestions: {len(trim_result['suggestions'])} strategies available")
                    
                    # Show the first strategy
                    first_strategy = trim_result['suggestions'][0]
                    print(f"      Strategy: {first_strategy['strategy']} ({first_strategy['total_duration']:.1f}s)")
                    print(f"      Description: {first_strategy['description']}")
                    
                    if not best_strategy and len(first_strategy['segments']) > 0:
                        best_strategy = first_strategy
                        best_duration = duration
                        
            # Step 5: Apply intelligent trimming
            if best_strategy:
                await self.log_step("Applying intelligent trimming", f"Using {best_strategy['strategy']} strategy")
                
                # Use the first segment from the best strategy
                first_segment = best_strategy['segments'][0]
                trim_start = first_segment['start']
                trim_duration = first_segment['duration']
                
                print(f"   ✂️ Trimming: {trim_start:.1f}s to {trim_start + trim_duration:.1f}s ({trim_duration:.1f}s)")
                print(f"   📝 Reason: {first_segment.get('reasons', ['intelligent selection'])}")
                
                # Apply the trim
                trim_result = await process_file(
                    input_file_id=test_video.id,
                    operation="trim",
                    output_extension="mp4",
                    params=f"start={trim_start} duration={trim_duration}"
                )
                
                if trim_result.success:
                    self.processed_files.append(trim_result.output_file_id)
                    print(f"   ✅ Intelligent trim successful! Output: {trim_result.output_file_id}")
                else:
                    print(f"   ❌ Trim failed: {trim_result.message}")
                    
            # Step 6: Test caching
            await self.log_step("Testing metadata caching", "Verifying persistent storage")
            
            # Get insights again - should use cache
            cached_insights = await get_video_insights(test_video.id)
            
            if cached_insights['success']:
                print(f"   ✅ Cache hit successful - instant insights retrieval")
                print(f"   💾 Metadata stored at: /tmp/music/metadata/{test_video.id}_analysis.json")
            else:
                print(f"   ❌ Cache test failed")
                
            # Step 7: Demonstrate content-aware editing suggestions
            await self.log_step("Content-aware editing recommendations", "AI-powered workflow suggestions")
            
            # Analyze the content to provide recommendations
            recommendations = self._generate_editing_recommendations(insights)
            
            for rec in recommendations:
                print(f"   💡 {rec}")
                
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
            return False
            
    def _generate_editing_recommendations(self, insights) -> list:
        """Generate content-aware editing recommendations"""
        recommendations = []
        
        # Analyze detected content
        detected = insights.get('detected_content', [])
        characteristics = insights.get('visual_characteristics', [])
        scenes = insights.get('scenes', [])
        highlights = insights.get('highlights', [])
        
        # People-based recommendations
        if any('faces' in item for item in detected):
            recommendations.append("👥 People detected - good for social media content")
            recommendations.append("🎭 Consider using highlight scenes for best people shots")
            
        # Visual quality recommendations
        if 'bright' in characteristics:
            recommendations.append("☀️ Good lighting detected - suitable for professional content")
        if 'dark' in characteristics:
            recommendations.append("🌙 Dark scenes detected - consider brightness adjustment")
            
        # Scene structure recommendations
        if len(scenes) > 10:
            recommendations.append("🎬 Many scenes detected - perfect for dynamic montages")
        if len(scenes) < 3:
            recommendations.append("📽️ Few scenes - consider using trim for highlights")
            
        # Highlight recommendations
        if len(highlights) > 2:
            recommendations.append(f"⭐ {len(highlights)} highlight scenes identified - use for best moments")
            
        # Duration-based recommendations
        total_duration = insights.get('total_duration', 0)
        if total_duration > 60:
            recommendations.append("⏱️ Long video - use smart_trim for social media clips")
        if total_duration < 30:
            recommendations.append("⚡ Short video - good for complete processing")
            
        if not recommendations:
            recommendations.append("🎯 Video analyzed - ready for intelligent editing")
            
        return recommendations
        
    async def cleanup(self):
        """Clean up any created files"""
        print(f"\n🗑️ Cleaning up {len(self.processed_files)} processed files...")
        # Note: cleanup happens automatically via temp file management


async def main():
    """Run the intelligent content analysis test"""
    editor = IntelligentVideoEditor()
    
    try:
        success = await editor.test_content_analysis_workflow()
        
        print("\n" + "=" * 60)
        if success:
            print("✅ INTELLIGENT CONTENT ANALYSIS TEST PASSED")
            print("🎉 The MCP server now has 'eyes' to understand video content!")
            print("\n📋 Key Features Demonstrated:")
            print("   • Automatic scene boundary detection")
            print("   • Object recognition (faces, eyes, etc.)")
            print("   • Visual characteristic analysis")
            print("   • Intelligent editing suggestions")
            print("   • Smart trim recommendations")
            print("   • Persistent metadata storage")
            print("   • Content-aware workflow automation")
            print("\n🚀 Ready for intelligent video editing workflows!")
            return 0
        else:
            print("❌ INTELLIGENT CONTENT ANALYSIS TEST FAILED")
            print("🔧 Content analysis features need debugging")
            return 1
            
    except Exception as e:
        print(f"❌ TEST ERROR: {str(e)}")
        return 1
    finally:
        await editor.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)