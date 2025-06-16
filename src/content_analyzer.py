"""
Content Analysis Module for FFMPEG MCP Server

Provides intelligent video content understanding using:
- PySceneDetect for scene boundary detection  
- OpenCV for basic object recognition
- Metadata storage for persistent content insights

This gives the MCP server "eyes" to understand video content and suggest
intelligent editing operations based on scene structure and visual content.
"""

import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import tempfile
import cv2
import numpy as np

# PySceneDetect imports
try:
    from scenedetect import detect, ContentDetector, AdaptiveDetector
    from scenedetect.video_splitter import split_video_ffmpeg # Not used in this file currently
    SCENEDETECT_AVAILABLE = True
    print("INFO: PySceneDetect imported successfully. Full scene detection capabilities enabled.")
except ImportError:
    SCENEDETECT_AVAILABLE = False
    # Define placeholders for type hinting or if accessed directly elsewhere (though current usage is guarded)
    detect, ContentDetector, AdaptiveDetector, split_video_ffmpeg = None, None, None, None
    print("WARNING: PySceneDetect not found. Scene detection will use a fallback mechanism (single scene).")

try:
    from .config import SecurityConfig
except ImportError:
    from config import SecurityConfig


async def _generate_screenshot_for_scene(
    video_path: Path, 
    start_time: float, 
    scene_id: int, 
    screenshot_output_dir: Path,
    ffmpeg_path: str, 
    process_timeout: int, 
    screenshots_base_url: str,
    source_ref: str
) -> Optional[str]:
    """Generate screenshot from scene start using FFMPEG"""
    try:
        # Create filename for screenshot
        screenshot_filename = f"scene_{scene_id:03d}_{start_time:.2f}s.jpg"
        screenshot_path = screenshot_output_dir / screenshot_filename
        
        # FFMPEG command to extract frame at specific time
        cmd = [
            ffmpeg_path,
            "-i", str(video_path),
            "-ss", str(start_time),  # Seek to start time
            "-vframes", "1",         # Extract only 1 frame
            "-q:v", "2",            # High quality
            "-y",                   # Overwrite existing
            str(screenshot_path)
        ]
        
        # Execute FFMPEG command
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=process_timeout
        )
        
        if process.returncode == 0 and screenshot_path.exists():
            # Generate URL for screenshot
            screenshot_url = f"{screenshots_base_url}/{source_ref}/{screenshot_filename}"
            print(f"    Generated screenshot: {screenshot_url}")
            return screenshot_url
        else:
            print(f"    Failed to generate screenshot for scene {scene_id}: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"    Error generating screenshot for scene {scene_id}: {e}")
        return None


class VideoContentAnalyzer:
    """Analyzes video content to provide scene boundaries and visual insights"""
    
    def __init__(self):
        self.metadata_dir = Path("/tmp/music/metadata")
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize screenshots directory
        self.screenshots_dir = SecurityConfig.SCREENSHOTS_DIR
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize OpenCV object detectors
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
    def _get_metadata_path(self, file_id: str) -> Path:
        """Get metadata file path for a video file"""
        return self.metadata_dir / f"{file_id}_analysis.json"
        
    async def analyze_video_content(self, file_path: Path, file_id: str, force_reanalysis: bool = False) -> Dict[str, Any]:
        """
        Comprehensive video content analysis combining scene detection and object recognition
        
        Returns:
        {
            "success": bool,
            "analysis": {
                "file_info": {...},
                "scenes": [{"start": float, "end": float, "duration": float, "objects": [...]}],
                "summary": {...},
                "keyframes": [...]
            }
        }
        """
        metadata_path = self._get_metadata_path(file_id)
        
        # Check if analysis already exists and is recent
        if not force_reanalysis and metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    cached_analysis = json.load(f)
                    
                # Verify the analysis is for the same file (basic check)
                if cached_analysis.get('file_info', {}).get('name') == file_path.name:
                    print(f"Using cached analysis for {file_path.name}")
                    return {"success": True, "analysis": cached_analysis}
            except Exception:
                pass  # If cache is corrupted, proceed with fresh analysis
        
        print(f"Analyzing video content: {file_path.name}")
        
        try:
            # Step 1: Scene Detection
            scenes_data = await self._detect_scenes(file_path)
            
            # Step 2: Extract keyframes and analyze objects
            enhanced_scenes = await self._analyze_scene_content(file_path, scenes_data)
            
            # Step 3: Generate summary
            summary = self._generate_content_summary(enhanced_scenes, file_path)
            
            # Step 4: Compile complete analysis
            analysis = {
                "timestamp": asyncio.get_event_loop().time(),
                "file_info": {
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": file_path.stat().st_size
                },
                "scenes": enhanced_scenes,
                "summary": summary,
                "total_scenes": len(enhanced_scenes),
                "total_duration": enhanced_scenes[-1]["end"] if enhanced_scenes else 0
            }
            
            # Step 5: Cache the analysis
            await self._save_analysis(file_id, analysis)
            
            return {"success": True, "analysis": analysis}
            
        except Exception as e:
            error_msg = f"Content analysis failed for {file_path.name}: {str(e)}"
            print(error_msg)
            return {"success": False, "error": error_msg}
    
    async def _detect_scenes(self, video_path: Path) -> List[Tuple[float, float]]:
        """Detect scene boundaries using PySceneDetect"""
        print(f"  Detecting scenes in {video_path.name}...")

        if not SCENEDETECT_AVAILABLE:
            print("  PySceneDetect not available. Using fallback: single scene for the video.")
            # Fallback: create a single scene for the entire video.
            # The existing fallback assumes 60s; a future improvement could be to get actual video duration.
            return [(0.0, 60.0)] 
        
        try:
            # Use ContentDetector for general scene changes
            # Ensure scenedetect components are available (they should be if SCENEDETECT_AVAILABLE is True)
            if not detect or not ContentDetector:
                # This case should ideally not be reached if SCENEDETECT_AVAILABLE is True
                # and imports were successful.
                raise ImportError("PySceneDetect components (detect or ContentDetector) are not available even though SCENEDETECT_AVAILABLE is True.")
            
            scene_list = detect(str(video_path), ContentDetector(threshold=30.0))
            
            # Convert to list of (start, end) tuples in seconds
            scenes = []
            for i, scene in enumerate(scene_list):
                start_time = scene[0].get_seconds()
                end_time = scene[1].get_seconds()
                scenes.append((start_time, end_time))
                
            print(f"  Found {len(scenes)} scenes")
            return scenes
            
        except Exception as e:
            print(f"  Scene detection using PySceneDetect failed: {e}")
            # Fallback: create a single scene for the entire video
            return [(0.0, 60.0)]  # Assume max 60 seconds if we can't detect properly
    
    async def _analyze_scene_content(self, video_path: Path, scenes_data: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
        """Extract keyframes from scenes and analyze visual content"""
        print(f"  Analyzing content of {len(scenes_data)} scenes...")
        
        enhanced_scenes = []
        
        # Create sourceRef directory for screenshots
        source_ref = video_path.stem  # filename without extension
        screenshots_source_dir = self.screenshots_dir / source_ref
        screenshots_source_dir.mkdir(parents=True, exist_ok=True)
        
        # Open video for frame extraction
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        try:
            for i, (start_time, end_time) in enumerate(scenes_data):
                duration = end_time - start_time
                mid_time = start_time + (duration / 2)
                
                # Extract keyframe from middle of scene
                frame_number = int(mid_time * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()
                
                scene_data = {
                    "scene_id": i,
                    "start": start_time,
                    "end": end_time,
                    "duration": duration,
                    "mid_time": mid_time,
                    "objects": [],
                    "characteristics": [],
                    "screenshot_url": None
                }
                
                if ret and frame is not None:
                    # Analyze frame content
                    objects = self._detect_objects_in_frame(frame)
                    characteristics = self._analyze_frame_characteristics(frame)
                    
                    scene_data["objects"] = objects
                    scene_data["characteristics"] = characteristics
                    
                    # Generate screenshot from scene start
                    screenshot_url = await _generate_screenshot_for_scene(
                        video_path,
                        start_time,
                        i,  # scene_id
                        screenshots_source_dir, # Full path to dir for this source's screenshots
                        SecurityConfig.FFMPEG_PATH,
                        SecurityConfig.PROCESS_TIMEOUT,
                        SecurityConfig.SCREENSHOTS_BASE_URL,
                        source_ref # source_ref for URL construction
                    )
                    scene_data["screenshot_url"] = screenshot_url
                else:
                    print(f"    Warning: Could not extract keyframe for scene {i}")
                
                enhanced_scenes.append(scene_data)
                
        finally:
            cap.release()
            
        return enhanced_scenes
    
    def _detect_objects_in_frame(self, frame: np.ndarray) -> List[str]:
        """Detect objects in a video frame using OpenCV"""
        objects = []
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) > 0:
            objects.append(f"faces ({len(faces)})")
            
        # Detect eyes (indicates close-up shots)
        eyes = self.eye_cascade.detectMultiScale(gray, 1.1, 4)
        if len(eyes) > 0:
            objects.append(f"eyes ({len(eyes)})")
            
        return objects
    
    def _analyze_frame_characteristics(self, frame: np.ndarray) -> List[str]:
        """Analyze general characteristics of a frame"""
        characteristics = []
        
        # Analyze brightness
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        
        if brightness < 50:
            characteristics.append("dark")
        elif brightness > 200:
            characteristics.append("bright")
        else:
            characteristics.append("normal_lighting")
            
        # Analyze color dominance
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Check for dominant colors
        hist_hue = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        dominant_hue = np.argmax(hist_hue)
        
        if dominant_hue < 10 or dominant_hue > 170:
            characteristics.append("red_tones")
        elif 10 <= dominant_hue < 30:
            characteristics.append("orange_tones")
        elif 30 <= dominant_hue < 60:
            characteristics.append("green_tones")
        elif 100 <= dominant_hue < 130:
            characteristics.append("blue_tones")
            
        # Analyze motion/complexity (edge detection)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        if edge_density > 0.1:
            characteristics.append("high_detail")
        elif edge_density < 0.03:
            characteristics.append("low_detail")
        else:
            characteristics.append("medium_detail")
            
        return characteristics
    
    def _generate_content_summary(self, scenes: List[Dict[str, Any]], file_path: Path) -> Dict[str, Any]:
        """Generate a summary of the video content analysis"""
        total_duration = sum(scene["duration"] for scene in scenes)
        
        # Count objects across all scenes
        all_objects = []
        all_characteristics = []
        
        for scene in scenes:
            all_objects.extend(scene["objects"])
            all_characteristics.extend(scene["characteristics"])
            
        # Find most common elements
        object_counts = {}
        char_counts = {}
        
        for obj in all_objects:
            object_counts[obj] = object_counts.get(obj, 0) + 1
            
        for char in all_characteristics:
            char_counts[char] = char_counts.get(char, 0) + 1
            
        # Generate editing suggestions
        suggestions = []
        
        # Scene-based suggestions
        if len(scenes) > 3:
            suggestions.append("Multiple scenes detected - good for dynamic montage creation")
        
        # Object-based suggestions  
        if any("faces" in obj for obj in all_objects):
            suggestions.append("Contains people - suitable for social/personal content")
            
        # Lighting-based suggestions
        dark_scenes = sum(1 for scene in scenes if "dark" in scene["characteristics"])
        if dark_scenes > len(scenes) / 2:
            suggestions.append("Many dark scenes - consider brightness adjustment")
            
        # Duration-based suggestions
        avg_scene_duration = total_duration / len(scenes) if scenes else 0
        if avg_scene_duration < 2:
            suggestions.append("Short scenes - good for fast-paced editing")
        elif avg_scene_duration > 10:
            suggestions.append("Long scenes - consider trimming for dynamic content")
            
        return {
            "total_duration": total_duration,
            "average_scene_duration": avg_scene_duration,
            "scene_count": len(scenes),
            "detected_objects": list(object_counts.keys()),
            "common_characteristics": list(char_counts.keys()),
            "editing_suggestions": suggestions,
            "best_scenes_for_highlights": self._identify_highlight_scenes(scenes)
        }
    
    def _identify_highlight_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify scenes that would make good highlights"""
        highlights = []
        
        for scene in scenes:
            score = 0
            reasons = []
            
            # Score based on objects detected
            if any("faces" in obj for obj in scene["objects"]):
                score += 2
                reasons.append("contains people")
                
            # Score based on visual characteristics
            if "high_detail" in scene["characteristics"]:
                score += 1
                reasons.append("visually interesting")
                
            if "bright" in scene["characteristics"]:
                score += 1
                reasons.append("good lighting")
                
            # Score based on duration (not too short, not too long)
            if 3 <= scene["duration"] <= 8:
                score += 1
                reasons.append("good duration")
                
            if score >= 2:  # Threshold for highlight
                highlights.append({
                    "scene_id": scene["scene_id"],
                    "start": scene["start"],
                    "end": scene["end"],
                    "duration": scene["duration"],
                    "score": score,
                    "reasons": reasons
                })
                
        # Sort by score, return top highlights
        highlights.sort(key=lambda x: x["score"], reverse=True)
        return highlights[:5]  # Return top 5 highlights
    
    async def _save_analysis(self, file_id: str, analysis: Dict[str, Any]):
        """Save analysis to metadata file"""
        metadata_path = self._get_metadata_path(file_id)
        
        try:
            with open(metadata_path, 'w') as f:
                json.dump(analysis, f, indent=2)
            print(f"  Saved analysis metadata to {metadata_path}")
        except Exception as e:
            print(f"  Warning: Could not save analysis metadata: {e}")
    
    async def get_cached_analysis(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis for a file"""
        metadata_path = self._get_metadata_path(file_id)
        
        if not metadata_path.exists():
            return None
            
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    
    def get_smart_trim_suggestions(self, analysis: Dict[str, Any], desired_duration: float = 10.0) -> List[Dict[str, Any]]:
        """Get intelligent trim suggestions based on content analysis"""
        if not analysis or "scenes" not in analysis:
            return []
            
        scenes = analysis["scenes"]
        suggestions = []
        
        # Strategy 1: Use highlight scenes
        highlights = analysis.get("summary", {}).get("best_scenes_for_highlights", [])
        
        if highlights:
            # Try to fit highlights within desired duration
            current_duration = 0
            selected_scenes = []
            
            for highlight in highlights:
                if current_duration + highlight["duration"] <= desired_duration:
                    selected_scenes.append({
                        "type": "highlight",
                        "start": highlight["start"],
                        "end": highlight["end"],
                        "duration": highlight["duration"],
                        "reasons": highlight["reasons"]
                    })
                    current_duration += highlight["duration"]
                else:
                    break
                    
            if selected_scenes:
                suggestions.append({
                    "strategy": "highlight_scenes",
                    "total_duration": current_duration,
                    "segments": selected_scenes,
                    "description": "Best highlights from the video"
                })
        
        # Strategy 2: Even sampling across video
        total_duration = analysis.get("summary", {}).get("total_duration", 0)
        if total_duration > desired_duration:
            num_segments = min(3, len(scenes))
            segment_duration = desired_duration / num_segments
            
            even_segments = []
            for i in range(num_segments):
                scene_index = int(i * len(scenes) / num_segments)
                scene = scenes[scene_index]
                
                # Take segment from middle of scene
                scene_mid = scene["start"] + (scene["duration"] / 2)
                seg_start = max(scene["start"], scene_mid - segment_duration / 2)
                seg_end = min(scene["end"], seg_start + segment_duration)
                
                even_segments.append({
                    "type": "sampled",
                    "start": seg_start,
                    "end": seg_end,
                    "duration": seg_end - seg_start,
                    "scene_id": scene["scene_id"]
                })
                
            suggestions.append({
                "strategy": "even_sampling",
                "total_duration": sum(seg["duration"] for seg in even_segments),
                "segments": even_segments,
                "description": "Even sampling across the video timeline"
            })
        
        return suggestions
    
    async def get_scene_screenshots(self, file_id: str) -> Dict[str, Any]:
        """Get all scene screenshots for a video file"""
        analysis = await self.get_cached_analysis(file_id)
        
        if not analysis or "scenes" not in analysis:
            return {"success": False, "error": "No analysis found for this file"}
            
        screenshots = []
        for scene in analysis["scenes"]:
            if scene.get("screenshot_url"):
                screenshots.append({
                    "scene_id": scene["scene_id"],
                    "start": scene["start"],
                    "end": scene["end"],
                    "duration": scene["duration"],
                    "screenshot_url": scene["screenshot_url"],
                    "objects": scene.get("objects", []),
                    "characteristics": scene.get("characteristics", [])
                })
        
        return {
            "success": True,
            "file_info": analysis.get("file_info", {}),
            "total_scenes": len(screenshots),
            "screenshots": screenshots
        }
