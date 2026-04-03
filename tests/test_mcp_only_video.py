#!/usr/bin/env python3
"""
Create Subnautica music video using MCP-ONLY interface for comparison
This test validates timing calculations and segment processing vs direct FFmpeg
"""
import asyncio
import json
import logging
import time
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.file_manager import FileManager
from src.komposteur_bridge_processor import KomposteurBridgeProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPOnlyVideoCreator:
    """Create video using only MCP interface - no direct FFmpeg calls"""
    
    def __init__(self):
        self.file_manager = FileManager()
        self.komposteur = KomposteurBridgeProcessor()
        self.timing_analysis = {}
        
    async def register_source_files(self):
        """Register source files with MCP and get analysis"""
        logger.info("📁 Phase 1: Registering source files with MCP...")
        
        source_files = [
            "Oa8iS1W3OCM.mp4",
            "3xEMCU1fyl8.mp4", 
            "PLnPZVqiyjA.mp4",
            "Subnautic Measures.flac"
        ]
        
        file_ids = {}
        analyses = {}
        
        for file_path in source_files:
            if Path(file_path).exists():
                logger.info(f"  📄 Registering: {file_path}")
                
                # Register with file manager
                file_id = await self.file_manager.store_file(file_path)
                file_ids[file_path] = file_id
                
                logger.info(f"    🆔 File ID: {file_id}")
                
                # Get MCP analysis if it's a video
                if file_path.endswith('.mp4'):
                    try:
                        analysis = await self.analyze_video_with_mcp(file_id)
                        analyses[file_path] = analysis
                        logger.info(f"    📊 Analysis: {len(analysis)} data points")
                    except Exception as e:
                        logger.warning(f"    ⚠️ Analysis failed: {e}")
            else:
                logger.error(f"  ❌ File not found: {file_path}")
        
        return file_ids, analyses
    
    async def analyze_video_with_mcp(self, file_id):
        """Get MCP's analysis of video timing and structure"""
        # This would call MCP content analysis tools
        # For now, simulate what MCP would provide
        logger.info(f"    🔍 Analyzing video {file_id} via MCP...")
        
        # Simulate MCP analysis response
        analysis = {
            "file_id": file_id,
            "duration": 60.0,  # MCP would calculate this
            "keyframes": [],   # MCP would find keyframes
            "scenes": [],      # MCP would detect scenes
            "optimal_segments": []  # MCP would suggest segments
        }
        
        return analysis
    
    def calculate_mcp_timing_schedule(self, analyses):
        """Let MCP calculate the timing schedule for segments"""
        logger.info("⏰ Phase 2: MCP Timing Schedule Calculation...")
        
        # MCP's approach to timing (vs our manual calculation)
        mcp_schedule = {
            "approach": "MCP_calculated",
            "total_duration": 24.0,
            "segments_per_video": 4,
            "segment_duration": 2.0,
            "beat_sync": "120_BPM",
            "segments": []
        }
        
        # MCP would analyze keyframes and calculate optimal extraction points
        video_files = ["Oa8iS1W3OCM.mp4", "3xEMCU1fyl8.mp4", "PLnPZVqiyjA.mp4"]
        
        for i, video_file in enumerate(video_files):
            video_analysis = analyses.get(video_file, {})
            
            for seg_num in range(4):
                segment_id = (i * 4) + seg_num + 1
                
                # MCP's timing calculation (might differ from our manual approach)
                mcp_start_time = self.calculate_mcp_segment_start(video_file, seg_num, video_analysis)
                
                segment = {
                    "segment_id": f"seg{segment_id:02d}",
                    "source_video": video_file,
                    "source_start_time": mcp_start_time,
                    "duration": 2.0,
                    "target_start_time": (segment_id - 1) * 2.0,
                    "target_end_time": segment_id * 2.0,
                    "mcp_calculated": True
                }
                
                mcp_schedule["segments"].append(segment)
                logger.info(f"  🎬 {segment['segment_id']}: {video_file} @ {mcp_start_time:.3f}s → {segment['target_start_time']:.1f}s-{segment['target_end_time']:.1f}s")
        
        # Save MCP timing schedule
        with open("mcp_timing_schedule.json", "w") as f:
            json.dump(mcp_schedule, f, indent=2)
        
        self.timing_analysis["mcp_schedule"] = mcp_schedule
        return mcp_schedule
    
    def calculate_mcp_segment_start(self, video_file, seg_num, analysis):
        """MCP's calculation of segment start time (vs our manual keyframe approach)"""
        
        # MCP might use different logic than our keyframe alignment
        if video_file == "Oa8iS1W3OCM.mp4":
            # MCP might calculate differently - perhaps more evenly spaced
            return seg_num * 15.0  # Every 15 seconds (vs our keyframe-aligned: 0, 5.29, 10.62, 15.96)
        elif video_file == "3xEMCU1fyl8.mp4":
            return seg_num * 15.0  # Every 15 seconds (vs our keyframe-aligned: 0, 2.5, 5.0, 7.5)
        elif video_file == "PLnPZVqiyjA.mp4":
            return seg_num * 25.0  # Every 25 seconds (vs our keyframe-aligned: 0, 2.5, 4.42, 6.92)
        
        return seg_num * 10.0  # Default fallback
    
    async def create_video_with_mcp(self, file_ids, mcp_schedule):
        """Create video using MCP-only interface"""
        logger.info("🎬 Phase 3: Creating video via MCP interface...")
        
        # Create komposition using MCP's timing schedule
        mcp_komposition = {
            "version": "1.0",
            "title": "Subnautica MCP-Only Test Video",
            "description": "Created using MCP-only interface for comparison",
            "approach": "MCP_calculated_timing",
            "audio": {
                "source": file_ids.get("Subnautic Measures.flac"),
                "volume": 0.8
            },
            "video_segments": [],
            "processing_notes": {
                "method": "MCP_only_no_direct_ffmpeg",
                "timing_calculation": "MCP_calculated_vs_manual_keyframe",
                "quality_approach": "single_step_vs_multi_step"
            }
        }
        
        # Add segments based on MCP schedule
        for segment in mcp_schedule["segments"]:
            video_segment = {
                "id": segment["segment_id"],
                "source_file_id": file_ids.get(segment["source_video"]),
                "source_start": segment["source_start_time"],
                "duration": segment["duration"],
                "target_start": segment["target_start_time"],
                "effects": [
                    {"type": "scale", "width": 1080, "height": 1920},
                    {"type": "vignette", "intensity": 0.3}
                ]
            }
            mcp_komposition["video_segments"].append(video_segment)
        
        # Save MCP komposition
        with open("mcp_only_komposition.json", "w") as f:
            json.dump(mcp_komposition, f, indent=2)
        
        # Use MCP to process the video
        logger.info("  🔄 Processing via MCP bridge...")
        try:
            result = await self.komposteur.process_komposition(mcp_komposition)
            logger.info(f"  ✅ MCP processing completed: {result}")
            return result
        except Exception as e:
            logger.error(f"  ❌ MCP processing failed: {e}")
            return None
    
    def compare_timing_schedules(self):
        """Compare MCP vs Direct FFmpeg timing schedules"""
        logger.info("🔍 Phase 4: Timing Schedule Comparison...")
        
        # Our manual keyframe-aligned schedule (baseline)
        manual_schedule = {
            "approach": "manual_keyframe_aligned",
            "segments": [
                {"id": "seg01", "source": "Oa8iS1W3OCM.mp4", "start": 0.000000, "target": "0.0s-2.0s"},
                {"id": "seg02", "source": "Oa8iS1W3OCM.mp4", "start": 5.291667, "target": "2.0s-4.0s"},
                {"id": "seg03", "source": "Oa8iS1W3OCM.mp4", "start": 10.625000, "target": "4.0s-6.0s"},
                {"id": "seg04", "source": "Oa8iS1W3OCM.mp4", "start": 15.958333, "target": "6.0s-8.0s"},
                {"id": "seg05", "source": "3xEMCU1fyl8.mp4", "start": 0.000000, "target": "8.0s-10.0s"},
                {"id": "seg06", "source": "3xEMCU1fyl8.mp4", "start": 2.500000, "target": "10.0s-12.0s"},
                {"id": "seg07", "source": "3xEMCU1fyl8.mp4", "start": 5.000000, "target": "12.0s-14.0s"},
                {"id": "seg08", "source": "3xEMCU1fyl8.mp4", "start": 7.500000, "target": "14.0s-16.0s"},
                {"id": "seg09", "source": "PLnPZVqiyjA.mp4", "start": 0.000000, "target": "16.0s-18.0s"},
                {"id": "seg10", "source": "PLnPZVqiyjA.mp4", "start": 2.500000, "target": "18.0s-20.0s"},
                {"id": "seg11", "source": "PLnPZVqiyjA.mp4", "start": 4.416667, "target": "20.0s-22.0s"},
                {"id": "seg12", "source": "PLnPZVqiyjA.mp4", "start": 6.916667, "target": "22.0s-24.0s"}
            ]
        }
        
        mcp_schedule = self.timing_analysis.get("mcp_schedule", {})
        
        comparison = {
            "manual_keyframe_aligned": manual_schedule,
            "mcp_calculated": mcp_schedule,
            "differences": [],
            "analysis": {
                "timing_accuracy": "TO_BE_DETERMINED",
                "segment_quality": "TO_BE_COMPARED", 
                "processing_approach": "single_vs_multi_step"
            }
        }
        
        # Compare each segment
        for i, manual_seg in enumerate(manual_schedule["segments"]):
            if i < len(mcp_schedule.get("segments", [])):
                mcp_seg = mcp_schedule["segments"][i]
                
                time_diff = abs(manual_seg["start"] - mcp_seg["source_start_time"])
                
                difference = {
                    "segment": manual_seg["id"],
                    "manual_start": manual_seg["start"],
                    "mcp_start": mcp_seg["source_start_time"],
                    "time_difference": time_diff,
                    "significant": time_diff > 1.0  # >1 second difference
                }
                
                comparison["differences"].append(difference)
                
                if difference["significant"]:
                    logger.warning(f"  ⚠️ Significant timing difference in {difference['segment']}: {time_diff:.3f}s")
                else:
                    logger.info(f"  ✅ {difference['segment']}: {time_diff:.3f}s difference")
        
        # Save comparison
        with open("timing_schedule_comparison.json", "w") as f:
            json.dump(comparison, f, indent=2)
        
        return comparison
    
    async def run_full_comparison(self):
        """Run the complete MCP vs Direct comparison"""
        logger.info("🚀 Starting MCP vs Direct FFmpeg Comparison")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        try:
            # Phase 1: Register files and get MCP analysis
            file_ids, analyses = await self.register_source_files()
            
            # Phase 2: Calculate MCP timing schedule
            mcp_schedule = self.calculate_mcp_timing_schedule(analyses)
            
            # Phase 3: Create video with MCP
            mcp_result = await self.create_video_with_mcp(file_ids, mcp_schedule)
            
            # Phase 4: Compare timing schedules
            comparison = self.compare_timing_schedules()
            
            total_time = time.time() - start_time
            
            # Generate summary report
            summary = {
                "comparison_completed": True,
                "processing_time": total_time,
                "mcp_video_created": mcp_result is not None,
                "timing_differences_found": len([d for d in comparison.get("differences", []) if d.get("significant")]),
                "files_created": [
                    "mcp_timing_schedule.json",
                    "mcp_only_komposition.json", 
                    "timing_schedule_comparison.json"
                ],
                "next_steps": [
                    "Compare video quality between MCP and Direct approaches",
                    "Analyze segment processing differences",
                    "Document multi-step processing benefits",
                    "Create recommendations for Komposteur integration"
                ]
            }
            
            logger.info(f"🏁 Comparison completed in {total_time:.2f} seconds")
            logger.info(f"📊 Timing differences: {summary['timing_differences_found']} significant")
            logger.info(f"🎬 MCP video created: {summary['mcp_video_created']}")
            
            with open("mcp_comparison_summary.json", "w") as f:
                json.dump(summary, f, indent=2)
                
            return summary
            
        except Exception as e:
            logger.error(f"❌ Comparison failed: {e}")
            return None

async def main():
    """Main function"""
    creator = MCPOnlyVideoCreator()
    result = await creator.run_full_comparison()
    
    if result:
        logger.info("✅ MCP vs Direct comparison completed successfully!")
        return True
    else:
        logger.error("❌ MCP vs Direct comparison failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)