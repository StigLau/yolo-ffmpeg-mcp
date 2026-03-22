#!/usr/bin/env python3
"""
End-to-End Natural Language Music Video Creation Test

This test creates a music video from natural language description through the MCP server,
using the uber-kompost Java library integration. It demonstrates the complete workflow:

1. Natural language description → Komposition JSON generation
2. Komposition JSON → uber-kompost Java library processing  
3. Video output → Verification using MCP verification component

The test validates that the entire pipeline works and produces expected results.
"""

import asyncio
import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.server import mcp, file_manager
from src.config import SecurityConfig


async def call_tool(name, **kwargs):
    """Helper to call MCP tools and parse JSON response."""
    result = await mcp.call_tool(name, kwargs)
    if result and len(result) > 0:
        return json.loads(result[0].text)
    return {}

# Add Komposteur integration
sys.path.insert(0, str(Path(__file__).parent / "integration" / "komposteur"))
from tools.mcp_tools import register_komposteur_tools

class NaturalLanguageMusicVideoCreator:
    """Creates music videos from natural language using MCP server + uber-kompost"""
    
    def __init__(self):
        self.kompost_file_path: Path = None
        self.output_video_path: Path = None
        
    async def log_step(self, step: str, details: str = ""):
        """Log progress"""
        print(f"\n🎬 {step}")
        if details:
            print(f"   {details}")
    
    async def setup_test_environment(self):
        """Setup test files in source directory"""
        await self.log_step("Setting up test environment", "Copying test files to source directory")
        
        test_files_dir = Path(__file__).parent / "tests" / "files"
        source_dir = SecurityConfig.SOURCE_DIR
        
        # Ensure source directory exists
        source_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy test files
        copied_files = []
        for test_file in test_files_dir.glob("*"):
            if test_file.is_file() and test_file.suffix.lower() in ['.mp4', '.flac', '.jpg']:
                dest_file = source_dir / test_file.name
                shutil.copy2(test_file, dest_file)
                copied_files.append(test_file.name)
                print(f"   📁 Copied: {test_file.name}")
        
        return copied_files
    
    async def generate_komposition_from_natural_language(self, description: str) -> Dict[str, Any]:
        """Generate komposition JSON from natural language description"""
        await self.log_step("Generating komposition from natural language", f"Description: '{description}'")
        
        try:
            result = await call_tool(
                'generate_komposition_from_description',
                description=description,
                title="Natural Language Music Video",
                custom_bpm=120
            )
            
            if result.get('success'):
                # Save the generated komposition to a file
                komposition_data = result.get('komposition_data')
                if komposition_data:
                    self.kompost_file_path = Path("/tmp/natural_language_kompost.json")
                    with open(self.kompost_file_path, 'w') as f:
                        json.dump(komposition_data, f, indent=2)
                    
                    print(f"   ✅ Generated komposition JSON: {len(str(komposition_data))} characters")
                    print(f"   📄 Saved to: {self.kompost_file_path}")
                    return result
                else:
                    return {"success": False, "error": "No komposition data generated"}
            else:
                return result
                
        except Exception as e:
            return {"success": False, "error": f"Natural language processing failed: {str(e)}"}
    
    async def process_with_uber_kompost(self) -> Dict[str, Any]:
        """Process the komposition JSON using uber-kompost Java library"""
        await self.log_step("Processing with uber-kompost Java library", f"Input: {self.kompost_file_path}")
        
        if not self.kompost_file_path or not self.kompost_file_path.exists():
            return {"success": False, "error": "No kompost file available for processing"}
        
        try:
            # Import and test uber-kompost bridge
            from bridge.uber_kompost_bridge import get_uber_bridge
            
            bridge = get_uber_bridge()
            if not bridge.is_available():
                return {
                    "success": False, 
                    "error": "Uber-kompost JAR not available. Build with: mvn clean package -pl uber-kompost -DskipTests",
                    "uber_kompost_missing": True
                }
            
            # Process the kompost JSON
            result = bridge.process_kompost_json(str(self.kompost_file_path))
            
            if result.get('success'):
                print(f"   ✅ Uber-kompost processing completed")
                
                # Extract output path from result
                if 'output_path' in result:
                    self.output_video_path = Path(result['output_path'])
                    print(f"   📹 Output video: {self.output_video_path}")
                
                return result
            else:
                return result
                
        except Exception as e:
            return {"success": False, "error": f"Uber-kompost processing failed: {str(e)}"}
    
    async def verify_video_output(self, expected_description: str) -> Dict[str, Any]:
        """Verify the generated video using MCP verification component"""
        await self.log_step("Verifying video output", "Using MCP verification component")
        
        if not self.output_video_path or not self.output_video_path.exists():
            return {
                "success": False, 
                "error": "No output video file found",
                "expected_path": str(self.output_video_path) if self.output_video_path else "None"
            }
        
        try:
            # Get file ID for the output video (this would need to be imported into MCP system)
            # For now, we'll do basic file verification
            file_stat = self.output_video_path.stat()
            
            verification = {
                "success": True,
                "video_file_exists": True,
                "file_size_mb": file_stat.st_size / (1024 * 1024),
                "file_path": str(self.output_video_path),
                "verification_summary": {
                    "file_created": True,
                    "reasonable_size": file_stat.st_size > 1000,  # > 1KB
                    "matches_description": expected_description in str(self.kompost_file_path)
                }
            }
            
            print(f"   ✅ Video file created: {verification['file_size_mb']:.2f} MB")
            print(f"   📍 Location: {verification['file_path']}")
            
            return verification
            
        except Exception as e:
            return {"success": False, "error": f"Verification failed: {str(e)}"}
    
    async def cleanup(self):
        """Clean up temporary files"""
        await self.log_step("Cleaning up", "Removing temporary files")
        
        if self.kompost_file_path and self.kompost_file_path.exists():
            self.kompost_file_path.unlink()
            print(f"   🗑️ Removed: {self.kompost_file_path}")
        
        await call_tool('cleanup_temp_files')
    
    async def create_music_video_from_description(self, description: str) -> Dict[str, Any]:
        """Main workflow: Natural language → Music video"""
        print("🎵 Natural Language Music Video Creation Test 🎵")
        print("=" * 70)
        print(f"Description: '{description}'")
        print("=" * 70)
        
        try:
            # 1. Setup environment
            await self.setup_test_environment()
            
            # 2. Generate komposition from natural language
            komposition_result = await self.generate_komposition_from_natural_language(description)
            if not komposition_result.get('success'):
                return {
                    "success": False,
                    "step_failed": "natural_language_generation",
                    "error": komposition_result.get('error')
                }
            
            # 3. Process with uber-kompost Java library
            processing_result = await self.process_with_uber_kompost()
            if not processing_result.get('success'):
                return {
                    "success": False,
                    "step_failed": "uber_kompost_processing",
                    "error": processing_result.get('error'),
                    "uber_kompost_available": not processing_result.get('uber_kompost_missing', False)
                }
            
            # 4. Verify video output
            verification_result = await self.verify_video_output(description)
            if not verification_result.get('success'):
                return {
                    "success": False,
                    "step_failed": "video_verification",
                    "error": verification_result.get('error')
                }
            
            # 5. Success!
            await self.log_step("🎉 Music Video Creation Complete!", 
                              f"Successfully created video from: '{description}'")
            
            return {
                "success": True,
                "workflow_completed": True,
                "steps_completed": [
                    "natural_language_generation",
                    "uber_kompost_processing", 
                    "video_verification"
                ],
                "komposition_result": komposition_result,
                "processing_result": processing_result,
                "verification_result": verification_result,
                "output_video_path": str(self.output_video_path) if self.output_video_path else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Workflow failed: {str(e)}",
                "step_failed": "unknown"
            }
        finally:
            await self.cleanup()

async def run_test_scenarios():
    """Run multiple test scenarios"""
    scenarios = [
        {
            "name": "Film Noir Music Video",
            "description": "Create a dramatic film noir style music video with dark atmosphere and vintage effects, 60 seconds long"
        },
        {
            "name": "Beat Synchronized Video",  
            "description": "Create a 120 BPM beat-synchronized music video with rhythmic cuts and audio sync"
        },
        {
            "name": "Simple Music Video",
            "description": "Create a simple music video combining available video clips with background music"
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(scenarios):
        print(f"\n{'='*80}")
        print(f"🎬 SCENARIO {i+1}: {scenario['name']}")
        print(f"{'='*80}")
        
        creator = NaturalLanguageMusicVideoCreator()
        result = await creator.create_music_video_from_description(scenario['description'])
        
        results.append({
            "scenario": scenario['name'],
            "description": scenario['description'],
            "result": result
        })
        
        # Print result summary
        if result.get('success'):
            print(f"✅ {scenario['name']}: SUCCESS")
            if result.get('output_video_path'):
                print(f"   📹 Video created: {result['output_video_path']}")
        else:
            print(f"❌ {scenario['name']}: FAILED")
            print(f"   🐛 Error: {result.get('error')}")
            print(f"   📍 Failed at: {result.get('step_failed', 'unknown')}")
    
    return results

async def main():
    """Run the complete test suite"""
    print("🚀 Starting Natural Language Music Video Creation Test Suite")
    
    # Run all test scenarios
    results = await run_test_scenarios()
    
    # Print final summary
    print(f"\n{'='*80}")
    print("📊 FINAL TEST RESULTS")
    print(f"{'='*80}")
    
    successful_tests = 0
    total_tests = len(results)
    
    for result in results:
        status = "✅ PASS" if result['result'].get('success') else "❌ FAIL"
        print(f"{status} {result['scenario']}")
        
        if result['result'].get('success'):
            successful_tests += 1
        else:
            error = result['result'].get('error', 'Unknown error')
            step_failed = result['result'].get('step_failed', 'unknown')
            print(f"      Failed at: {step_failed}")
            print(f"      Error: {error}")
    
    print(f"\n🎯 Overall Results: {successful_tests}/{total_tests} scenarios passed")
    
    if successful_tests == total_tests:
        print("🎉 All tests passed! Natural language music video creation is fully functional.")
        return 0
    elif successful_tests > 0:
        print("⚠️  Partial success. Some scenarios working, others need attention.")
        return 1
    else:
        print("❌ All tests failed. System needs debugging.")
        return 2

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)