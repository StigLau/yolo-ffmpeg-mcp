"""
Video Comparison Tool for Side-by-Side Analysis
Creates comparative analysis workflows for music video production
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

try:
    from .ffmpeg_wrapper import FFMPEGWrapper
    from .config import SecurityConfig
    from .file_manager import FileManager
    from .content_analyzer import VideoContentAnalyzer
except ImportError:
    from ffmpeg_wrapper import FFMPEGWrapper
    from config import SecurityConfig
    from file_manager import FileManager
    from content_analyzer import VideoContentAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class ComparisonConfig:
    """Configuration for video comparison"""
    layout: str = "side_by_side"  # "side_by_side", "top_bottom", "picture_in_picture"
    sync_audio: bool = True  # Whether to sync audio tracks
    add_labels: bool = True  # Add text labels to identify versions
    resolution: str = "1920x1080"  # Output resolution
    background_color: str = "black"  # Background color for gaps

class VideoComparisonTool:
    """Tool for creating side-by-side video comparisons"""
    
    def __init__(self, ffmpeg_wrapper: FFMPEGWrapper, file_manager: FileManager, content_analyzer: VideoContentAnalyzer):
        self.ffmpeg = ffmpeg_wrapper
        self.file_manager = file_manager
        self.content_analyzer = content_analyzer
        
    async def create_side_by_side_comparison(self, 
                                          file_id_1: str, 
                                          file_id_2: str, 
                                          label_1: str = "Version A",
                                          label_2: str = "Version B",
                                          config: ComparisonConfig = None) -> Dict[str, Any]:
        """Create side-by-side comparison of two videos"""
        if config is None:
            config = ComparisonConfig()
            
        # Resolve file paths
        source_path_1 = self.file_manager.resolve_id(file_id_1)
        source_path_2 = self.file_manager.resolve_id(file_id_2)
        
        if not source_path_1 or not source_path_2:
            return {"success": False, "error": "One or both files not found"}
        
        # Generate output path
        output_path = SecurityConfig.TEMP_DIR / f"comparison_{file_id_1}_{file_id_2}_sidebyside.mp4"
        
        try:
            # Get video information for both files
            info_1 = await self.ffmpeg.get_file_info(source_path_1, self.file_manager, file_id_1)
            info_2 = await self.ffmpeg.get_file_info(source_path_2, self.file_manager, file_id_2)
            
            if not info_1.get("success") or not info_2.get("success"):
                return {"success": False, "error": "Failed to get video information"}
            
            # Determine output dimensions
            target_width, target_height = map(int, config.resolution.split('x'))
            video_width = target_width // 2
            video_height = target_height
            
            # Build FFmpeg filter complex for side-by-side layout
            if config.add_labels:
                # Add text labels to identify versions
                filter_complex = (
                    f"[0:v]scale={video_width}:{video_height},setsar=1:1,"
                    f"drawtext=text='{label_1}':fontsize=24:fontcolor=white:x=10:y=10:box=1:boxcolor=black@0.5[left];"
                    f"[1:v]scale={video_width}:{video_height},setsar=1:1,"
                    f"drawtext=text='{label_2}':fontsize=24:fontcolor=white:x=10:y=10:box=1:boxcolor=black@0.5[right];"
                    f"color=c={config.background_color}:s={target_width}x{target_height}:r=25[bg];"
                    f"[bg][left]overlay=x=0:y=0[bg_left];"
                    f"[bg_left][right]overlay=x={video_width}:y=0[outv]"
                )
            else:
                # Simple side-by-side without labels
                filter_complex = (
                    f"[0:v]scale={video_width}:{video_height},setsar=1:1[left];"
                    f"[1:v]scale={video_width}:{video_height},setsar=1:1[right];"
                    f"[left][right]hstack=inputs=2[outv]"
                )
            
            # Handle audio
            if config.sync_audio:
                # Mix both audio tracks
                audio_filter = "[0:a][1:a]amix=inputs=2:duration=longest[outa]"
                audio_map = ["-map", "[outa]"]
            else:
                # Use audio from first video only
                audio_map = ["-map", "0:a"]
            
            # Build complete command
            command = [
                self.ffmpeg.ffmpeg_path,
                "-i", str(source_path_1),
                "-i", str(source_path_2),
                "-filter_complex", f"{filter_complex};{audio_filter}" if config.sync_audio else filter_complex,
                "-map", "[outv]",
                *audio_map,
                "-c:v", "libx264",
                "-c:a", "aac",
                "-y",
                str(output_path)
            ]
            
            result = await self.ffmpeg.execute_command(command)
            
            if result["success"]:
                output_file_id = self.file_manager.register_file(output_path)
                
                return {
                    "success": True,
                    "comparison_type": "side_by_side",
                    "input_files": [
                        {"file_id": file_id_1, "label": label_1},
                        {"file_id": file_id_2, "label": label_2}
                    ],
                    "output_file_id": output_file_id,
                    "output_path": str(output_path),
                    "configuration": {
                        "layout": config.layout,
                        "resolution": config.resolution,
                        "labels_enabled": config.add_labels,
                        "audio_sync": config.sync_audio
                    },
                    "processing_time": result.get("processing_time", 0)
                }
            else:
                return {"success": False, "error": result.get("error", "FFmpeg processing failed")}
                
        except Exception as e:
            logger.error(f"Error creating side-by-side comparison: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_analysis_comparison(self, 
                                       file_id_1: str, 
                                       file_id_2: str,
                                       analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Create detailed analysis comparison between two videos"""
        try:
            # Get analysis for both videos
            analysis_1 = await self.content_analyzer.analyze_video_content(file_id_1)
            analysis_2 = await self.content_analyzer.analyze_video_content(file_id_2)
            
            if not analysis_1.get("success") or not analysis_2.get("success"):
                return {"success": False, "error": "Failed to analyze video content"}
            
            # Compare key metrics
            comparison_result = {
                "success": True,
                "comparison_type": "analysis",
                "video_1": {
                    "file_id": file_id_1,
                    "analysis": analysis_1
                },
                "video_2": {
                    "file_id": file_id_2,
                    "analysis": analysis_2
                },
                "differences": self._calculate_differences(analysis_1, analysis_2),
                "recommendations": self._generate_recommendations(analysis_1, analysis_2)
            }
            
            return comparison_result
            
        except Exception as e:
            logger.error(f"Error creating analysis comparison: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_differences(self, analysis_1: Dict[str, Any], analysis_2: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate key differences between two video analyses"""
        differences = {
            "scene_count": {
                "video_1": len(analysis_1.get("scenes", [])),
                "video_2": len(analysis_2.get("scenes", [])),
                "difference": len(analysis_2.get("scenes", [])) - len(analysis_1.get("scenes", []))
            },
            "duration": {
                "video_1": analysis_1.get("duration", 0),
                "video_2": analysis_2.get("duration", 0),
                "difference": analysis_2.get("duration", 0) - analysis_1.get("duration", 0)
            },
            "visual_complexity": {
                "video_1": analysis_1.get("visual_complexity", "unknown"),
                "video_2": analysis_2.get("visual_complexity", "unknown")
            }
        }
        
        # Compare quality scores if available
        if "quality_score" in analysis_1 and "quality_score" in analysis_2:
            differences["quality_score"] = {
                "video_1": analysis_1["quality_score"],
                "video_2": analysis_2["quality_score"],
                "difference": analysis_2["quality_score"] - analysis_1["quality_score"]
            }
        
        return differences
    
    def _generate_recommendations(self, analysis_1: Dict[str, Any], analysis_2: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on comparison"""
        recommendations = []
        
        # Compare scene counts
        scenes_1 = len(analysis_1.get("scenes", []))
        scenes_2 = len(analysis_2.get("scenes", []))
        
        if scenes_1 > scenes_2 * 1.5:
            recommendations.append("Video 1 has significantly more scene changes - may be more dynamic")
        elif scenes_2 > scenes_1 * 1.5:
            recommendations.append("Video 2 has significantly more scene changes - may be more dynamic")
        
        # Compare durations
        duration_1 = analysis_1.get("duration", 0)
        duration_2 = analysis_2.get("duration", 0)
        
        if abs(duration_1 - duration_2) > 5:  # More than 5 second difference
            longer_video = "Video 1" if duration_1 > duration_2 else "Video 2"
            recommendations.append(f"{longer_video} is significantly longer - consider if this affects pacing")
        
        # Quality comparison
        if "quality_score" in analysis_1 and "quality_score" in analysis_2:
            quality_diff = analysis_2["quality_score"] - analysis_1["quality_score"]
            if quality_diff > 0.1:
                recommendations.append("Video 2 appears to have higher technical quality")
            elif quality_diff < -0.1:
                recommendations.append("Video 1 appears to have higher technical quality")
        
        if not recommendations:
            recommendations.append("Videos appear to have similar characteristics")
        
        return recommendations
    
    async def create_four_way_comparison(self, 
                                       file_ids: List[str],
                                       labels: List[str] = None,
                                       config: ComparisonConfig = None) -> Dict[str, Any]:
        """Create 2x2 grid comparison of up to 4 videos"""
        if len(file_ids) < 2 or len(file_ids) > 4:
            return {"success": False, "error": "Four-way comparison requires 2-4 videos"}
        
        if config is None:
            config = ComparisonConfig()
        
        if labels is None:
            labels = [f"Version {chr(65+i)}" for i in range(len(file_ids))]
        
        # Resolve all file paths
        source_paths = []
        for file_id in file_ids:
            source_path = self.file_manager.resolve_id(file_id)
            if not source_path:
                return {"success": False, "error": f"File not found: {file_id}"}
            source_paths.append(source_path)
        
        # Generate output path
        output_path = SecurityConfig.TEMP_DIR / f"comparison_4way_{'_'.join(file_ids[:4])}.mp4"
        
        try:
            # Determine output dimensions
            target_width, target_height = map(int, config.resolution.split('x'))
            video_width = target_width // 2
            video_height = target_height // 2
            
            # Build filter complex for 2x2 grid
            inputs = []
            for i, (source_path, label) in enumerate(zip(source_paths, labels)):
                if config.add_labels:
                    inputs.append(
                        f"[{i}:v]scale={video_width}:{video_height},setsar=1:1,"
                        f"drawtext=text='{label}':fontsize=20:fontcolor=white:x=10:y=10:box=1:boxcolor=black@0.5[v{i}]"
                    )
                else:
                    inputs.append(f"[{i}:v]scale={video_width}:{video_height},setsar=1:1[v{i}]")
            
            # Create grid layout
            if len(file_ids) == 2:
                # Side by side
                filter_complex = ";".join(inputs) + f";[v0][v1]hstack=inputs=2[outv]"
            elif len(file_ids) == 3:
                # Top row: 2 videos, bottom row: 1 video centered
                filter_complex = (
                    ";".join(inputs) + 
                    f";[v0][v1]hstack=inputs=2[top];"
                    f"color=c={config.background_color}:s={video_width}x{video_height}[blank];"
                    f"[blank][v2]hstack=inputs=2[bottom];"
                    f"[top][bottom]vstack=inputs=2[outv]"
                )
            else:  # 4 videos
                # 2x2 grid
                filter_complex = (
                    ";".join(inputs) + 
                    f";[v0][v1]hstack=inputs=2[top];"
                    f"[v2][v3]hstack=inputs=2[bottom];"
                    f"[top][bottom]vstack=inputs=2[outv]"
                )
            
            # Build command with all input files
            command = [self.ffmpeg.ffmpeg_path]
            for source_path in source_paths:
                command.extend(["-i", str(source_path)])
            
            command.extend([
                "-filter_complex", filter_complex,
                "-map", "[outv]",
                "-map", "0:a",  # Use audio from first video
                "-c:v", "libx264",
                "-c:a", "aac",
                "-y",
                str(output_path)
            ])
            
            result = await self.ffmpeg.execute_command(command)
            
            if result["success"]:
                output_file_id = self.file_manager.register_file(output_path)
                
                return {
                    "success": True,
                    "comparison_type": "four_way_grid",
                    "input_files": [
                        {"file_id": file_id, "label": label} 
                        for file_id, label in zip(file_ids, labels)
                    ],
                    "output_file_id": output_file_id,
                    "output_path": str(output_path),
                    "configuration": {
                        "layout": f"{len(file_ids)}_way_grid",
                        "resolution": config.resolution,
                        "labels_enabled": config.add_labels
                    },
                    "processing_time": result.get("processing_time", 0)
                }
            else:
                return {"success": False, "error": result.get("error", "FFmpeg processing failed")}
                
        except Exception as e:
            logger.error(f"Error creating four-way comparison: {e}")
            return {"success": False, "error": str(e)}