#!/usr/bin/env python3
"""Quick test to verify video intelligence fixes"""
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_fixed_video_intelligence():
    from src.video_intelligence import VideoIntelligenceAnalyzer
    from src.mcp_hybrid_bridge import MCPHybridBridge
    
    print('🧠 Testing Fixed Video Intelligence')
    print('='*50)
    
    analyzer = VideoIntelligenceAnalyzer()
    
    # Test with our known problematic video
    test_video = "Oa8iS1W3OCM.mp4"
    
    if Path(test_video).exists():
        print(f'🎬 Testing with: {test_video}')
        
        # Test optimal cut points - the KEY API
        result = await analyzer.detect_optimal_cut_points(test_video, 4)
        
        print(f'📊 Cut Points Analysis:')
        print(f'  Method: {result.method.value}')
        print(f'  Confidence: {result.confidence:.2f}')
        print(f'  Cut points: {result.cut_points}')
        print(f'  Reasoning: {result.reasoning}')
        
        # Compare with uniform approach to show improvement
        uniform_points = [0.0, 15.0, 30.0, 45.0]
        print(f'')
        print(f'🎯 TIMING COMPARISON (The key test):')
        print(f'  Uniform approach: {uniform_points}')
        print(f'  Intelligence approach: {result.cut_points}')
        
        if len(result.cut_points) >= 4:
            for i, (intelligent, uniform) in enumerate(zip(result.cut_points, uniform_points)):
                diff = abs(intelligent - uniform)
                status = "🎯 IMPROVEMENT" if diff > 1.0 else "➖ Similar"
                print(f'    Segment {i+1}: {intelligent:.3f}s vs {uniform:.3f}s (Δ{diff:.3f}s) {status}')
        
        # Test hybrid bridge integration
        print(f'')
        print(f'🔗 Testing Hybrid Bridge Integration:')
        bridge = MCPHybridBridge()
        bridge_result = await bridge.detect_optimal_cut_points(test_video, 4)
        
        if bridge_result.success:
            print(f'  ✅ Bridge result: success={bridge_result.success}, method={bridge_result.method}')
            print(f'  📊 Cut points: {bridge_result.data.get("cut_points", [])}')
            print(f'  🎯 Confidence: {bridge_result.data.get("confidence", 0):.2f}')
        else:
            print(f'  ❌ Bridge failed: {bridge_result.error}')
        
    else:
        print(f'⚠️ Test video not found: {test_video}')
        print('Testing with nonexistent file to verify error handling...')
        
        result = await analyzer.detect_optimal_cut_points("nonexistent.mp4", 4)
        print(f'📊 Error handling test:')
        print(f'  Confidence: {result.confidence:.2f}')
        print(f'  Reasoning: {result.reasoning}')
    
    print('')
    print('🎯 Video Intelligence Fix Test Complete!')

if __name__ == "__main__":
    asyncio.run(test_fixed_video_intelligence())