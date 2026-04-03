#!/usr/bin/env python3
"""
Tests for AI Context Enhancement - Priority 3: AI Context Enhancement

Tests the rich contextual information system that helps AI make intelligent
video processing decisions.
"""

import asyncio
import json
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_context_enhancement import (
    AIContextEnhancer,
    VideoCharacteristics,
    ProcessingComplexity,
    ToolRecommendation,
    generate_ai_context,
    get_video_characteristics,
    record_processing_result
)

class TestAIContextEnhancement:
    """Test suite for AI Context Enhancement"""
    
    def setup_method(self):
        """Set up test environment"""
        self.enhancer = AIContextEnhancer()
        self.test_video = "Oa8iS1W3OCM.mp4"  # Our actual test video
    
    def test_enhancer_initialization(self):
        """Test enhancer initializes correctly"""
        enhancer = AIContextEnhancer()
        assert enhancer.history_retention_days == 30
        assert isinstance(enhancer.processing_history, list)
        assert isinstance(enhancer.performance_baselines, dict)
    
    async def test_video_characteristics_analysis_real_video(self):
        """Test video characteristics analysis with real video"""
        
        video_path = Path(self.test_video)
        if not video_path.exists():
            print(f"⚠️ Skipping real video test - {self.test_video} not found")
            return
        
        print(f"🎬 Testing video characteristics analysis with: {self.test_video}")
        
        characteristics = await self.enhancer._analyze_video_characteristics(video_path)
        
        # Validate characteristics
        assert characteristics.duration >= 0
        assert characteristics.resolution[0] >= 0
        assert characteristics.resolution[1] >= 0
        assert characteristics.bitrate >= 0
        assert len(characteristics.codec) > 0
        assert characteristics.frame_rate >= 0
        assert isinstance(characteristics.has_audio, bool)
        assert characteristics.estimated_keyframes >= 0
        assert characteristics.motion_level in ["low", "medium", "high", "unknown"]
        assert characteristics.color_complexity in ["simple", "moderate", "complex", "unknown"]
        assert characteristics.file_size_mb >= 0
        
        print(f"  ✅ Duration: {characteristics.duration:.1f}s")
        print(f"  ✅ Resolution: {characteristics.resolution[0]}x{characteristics.resolution[1]}")
        print(f"  ✅ Bitrate: {characteristics.bitrate/1000000:.1f}Mbps") 
        print(f"  ✅ Codec: {characteristics.codec}")
        print(f"  ✅ Frame rate: {characteristics.frame_rate:.1f}fps")
        print(f"  ✅ Has audio: {characteristics.has_audio}")
        print(f"  ✅ Est. keyframes: {characteristics.estimated_keyframes}")
        print(f"  ✅ Motion level: {characteristics.motion_level}")
        print(f"  ✅ File size: {characteristics.file_size_mb:.1f}MB")
    
    async def test_processing_complexity_assessment(self):
        """Test processing complexity assessment"""
        
        print("📊 Testing processing complexity assessment")
        
        # Test simple video characteristics
        simple_char = VideoCharacteristics(
            duration=30.0,
            resolution=(1280, 720),
            bitrate=2000000,
            codec="h264",
            frame_rate=30.0,
            has_audio=True,
            estimated_keyframes=6,
            motion_level="low",
            color_complexity="simple",
            file_size_mb=50.0
        )
        
        complexity = self.enhancer._assess_processing_complexity(simple_char, "concat")
        print(f"  ✅ Simple video complexity: {complexity.value}")
        assert complexity in [ProcessingComplexity.TRIVIAL, ProcessingComplexity.SIMPLE]
        
        # Test complex video characteristics
        complex_char = VideoCharacteristics(
            duration=600.0,  # 10 minutes
            resolution=(3840, 2160),  # 4K
            bitrate=25000000,  # 25Mbps
            codec="h265",
            frame_rate=60.0,
            has_audio=True,
            estimated_keyframes=120,
            motion_level="high",
            color_complexity="complex",
            file_size_mb=2000.0
        )
        
        complexity = self.enhancer._assess_processing_complexity(complex_char, "transcode")
        print(f"  ✅ Complex video complexity: {complexity.value}")
        assert complexity in [ProcessingComplexity.COMPLEX, ProcessingComplexity.EXTREME]
    
    async def test_contextual_recommendations_generation(self):
        """Test generation of contextual recommendations"""
        
        print("🧠 Testing contextual recommendations generation")
        
        # Test with moderate complexity video
        moderate_char = VideoCharacteristics(
            duration=120.0,
            resolution=(1920, 1080),
            bitrate=8000000,
            codec="h264",
            frame_rate=30.0,
            has_audio=True,
            estimated_keyframes=24,
            motion_level="medium",
            color_complexity="moderate",
            file_size_mb=200.0
        )
        
        recommendations = await self.enhancer._generate_contextual_recommendations(
            moderate_char, "concat", [], None
        )
        
        assert len(recommendations) > 0
        print(f"  ✅ Generated {len(recommendations)} recommendations")
        
        for i, rec in enumerate(recommendations):
            assert isinstance(rec.recommended_tool, ToolRecommendation)
            assert 0.0 <= rec.confidence <= 1.0
            assert len(rec.reasoning) > 0
            assert rec.expected_processing_time >= 0
            assert rec.expected_cpu_usage >= 0
            assert rec.expected_memory_mb >= 0
            assert rec.cost_estimate >= 0
            assert 0.0 <= rec.quality_expectation <= 1.0
            assert isinstance(rec.risk_factors, list)
            assert isinstance(rec.optimization_tips, list)
            assert isinstance(rec.fallback_options, list)
            
            print(f"    {i+1}. {rec.recommended_tool.value}: confidence={rec.confidence:.2f}")
            print(f"       Time: {rec.expected_processing_time:.1f}s, CPU: {rec.expected_cpu_usage:.1f}%")
            print(f"       Reasoning: {rec.reasoning[:60]}...")
    
    async def test_full_ai_context_generation_real_video(self):
        """Test full AI context generation with real video"""
        
        video_path = Path(self.test_video)
        if not video_path.exists():
            print(f"⚠️ Skipping AI context test - {self.test_video} not found")
            return
        
        print(f"🎯 Testing full AI context generation with: {self.test_video}")
        
        # Test without resource constraints
        ai_context = await self.enhancer.generate_ai_context(video_path, "concat")
        
        # Validate AI context structure
        assert isinstance(ai_context.video_analysis, VideoCharacteristics)
        assert isinstance(ai_context.complexity_assessment, ProcessingComplexity)
        assert isinstance(ai_context.historical_insights, list)
        assert isinstance(ai_context.tool_recommendations, list)
        assert isinstance(ai_context.resource_constraints, dict)
        assert isinstance(ai_context.performance_predictions, dict)
        assert isinstance(ai_context.contextual_warnings, list)
        assert isinstance(ai_context.optimization_opportunities, list)
        
        print(f"  ✅ Complexity assessment: {ai_context.complexity_assessment.value}")
        print(f"  ✅ Tool recommendations: {len(ai_context.tool_recommendations)}")
        print(f"  ✅ Performance predictions: {len(ai_context.performance_predictions)}")
        print(f"  ✅ Warnings: {len(ai_context.contextual_warnings)}")
        print(f"  ✅ Optimizations: {len(ai_context.optimization_opportunities)}")
        
        # Print top recommendation
        if ai_context.tool_recommendations:
            top_rec = ai_context.tool_recommendations[0]
            print(f"  🏆 Top recommendation: {top_rec.recommended_tool.value}")
            print(f"      Confidence: {top_rec.confidence:.2f}")
            print(f"      Expected time: {top_rec.expected_processing_time:.1f}s")
            print(f"      Reasoning: {top_rec.reasoning}")
        
        # Test with resource constraints
        constraints = {
            'max_processing_time': 60.0,
            'max_cpu_usage': 70.0,
            'max_memory_mb': 500.0,
            'max_cost': 0.05
        }
        
        constrained_context = await self.enhancer.generate_ai_context(
            video_path, "concat", constraints
        )
        
        # Should have fewer or same recommendations due to constraints
        assert len(constrained_context.tool_recommendations) <= len(ai_context.tool_recommendations)
        print(f"  ✅ Constrained recommendations: {len(constrained_context.tool_recommendations)}")
        
        # All recommendations should meet constraints
        for rec in constrained_context.tool_recommendations:
            if rec.expected_processing_time > constraints['max_processing_time']:
                print(f"    ⚠️ Time constraint violation: {rec.expected_processing_time:.1f}s > {constraints['max_processing_time']}")
    
    async def test_similarity_scoring(self):
        """Test video similarity scoring for historical context"""
        
        print("📊 Testing video similarity scoring")
        
        base_char = VideoCharacteristics(
            duration=120.0,
            resolution=(1920, 1080),
            bitrate=8000000,
            codec="h264",
            frame_rate=30.0,
            has_audio=True,
            estimated_keyframes=24,
            motion_level="medium",
            color_complexity="moderate",
            file_size_mb=200.0
        )
        
        # Very similar video
        similar_char = VideoCharacteristics(
            duration=115.0,  # Slightly different
            resolution=(1920, 1080),  # Same
            bitrate=7500000,  # Slightly different
            codec="h264",  # Same
            frame_rate=30.0,  # Same
            has_audio=True,
            estimated_keyframes=23,
            motion_level="medium",  # Same
            color_complexity="moderate",  # Same
            file_size_mb=190.0
        )
        
        similarity = self.enhancer._calculate_similarity_score(base_char, similar_char)
        print(f"  ✅ Similar video similarity: {similarity:.3f}")
        assert similarity > 0.8  # Should be very similar
        
        # Very different video
        different_char = VideoCharacteristics(
            duration=30.0,  # Much shorter
            resolution=(640, 480),  # Much smaller
            bitrate=1000000,  # Much lower
            codec="vp8",  # Different
            frame_rate=15.0,  # Different
            has_audio=False,
            estimated_keyframes=6,
            motion_level="low",  # Different
            color_complexity="simple",  # Different
            file_size_mb=25.0
        )
        
        dissimilarity = self.enhancer._calculate_similarity_score(base_char, different_char)
        print(f"  ✅ Different video similarity: {dissimilarity:.3f}")
        assert dissimilarity < 0.5  # Should be quite different
        
        assert similarity > dissimilarity
    
    async def test_performance_predictions(self):
        """Test performance prediction generation"""
        
        print("⚡ Testing performance predictions")
        
        test_char = VideoCharacteristics(
            duration=60.0,
            resolution=(1920, 1080),
            bitrate=5000000,
            codec="h264",
            frame_rate=30.0,
            has_audio=True,
            estimated_keyframes=12,
            motion_level="medium",
            color_complexity="moderate",
            file_size_mb=100.0
        )
        
        predictions = self.enhancer._predict_performance(test_char, "concat", [])
        
        # Validate prediction structure
        expected_keys = ['success_probability', 'expected_quality_score', 
                        'resource_efficiency', 'time_accuracy_confidence']
        
        for key in expected_keys:
            assert key in predictions
            assert 0.0 <= predictions[key] <= 1.0
            print(f"  ✅ {key}: {predictions[key]:.3f}")
    
    async def test_optimization_opportunities_identification(self):
        """Test identification of optimization opportunities"""
        
        print("🔍 Testing optimization opportunities identification")
        
        # Test high-bitrate video
        high_bitrate_char = VideoCharacteristics(
            duration=180.0,
            resolution=(2560, 1440),  # 1440p
            bitrate=25000000,  # Very high bitrate
            codec="h264",
            frame_rate=60.0,  # High frame rate
            has_audio=True,
            estimated_keyframes=36,
            motion_level="high",
            color_complexity="complex",
            file_size_mb=800.0
        )
        
        predictions = {'resource_efficiency': 0.4, 'success_probability': 0.6}
        opportunities = self.enhancer._identify_optimization_opportunities(
            high_bitrate_char, "concat", predictions
        )
        
        assert len(opportunities) > 0
        print(f"  ✅ Found {len(opportunities)} optimization opportunities:")
        
        for i, opp in enumerate(opportunities):
            print(f"    {i+1}. {opp}")
            
        # Should suggest bitrate and resolution optimizations
        bitrate_suggestions = [opp for opp in opportunities if 'bitrate' in opp.lower()]
        resolution_suggestions = [opp for opp in opportunities if 'resolution' in opp.lower() or 'downscal' in opp.lower()]
        
        assert len(bitrate_suggestions) > 0
        print(f"  ✅ Bitrate optimization suggestions: {len(bitrate_suggestions)}")
    
    async def test_contextual_warnings_generation(self):
        """Test generation of contextual warnings"""
        
        print("⚠️ Testing contextual warnings generation")
        
        # Test problematic video characteristics
        problematic_char = VideoCharacteristics(
            duration=900.0,  # 15 minutes - very long
            resolution=(7680, 4320),  # 8K - very high resolution
            bitrate=100000000,  # 100Mbps - extremely high
            codec="av1",  # Modern, slow codec
            frame_rate=120.0,  # Very high frame rate
            has_audio=False,  # No audio
            estimated_keyframes=180,
            motion_level="high",
            color_complexity="complex",
            file_size_mb=5000.0  # 5GB - very large
        )
        
        # With restrictive resource constraints
        constraints = {
            'max_memory_mb': 200,
            'max_processing_time': 30.0
        }
        
        warnings = self.enhancer._generate_contextual_warnings(
            problematic_char, "concat", constraints
        )
        
        assert len(warnings) > 0
        print(f"  ✅ Generated {len(warnings)} warnings:")
        
        for i, warning in enumerate(warnings):
            print(f"    {i+1}. {warning}")
        
        # Should warn about various issues
        size_warnings = [w for w in warnings if 'size' in w.lower()]
        duration_warnings = [w for w in warnings if 'duration' in w.lower() or 'minutes' in w.lower()]
        resolution_warnings = [w for w in warnings if 'resolution' in w.lower() or '8k' in w.lower() or '4k' in w.lower()]
        codec_warnings = [w for w in warnings if 'codec' in w.lower()]
        constraint_warnings = [w for w in warnings if 'memory' in w.lower() or 'constraint' in w.lower()]
        
        print(f"  📊 Warning categories found:")
        print(f"    Size warnings: {len(size_warnings)}")
        print(f"    Duration warnings: {len(duration_warnings)}")
        print(f"    Resolution warnings: {len(resolution_warnings)}")
        print(f"    Codec warnings: {len(codec_warnings)}")
        print(f"    Constraint warnings: {len(constraint_warnings)}")
    
    async def test_processing_history_recording(self):
        """Test recording and retrieval of processing history"""
        
        print("📚 Testing processing history recording")
        
        test_char = VideoCharacteristics(
            duration=60.0,
            resolution=(1920, 1080),
            bitrate=5000000,
            codec="h264",
            frame_rate=30.0,
            has_audio=True,
            estimated_keyframes=12,
            motion_level="medium",
            color_complexity="moderate",
            file_size_mb=100.0
        )
        
        # Record successful operation
        self.enhancer.record_processing_result(
            tool_name="keyframe_align",
            video_characteristics=test_char,
            processing_time=15.5,
            success=True,
            cpu_usage=65.0,
            memory_usage_mb=400.0,
            output_quality=0.92
        )
        
        # Record failed operation
        self.enhancer.record_processing_result(
            tool_name="direct_ffmpeg",
            video_characteristics=test_char,
            processing_time=8.2,
            success=False,
            cpu_usage=45.0,
            memory_usage_mb=200.0,
            output_quality=0.0,
            error_message="Timeout exceeded"
        )
        
        assert len(self.enhancer.processing_history) == 2
        print(f"  ✅ Recorded {len(self.enhancer.processing_history)} history items")
        
        # Test history retrieval
        relevant_history = self.enhancer._get_relevant_history(test_char, "keyframe_align")
        
        print(f"  ✅ Found {len(relevant_history)} relevant history items")
        
        if relevant_history:
            latest = relevant_history[0]
            print(f"    Latest: {latest.tool_name}, success={latest.success}, time={latest.processing_time:.1f}s")
    
    async def test_convenience_functions(self):
        """Test convenience functions"""
        
        video_path = Path(self.test_video)
        if not video_path.exists():
            print(f"⚠️ Skipping convenience function tests - {self.test_video} not found")
            return
        
        print(f"🛠️ Testing convenience functions with: {self.test_video}")
        
        # Test generate_ai_context function
        context = await generate_ai_context(video_path, "concat")
        assert isinstance(context.complexity_assessment, ProcessingComplexity)
        assert len(context.tool_recommendations) > 0
        print(f"  ✅ generate_ai_context: {context.complexity_assessment.value} complexity")
        
        # Test get_video_characteristics function
        characteristics = await get_video_characteristics(video_path)
        assert characteristics.duration > 0
        assert characteristics.file_size_mb > 0
        print(f"  ✅ get_video_characteristics: {characteristics.duration:.1f}s video")

class TestAIContextIntegration:
    """Integration tests for AI context enhancement"""
    
    async def test_real_world_scenario_small_video(self):
        """Test real-world scenario with small video"""
        
        test_video = "Oa8iS1W3OCM.mp4"
        if not Path(test_video).exists():
            print(f"⚠️ Skipping integration test - {test_video} not found")
            return
        
        print("🌍 REAL-WORLD SCENARIO: Small video concatenation")
        print("=" * 60)
        
        enhancer = AIContextEnhancer()
        
        # Generate AI context for concatenation
        context = await enhancer.generate_ai_context(test_video, "concat")
        
        print(f"📹 Video Analysis:")
        print(f"  Duration: {context.video_analysis.duration:.1f}s")
        print(f"  Resolution: {context.video_analysis.resolution[0]}x{context.video_analysis.resolution[1]}")
        print(f"  Size: {context.video_analysis.file_size_mb:.1f}MB")
        print(f"  Codec: {context.video_analysis.codec}")
        
        print(f"\\n🧠 AI Assessment:")
        print(f"  Complexity: {context.complexity_assessment.value}")
        print(f"  Warnings: {len(context.contextual_warnings)}")
        print(f"  Optimizations: {len(context.optimization_opportunities)}")
        
        print(f"\\n🏆 Top Recommendations:")
        for i, rec in enumerate(context.tool_recommendations[:3]):
            print(f"  {i+1}. {rec.recommended_tool.value}")
            print(f"     Confidence: {rec.confidence:.2f}")
            print(f"     Time: {rec.expected_processing_time:.1f}s")
            print(f"     CPU: {rec.expected_cpu_usage:.1f}%")
            print(f"     Memory: {rec.expected_memory_mb:.0f}MB")
            print(f"     Quality: {rec.quality_expectation:.2f}")
            print(f"     Cost: ${rec.cost_estimate:.3f}")
            print(f"     Reasoning: {rec.reasoning}")
            if rec.risk_factors:
                print(f"     Risks: {', '.join(rec.risk_factors[:2])}")
            print()
        
        if context.contextual_warnings:
            print(f"⚠️ Contextual Warnings:")
            for warning in context.contextual_warnings:
                print(f"  • {warning}")
            print()
        
        if context.optimization_opportunities:
            print(f"🔍 Optimization Opportunities:")
            for opp in context.optimization_opportunities[:3]:
                print(f"  • {opp}")
        
        print("\\n✅ Real-world scenario test complete!")
    
    async def test_resource_constrained_scenario(self):
        """Test scenario with tight resource constraints"""
        
        test_video = "Oa8iS1W3OCM.mp4"
        if not Path(test_video).exists():
            print(f"⚠️ Skipping resource constraint test - {test_video} not found")
            return
        
        print("\\n💾 RESOURCE-CONSTRAINED SCENARIO")
        print("=" * 40)
        
        # Very tight constraints
        constraints = {
            'max_processing_time': 10.0,  # 10 seconds max
            'max_cpu_usage': 50.0,        # 50% CPU max
            'max_memory_mb': 256.0,       # 256MB max
            'max_cost': 0.01              # 1 cent max
        }
        
        enhancer = AIContextEnhancer()
        context = await enhancer.generate_ai_context(test_video, "concat", constraints)
        
        print(f"🔒 Applied Constraints:")
        print(f"  Max time: {constraints['max_processing_time']}s")
        print(f"  Max CPU: {constraints['max_cpu_usage']}%")
        print(f"  Max memory: {constraints['max_memory_mb']}MB")
        print(f"  Max cost: ${constraints['max_cost']}")
        
        print(f"\\n📊 Results:")
        print(f"  Recommendations: {len(context.tool_recommendations)}")
        print(f"  Warnings: {len(context.contextual_warnings)}")
        
        # Verify constraints are respected
        constraint_violations = 0
        for rec in context.tool_recommendations:
            violations = []
            if rec.expected_processing_time > constraints['max_processing_time']:
                violations.append(f"time: {rec.expected_processing_time:.1f}s")
            if rec.expected_cpu_usage > constraints['max_cpu_usage']:
                violations.append(f"CPU: {rec.expected_cpu_usage:.1f}%")
            if rec.expected_memory_mb > constraints['max_memory_mb']:
                violations.append(f"memory: {rec.expected_memory_mb:.0f}MB")
            if rec.cost_estimate > constraints['max_cost']:
                violations.append(f"cost: ${rec.cost_estimate:.3f}")
            
            if violations:
                constraint_violations += 1
                print(f"  ⚠️ {rec.recommended_tool.value}: violates {', '.join(violations)}")
            else:
                print(f"  ✅ {rec.recommended_tool.value}: meets all constraints")
        
        if constraint_violations == 0:
            print(f"\\n🎯 All recommendations respect resource constraints!")
        else:
            print(f"\\n⚠️ {constraint_violations} recommendations violate constraints")

# Manual integration test
async def manual_ai_context_test():
    """Manual test for development verification"""
    
    print("🧠 Manual AI Context Enhancement Test")
    print("=" * 50)
    
    # Test all components
    test_suite = TestAIContextEnhancement()
    test_suite.setup_method()
    
    print("\\n1. Testing video characteristics analysis...")
    await test_suite.test_video_characteristics_analysis_real_video()
    
    print("\\n2. Testing processing complexity assessment...")
    await test_suite.test_processing_complexity_assessment()
    
    print("\\n3. Testing contextual recommendations...")
    await test_suite.test_contextual_recommendations_generation()
    
    print("\\n4. Testing full AI context generation...")
    await test_suite.test_full_ai_context_generation_real_video()
    
    print("\\n5. Testing similarity scoring...")
    await test_suite.test_similarity_scoring()
    
    print("\\n6. Testing performance predictions...")
    await test_suite.test_performance_predictions()
    
    print("\\n7. Testing optimization opportunities...")
    await test_suite.test_optimization_opportunities_identification()
    
    print("\\n8. Testing contextual warnings...")
    await test_suite.test_contextual_warnings_generation()
    
    print("\\n9. Testing processing history...")
    await test_suite.test_processing_history_recording()
    
    print("\\n10. Testing convenience functions...")
    await test_suite.test_convenience_functions()
    
    # Integration tests
    print("\\n" + "=" * 50)
    integration_test = TestAIContextIntegration()
    await integration_test.test_real_world_scenario_small_video()
    await integration_test.test_resource_constrained_scenario()
    
    print("\\n🎯 AI Context Enhancement Test Complete!")

if __name__ == "__main__":
    # Run manual integration test
    asyncio.run(manual_ai_context_test())