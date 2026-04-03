#!/usr/bin/env python3
"""Quick test of trace logger functionality"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.trace_logger import get_trace_logger, trace_start, trace_step, trace_ffmpeg, trace_end
import os

def test_trace_logger():
    """Test basic trace logger functionality"""
    print("Testing trace logger...")
    
    # Test basic operation tracing
    op_id = trace_start("test_operation", {"param1": "value1", "param2": 123})
    print(f"Started operation: {op_id}")
    
    # Test various steps
    trace_step(op_id, "step1", "initialization", status="success")
    trace_ffmpeg(op_id, ["ffmpeg", "-i", "input.mp4", "output.mp4"], pid=12345)
    trace_step(op_id, "step2", "processing", progress=50, message="halfway done")
    
    # Test context manager
    logger = get_trace_logger()
    with logger.trace_operation("context_test", {"file": "test.mp4"}) as ctx_op_id:
        trace_step(ctx_op_id, "context_step", "context_processing")
        logger.log_file_operation(ctx_op_id, "create", "/tmp/test.mp4", success=True, size_bytes=1024)
    
    trace_end(op_id, success=True, final_message="Operation completed successfully")
    
    # Check that files were created
    trace_dir = "/tmp/mcp-traces"
    if os.path.exists(trace_dir):
        print(f"✅ Trace directory created: {trace_dir}")
        
        # List trace files
        for root, dirs, files in os.walk(trace_dir):
            for file in files:
                print(f"  📄 {os.path.join(root, file)}")
                
                # Show first few lines of a trace file
                with open(os.path.join(root, file)) as f:
                    print(f"    Content preview:")
                    for i, line in enumerate(f):
                        if i < 3:
                            print(f"      {line.strip()}")
                        else:
                            break
    else:
        print("❌ Trace directory not found")

if __name__ == "__main__":
    test_trace_logger()