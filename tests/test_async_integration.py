#!/usr/bin/env python3
"""Quick test for Async Interface integration"""
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_async_integration():
    from src.async_interface import AsyncMCPInterface, TaskPriority, TaskStatus, create_async_interface
    
    print('🚀 Testing Async Interface Integration')
    print('='*50)
    
    # Test 1: Basic interface creation
    interface = await create_async_interface(max_concurrent=2)
    
    stats = await interface.get_processing_stats()
    print(f'✅ Interface created: concurrent={interface.max_concurrent}')
    print(f'📊 Initial stats: {stats["total_tasks"]} tasks, {stats["success_rate"]:.2f} success rate')
    
    # Test 2: Single task processing
    test_video = 'Oa8iS1W3OCM.mp4'
    if Path(test_video).exists():
        print(f'🎬 Testing single task with: {test_video}')
        
        # Enqueue a video analysis task
        task_id = await interface.analyze_video_async(
            video_path=test_video,
            target_operation="concat",
            priority=TaskPriority.HIGH,
            timeout=30.0
        )
        
        print(f'📝 Task enqueued: {task_id}')
        
        # Wait for completion
        result = await interface.wait_for_task(task_id)
        print(f'📊 Task result: {result.status.value} in {result.execution_time:.2f}s')
        
        if result.status == TaskStatus.COMPLETED:
            ai_context = result.result_data.get("data", {}).get("ai_context", {})
            if ai_context:
                print(f'🧠 AI Context: {ai_context.get("complexity_assessment", "unknown")} complexity')
                recs = ai_context.get("tool_recommendations", [])
                print(f'🏆 Recommendations: {len(recs)} options available')
    
    # Test 3: Batch processing  
    print(f'\\n📦 Testing batch processing...')
    
    # Use multiple copies for testing
    test_files = [test_video] * 2 if Path(test_video).exists() else ["test1.mp4", "test2.mp4"]
    
    batch_id = await interface.process_video_batch_async(
        video_files=test_files,
        operation="calculate_complexity_metrics",
        priority=TaskPriority.NORMAL,
        timeout=30.0
    )
    
    print(f'📦 Batch started: {batch_id}')
    
    # Wait for batch completion
    try:
        batch_result = await asyncio.wait_for(
            interface.wait_for_batch(batch_id),
            timeout=35.0
        )
        
        print(f'📊 Batch completed: {batch_result.completed}/{batch_result.total_tasks} successful')
        print(f'⏱️  Total time: {batch_result.total_execution_time:.2f}s')
    
    except asyncio.TimeoutError:
        print(f'⏰ Batch processing timed out - cancelling...')
        cancel_result = await interface.cancel_batch(batch_id)
        print(f'🚫 Cancelled {cancel_result["cancelled_tasks"]}/{cancel_result["total_tasks"]} tasks')
    
    # Test 4: Final stats
    final_stats = await interface.get_processing_stats()
    print(f'\\n📈 Final Statistics:')
    print(f'  Total tasks: {final_stats["total_tasks"]}')
    print(f'  Success rate: {final_stats["success_rate"]:.2f}')
    print(f'  Average time: {final_stats["average_processing_time"]:.2f}s')
    print(f'  Queue size: {final_stats["queue_size"]}')
    
    # Cleanup
    await interface.shutdown()
    print('\\n🎯 Async Interface Integration Test Complete!')

if __name__ == "__main__":
    asyncio.run(test_async_integration())