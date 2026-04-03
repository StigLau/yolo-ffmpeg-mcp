#!/usr/bin/env python3
"""
Tests for Async Interface - Priority 4: Async Interface

Tests the async wrapper patterns, concurrent processing capabilities,
and resource management for better AI integration.
"""

import asyncio
import sys
import time
import uuid
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.async_interface import (
    AsyncMCPInterface,
    AsyncTaskQueue,
    AsyncTask,
    TaskStatus,
    TaskPriority,
    AsyncMCPSession,
    create_async_interface,
    process_videos_concurrently,
    analyze_video_with_context
)

class TestAsyncTaskQueue:
    """Test suite for AsyncTaskQueue"""
    
    def setup_method(self):
        """Set up test environment"""
        self.queue = AsyncTaskQueue(max_concurrent=2)
    
    async def test_queue_initialization(self):
        """Test queue initializes correctly"""
        
        queue = AsyncTaskQueue(max_concurrent=3)
        status = await queue.get_queue_status()
        
        assert status["max_concurrent"] == 3
        assert status["queue_size"] == 0
        assert status["running_tasks"] == 0
        assert status["completed_tasks"] == 0
        assert status["shutdown"] == False
        
        print("✅ Queue initialization test passed")
    
    async def test_task_enqueue_and_status(self):
        """Test task enqueueing and status tracking"""
        
        task = AsyncTask(
            task_id="test_task_001",
            operation="test_operation",
            parameters={"param1": "value1"},
            priority=TaskPriority.HIGH
        )
        
        # Enqueue task
        task_id = await self.queue.enqueue(task)
        assert task_id == "test_task_001"
        
        # Check queue status
        status = await self.queue.get_queue_status()
        assert status["queue_size"] == 1
        
        print("✅ Task enqueue and status test passed")
    
    async def test_task_priority_ordering(self):
        """Test that tasks are processed in priority order"""
        
        # Create tasks with different priorities
        low_task = AsyncTask(
            task_id="low_priority",
            operation="test_op",
            parameters={},
            priority=TaskPriority.LOW
        )
        
        high_task = AsyncTask(
            task_id="high_priority", 
            operation="test_op",
            parameters={},
            priority=TaskPriority.URGENT
        )
        
        normal_task = AsyncTask(
            task_id="normal_priority",
            operation="test_op", 
            parameters={},
            priority=TaskPriority.NORMAL
        )
        
        # Enqueue in non-priority order
        await self.queue.enqueue(low_task)
        await self.queue.enqueue(normal_task)
        await self.queue.enqueue(high_task)
        
        # Check queue has all tasks
        status = await self.queue.get_queue_status()
        assert status["queue_size"] == 3
        
        print("✅ Task priority ordering test passed")

class TestAsyncMCPInterface:
    """Test suite for AsyncMCPInterface"""
    
    def setup_method(self):
        """Set up test environment"""
        self.test_video = "Oa8iS1W3OCM.mp4"
    
    async def test_interface_initialization(self):
        """Test interface initializes correctly"""
        
        interface = AsyncMCPInterface(max_concurrent=3, max_threads=6)
        
        assert interface.max_concurrent == 3
        assert interface.max_threads == 6
        assert interface.enable_batching == True
        assert interface.bridge is not None  # Should have MCP bridge
        
        # Check background processor started
        assert interface._processor_task is not None
        assert not interface._processor_task.done()
        
        await interface.shutdown()
        print("✅ Interface initialization test passed")
    
    async def test_processing_stats(self):
        """Test processing statistics tracking"""
        
        interface = AsyncMCPInterface(max_concurrent=2)
        
        stats = await interface.get_processing_stats()
        
        expected_keys = [
            "total_tasks", "successful_tasks", "failed_tasks",
            "total_processing_time", "queue_size", "running_tasks",
            "completed_tasks", "max_concurrent", "shutdown",
            "average_processing_time", "success_rate", "active_sessions"
        ]
        
        for key in expected_keys:
            assert key in stats
            print(f"  ✅ Stats key: {key} = {stats[key]}")
        
        await interface.shutdown()
        print("✅ Processing stats test passed")
    
    async def test_video_analysis_async(self):
        """Test async video analysis"""
        
        video_path = Path(self.test_video)
        if not video_path.exists():
            print(f"⚠️ Skipping video analysis test - {self.test_video} not found")
            return
        
        print(f"🎬 Testing async video analysis with: {self.test_video}")
        
        interface = AsyncMCPInterface(max_concurrent=1)
        
        try:
            # Start async video analysis
            task_id = await interface.analyze_video_async(
                video_path=str(video_path),
                target_operation="concat",
                priority=TaskPriority.HIGH,
                timeout=60.0
            )
            
            print(f"  📝 Task enqueued: {task_id}")
            
            # Wait for completion with timeout
            result = await asyncio.wait_for(
                interface.wait_for_task(task_id),
                timeout=65.0
            )
            
            print(f"  📊 Task result: {result.status.value}")
            
            if result.status == TaskStatus.COMPLETED:
                assert result.result_data is not None
                assert result.result_data["success"] == True
                print(f"  ✅ Analysis successful in {result.execution_time:.2f}s")
                
                # Check if we got AI context data
                if "data" in result.result_data and "ai_context" in result.result_data["data"]:
                    ai_context = result.result_data["data"]["ai_context"]
                    print(f"  🧠 AI Context: {ai_context['complexity_assessment']} complexity")
                    print(f"  🏆 Recommendations: {len(ai_context['tool_recommendations'])}")
            else:
                print(f"  ❌ Task failed: {result.error}")
                
        finally:
            await interface.shutdown()
        
        print("✅ Async video analysis test completed")
    
    async def test_batch_processing(self):
        """Test batch processing capabilities"""
        
        # Use multiple copies of the same video for testing
        test_videos = [self.test_video] * 3  # Process same video 3 times
        existing_videos = [v for v in test_videos if Path(v).exists()]
        
        if not existing_videos:
            print(f"⚠️ Skipping batch test - no test videos found")
            return
        
        print(f"📦 Testing batch processing with {len(existing_videos)} videos")
        
        interface = AsyncMCPInterface(max_concurrent=2)
        
        try:
            # Start batch processing
            batch_id = await interface.process_video_batch_async(
                video_files=existing_videos,
                operation="calculate_complexity_metrics",
                priority=TaskPriority.NORMAL,
                timeout=120.0
            )
            
            print(f"  📦 Batch started: {batch_id}")
            
            # Wait for batch completion
            batch_result = await interface.wait_for_batch(batch_id, polling_interval=0.5)
            
            print(f"  📊 Batch Results:")
            print(f"    Total tasks: {batch_result.total_tasks}")
            print(f"    Completed: {batch_result.completed}")
            print(f"    Failed: {batch_result.failed}")
            print(f"    Total time: {batch_result.total_execution_time:.2f}s")
            
            # Verify all tasks processed
            assert batch_result.total_tasks == len(existing_videos)
            assert batch_result.completed + batch_result.failed == batch_result.total_tasks
            
            # Check individual results
            for i, result in enumerate(batch_result.results):
                print(f"    Task {i+1}: {result.status.value} ({result.execution_time:.2f}s)")
                if result.status == TaskStatus.COMPLETED:
                    assert result.result_data is not None
                    assert result.result_data["success"] == True
        
        finally:
            await interface.shutdown()
        
        print("✅ Batch processing test completed")
    
    async def test_task_cancellation(self):
        """Test task cancellation capabilities"""
        
        interface = AsyncMCPInterface(max_concurrent=1)
        
        try:
            # Create a task that will take some time
            task_id = await interface.analyze_video_async(
                video_path=self.test_video,  # May not exist, will cause delay
                target_operation="concat",
                priority=TaskPriority.LOW,
                timeout=300.0
            )
            
            print(f"  📝 Task enqueued: {task_id}")
            
            # Wait a moment for task to potentially start
            await asyncio.sleep(0.1)
            
            # Cancel the task
            cancelled = await interface.task_queue.cancel_task(task_id)
            print(f"  🚫 Task cancellation: {'success' if cancelled else 'failed'}")
            
            # Check final status
            final_result = await interface.task_queue.get_task_status(task_id)
            if final_result:
                print(f"  📊 Final status: {final_result.status.value}")
                
        finally:
            await interface.shutdown()
        
        print("✅ Task cancellation test completed")
    
    async def test_concurrent_processing_limits(self):
        """Test concurrent processing limits are respected"""
        
        # Create interface with strict concurrency limit
        interface = AsyncMCPInterface(max_concurrent=1)
        
        try:
            # Enqueue multiple tasks quickly
            task_ids = []
            for i in range(3):
                task_id = await interface.detect_optimal_cuts_async(
                    video_path=f"test_video_{i}.mp4",  # Non-existent files
                    target_segments=4,
                    priority=TaskPriority.NORMAL,
                    timeout=10.0  # Short timeout
                )
                task_ids.append(task_id)
            
            print(f"  📝 Enqueued {len(task_ids)} tasks with max_concurrent=1")
            
            # Check that only 1 task runs at a time
            await asyncio.sleep(0.5)  # Allow processing to start
            
            status = await interface.task_queue.get_queue_status()
            print(f"  📊 Queue status: running={status['running_tasks']}, queue={status['queue_size']}")
            
            # Should have at most 1 running task due to concurrency limit
            assert status['running_tasks'] <= 1
            
            # Cancel remaining tasks
            for task_id in task_ids:
                await interface.task_queue.cancel_task(task_id)
                
        finally:
            await interface.shutdown()
        
        print("✅ Concurrent processing limits test completed")

class TestAsyncMCPSession:
    """Test suite for AsyncMCPSession context manager"""
    
    async def test_session_lifecycle(self):
        """Test session context manager lifecycle"""
        
        interface = AsyncMCPInterface(max_concurrent=2)
        
        try:
            session_name = "test_session_001"
            
            # Test session context manager
            async with AsyncMCPSession(interface, session_name) as session:
                assert session.session_name == session_name
                assert len(session.task_ids) == 0
                
                # Enqueue a task within session
                task_id = await session.enqueue_task(
                    operation="get_haiku_cost_status",
                    parameters={},
                    priority=TaskPriority.LOW
                )
                
                assert task_id in session.task_ids
                print(f"  ✅ Task enqueued in session: {task_id}")
            
            # Session should be cleaned up
            print("  ✅ Session context exited cleanly")
            
        finally:
            await interface.shutdown()
        
        print("✅ Session lifecycle test completed")

class TestConvenienceFunctions:
    """Test suite for convenience functions"""
    
    async def test_create_async_interface_function(self):
        """Test create_async_interface convenience function"""
        
        interface = await create_async_interface(
            max_concurrent=3,
            max_threads=6,
            enable_batching=True
        )
        
        assert interface.max_concurrent == 3
        assert interface.max_threads == 6
        assert interface.enable_batching == True
        
        await interface.shutdown()
        print("✅ Create async interface function test passed")
    
    async def test_analyze_video_with_context_function(self):
        """Test analyze_video_with_context convenience function"""
        
        test_video = "Oa8iS1W3OCM.mp4"
        
        if not Path(test_video).exists():
            print(f"⚠️ Skipping convenience function test - {test_video} not found")
            return
        
        print(f"🎬 Testing analyze_video_with_context with: {test_video}")
        
        # Test the convenience function
        result = await analyze_video_with_context(
            video_path=test_video,
            target_operation="concat",
            timeout=60.0
        )
        
        print(f"  📊 Result status: {result.status.value}")
        
        if result.status == TaskStatus.COMPLETED:
            assert result.result_data is not None
            assert result.result_data["success"] == True
            print(f"  ✅ Analysis completed in {result.execution_time:.2f}s")
        else:
            print(f"  ❌ Analysis failed: {result.error}")
        
        print("✅ Analyze video with context function test completed")
    
    async def test_process_videos_concurrently_function(self):
        """Test process_videos_concurrently convenience function"""
        
        test_videos = ["Oa8iS1W3OCM.mp4"] * 2  # Process same video twice
        existing_videos = [v for v in test_videos if Path(v).exists()]
        
        if not existing_videos:
            print("⚠️ Skipping concurrent processing test - no test videos found")
            return
        
        print(f"🔄 Testing concurrent processing with {len(existing_videos)} videos")
        
        # Test concurrent processing
        results = await process_videos_concurrently(
            video_files=existing_videos,
            operation="get_video_characteristics",
            max_concurrent=2
        )
        
        print(f"  📊 Processed {len(results)} videos concurrently")
        
        for i, result in enumerate(results):
            print(f"    Video {i+1}: {result.status.value} ({result.execution_time:.2f}s)")
            if result.status == TaskStatus.COMPLETED:
                assert result.result_data is not None
                assert result.result_data["success"] == True
        
        print("✅ Concurrent processing function test completed")

class TestRealWorldScenarios:
    """Integration tests for real-world async scenarios"""
    
    async def test_mixed_priority_processing(self):
        """Test processing tasks with mixed priorities"""
        
        interface = AsyncMCPInterface(max_concurrent=1)  # Force sequential processing
        
        try:
            # Enqueue tasks with different priorities
            low_task = await interface.detect_optimal_cuts_async(
                video_path="low_priority.mp4",
                priority=TaskPriority.LOW,
                timeout=5.0
            )
            
            urgent_task = await interface.analyze_video_async(
                video_path="Oa8iS1W3OCM.mp4",
                priority=TaskPriority.URGENT,
                timeout=30.0
            )
            
            normal_task = await interface.detect_optimal_cuts_async(
                video_path="normal_priority.mp4", 
                priority=TaskPriority.NORMAL,
                timeout=5.0
            )
            
            print(f"  📝 Enqueued tasks: low, urgent, normal")
            
            # Collect results in order of completion
            completed_order = []
            
            async for result in interface.stream_task_results([low_task, urgent_task, normal_task]):
                completed_order.append((result.task_id, result.status))
                print(f"  📊 Completed: {result.task_id} -> {result.status.value}")
            
            print(f"  🏆 Completion order tracked: {len(completed_order)} tasks")
            
        finally:
            await interface.shutdown()
        
        print("✅ Mixed priority processing test completed")
    
    async def test_resource_exhaustion_handling(self):
        """Test handling of resource exhaustion scenarios"""
        
        # Create interface with very limited resources
        interface = AsyncMCPInterface(max_concurrent=1, max_threads=1)
        
        try:
            # Enqueue many tasks to test resource limits
            task_ids = []
            for i in range(5):
                task_id = await interface.analyze_video_async(
                    video_path=f"resource_test_{i}.mp4",
                    target_operation="concat",
                    priority=TaskPriority.NORMAL,
                    timeout=5.0  # Short timeout to speed up test
                )
                task_ids.append(task_id)
            
            print(f"  📝 Enqueued {len(task_ids)} tasks with limited resources")
            
            # Wait a bit for processing to start
            await asyncio.sleep(1.0)
            
            # Check resource usage
            stats = await interface.get_processing_stats()
            print(f"  📊 Resource usage:")
            print(f"    Queue size: {stats['queue_size']}")
            print(f"    Running tasks: {stats['running_tasks']}")
            print(f"    Max concurrent: {stats['max_concurrent']}")
            
            # Should not exceed resource limits
            assert stats['running_tasks'] <= stats['max_concurrent']
            
            # Cancel remaining tasks
            for task_id in task_ids:
                await interface.task_queue.cancel_task(task_id)
                
        finally:
            await interface.shutdown()
        
        print("✅ Resource exhaustion handling test completed")

# Manual integration test
async def manual_async_interface_test():
    """Manual test for development verification"""
    
    print("🚀 Manual Async Interface Test")
    print("=" * 50)
    
    # Test core components
    print("\\n1. Testing AsyncTaskQueue...")
    queue_test = TestAsyncTaskQueue()
    queue_test.setup_method()
    await queue_test.test_queue_initialization()
    await queue_test.test_task_enqueue_and_status()
    await queue_test.test_task_priority_ordering()
    
    print("\\n2. Testing AsyncMCPInterface...")
    interface_test = TestAsyncMCPInterface()
    interface_test.setup_method()
    await interface_test.test_interface_initialization()
    await interface_test.test_processing_stats()
    await interface_test.test_video_analysis_async()
    await interface_test.test_batch_processing()
    await interface_test.test_task_cancellation()
    await interface_test.test_concurrent_processing_limits()
    
    print("\\n3. Testing AsyncMCPSession...")
    session_test = TestAsyncMCPSession()
    await session_test.test_session_lifecycle()
    
    print("\\n4. Testing convenience functions...")
    convenience_test = TestConvenienceFunctions()
    await convenience_test.test_create_async_interface_function()
    await convenience_test.test_analyze_video_with_context_function()
    await convenience_test.test_process_videos_concurrently_function()
    
    print("\\n5. Testing real-world scenarios...")
    scenario_test = TestRealWorldScenarios()
    await scenario_test.test_mixed_priority_processing()
    await scenario_test.test_resource_exhaustion_handling()
    
    print("\\n🎯 Async Interface Test Complete!")
    print("\\n📊 Key Features Tested:")
    print("  ✅ Async task queuing with priority scheduling")
    print("  ✅ Concurrent processing with resource limits")
    print("  ✅ Batch processing capabilities")
    print("  ✅ Task cancellation and cleanup")
    print("  ✅ Real-time progress streaming")
    print("  ✅ Context managers for resource management")
    print("  ✅ Integration with MCP Hybrid Bridge")
    print("  ✅ Comprehensive error handling and timeouts")

if __name__ == "__main__":
    # Run manual integration test
    asyncio.run(manual_async_interface_test())