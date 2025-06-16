#!/usr/bin/env python3
"""
Format Manager - Intelligent aspect ratio and cropping management
Handles form-factor selection, aspect ratio analysis, and smart cropping options
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import subprocess

class AspectRatio(Enum):
    """Common aspect ratios with their numeric values"""
    LANDSCAPE_16_9 = (16, 9, "16:9")
    LANDSCAPE_4_3 = (4, 3, "4:3") 
    PORTRAIT_9_16 = (9, 16, "9:16")
    PORTRAIT_3_4 = (3, 4, "3:4")
    SQUARE_1_1 = (1, 1, "1:1")
    CINEMA_21_9 = (21, 9, "21:9")
    
    def __init__(self, width_ratio, height_ratio, display_name):
        self.width_ratio = width_ratio
        self.height_ratio = height_ratio
        self.display_name = display_name
        self.numeric_ratio = width_ratio / height_ratio

class CropMode(Enum):
    """Different cropping strategies for aspect ratio mismatches"""
    CENTER_CROP = "center_crop"           # Crop from center, losing edges
    SMART_CROP = "smart_crop"             # AI-detected focal point cropping  
    SCALE_LETTERBOX = "scale_letterbox"   # Fit with black bars
    SCALE_BLUR_BG = "scale_blur_bg"       # Fit with blurred background
    SCALE_STRETCH = "scale_stretch"       # Distort to fit (not recommended)
    TOP_CROP = "top_crop"                 # Crop from top (good for people)
    BOTTOM_CROP = "bottom_crop"           # Crop from bottom

@dataclass
class FormatSpec:
    """Complete format specification for video composition"""
    aspect_ratio: AspectRatio
    resolution: Tuple[int, int]  # (width, height)
    crop_mode: CropMode
    target_fps: int = 30
    
    @property
    def width(self) -> int:
        return self.resolution[0]
    
    @property
    def height(self) -> int:
        return self.resolution[1]
    
    @property
    def orientation(self) -> str:
        if self.width > self.height:
            return "landscape"
        elif self.height > self.width:
            return "portrait"
        else:
            return "square"

@dataclass
class VideoAnalysis:
    """Analysis of a video file's format properties"""
    file_id: str
    width: int
    height: int
    duration: float
    fps: float
    aspect_ratio: float
    suggested_crop_mode: CropMode
    crop_compatibility: Dict[CropMode, str]  # mode -> quality rating
    
    @property
    def orientation(self) -> str:
        if self.width > self.height:
            return "landscape"
        elif self.height > self.width:
            return "portrait"
        else:
            return "square"

class FormatManager:
    """Manages video format analysis, conversion planning, and intelligent cropping"""
    
    def __init__(self):
        self.common_resolutions = {
            AspectRatio.LANDSCAPE_16_9: [(1920, 1080), (1280, 720), (3840, 2160)],
            AspectRatio.PORTRAIT_9_16: [(1080, 1920), (720, 1280), (2160, 3840)],
            AspectRatio.SQUARE_1_1: [(1080, 1080), (720, 720), (1200, 1200)],
            AspectRatio.LANDSCAPE_4_3: [(1024, 768), (1280, 960)],
            AspectRatio.PORTRAIT_3_4: [(768, 1024), (960, 1280)],
            AspectRatio.CINEMA_21_9: [(2560, 1080), (3440, 1440)]
        }
    
    def analyze_video_format(self, file_path: str, file_id: str) -> VideoAnalysis:
        """Analyze a video file's format properties and suggest optimal cropping"""
        try:
            # Get video properties with ffprobe
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(result.stdout)
            
            # Find video stream
            video_stream = None
            for stream in data['streams']:
                if stream['codec_type'] == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                raise ValueError(f"No video stream found in {file_path}")
            
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            duration = float(video_stream.get('duration', 0))
            fps = eval(video_stream.get('r_frame_rate', '30/1'))
            aspect_ratio = width / height
            
            # Determine best crop mode based on content analysis
            suggested_crop_mode = self._suggest_crop_mode(width, height, aspect_ratio)
            
            # Rate crop compatibility
            crop_compatibility = self._rate_crop_compatibility(width, height, aspect_ratio)
            
            return VideoAnalysis(
                file_id=file_id,
                width=width,
                height=height,
                duration=duration,
                fps=fps,
                aspect_ratio=aspect_ratio,
                suggested_crop_mode=suggested_crop_mode,
                crop_compatibility=crop_compatibility
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to analyze video format: {e}")
    
    def _suggest_crop_mode(self, width: int, height: int, aspect_ratio: float) -> CropMode:
        """Suggest the best crop mode based on video dimensions"""
        if aspect_ratio > 1.5:  # Very wide (landscape)
            return CropMode.CENTER_CROP
        elif aspect_ratio < 0.7:  # Very tall (portrait)
            return CropMode.TOP_CROP  # Good for people in portraits
        elif 0.9 <= aspect_ratio <= 1.1:  # Nearly square
            return CropMode.CENTER_CROP
        else:
            return CropMode.SMART_CROP  # Moderate mismatches benefit from AI
    
    def _rate_crop_compatibility(self, width: int, height: int, aspect_ratio: float) -> Dict[CropMode, str]:
        """Rate how well different crop modes will work for this video"""
        ratings = {}
        
        # Center crop: Good for symmetric content
        ratings[CropMode.CENTER_CROP] = "excellent" if 0.8 <= aspect_ratio <= 1.25 else "good"
        
        # Smart crop: Generally good, but needs processing time
        ratings[CropMode.SMART_CROP] = "good"
        
        # Letterbox: Always preserves content but may have bars
        ratings[CropMode.SCALE_LETTERBOX] = "excellent"
        
        # Blur background: Great for social media
        ratings[CropMode.SCALE_BLUR_BG] = "excellent" if aspect_ratio != 1.0 else "good"
        
        # Stretch: Usually bad except for minor adjustments
        ratings[CropMode.SCALE_STRETCH] = "poor" if abs(aspect_ratio - 1.0) > 0.3 else "fair"
        
        # Top/bottom crop: Good for portraits with people
        if aspect_ratio < 1:  # Portrait
            ratings[CropMode.TOP_CROP] = "excellent"
            ratings[CropMode.BOTTOM_CROP] = "good"
        else:
            ratings[CropMode.TOP_CROP] = "fair"
            ratings[CropMode.BOTTOM_CROP] = "fair"
        
        return ratings
    
    def suggest_target_format(self, video_analyses: List[VideoAnalysis]) -> FormatSpec:
        """Suggest optimal target format based on multiple input videos"""
        if not video_analyses:
            return FormatSpec(AspectRatio.LANDSCAPE_16_9, (1920, 1080), CropMode.CENTER_CROP)
        
        # Analyze orientation distribution
        orientations = [analysis.orientation for analysis in video_analyses]
        orientation_counts = {
            "landscape": orientations.count("landscape"),
            "portrait": orientations.count("portrait"), 
            "square": orientations.count("square")
        }
        
        # Choose dominant orientation
        dominant_orientation = max(orientation_counts.keys(), key=lambda k: orientation_counts[k])
        
        # Select appropriate aspect ratio and resolution
        if dominant_orientation == "portrait":
            aspect_ratio = AspectRatio.PORTRAIT_9_16
            resolution = (1080, 1920)  # Instagram/TikTok friendly
        elif dominant_orientation == "square":
            aspect_ratio = AspectRatio.SQUARE_1_1
            resolution = (1080, 1080)  # Instagram square
        else:
            aspect_ratio = AspectRatio.LANDSCAPE_16_9
            resolution = (1920, 1080)  # YouTube/general purpose
        
        # Choose crop mode based on input variety
        if len(set(analysis.orientation for analysis in video_analyses)) > 1:
            # Mixed orientations - use blur background
            crop_mode = CropMode.SCALE_BLUR_BG
        else:
            # Consistent orientation - use center crop
            crop_mode = CropMode.CENTER_CROP
        
        return FormatSpec(aspect_ratio, resolution, crop_mode)
    
    def create_format_conversion_plan(
        self, 
        video_analyses: List[VideoAnalysis], 
        target_format: FormatSpec
    ) -> Dict[str, Any]:
        """Create detailed plan for converting videos to target format"""
        plan = {
            "target_format": {
                "aspect_ratio": target_format.aspect_ratio.display_name,
                "resolution": f"{target_format.width}x{target_format.height}",
                "orientation": target_format.orientation,
                "crop_mode": target_format.crop_mode.value
            },
            "video_conversions": [],
            "warnings": [],
            "estimated_quality_loss": "minimal"
        }
        
        quality_scores = []
        
        for analysis in video_analyses:
            conversion = {
                "file_id": analysis.file_id,
                "source_resolution": f"{analysis.width}x{analysis.height}",
                "source_aspect_ratio": f"{analysis.aspect_ratio:.2f}",
                "conversion_required": self._needs_conversion(analysis, target_format),
                "crop_strategy": target_format.crop_mode.value,
                "quality_rating": analysis.crop_compatibility.get(target_format.crop_mode, "unknown"),
                "ffmpeg_filters": self._generate_ffmpeg_filters(analysis, target_format)
            }
            
            # Add warnings for significant format mismatches
            if abs(analysis.aspect_ratio - target_format.aspect_ratio.numeric_ratio) > 0.5:
                plan["warnings"].append(
                    f"File {analysis.file_id}: Significant aspect ratio change "
                    f"({analysis.aspect_ratio:.2f} → {target_format.aspect_ratio.numeric_ratio:.2f})"
                )
            
            # Track quality scores
            quality_map = {"excellent": 5, "good": 4, "fair": 3, "poor": 2, "unknown": 3}
            quality_scores.append(quality_map.get(conversion["quality_rating"], 3))
            
            plan["video_conversions"].append(conversion)
        
        # Calculate overall quality estimate
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 3
        if avg_quality >= 4.5:
            plan["estimated_quality_loss"] = "minimal"
        elif avg_quality >= 3.5:
            plan["estimated_quality_loss"] = "moderate"
        else:
            plan["estimated_quality_loss"] = "significant"
        
        return plan
    
    def _needs_conversion(self, analysis: VideoAnalysis, target_format: FormatSpec) -> bool:
        """Check if video needs format conversion"""
        return (
            analysis.width != target_format.width or
            analysis.height != target_format.height or
            abs(analysis.aspect_ratio - target_format.aspect_ratio.numeric_ratio) > 0.01
        )
    
    def _generate_ffmpeg_filters(self, analysis: VideoAnalysis, target_format: FormatSpec) -> List[str]:
        """Generate FFmpeg filter chain for format conversion"""
        filters = []
        
        if target_format.crop_mode == CropMode.CENTER_CROP:
            # Scale and center crop
            filters.append(f"scale={target_format.width}:{target_format.height}:force_original_aspect_ratio=increase")
            filters.append(f"crop={target_format.width}:{target_format.height}")
            
        elif target_format.crop_mode == CropMode.SCALE_LETTERBOX:
            # Scale with letterboxing (black bars)
            filters.append(f"scale={target_format.width}:{target_format.height}:force_original_aspect_ratio=decrease")
            filters.append(f"pad={target_format.width}:{target_format.height}:(ow-iw)/2:(oh-ih)/2:black")
            
        elif target_format.crop_mode == CropMode.SCALE_BLUR_BG:
            # Scale with blurred background
            blur_bg = f"scale={target_format.width}:{target_format.height}:force_original_aspect_ratio=decrease"
            main_video = f"scale={target_format.width}:{target_format.height}:force_original_aspect_ratio=decrease"
            filters.append(f"[0:v]split=2[bg][main]")
            filters.append(f"[bg]{blur_bg},gblur=sigma=20[blurred]")
            filters.append(f"[main]{main_video}[scaled]")
            filters.append(f"[blurred][scaled]overlay=(W-w)/2:(H-h)/2")
            
        elif target_format.crop_mode == CropMode.TOP_CROP:
            # Crop from top (good for portraits with people)
            filters.append(f"scale={target_format.width}:{target_format.height}:force_original_aspect_ratio=increase")
            filters.append(f"crop={target_format.width}:{target_format.height}:0:0")
            
        elif target_format.crop_mode == CropMode.BOTTOM_CROP:
            # Crop from bottom
            filters.append(f"scale={target_format.width}:{target_format.height}:force_original_aspect_ratio=increase")
            filters.append(f"crop={target_format.width}:{target_format.height}:0:ih-{target_format.height}")
            
        elif target_format.crop_mode == CropMode.SCALE_STRETCH:
            # Simple stretch (may distort)
            filters.append(f"scale={target_format.width}:{target_format.height}")
        
        return filters
    
    def generate_preview_frame(
        self, 
        file_path: str, 
        target_format: FormatSpec, 
        timestamp: float = 5.0
    ) -> str:
        """Generate preview frame showing how video will look after conversion"""
        try:
            analysis = self.analyze_video_format(file_path, "preview")
            filters = self._generate_ffmpeg_filters(analysis, target_format)
            
            output_path = f"/tmp/music/temp/preview_{target_format.aspect_ratio.display_name.replace(':', '_')}.jpg"
            
            # Build ffmpeg command
            cmd = [
                'ffmpeg', '-y', '-ss', str(timestamp), '-i', file_path,
                '-vf', ','.join(filters) if filters else f"scale={target_format.width}:{target_format.height}",
                '-frames:v', '1', '-q:v', '2',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg preview generation failed: {result.stderr}")
            
            return output_path
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate preview: {e}")

# Predefined format presets for common use cases
COMMON_PRESETS = {
    "youtube_landscape": FormatSpec(AspectRatio.LANDSCAPE_16_9, (1920, 1080), CropMode.CENTER_CROP),
    "instagram_square": FormatSpec(AspectRatio.SQUARE_1_1, (1080, 1080), CropMode.CENTER_CROP),
    "instagram_story": FormatSpec(AspectRatio.PORTRAIT_9_16, (1080, 1920), CropMode.CENTER_CROP),
    "tiktok_vertical": FormatSpec(AspectRatio.PORTRAIT_9_16, (1080, 1920), CropMode.TOP_CROP),
    "twitter_landscape": FormatSpec(AspectRatio.LANDSCAPE_16_9, (1280, 720), CropMode.CENTER_CROP),
    "facebook_square": FormatSpec(AspectRatio.SQUARE_1_1, (1200, 1200), CropMode.SCALE_BLUR_BG),
    "cinema_wide": FormatSpec(AspectRatio.CINEMA_21_9, (2560, 1080), CropMode.CENTER_CROP)
}