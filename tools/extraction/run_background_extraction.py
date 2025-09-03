#!/usr/bin/env python3
"""
Background Knowledge Extraction Runner

Usage:
    python run_background_extraction.py [--resume SESSION_ID]
    
This will run the comprehensive knowledge extraction in the background
while you continue working on other tasks.
"""

import asyncio
import sys
import os
import signal
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from async_knowledge_extractor import run_comprehensive_extraction

class BackgroundExtractionRunner:
    def __init__(self):
        self.extraction_task = None
        self.cancelled = False
    
    def signal_handler(self, signum, frame):
        """Handle interrupt signals gracefully"""
        print(f"\n🛑 Received signal {signum}, gracefully shutting down...")
        self.cancelled = True
        if self.extraction_task:
            self.extraction_task.cancel()
    
    async def run_with_progress_monitoring(self, **kwargs):
        """Run extraction with progress monitoring"""
        print("🚀 Starting comprehensive knowledge extraction in background...")
        print("📊 You can continue working - this will run independently")
        print("⏸️  Press Ctrl+C to gracefully stop\n")
        
        try:
            self.extraction_task = asyncio.create_task(
                run_comprehensive_extraction(**kwargs)
            )
            
            # Monitor progress while allowing other work
            while not self.extraction_task.done():
                if self.cancelled:
                    break
                
                await asyncio.sleep(30)  # Check every 30 seconds
                print("🔄 Extraction still running in background...")
            
            if not self.cancelled:
                result = await self.extraction_task
                if result:
                    print(f"\n🎉 Background extraction completed successfully!")
                    print(f"📚 Results available at: {result}")
                    return result
                else:
                    print("\n❌ Background extraction failed")
                    return None
        
        except asyncio.CancelledError:
            print("\n⏸️ Background extraction was cancelled")
            return None
        except Exception as e:
            print(f"\n❌ Background extraction failed: {e}")
            return None

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Background Knowledge Extraction Runner")
    parser.add_argument("--resume", help="Resume session ID")
    parser.add_argument("--api-key", help="Anthropic API key (optional)")
    
    args = parser.parse_args()
    
    runner = BackgroundExtractionRunner()
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, runner.signal_handler)
    signal.signal(signal.SIGTERM, runner.signal_handler)
    
    # Configuration
    config = {
        'target_codebase': '/Users/stiglau/utvikling/privat/komposteur',
        'output_dir': '/Users/stiglau/utvikling/privat/komposteur/docs/knowledge-analysis',
        'anthropic_api_key': args.api_key,
        'session_id': args.resume,
        'resume': bool(args.resume)
    }
    
    print("🎯 Configuration:")
    print(f"   📂 Target: {config['target_codebase']}")
    print(f"   📝 Output: {config['output_dir']}")
    print(f"   🔑 API Key: {'Provided' if config['anthropic_api_key'] else 'Not provided (will use heuristics)'}")
    if args.resume:
        print(f"   🔄 Resuming: {args.resume}")
    print()
    
    # Run the extraction
    try:
        result = asyncio.run(runner.run_with_progress_monitoring(**config))
        
        if result:
            print(f"\n✅ Complete! Open this file to explore the knowledge base:")
            print(f"📖 {result}")
        else:
            print("\n❌ Extraction did not complete successfully")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n👋 Extraction stopped by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()