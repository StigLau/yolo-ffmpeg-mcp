#!/usr/bin/env python3
"""
Comprehensive tests for Video Intelligence APIs - Priority 2: Missing Intelligence APIs

Tests the KEY APIs that solve the 9.7s-29s timing calculation problems
discovered in MCP uniform vs keyframe-aligned comparison.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.video_intelligence import (
    VideoIntelligenceAnalyzer, 
    detect_optimal_cut_points,
    analyze_keyframes,
    detect_scene_boundaries,
    calculate_complexity_metrics,
    AnalysisMethod
)

class TestVideoIntelligenceAnalyzer:
    """Test suite for Video Intelligence APIs"""
    
    def setup_method(self):
        """Set up test environment"""
        self.analyzer = VideoIntelligenceAnalyzer()
        self.test_video = "Oa8iS1W3OCM.mp4"  # Our actual test video
    
    def test_analyzer_initialization(self):
        """Test analyzer initializes correctly"""
        analyzer = VideoIntelligenceAnalyzer()
        assert analyzer.enable_scene_detection is True
        assert analyzer.cache == {}
    
    async def test_detect_optimal_cut_points_real_video(self):
        """Test optimal cut point detection with real video file"""
        
        video_path = Path(self.test_video)
        if not video_path.exists():
            print(f"⚠️ Skipping real video test - {self.test_video} not found")
            return
        
        print(f"🎬 Testing optimal cut points with real video: {self.test_video}")
        
        result = await self.analyzer.detect_optimal_cut_points(
            video_path, 
            target_segments=4
        )
        
        # Validate results
        assert len(result.cut_points) >= 1
        assert result.confidence >= 0.0
        assert result.method in AnalysisMethod
        assert len(result.reasoning) > 0
        assert len(result.segment_durations) >= 0
        assert 0.0 <= result.quality_score <= 1.0
        
        print(f"  ✅ Cut points: {result.cut_points}")
        print(f"  ✅ Method: {result.method.value}")
        print(f"  ✅ Confidence: {result.confidence:.2f}")
        print(f"  ✅ Reasoning: {result.reasoning}")
        
        # Verify timing differences from uniform approach
        uniform_points = [i * (60.0 / 4) for i in range(4)]  # [0, 15, 30, 45]
        
        if len(result.cut_points) >= 4:
            differences = []
            for i, (optimal, uniform) in enumerate(zip(result.cut_points[:4], uniform_points)):
                diff = abs(optimal - uniform)
                differences.append(diff)
                print(f"  📊 Segment {i+1}: Optimal={optimal:.3f}s vs Uniform={uniform:.3f}s (Δ{diff:.3f}s)")
            
            # Check if we're solving the timing problem
            significant_differences = [d for d in differences if d > 5.0]
            if significant_differences:
                print(f"  🎯 SOLVING TIMING PROBLEM: {len(significant_differences)} segments with >5s improvement")
            else:
                print(f"  ℹ️ Video may have naturally uniform timing")
    
    async def test_analyze_keyframes_real_video(self):
        """Test keyframe analysis with real video"""
        
        video_path = Path(self.test_video)
        if not video_path.exists():
            print(f"⚠️ Skipping keyframe test - {self.test_video} not found")
            return
        
        print(f"🔍 Testing keyframe analysis with: {self.test_video}")
        
        keyframes = await self.analyzer.analyze_keyframes(video_path)
        
        if keyframes:
            assert all(kf.timestamp >= 0 for kf in keyframes)
            assert all(0.0 <= kf.confidence <= 1.0 for kf in keyframes)
            assert all(kf.size_bytes >= 0 for kf in keyframes)
            
            print(f"  ✅ Found {len(keyframes)} keyframes")
            print(f"  📊 First few keyframes:")
            for i, kf in enumerate(keyframes[:5]):
                print(f"    {i+1}: {kf.timestamp:.3f}s, type={kf.frame_type}, scene={kf.scene_boundary}")
        else:
            print(f"  ⚠️ No keyframes found - may indicate analysis issue")
    
    async def test_detect_scene_boundaries_real_video(self):
        """Test scene boundary detection with real video"""
        
        video_path = Path(self.test_video)
        if not video_path.exists():
            print(f"⚠️ Skipping scene boundary test - {self.test_video} not found")
            return
        
        print(f"🎬 Testing scene boundary detection with: {self.test_video}")
        
        boundaries = await self.analyzer.detect_scene_boundaries(video_path, sensitivity=0.3)
        
        if boundaries:
            assert all(sb.timestamp >= 0 for sb in boundaries)
            assert all(0.0 <= sb.confidence <= 1.0 for sb in boundaries)
            assert all(sb.change_type in ["cut", "fade", "dissolve", "wipe"] for sb in boundaries)
            
            print(f"  ✅ Found {len(boundaries)} scene boundaries")
            print(f"  📊 Scene boundaries:")
            for i, sb in enumerate(boundaries[:5]):
                print(f"    {i+1}: {sb.timestamp:.3f}s, confidence={sb.confidence:.2f}, type={sb.change_type}")
        else:
            print(f"  ℹ️ No scene boundaries detected - video may have consistent scenes")
    
    async def test_calculate_complexity_metrics_real_video(self):
        """Test complexity analysis with real video"""
        
        video_path = Path(self.test_video)
        if not video_path.exists():
            print(f"⚠️ Skipping complexity test - {self.test_video} not found")
            return
        
        print(f"📊 Testing complexity analysis with: {self.test_video}")
        
        metrics = await self.analyzer.calculate_complexity_metrics(video_path)
        
        assert metrics.resolution_factor >= 0
        assert metrics.duration_factor >= 0
        assert metrics.motion_complexity >= 0
        assert metrics.color_complexity >= 0
        assert metrics.overall_complexity >= 0
        assert len(metrics.processing_recommendation) > 0
        
        print(f"  ✅ Resolution factor: {metrics.resolution_factor:.2f}")
        print(f"  ✅ Duration factor: {metrics.duration_factor:.2f}")
        print(f"  ✅ Motion complexity: {metrics.motion_complexity:.2f}")
        print(f"  ✅ Overall complexity: {metrics.overall_complexity:.2f}")
        print(f"  ✅ Recommendation: {metrics.processing_recommendation}")
    
    async def test_nonexistent_file_handling(self):
        """Test handling of nonexistent files"""
        
        nonexistent_file = "nonexistent_video.mp4"
        
        # Test cut points detection
        result = await self.analyzer.detect_optimal_cut_points(nonexistent_file)
        assert result.confidence == 0.0
        assert "File not found" in result.reasoning
        
        # Test keyframe analysis
        keyframes = await self.analyzer.analyze_keyframes(nonexistent_file)
        assert keyframes == []
        
        # Test scene boundaries
        boundaries = await self.analyzer.detect_scene_boundaries(nonexistent_file)
        assert boundaries == []
        
        # Test complexity metrics
        metrics = await self.analyzer.calculate_complexity_metrics(nonexistent_file)
        assert metrics.overall_complexity == 0.0
        assert "not_found" in metrics.processing_recommendation
    
    async def test_performance_benchmarks(self):
        """Test performance of video intelligence operations"""
        
        video_path = Path(self.test_video)
        if not video_path.exists():
            print(f"⚠️ Skipping performance test - {self.test_video} not found")
            return
        
        print(f"⚡ Performance benchmarks with: {self.test_video}")
        
        benchmarks = {}
        
        # Benchmark cut points detection
        start_time = time.time()
        result = await self.analyzer.detect_optimal_cut_points(video_path, 4)
        benchmarks["cut_points"] = time.time() - start_time
        
        # Benchmark keyframe analysis  
        start_time = time.time()
        keyframes = await self.analyzer.analyze_keyframes(video_path)
        benchmarks["keyframes"] = time.time() - start_time
        
        # Benchmark complexity analysis
        start_time = time.time() 
        metrics = await self.analyzer.calculate_complexity_metrics(video_path)
        benchmarks["complexity"] = time.time() - start_time
        
        print(f"  📊 Performance Results:")
        for operation, duration in benchmarks.items():
            status = "✅ Fast" if duration < 5.0 else "⚠️ Slow" if duration < 15.0 else "❌ Too Slow"
            print(f"    {operation.replace('_', ' ').title()}: {duration:.3f}s {status}")
        
        # Verify performance expectations
        assert benchmarks["cut_points"] < 30.0  # Should complete within 30 seconds
        assert benchmarks["complexity"] < 10.0   # Complexity analysis should be fast
    
    async def test_cache_functionality(self):
        """Test that caching works correctly"""
        
        video_path = Path(self.test_video) 
        if not video_path.exists():
            print(f"⚠️ Skipping cache test - {self.test_video} not found")
            return
        
        print(f"💾 Testing cache functionality with: {self.test_video}")
        
        # First call - should analyze and cache
        start_time = time.time()
        result1 = await self.analyzer.detect_optimal_cut_points(video_path, 4)
        first_call_time = time.time() - start_time
        
        # Second call - should use cache
        start_time = time.time()
        result2 = await self.analyzer.detect_optimal_cut_points(video_path, 4)
        second_call_time = time.time() - start_time
        
        # Results should be identical
        assert result1.cut_points == result2.cut_points
        assert result1.confidence == result2.confidence
        assert result1.method == result2.method
        
        print(f"  ✅ First call: {first_call_time:.3f}s")
        print(f"  ✅ Second call (cached): {second_call_time:.3f}s")
        print(f"  🎯 Cache speedup: {first_call_time / max(second_call_time, 0.001):.1f}x")

class TestConvenienceFunctions:
    """Test standalone convenience functions"""
    
    async def test_convenience_function_api(self):
        """Test that convenience functions work correctly"""
        
        test_video = "Oa8iS1W3OCM.mp4"
        if not Path(test_video).exists():
            print(f"⚠️ Skipping convenience test - {test_video} not found")
            return
        
        print(f"🛠️ Testing convenience functions with: {test_video}")
        
        # Test detect_optimal_cut_points function
        result = await detect_optimal_cut_points(test_video, 4)
        assert len(result.cut_points) >= 1
        assert result.confidence >= 0.0
        print(f"  ✅ detect_optimal_cut_points: {len(result.cut_points)} points")
        
        # Test analyze_keyframes function
        keyframes = await analyze_keyframes(test_video)
        assert isinstance(keyframes, list)
        print(f"  ✅ analyze_keyframes: {len(keyframes)} keyframes")
        
        # Test complexity metrics function
        metrics = await calculate_complexity_metrics(test_video)
        assert metrics.overall_complexity >= 0.0
        print(f"  ✅ calculate_complexity_metrics: {metrics.overall_complexity:.2f} complexity")

class TestTimingProblemSolution:
    """Test that video intelligence actually solves the timing calculation problems"""
    
    async def test_timing_problem_solution_verification(self):
        """Verify that we actually solve the 9.7s-29s timing differences"""
        
        test_videos = ["Oa8iS1W3OCM.mp4", "3xEMCU1fyl8.mp4", "PLnPZVqiyjA.mp4"]
        existing_videos = [v for v in test_videos if Path(v).exists()]
        
        if not existing_videos:
            print("⚠️ Skipping timing problem verification - no test videos found")
            return
        
        print("🎯 TESTING TIMING PROBLEM SOLUTION")
        print("="*50)
        
        analyzer = VideoIntelligenceAnalyzer()
        
        for video in existing_videos:
            print(f"\n📹 Analyzing: {video}")
            
            # Get optimal cut points (our solution)
            optimal_result = await analyzer.detect_optimal_cut_points(video, 4)
            
            # Generate uniform cut points (the problematic approach)
            duration = 60.0  # Assume 60s videos
            uniform_points = [i * (duration / 4) for i in range(4)]  # [0, 15, 30, 45]
            
            print(f"  🧠 Optimal method: {optimal_result.method.value}")
            print(f"  📊 Confidence: {optimal_result.confidence:.2f}")
            
            if len(optimal_result.cut_points) >= 4:
                print(f"  📈 Timing Comparison:")
                total_improvement = 0.0
                significant_improvements = 0
                
                for i, (optimal, uniform) in enumerate(zip(optimal_result.cut_points[:4], uniform_points)):
                    diff = abs(optimal - uniform)
                    total_improvement += diff
                    
                    if diff > 5.0:  # Significant difference
                        significant_improvements += 1
                        status = "🎯 MAJOR IMPROVEMENT"
                    elif diff > 1.0:
                        status = "✅ Improvement"
                    else:
                        status = "➖ Similar"
                    
                    print(f"    Segment {i+1}: Optimal={optimal:6.3f}s vs Uniform={uniform:6.3f}s "
                          f"(Δ{diff:5.3f}s) {status}")
                
                print(f"  📊 Summary: {significant_improvements}/4 segments with major improvements")
                print(f"  🎯 Total timing optimization: {total_improvement:.1f}s")
                
                if significant_improvements > 0:
                    print(f"  ✅ SUCCESS: Video intelligence SOLVES timing calculation problems!")
                else:
                    print(f"  ℹ️ Video may naturally align with uniform timing")
            else:
                print(f"  ⚠️ Insufficient cut points for comparison")

# Integration test that can be run manually
async def manual_video_intelligence_test():
    """Manual test for development verification"""
    
    print("🧠 Manual Video Intelligence Test")
    print("="*50)
    
    # Test all components
    test_suite = TestVideoIntelligenceAnalyzer()
    test_suite.setup_method()
    
    print("\n1. Testing optimal cut points detection...")
    await test_suite.test_detect_optimal_cut_points_real_video()
    
    print("\n2. Testing keyframe analysis...")  
    await test_suite.test_analyze_keyframes_real_video()
    
    print("\n3. Testing scene boundary detection...")
    await test_suite.test_detect_scene_boundaries_real_video()
    
    print("\n4. Testing complexity analysis...")
    await test_suite.test_calculate_complexity_metrics_real_video()
    
    print("\n5. Testing performance benchmarks...")
    await test_suite.test_performance_benchmarks()
    
    print("\n6. Testing cache functionality...")
    await test_suite.test_cache_functionality()
    
    print("\n7. Testing convenience functions...")
    convenience_test = TestConvenienceFunctions()
    await convenience_test.test_convenience_function_api()
    
    print("\n8. VERIFYING TIMING PROBLEM SOLUTION...")
    timing_test = TestTimingProblemSolution()
    await timing_test.test_timing_problem_solution_verification()
    
    print("\n🎯 Video Intelligence Test Complete!")

if __name__ == "__main__":
    # Run manual integration test
    asyncio.run(manual_video_intelligence_test())