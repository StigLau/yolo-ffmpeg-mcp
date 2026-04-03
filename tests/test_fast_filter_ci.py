#!/usr/bin/env python3
"""
Fast CI Test: Random Filter Comparison
Picks random filters, logs combinations, allows specific filter testing.
Optimized for CI speed and debugging.
"""
import subprocess
import json
import time
import random
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from tools.video_comparison_test_library import VideoComparisonTester

class FastFilterCITest:
    """Fast CI test with random filter selection and specific testing capability"""
    
    def __init__(self, test_duration: int = 10):
        self.source_dir = Path("/tmp/music/source")
        self.test_output_dir = Path("/tmp/music/ci_test_outputs")
        self.test_output_dir.mkdir(exist_ok=True)
        
        self.test_duration = test_duration  # Configurable duration
        self.source_video = self.source_dir / "_wZ5Hof5tXY_136.mp4"
        self.audio_track = self.source_dir / "Subnautic Measures.flac"
        
        # Comprehensive filter library organized by expected effectiveness
        self.filter_library = {
            # MAJOR EFFECTS (should always be detected)
            "major": {
                "dramatic_bw": "format=gray,eq=contrast=3.0:brightness=0.1",
                "edge_detect": "edgedetect=low=0.1:high=0.4", 
                "negative": "negate",
                "posterize": "format=gray,eq=contrast=4.0",
                "sobel_edges": "sobel",
                "emboss": "convolution='1 1 1|1 -8 1|1 1 1:1 1 1|1 -8 1|1 1 1:1 1 1|1 -8 1|1 1 1:1 1 1|1 -8 1|1 1 1'"
            },
            
            # SIGNIFICANT EFFECTS (should usually be detected)
            "significant": {
                "sepia": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131",
                "high_contrast": "eq=contrast=2.0:brightness=0.1",
                "heavy_blur": "boxblur=5:2",
                "vintage": "eq=contrast=1.8:brightness=-0.2:saturation=0.7",
                "warm_tone": "colortemperature=4000",
                "cold_tone": "colortemperature=8000"
            },
            
            # MINOR EFFECTS (may or may not be detected)
            "minor": {
                "subtle_saturation": "eq=saturation=1.3:brightness=0.05",
                "mild_blur": "boxblur=2:1",
                "slight_sharpen": "unsharp=5:5:1.0:5:5:0.0",
                "gamma_adjust": "eq=gamma=1.2",
                "mild_contrast": "eq=contrast=1.1"
            },
            
            # CONTROL (should show no difference)
            "control": {
                "passthrough": "null",
                "copy": "copy"
            }
        }
        
        self.tester = VideoComparisonTester()
        
    def get_random_filter_pair(self, categories: Optional[List[str]] = None) -> Tuple[str, str, str, str]:
        """Get random filter pair for testing"""
        
        if categories is None:
            categories = ["major", "significant", "minor", "control"]
        
        # Select random category and filter
        category = random.choice(categories)
        filters = self.filter_library[category]
        filter_name = random.choice(list(filters.keys()))
        filter_cmd = filters[filter_name]
        
        return category, filter_name, filter_cmd, f"{category}_{filter_name}"
    
    def create_video_with_filter(self, filter_cmd: str, output_name: str) -> Tuple[bool, str, Dict]:
        """Create video with specified filter, return success, path, and metadata"""
        
        output_file = self.test_output_dir / f"{output_name}_{int(time.time())}.mp4"
        
        cmd = [
            "ffmpeg", "-y", "-v", "quiet",  # Quiet for CI speed
            "-i", str(self.source_video),
            "-i", str(self.audio_track),
            "-t", str(self.test_duration),
            "-vf", filter_cmd,
            "-c:v", "libx264", "-c:a", "aac",
            "-shortest",
            str(output_file)
        ]
        
        start_time = time.time()
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            creation_time = time.time() - start_time
            
            # Get basic file info
            file_size = output_file.stat().st_size
            
            metadata = {
                "creation_time": creation_time,
                "file_size": file_size,
                "file_size_mb": file_size / (1024 * 1024),
                "filter_cmd": filter_cmd
            }
            
            return True, str(output_file), metadata
            
        except subprocess.CalledProcessError as e:
            return False, "", {"error": str(e)}
    
    def run_random_filter_test(self, num_tests: int = 1) -> Dict:
        """Run random filter comparison test"""
        
        print(f"🎲 FAST RANDOM FILTER CI TEST")
        print(f"   Tests: {num_tests}, Duration: {self.test_duration}s each")
        print("=" * 50)
        
        start_time = time.time()
        results = []
        
        for test_num in range(num_tests):
            print(f"\n🧪 Test {test_num + 1}/{num_tests}")
            
            # Create original video
            success, original_path, orig_meta = self.create_video_with_filter("null", "original")
            if not success:
                results.append({"test_num": test_num + 1, "success": False, "error": "Failed to create original"})
                continue
            
            # Get random filter
            category, filter_name, filter_cmd, full_name = self.get_random_filter_pair()
            
            print(f"   🎨 Filter: {filter_name} (category: {category})")
            print(f"   📝 Command: {filter_cmd}")
            
            # Create filtered video
            success, filtered_path, filt_meta = self.create_video_with_filter(filter_cmd, f"filtered_{filter_name}")
            if not success:
                results.append({
                    "test_num": test_num + 1, 
                    "success": False, 
                    "filter_tested": full_name,
                    "error": "Failed to create filtered video"
                })
                continue
            
            # Analyze difference
            analysis = self.tester.compare_videos(original_path, filtered_path)
            
            # Determine if result makes sense
            expected_levels = {
                "major": ["major", "significant"],
                "significant": ["significant", "major", "minor"],
                "minor": ["minor", "significant", "none"],
                "control": ["none"]
            }
            
            actual_level = analysis["processing_level"]
            expected_for_category = expected_levels[category]
            result_makes_sense = actual_level in expected_for_category
            
            # Log result
            test_result = {
                "test_num": test_num + 1,
                "success": True,
                "filter_tested": full_name,
                "filter_category": category,
                "filter_name": filter_name,
                "filter_cmd": filter_cmd,
                "expected_levels": expected_for_category,
                "actual_level": actual_level,
                "result_makes_sense": result_makes_sense,
                "metrics": {
                    "bitrate_ratio": analysis["metrics"]["bitrate_ratio"],
                    "size_ratio": analysis["metrics"]["size_ratio"],
                    "pixel_format_change": analysis["metrics"]["pixel_format_change"],
                    "profile_change": analysis["metrics"]["profile_change"]
                },
                "creation_times": {
                    "original": orig_meta["creation_time"],
                    "filtered": filt_meta["creation_time"]
                },
                "file_sizes": {
                    "original_mb": orig_meta["file_size_mb"],
                    "filtered_mb": filt_meta["file_size_mb"]
                }
            }
            
            # Print result
            status = "✅ PASS" if result_makes_sense else "❌ FAIL"
            print(f"   {status} Expected: {expected_for_category}, Got: {actual_level}")
            print(f"   📊 Ratios: Bitrate {analysis['metrics']['bitrate_ratio']:.2f}x, Size {analysis['metrics']['size_ratio']:.2f}x")
            print(f"   ⏱️ Creation: {filt_meta['creation_time']:.1f}s")
            
            results.append(test_result)
            
            # Cleanup files to save space
            Path(original_path).unlink(missing_ok=True)
            Path(filtered_path).unlink(missing_ok=True)
        
        # Summary
        total_tests = len([r for r in results if r.get("success", False)])
        passed_tests = len([r for r in results if r.get("result_makes_sense", False)])
        elapsed_time = time.time() - start_time
        
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "elapsed_time": elapsed_time,
            "avg_time_per_test": elapsed_time / total_tests if total_tests > 0 else 0,
            "results": results
        }
        
        print(f"\n" + "=" * 50)
        print(f"🎯 SUMMARY")
        print(f"   Tests: {total_tests}, Passed: {passed_tests}, Failed: {total_tests - passed_tests}")
        print(f"   Pass Rate: {summary['pass_rate']:.1f}%")
        print(f"   Total Time: {elapsed_time:.1f}s, Avg: {summary['avg_time_per_test']:.1f}s/test")
        
        # Log problematic filters
        failed_results = [r for r in results if not r.get("result_makes_sense", True)]
        if failed_results:
            print(f"\n⚠️ PROBLEMATIC FILTERS:")
            for result in failed_results:
                print(f"   • {result['filter_tested']}: Expected {result['expected_levels']}, Got {result['actual_level']}")
                print(f"     Command: {result['filter_cmd']}")
        
        return summary
    
    def run_specific_filter_test(self, filter1: str, filter2: str) -> Dict:
        """Test two specific filters against each other"""
        
        print(f"🔬 SPECIFIC FILTER COMPARISON TEST")
        print(f"   Filter 1: {filter1}")
        print(f"   Filter 2: {filter2}")
        print("=" * 50)
        
        # Find filters in library
        filter1_cmd = None
        filter2_cmd = None
        
        for category, filters in self.filter_library.items():
            if filter1 in filters:
                filter1_cmd = filters[filter1]
            if filter2 in filters:
                filter2_cmd = filters[filter2]
        
        if not filter1_cmd or not filter2_cmd:
            return {
                "success": False, 
                "error": f"Filter(s) not found. Available: {self._list_available_filters()}"
            }
        
        start_time = time.time()
        
        # Create videos
        print(f"🎨 Creating video with {filter1}...")
        success1, path1, meta1 = self.create_video_with_filter(filter1_cmd, f"test_{filter1}")
        
        print(f"🎨 Creating video with {filter2}...")
        success2, path2, meta2 = self.create_video_with_filter(filter2_cmd, f"test_{filter2}")
        
        if not (success1 and success2):
            return {"success": False, "error": "Failed to create one or both videos"}
        
        # Analyze
        print(f"🔍 Analyzing differences...")
        analysis = self.tester.compare_videos(path1, path2)
        
        elapsed_time = time.time() - start_time
        
        result = {
            "success": True,
            "filter1": filter1,
            "filter2": filter2,
            "filter1_cmd": filter1_cmd,
            "filter2_cmd": filter2_cmd,
            "analysis": analysis,
            "elapsed_time": elapsed_time,
            "file_info": {
                "filter1_size_mb": meta1["file_size_mb"],
                "filter2_size_mb": meta2["file_size_mb"],
                "creation_times": [meta1["creation_time"], meta2["creation_time"]]
            }
        }
        
        # Print results
        print(f"\n📊 COMPARISON RESULTS:")
        print(f"   Processing Level: {analysis['processing_level']}")
        print(f"   Same Source: {analysis['same_source']}")
        print(f"   Bitrate Ratio: {analysis['metrics']['bitrate_ratio']:.2f}x")
        print(f"   Size Ratio: {analysis['metrics']['size_ratio']:.2f}x")
        print(f"   Pixel Format Change: {analysis['metrics']['pixel_format_change']}")
        print(f"   Profile Change: {analysis['metrics']['profile_change']}")
        print(f"   Total Time: {elapsed_time:.1f}s")
        
        return result
    
    def _list_available_filters(self) -> str:
        """List all available filters"""
        all_filters = []
        for category, filters in self.filter_library.items():
            all_filters.extend(filters.keys())
        return ", ".join(sorted(all_filters))

def main():
    """Main entry point with CLI arguments"""
    
    parser = argparse.ArgumentParser(description="Fast Filter CI Test")
    parser.add_argument("--tests", "-t", type=int, default=1, help="Number of random tests to run")
    parser.add_argument("--duration", "-d", type=int, default=10, help="Video duration in seconds")
    parser.add_argument("--specific", "-s", nargs=2, metavar=("FILTER1", "FILTER2"), 
                       help="Test two specific filters against each other")
    parser.add_argument("--list", "-l", action="store_true", help="List available filters")
    
    args = parser.parse_args()
    
    tester = FastFilterCITest(test_duration=args.duration)
    
    # List filters if requested
    if args.list:
        print("📋 AVAILABLE FILTERS:")
        for category, filters in tester.filter_library.items():
            print(f"\n{category.upper()}:")
            for name, cmd in filters.items():
                print(f"   {name}: {cmd}")
        return 0
    
    # Run specific filter test
    if args.specific:
        filter1, filter2 = args.specific
        result = tester.run_specific_filter_test(filter1, filter2)
        
        if result["success"]:
            print(f"\n✅ Specific filter test completed successfully")
            return 0
        else:
            print(f"\n❌ Specific filter test failed: {result.get('error')}")
            return 1
    
    # Run random tests
    try:
        result = tester.run_random_filter_test(args.tests)
        
        if result["pass_rate"] >= 80:  # 80% pass rate threshold
            print(f"\n✅ CI TEST PASSED (pass rate: {result['pass_rate']:.1f}%)")
            return 0
        else:
            print(f"\n⚠️ CI TEST NEEDS REVIEW (pass rate: {result['pass_rate']:.1f}%)")
            return 1
            
    except Exception as e:
        print(f"💥 CI TEST ERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())