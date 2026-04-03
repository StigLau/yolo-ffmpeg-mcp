#!/usr/bin/env python3
"""Simplified async test to debug the issue"""
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_simple_async():
    from src.async_interface import AsyncMCPInterface, TaskPriority, TaskStatus
    
    print('🔧 Simple Async Test')
    print('='*30)
    
    interface = AsyncMCPInterface(max_concurrent=1)
    
    try:
        # Test simple operation that should work
        task_id = await interface.task_queue.enqueue(
            type('AsyncTask', (), {
                'task_id': 'test-001',
                'operation': 'get_haiku_cost_status',
                'parameters': {},
                'priority': TaskPriority.NORMAL,
                'timeout': 30.0,
                'callback': None,
                'created_at': __import__('datetime').datetime.now()
            })()
        )
        
        print(f'📝 Task enqueued: {task_id}')
        
        # Wait a bit for processing
        await asyncio.sleep(2.0)
        
        # Check task status
        result = await interface.task_queue.get_task_status(task_id)
        if result:
            print(f'📊 Task status: {result.status.value}')
            if result.result_data:
                print(f'✅ Has result data')
        else:
            print('❌ Task not found')
        
        # Check queue stats
        stats = await interface.task_queue.get_queue_status()
        print(f'📈 Queue: size={stats["queue_size"]}, running={stats["running_tasks"]}, completed={stats["completed_tasks"]}')
        
    finally:
        await interface.shutdown()
    
    print('🎯 Simple test complete')

if __name__ == "__main__":
    asyncio.run(test_simple_async())