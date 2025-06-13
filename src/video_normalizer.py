"""
Video Normalization Module
Handles orientation and resolution standardization for seamless concatenation
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

try:
    from .config import SecurityConfig
    from .ffmpeg_wrapper import FFMPEGWrapper
except ImportError:
    from config import SecurityConfig
    from ffmpeg_wrapper import FFMPEGWrapper

class VideoNormalizer:
    """Normalizes videos to consistent format for concatenation"""
    
    def __init__(self, ffmpeg_wrapper: FFMPEGWrapper):
        self.ffmpeg_wrapper = ffmpeg_wrapper
        self.temp_dir = Path("/tmp/music/temp")
        
    async def get_video_info(self, video_path: Path) -> Dict[str, Any]:
        """Get detailed video information using ffprobe"""
        cmd = [
            SecurityConfig.FFMPEG_PATH.replace("ffmpeg", "ffprobe"),
            "-v", "quiet",
            "-print_format", "json", 
            "-show_format",
            "-show_streams",
            str(video_path)
        ]
        
        result = await self.ffmpeg_wrapper.execute_command(cmd, timeout=30)
        
        if result["success"]:
            try:
                info = json.loads(result["logs"])
                
                # Find video stream
                video_stream = None
                for stream in info.get("streams", []):
                    if stream.get("codec_type") == "video":
                        video_stream = stream
                        break
                
                if video_stream:
                    width = int(video_stream.get("width", 0))
                    height = int(video_stream.get("height", 0))
                    rotation = video_stream.get("tags", {}).get("rotate", "0")
                    duration = float(video_stream.get("duration", 0))
                    fps = eval(video_stream.get("r_frame_rate", "30/1"))
                    
                    # Determine actual orientation considering rotation
                    if rotation in ["90", "270"]:
                        actual_width, actual_height = height, width
                    else:
                        actual_width, actual_height = width, height
                    
                    orientation = "portrait" if actual_height > actual_width else "landscape"
                    
                    return {
                        "width": width,
                        "height": height,
                        "actual_width": actual_width,
                        "actual_height": actual_height,
                        "rotation": int(rotation),
                        "orientation": orientation,
                        "duration": duration,
                        "fps": fps,
                        "valid": True
                    }
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                print(f"   ⚠️  Failed to parse video info: {e}")
        
        return {"valid": False}
    
    async def normalize_video(self, input_path: Path, target_format: Dict[str, Any]) -> Optional[Path]:
        """Normalize video to target format"""
        
        # Get input video info
        input_info = await self.get_video_info(input_path)
        if not input_info["valid"]:
            print(f"   ❌ Could not analyze input video")
            return None
        
        print(f"   📐 Input: {input_info['actual_width']}x{input_info['actual_height']} ({input_info['orientation']})")
        print(f"   🎯 Target: {target_format['width']}x{target_format['height']} ({target_format['orientation']})")
        
        # Check if normalization is needed
        if (input_info["actual_width"] == target_format["width"] and 
            input_info["actual_height"] == target_format["height"] and
            input_info["rotation"] == 0):
            print(f"   ✅ Video already in target format")
            return input_path
        
        # Create normalized output file
        output_path = self.temp_dir / f"normalized_{input_path.stem}_{target_format['width']}x{target_format['height']}.mp4"
        
        # Build normalization command
        cmd = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(input_path)
        ]
        
        # Build video filter chain
        filters = []
        
        # Handle rotation first if needed
        if input_info["rotation"] != 0:
            if input_info["rotation"] == 90:
                filters.append("transpose=1")  # 90 degrees clockwise
            elif input_info["rotation"] == 180:
                filters.append("transpose=1,transpose=1")  # 180 degrees
            elif input_info["rotation"] == 270:
                filters.append("transpose=2")  # 90 degrees counter-clockwise
        
        # Scale to target resolution with padding
        scale_filter = f"scale={target_format['width']}:{target_format['height']}:force_original_aspect_ratio=decrease"
        pad_filter = f"pad={target_format['width']}:{target_format['height']}:(ow-iw)/2:(oh-ih)/2:black"
        
        filters.extend([scale_filter, pad_filter])
        
        # Apply filters
        if filters:
            cmd.extend(["-vf", ",".join(filters)])
        
        # Output settings
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-y",  # Overwrite output
            str(output_path)
        ])
        
        print(f"   🔧 Normalizing: {' '.join(cmd[:8])}...")
        
        result = await self.ffmpeg_wrapper.execute_command(cmd, timeout=300)
        
        if result["success"] and output_path.exists():
            file_size = output_path.stat().st_size
            print(f"   ✅ Normalized: {file_size:,} bytes")
            return output_path
        else:
            print(f"   ❌ Normalization failed: {result.get('logs', 'Unknown error')[:200]}")
            return None
    
    async def analyze_video_set(self, video_paths: list[Path]) -> Dict[str, Any]:
        """Analyze a set of videos and determine optimal target format"""
        
        print(f"🔍 ANALYZING {len(video_paths)} VIDEOS FOR NORMALIZATION")
        
        video_infos = []
        orientations = []
        
        for i, path in enumerate(video_paths):
            print(f"   📹 Video {i+1}: {path.name}")
            info = await self.get_video_info(path)
            
            if info["valid"]:
                video_infos.append(info)
                orientations.append(info["orientation"])
                print(f"      {info['actual_width']}x{info['actual_height']} ({info['orientation']})")
            else:
                print(f"      ❌ Analysis failed")
        
        if not video_infos:
            return {"valid": False, "error": "No valid videos found"}
        
        # Determine dominant orientation
        portrait_count = orientations.count("portrait")
        landscape_count = orientations.count("landscape") 
        
        if portrait_count >= landscape_count:
            target_orientation = "portrait"
            # Use common portrait resolution
            target_width, target_height = 1080, 1920
        else:
            target_orientation = "landscape"
            # Use common landscape resolution  
            target_width, target_height = 1920, 1080
        
        print(f"\n🎯 TARGET FORMAT DETERMINED:")
        print(f"   Orientation: {target_orientation}")
        print(f"   Resolution: {target_width}x{target_height}")
        print(f"   Reasoning: {portrait_count} portrait, {landscape_count} landscape videos")
        
        return {
            "valid": True,
            "target_format": {
                "width": target_width,
                "height": target_height,
                "orientation": target_orientation
            },
            "video_infos": video_infos,
            "needs_normalization": len(set(orientations)) > 1  # Mixed orientations
        }
    
    async def normalize_video_set(self, video_paths: list[Path]) -> list[Path]:
        """Normalize a set of videos to consistent format"""
        
        analysis = await self.analyze_video_set(video_paths)
        
        if not analysis["valid"]:
            print(f"❌ Video analysis failed: {analysis.get('error')}")
            return video_paths
        
        if not analysis["needs_normalization"]:
            print(f"✅ All videos have consistent orientation - no normalization needed")
            return video_paths
        
        print(f"\n🔧 NORMALIZING VIDEOS TO CONSISTENT FORMAT")
        print("=" * 50)
        
        normalized_paths = []
        target_format = analysis["target_format"]
        
        for i, path in enumerate(video_paths):
            print(f"\n📹 Normalizing video {i+1}: {path.name}")
            
            normalized_path = await self.normalize_video(path, target_format)
            
            if normalized_path:
                normalized_paths.append(normalized_path)
            else:
                print(f"   ⚠️  Normalization failed, using original")
                normalized_paths.append(path)
        
        print(f"\n✅ VIDEO NORMALIZATION COMPLETE")
        print(f"   Original videos: {len(video_paths)}")
        print(f"   Normalized videos: {len(normalized_paths)}")
        
        return normalized_paths