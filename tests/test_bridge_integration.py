#!/usr/bin/env python3
"""Quick integration test for MCP Hybrid Bridge"""
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_hybrid_bridge():
    from src.mcp_hybrid_bridge import MCPHybridBridge, BridgeMode
    
    print('🔧 Manual Integration Test: MCP Hybrid Bridge')
    print('='*50)
    
    # Test bridge initialization
    bridge = MCPHybridBridge()
    status = bridge.get_bridge_status()
    
    print(f'✅ Bridge initialized: {status["operational_mode"]} mode')
    print(f'🔗 MCP available: {status["mcp_framework_available"]}')
    print(f'🛠️ Tools available: {status["standalone_tools_available"]}')
    
    # Test with actual project files
    project_files = ['Oa8iS1W3OCM.mp4', '3xEMCU1fyl8.mp4', 'PLnPZVqiyjA.mp4']
    existing_files = [f for f in project_files if Path(f).exists()]
    
    if existing_files:
        print(f'🎬 Testing with {len(existing_files)} project videos...')
        
        result = await bridge.yolo_smart_video_concat(existing_files)
        print(f'📊 Concat result: success={result.success}, method={result.method}, time={result.execution_time:.3f}s')
        if result.success:
            print(f'   Strategy: {result.data["recommended_strategy"]} (confidence: {result.data["confidence"]:.2f})')
        
        result = await bridge.analyze_video_processing_strategy(existing_files)
        print(f'🧠 Analysis result: success={result.success}, method={result.method}')
        if result.success:
            print(f'   Strategy: {result.data["recommended_strategy"]} (complexity: {result.data["complexity_score"]:.2f})')
    else:
        print('⚠️ No project video files found, testing with empty list...')
        result = await bridge.yolo_smart_video_concat([])
        print(f'📊 Empty list test: success={result.success}, method={result.method}')
    
    # Test cost status
    result = await bridge.get_haiku_cost_status()
    print(f'💰 Cost status: success={result.success}, method={result.method}')
    if result.success:
        print(f'   Budget: ${result.data["daily_spend"]:.2f} / ${result.data["daily_limit"]:.2f}')
    
    print('🎯 Integration test complete!')

if __name__ == "__main__":
    asyncio.run(test_hybrid_bridge())