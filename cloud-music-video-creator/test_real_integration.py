#!/usr/bin/env python3
"""
Test Real LLM Integration
Quick test of the new LLM integration system
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from llm_service import get_llm_service
from komposition_manager import get_komposition_manager
from interaction_logger import get_interaction_logger
from ffmpeg_processor import get_ffmpeg_processor


async def test_integration():
    print("🧪 Testing Cloud Music Video Creator - Real LLM Integration")
    print("=" * 60)
    
    # Test 1: LLM Service
    print("\n1. Testing LLM Service...")
    llm = get_llm_service()
    print(f"   ✅ LLM Service initialized: {llm.model_name}")
    print(f"   🔄 Fallback mode: {'ON' if llm.fallback_mode else 'OFF'}")
    
    # Test 2: Komposition Manager
    print("\n2. Testing Komposition Manager...")
    km = get_komposition_manager()
    session = km.create_session("Test Session", "# Test Komposition\nThis is a test.")
    print(f"   ✅ Session created: {session.session_id}")
    print(f"   📁 Komposition file: {session.komposition_file}")
    print(f"   💬 Chat log file: {session.chat_log_file}")
    
    # Test 3: Interaction Logger
    print("\n3. Testing Interaction Logger...")
    logger_service = get_interaction_logger()
    msg_id = logger_service.log_user_message(session.session_id, "Test message")
    print(f"   ✅ User message logged: {msg_id}")
    
    # Test 4: Chat Processing
    print("\n4. Testing Chat Processing...")
    try:
        response = await llm.process_chat_message(
            "I want to create a vintage music video",
            [],
            None
        )
        print(f"   ✅ Chat response: {response.response_text[:100]}...")
        print(f"   📝 Komposition updated: {'Yes' if response.updated_komposition else 'No'}")
    except Exception as e:
        print(f"   ⚠️  Chat processing: {str(e)}")
    
    # Test 5: FFmpeg Processor
    print("\n5. Testing FFmpeg Processor...")
    ffmpeg_proc = get_ffmpeg_processor()
    print(f"   ✅ FFmpeg processor initialized: {ffmpeg_proc.temp_dir}")
    
    # Test parsing
    test_komposition = """# Vintage Music Video
## Basic Parameters
- **Duration**: 15 seconds
- **Style**: Vintage with sepia effects
"""
    
    parsed = ffmpeg_proc.parse_komposition(test_komposition)
    print(f"   📋 Parsed style: {parsed['style']}")
    print(f"   ⏱️  Parsed duration: {parsed['duration']}s")
    
    # Test command generation
    try:
        commands = await ffmpeg_proc.generate_ffmpeg_commands(test_komposition, session.session_id)
        print(f"   ✅ Generated {len(commands)} FFmpeg command(s)")
        if commands:
            print(f"   🎬 Command purpose: {commands[0].purpose}")
    except Exception as e:
        print(f"   ⚠️  Command generation: {str(e)}")
    
    # Test 6: Session Summary
    print("\n6. Testing Session Summary...")
    summary = logger_service.get_session_summary(session.session_id)
    print(f"   📊 Total interactions: {summary['total_interactions']}")
    print(f"   🔧 LLM calls: {summary['llm_usage']['llm1_calls']}")
    print(f"   ⚙️  FFmpeg commands: {summary['ffmpeg_usage']['commands_executed']}")
    
    # Test 7: File Locations
    print("\n7. File Locations:")
    print(f"   📁 Kompositions: {km.base_dir}")
    print(f"   📝 Logs: {logger_service.base_dir}")
    print(f"   🎬 FFmpeg temp: {ffmpeg_proc.temp_dir}")
    
    print(f"\n🎉 Integration test completed!")
    print(f"   Session ID: {session.session_id}")
    print(f"   Files created in temp directories (avoiding root pollution)")
    
    return session.session_id


if __name__ == "__main__":
    session_id = asyncio.run(test_integration())