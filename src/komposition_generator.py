"""
Komposition Generator from Text Descriptions
============================================

Creates komposition.json files from natural language descriptions:
- Parses user intent for video composition requirements
- Determines segment structure and timing
- Assigns source files and effects
- Generates beat-synchronized compositions
- Handles various BPM and format requirements

Key Features:
- Natural language processing for video composition
- Intelligent source file matching
- Beat timing calculation and validation
- Effects chain suggestion
- Multi-format support (aspect ratios, resolutions)
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import difflib

try:
    from .file_manager import FileManager
    from .config import SecurityConfig
    from .content_analyzer import VideoContentAnalyzer
except ImportError:
    from file_manager import FileManager
    from config import SecurityConfig
    from content_analyzer import VideoContentAnalyzer


@dataclass
class CompositionIntent:
    """Parsed user intent for composition"""
    title: str
    description: str
    
    # Timing requirements
    bpm: int = 120
    total_beats: int = 64
    beats_per_measure: int = 16
    
    # Output requirements
    resolution: Tuple[int, int] = (1920, 1080)
    aspect_ratio: str = "16:9"
    
    # Content requirements
    video_sources: List[str] = None
    audio_sources: List[str] = None
    segment_descriptions: List[str] = None
    effects_requests: List[str] = None
    
    # Musical structure
    musical_structure: List[str] = None
    detected_structure_type: str = "simple_video"
    
    # Render specifications
    render_start_beat: Optional[int] = None
    render_end_beat: Optional[int] = None
    
    # Scene-based generation
    use_varied_scenes: bool = False
    beats_per_snippet: int = 16 # Default, can be overridden by parser
    
    def __post_init__(self):
        if self.video_sources is None:
            self.video_sources = []
        if self.audio_sources is None:
            self.audio_sources = []
        if self.segment_descriptions is None:
            self.segment_descriptions = []
        if self.effects_requests is None:
            self.effects_requests = []
        if self.musical_structure is None:
            self.musical_structure = []


class KompositionGenerator:
    """Generate komposition.json from text descriptions"""
    
    def __init__(self):
        self.file_manager = FileManager()
        self.content_analyzer = VideoContentAnalyzer()
        self.komposition_cache_dir = Path("/tmp/music/metadata/generated_kompositions")
        self.komposition_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Enhanced video file patterns for matching
        self.video_patterns = {
            "intro": ["intro", "introduction", "opening", "start", "beginning", "pxl"],
            "speech": ["speech", "talk", "voice", "speaking", "lookin", "dialogue", "narrator"],
            "action": ["action", "movement", "panning", "motion", "dynamic", "activity"],
            "outro": ["outro", "ending", "close", "final", "conclusion"],
            "verse": ["verse", "main", "content", "primary"],
            "refrain": ["refrain", "chorus", "hook", "repeat", "main theme"],
            "bridge": ["bridge", "transition", "middle", "interlude"],
            "music": ["music", "audio", "song", "track", "instrumental"]
        }
        
        # Enhanced effects patterns with style recognition
        self.effects_patterns = {
            "transition": ["transition", "fade", "crossfade", "wipe", "smooth", "blend"],
            "speed": ["slow", "fast", "time", "stretch", "tempo"],
            "visual": ["filter", "color", "brightness", "contrast", "leica", "cinematic", "film"],
            "audio": ["volume", "normalize", "mix", "background"],
            "style": ["leica-like", "vintage", "retro", "modern", "cinematic", "documentary"]
        }
        
        # Musical structure patterns for enhanced recognition
        self.musical_structures = {
            "standard_song": ["intro", "verse", "refrain", "outro"],
            "extended_song": ["intro", "verse", "refrain", "verse", "refrain", "bridge", "refrain", "outro"],
            "simple_video": ["intro", "main", "outro"],
            "documentary": ["opening", "content", "conclusion"],
            "music_video": ["intro", "verse", "chorus", "verse", "chorus", "outro"]
        }
        
        # Aesthetic style mappings to technical parameters
        self.style_mappings = {
            "leica-like": {
                "color_grade": {"style": "film_emulation", "warmth": 1.2, "contrast": 1.1},
                "film_grain": {"intensity": 0.3, "type": "35mm"},
                "vignette": {"strength": 0.2}
            },
            "cinematic": {
                "color_grade": {"style": "cinema", "saturation": 1.1, "shadows": 0.9},
                "letterbox": {"aspect": "2.35:1"},
                "motion_blur": {"intensity": 0.1}
            },
            "vintage": {
                "color_grade": {"style": "vintage", "sepia": 0.3, "fade": 0.2},
                "film_grain": {"intensity": 0.5, "type": "16mm"},
                "vignette": {"strength": 0.4}
            }
        }
    
    async def generate_from_description(
        self, 
        description: str,
        title: str = "Generated Composition",
        available_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate komposition from natural language description
        
        Args:
            description: Natural language description of desired composition
            title: Title for the composition
            available_sources: List of available source files
            
        Returns:
            Generated komposition.json structure
        """
        print(f"🤖 GENERATING KOMPOSITION FROM DESCRIPTION")
        print(f"   📝 Description: {description}")
        
        try:
            # Step 1: Parse user intent
            intent = await self._parse_intent(description, title, available_sources)
            
            # Step 2: Match source files
            match_result = await self._match_source_files(intent)
            
            # Check if file matching failed
            if not match_result.get("success", True):
                return match_result  # Return error with suggestions
            
            matched_sources = match_result.get("matched_sources", match_result)
            
            # Step 3: Generate segment structure
            segments = await self._generate_segments(intent, matched_sources)
            
            # Step 4: Generate effects tree
            effects_tree = await self._generate_effects_tree(intent)
            
            # Step 5: Create komposition structure
            komposition = await self._create_komposition(intent, segments, effects_tree)
            
            # Step 6: Save komposition
            komposition_file = await self._save_komposition(komposition, title)
            
            print(f"\n🎉 KOMPOSITION GENERATED!")
            print(f"   📊 {len(segments)} segments")
            print(f"   ✨ {len(effects_tree)} effects")
            print(f"   🎵 {intent.bpm} BPM, {intent.total_beats} beats")
            print(f"   📐 {intent.resolution[0]}x{intent.resolution[1]}")
            
            return {
                "success": True,
                "komposition": komposition,
                "komposition_file": str(komposition_file),
                "intent": asdict(intent),
                "summary": {
                    "segments": len(segments),
                    "effects": len(effects_tree),
                    "duration": intent.total_beats * 60 / intent.bpm,
                    "resolution": intent.resolution
                }
            }
            
        except Exception as e:
            print(f"❌ Komposition generation failed: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    async def _parse_intent(
        self, 
        description: str, 
        title: str,
        available_sources: Optional[List[str]]
    ) -> CompositionIntent:
        """Parse natural language description into structured intent"""
        
        intent = CompositionIntent(title=title, description=description)
        
        # Parse BPM
        bpm_match = re.search(r'(\d+)\s*bpm', description.lower())
        if bpm_match:
            intent.bpm = int(bpm_match.group(1))
        
        # Parse beat range
        beat_range_match = re.search(r'beat\s*(\d+)[-\s]*(\d+)', description.lower())
        if beat_range_match:
            intent.render_start_beat = int(beat_range_match.group(1))
            intent.render_end_beat = int(beat_range_match.group(2))
        
        # Parse resolution/format
        resolution_patterns = {
            r'(\d+)\s*[x×]\s*(\d+)': lambda m: (int(m.group(1)), int(m.group(2))),
            r'600\s*[x×]\s*800': lambda m: (600, 800),
            r'portrait': lambda m: (1080, 1920),
            r'landscape': lambda m: (1920, 1080),
            r'square': lambda m: (1080, 1080),
            r'vertical': lambda m: (1080, 1920)
        }
        
        for pattern, handler in resolution_patterns.items():
            match = re.search(pattern, description.lower())
            if match:
                intent.resolution = handler(match)
                break
        
        # Extract mentioned video sources with intelligent matching
        if available_sources:
            intent.video_sources = self._extract_mentioned_files(description, available_sources)
        
        # Enhanced musical structure recognition
        intent.musical_structure = self._detect_musical_structure(description)
        
        # Parse segment descriptions with musical awareness
        segment_keywords = ["intro", "introduction", "opening", "start", "verse", "refrain", "chorus", 
                           "bridge", "speech", "talk", "action", "outro", "ending", "conclusion"]
        for keyword in segment_keywords:
            if keyword in description.lower():
                intent.segment_descriptions.append(f"Segment with {keyword}")
        
        # Enhanced effects parsing with style recognition
        effects_keywords = ["fade", "transition", "crossfade", "slow", "fast", "filter", "crop", 
                           "smooth", "leica", "cinematic", "vintage", "beat", "8 beat"]
        for keyword in effects_keywords:
            if keyword in description.lower():
                intent.effects_requests.append(keyword)
        
        # Parse beat-specific transition timing
        beat_transition_match = re.search(r'(\d+)\s*beat\s*transition', description.lower())
        if beat_transition_match:
            beat_duration = int(beat_transition_match.group(1))
            intent.effects_requests.append(f"beat_transition_{beat_duration}")
        
        # Parse aesthetic style requests
        for style in self.style_mappings.keys():
            if style in description.lower():
                intent.effects_requests.append(f"style_{style}")
                break

        # Parse varied scenes request
        if "varied scenes" in description.lower() or "scene snippets" in description.lower():
            intent.use_varied_scenes = True
        
        # Parse beats per snippet
        beats_snippet_match = re.search(r'(\d+)\s*beat\s*snippet', description.lower())
        if beats_snippet_match:
            intent.beats_per_snippet = int(beats_snippet_match.group(1))
            if not intent.use_varied_scenes: # If "8 beat snippet" is mentioned, imply varied scenes
                intent.use_varied_scenes = True
        
        print(f"   🎯 Parsed intent: {intent.bpm} BPM, {intent.resolution}, {len(intent.video_sources)} sources, Varied Scenes: {intent.use_varied_scenes}, Beats/Snippet: {intent.beats_per_snippet}")
        return intent
    
    def _detect_musical_structure(self, description: str) -> List[str]:
        """Detect musical structure from description text"""
        desc_lower = description.lower()
        
        # Check for explicit structure mentions
        if "intro" in desc_lower and "verse" in desc_lower and "refrain" in desc_lower:
            return ["intro", "verse", "refrain", "outro"]
        elif "intro" in desc_lower and "verse" in desc_lower and "chorus" in desc_lower:
            return ["intro", "verse", "chorus", "outro"]
        elif "opening" in desc_lower and "content" in desc_lower:
            return ["opening", "content", "conclusion"]
        elif "introduction" in desc_lower and "main" in desc_lower:
            return ["introduction", "main", "ending"]
        
        # Check for music video patterns
        if any(word in desc_lower for word in ["music video", "song", "track", "bpm"]):
            if any(word in desc_lower for word in ["verse", "refrain", "chorus"]):
                return ["intro", "verse", "refrain", "outro"]
            else:
                return ["intro", "main", "outro"]
        
        # Default simple structure
        return ["intro", "main", "outro"]
    
    async def _match_source_files(self, intent: CompositionIntent) -> Dict[str, Any]:
        """Match intent requirements to available source files with validation"""
        matched_sources = {}
        failed_matches = []
        
        # Get all available files (security: only from allowed directory)
        all_files = self.get_available_sources()
        video_files = [f for f in all_files if f.split('.')[-1].lower() in ['mp4', 'avi', 'mov', 'mkv']]
        
        # If specific sources mentioned, validate them and map to musical roles
        if intent.video_sources:
            # Create role-based mapping when specific files are mentioned
            musical_roles = intent.musical_structure if intent.musical_structure else ["intro", "main", "outro"]
            
            for i, mentioned_source in enumerate(intent.video_sources):
                # Try exact match first
                exact_match = next((f for f in video_files if f.lower() == mentioned_source.lower()), None)
                if exact_match:
                    role = musical_roles[i] if i < len(musical_roles) else f"segment_{i+1}"
                    matched_sources[role] = exact_match
                    print(f"   ✅ Matched '{mentioned_source}' → '{exact_match}' (role: {role})")
                    continue
                
                # Try partial match (without extension)
                base_name = mentioned_source.split('.')[0].lower()
                partial_match = next((f for f in video_files if base_name in f.lower().split('.')[0]), None)
                if partial_match:
                    role = musical_roles[i] if i < len(musical_roles) else f"segment_{i+1}"
                    matched_sources[role] = partial_match
                    print(f"   🔍 Partial matched '{mentioned_source}' → '{partial_match}' (role: {role})")
                    continue
                
                # Try fuzzy match
                suggestions = self._suggest_similar_files(mentioned_source, video_files)
                if suggestions:
                    role = musical_roles[i] if i < len(musical_roles) else f"segment_{i+1}"
                    matched_sources[role] = suggestions[0]  # Use best suggestion
                    print(f"   🔍 Fuzzy matched '{mentioned_source}' → '{suggestions[0]}' (role: {role})")
                    continue
                
                # File not found - collect for error reporting
                failed_matches.append(mentioned_source)
        
        # Auto-match based on patterns if no specific sources matched
        if not matched_sources and video_files:
            print(f"   🔄 Auto-matching with patterns (no specific files found)")
            for category, patterns in self.video_patterns.items():
                for pattern in patterns:
                    for available_file in video_files:
                        if pattern in available_file.lower() and category not in matched_sources:
                            matched_sources[category] = available_file
                            print(f"      Pattern '{pattern}' matched '{available_file}' for category '{category}'")
                            break
        elif matched_sources:
            print(f"   ✅ Using matched specific sources: {list(matched_sources.keys())}")
        
        # Fallback: use first available files
        if not matched_sources and video_files:
            for i, file in enumerate(video_files[:3]):  # Use first 3 files
                matched_sources[f"segment_{i+1}"] = file
        
        # Return error if specific files couldn't be matched
        if failed_matches:
            error_info = {
                "success": False,
                "error": f"Could not find requested video files: {', '.join(failed_matches)}",
                "failed_files": failed_matches,
                "available_videos": video_files[:5],  # Limit for security
                "suggestions": {}
            }
            
            # Add suggestions for each failed file
            for failed_file in failed_matches:
                suggestions = self._suggest_similar_files(failed_file, video_files)
                if suggestions:
                    error_info["suggestions"][failed_file] = suggestions[:3]
            
            return error_info
        
        print(f"   📂 Matched sources: {len(matched_sources)} files")
        for category, filename in matched_sources.items():
            print(f"      {category}: {filename}")
        
        return {"success": True, "matched_sources": matched_sources}
    
    async def _generate_segments(
        self, 
        intent: CompositionIntent, 
        matched_sources: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Generate segments based on musical structure and matched sources"""
        segments = []
        current_beat = intent.render_start_beat or 0
        segment_id_counter = 0

        if intent.use_varied_scenes:
            print(f"   🎞️ Generating segments using varied scenes ({intent.beats_per_snippet} beats per snippet)")
            
            all_analyzed_scenes = []
            for source_category, source_filename in matched_sources.items():
                file_id = self.file_manager.get_id_by_name(source_filename)
                if not file_id:
                    print(f"      ⚠️ Could not get file ID for: {source_filename} (category: {source_category})")
                    continue
                
                file_path = self.file_manager.resolve_id(file_id)
                if not file_path:
                    print(f"      ⚠️ Could not resolve path for file ID: {file_id}")
                    continue

                print(f"      Analyzing scenes for {source_filename}...")
                # Ensure file_id is passed to analyze_video_content for caching key consistency
                analysis_result = await self.content_analyzer.analyze_video_content(file_path, file_id)
                
                if analysis_result.get("success"):
                    source_scenes = analysis_result.get("analysis", {}).get("scenes", [])
                    for sc in source_scenes:
                        sc["source_filename"] = source_filename # Augment scene with its original file
                        sc["file_id"] = file_id
                    all_analyzed_scenes.extend(source_scenes)
                    print(f"         Found {len(source_scenes)} scenes in {source_filename}")
                else:
                    print(f"      ⚠️ Scene analysis failed for {source_filename}: {analysis_result.get('error')}")

            if not all_analyzed_scenes:
                print(f"   ⚠️ No scenes found after analysis. Cannot generate scene-based snippets.")
                # Potentially fall back to default segment generation or return error
                # For now, let's fall through to default if no scenes.
                pass # This will lead to empty segments list if no fallback implemented below.

            num_required_snippets = intent.total_beats // intent.beats_per_snippet
            snippet_duration_seconds = (intent.beats_per_snippet * 60.0) / intent.bpm
            
            print(f"      🎬 Required snippets: {num_required_snippets}, each {snippet_duration_seconds:.2f}s long.")

            scene_idx = 0
            for i in range(num_required_snippets):
                if not all_analyzed_scenes: # No scenes to pick from
                    print(f"      ⚠️ Ran out of scenes for snippet {i+1}. Stopping segment generation.")
                    break

                scene = all_analyzed_scenes[scene_idx % len(all_analyzed_scenes)] # Cycle through scenes
                scene_idx += 1

                actual_scene_duration = scene['duration']
                source_snippet_duration = min(snippet_duration_seconds, actual_scene_duration)

                segment = {
                    "id": f"segment_snippet_{segment_id_counter}",
                    "sourceRef": scene["source_filename"],
                    "startBeat": current_beat,
                    "endBeat": current_beat + intent.beats_per_snippet,
                    "duration": intent.beats_per_snippet, # Duration in beats for the timeline
                    "operation": "time_stretch", # Ensures snippet fits the beat duration
                    "source_timing": { # Specifies which part of the source video to use
                        "original_start": scene['start'], # Start time of the scene in its source video
                        "original_duration": source_snippet_duration 
                    },
                    "params": {}, # Specific FFMPEG params for the operation, if any
                    "description": f"Snippet {i+1} from {scene['source_filename']} (Scene ID: {scene['scene_id']})",
                    "musical_role": "snippet"
                }
                segments.append(segment)
                print(f"      🎞️ Snippet {i+1}: {scene['source_filename']} (Scene {scene['scene_id']}, {scene['start']:.2f}s, {source_snippet_duration:.2f}s) -> beat {current_beat}-{current_beat + intent.beats_per_snippet}")
                current_beat += intent.beats_per_snippet
                segment_id_counter +=1
            
            if not segments and not all_analyzed_scenes : # Fallback if scene analysis yielded nothing
                 print(f"   ⚠️ No scenes available for scene-based generation. Falling back to musical structure.")
                 intent.use_varied_scenes = False # Force fallback

        # Fallback or default musical structure based generation
        if not intent.use_varied_scenes or not segments: # if varied_scenes was false OR it was true but no segments were made
            print(f"   🎵 Generating segments based on musical structure.")
            structure = intent.musical_structure if intent.musical_structure else ["intro", "main", "outro"]
            total_structure_beats = intent.render_end_beat - (intent.render_start_beat or 0) if intent.render_end_beat else intent.total_beats
            
            if not structure: # Ensure structure is not empty
                 print(f"   ⚠️ Musical structure is empty. Defaulting to simple structure.")
                 structure = ["main"]

            beats_per_structure_segment = total_structure_beats // len(structure) if len(structure) > 0 else total_structure_beats
            if beats_per_structure_segment == 0 and total_structure_beats > 0 : beats_per_structure_segment = total_structure_beats # Avoid 0 if possible

            current_beat = intent.render_start_beat or 0 # Reset current_beat for this block
            
            print(f"      🎵 Musical structure: {' → '.join(structure)}")
            print(f"      🎯 Beats per segment: {beats_per_structure_segment}")

            for structure_part in structure:
                if current_beat >= (intent.render_end_beat or intent.total_beats): break

                end_beat = current_beat + beats_per_structure_segment
                
                source_file_for_part = self._match_source_to_structure(structure_part, matched_sources)
                
                if source_file_for_part:
                    file_id = self.file_manager.get_id_by_name(source_file_for_part)
                    if not file_id:
                        print(f"      ⚠️ Could not get file ID for: {source_file_for_part}")
                        current_beat = end_beat
                        continue
                    
                    segment_duration_beats = end_beat - current_beat
                    segment_duration_seconds = (segment_duration_beats * 60.0) / intent.bpm

                    segment = {
                        "id": f"segment_structure_{segment_id_counter}",
                        "sourceRef": source_file_for_part,
                        "startBeat": current_beat,
                        "endBeat": end_beat,
                        "duration": segment_duration_beats,
                        "operation": self._determine_operation_enhanced(structure_part, intent),
                        # For structured segments, source_timing might take the whole file or a default chunk
                        # KompositionProcessor's extract_and_stretch_video defaults original_duration to target_duration
                        # if source_timing or original_duration is not provided.
                        "source_timing": { 
                            "original_start": 0, # Default: start of the source file
                            # "original_duration": segment_duration_seconds # Extract a chunk matching the target
                        },
                        "params": self._determine_params_enhanced(structure_part, intent, current_beat, end_beat),
                        "description": f"{structure_part.title()} segment using {source_file_for_part}",
                        "musical_role": structure_part
                    }
                    segments.append(segment)
                    segment_id_counter +=1
                    print(f"      🎬 {structure_part.title()}: {source_file_for_part} (beat {current_beat}-{end_beat})")
                else:
                    print(f"      ⚠️ No source found for {structure_part}, skipping")
                
                current_beat = end_beat
        
        return segments
    
    def _match_source_to_structure(self, structure_part: str, matched_sources: Dict[str, str]) -> Optional[str]:
        """Match a musical structure part to the best available source"""
        # Direct mapping priorities for structure parts
        structure_mappings = {
            "intro": ["intro", "opening", "start", "pxl"],
            "verse": ["speech", "talk", "lookin", "main"],
            "refrain": ["action", "motion", "panning", "dynamic"],
            "chorus": ["action", "motion", "panning", "dynamic"],
            "bridge": ["secondary", "transition", "alternative"],
            "outro": ["outro", "ending", "final"],
            "main": ["speech", "action", "primary"],
            "opening": ["intro", "start", "opening"],
            "content": ["speech", "main", "primary"],
            "conclusion": ["outro", "ending", "final"]
        }
        
        # Try to find best match for this structure part
        preferences = structure_mappings.get(structure_part, [structure_part])
        
        for preference in preferences:
            for category, source_file in matched_sources.items():
                if preference in category.lower():
                    return source_file
        
        # Fallback: return any available source
        if matched_sources:
            return list(matched_sources.values())[0]
        
        return None
    
    def _determine_operation_enhanced(self, structure_part: str, intent: CompositionIntent) -> str:
        """Enhanced operation determination based on musical structure"""
        # Speech-heavy parts should preserve quality
        if structure_part in ["verse", "content", "main"] and any("speech" in req.lower() for req in intent.effects_requests):
            return "smart_cut"
        
        # Action parts can use time stretching for better synchronization
        elif structure_part in ["refrain", "chorus", "action"]:
            return "time_stretch"
        
        # Intro/outro can be trimmed precisely
        elif structure_part in ["intro", "outro", "opening", "conclusion"]:
            return "trim"
        
        # Default to smart operation selection
        return "smart_cut"
    
    def _determine_params_enhanced(self, structure_part: str, intent: CompositionIntent, start_beat: int, end_beat: int) -> Dict[str, Any]:
        """Enhanced parameter determination with musical structure awareness"""
        duration = (end_beat - start_beat) * 60.0 / intent.bpm
        
        params = {
            "start": 0,
            "duration": duration
        }
        
        # Add structure-specific parameters
        if structure_part in ["intro", "opening"]:
            params["fade_in"] = True
        elif structure_part in ["outro", "conclusion", "ending"]:
            params["fade_out"] = True
        
        # Add resolution if specified
        if intent.resolution != (1920, 1080):
            params["width"] = intent.resolution[0]
            params["height"] = intent.resolution[1]
        
        return params
    
    def _determine_operation(self, category: str, intent: CompositionIntent) -> str:
        """Determine operation type based on segment category"""
        if "speech" in category or "talk" in category:
            return "smart_cut"  # Preserve speech quality
        elif "action" in category or "motion" in category:
            return "time_stretch"  # May need timing adjustment
        else:
            return "trim"  # Simple extraction
    
    def _determine_params(
        self, 
        category: str, 
        intent: CompositionIntent, 
        start_beat: int, 
        end_beat: int
    ) -> Dict[str, Any]:
        """Determine parameters based on segment requirements"""
        duration = (end_beat - start_beat) * 60 / intent.bpm
        
        params = {
            "start": 0,
            "duration": duration
        }
        
        # Add resolution adjustment if needed
        if intent.resolution != (1920, 1080):
            params["width"] = intent.resolution[0]
            params["height"] = intent.resolution[1]
        
        # Add effects requests
        if "crop" in intent.effects_requests:
            params["crop"] = "center"
        
        return params
    
    async def _generate_effects_tree(self, intent: CompositionIntent) -> List[Dict[str, Any]]:
        """Enhanced effects tree generation with style mapping and beat-aware transitions"""
        effects_tree = []
        
        # Add resolution adjustment if needed
        if intent.resolution != (1920, 1080):
            effects_tree.append({
                "effect": "resize",
                "params": {
                    "width": intent.resolution[0],
                    "height": intent.resolution[1],
                    "method": "scale_and_crop"
                }
            })
        
        # Enhanced transition handling with beat awareness
        beat_transition_duration = None
        for req in intent.effects_requests:
            if req.startswith("beat_transition_"):
                beat_count = int(req.split("_")[-1])
                beat_transition_duration = beat_count * 60.0 / intent.bpm
                break
        
        # Add transitions with proper timing
        if any(word in " ".join(intent.effects_requests) for word in ["fade", "transition", "smooth", "crossfade"]):
            transition_duration = beat_transition_duration or 0.5
            effects_tree.append({
                "effect": "crossfade_transition",
                "params": {
                    "duration": transition_duration,
                    "method": "crossfade",
                    "beat_aligned": beat_transition_duration is not None
                }
            })
        
        # Add aesthetic style effects
        for req in intent.effects_requests:
            if req.startswith("style_"):
                style_name = req.replace("style_", "")
                if style_name in self.style_mappings:
                    style_effects = self.style_mappings[style_name]
                    for effect_name, effect_params in style_effects.items():
                        effects_tree.append({
                            "effect": effect_name,
                            "params": effect_params.copy()
                        })
                    print(f"   ✨ Applied {style_name} aesthetic style")
        
        # Add visual filters if requested
        if any(word in " ".join(intent.effects_requests) for word in ["leica", "cinematic", "vintage"]):
            if not any(req.startswith("style_") for req in intent.effects_requests):
                # Fallback basic cinematic filter
                effects_tree.append({
                    "effect": "color_grade",
                    "params": {
                        "style": "cinematic",
                        "warmth": 1.1,
                        "contrast": 1.05
                    }
                })
        
        # Add speed effects if requested
        if "slow" in intent.effects_requests:
            effects_tree.append({
                "effect": "time_stretch",
                "params": {
                    "speed_factor": 0.8,
                    "preserve_pitch": True
                }
            })
        elif "fast" in intent.effects_requests:
            effects_tree.append({
                "effect": "time_stretch",
                "params": {
                    "speed_factor": 1.2,
                    "preserve_pitch": True
                }
            })
        
        # Add audio normalization (always last for proper audio levels)
        effects_tree.append({
            "effect": "audio_normalize",
            "params": {
                "target_level": -12
            }
        })
        
        print(f"   ✨ Generated {len(effects_tree)} effects")
        return effects_tree
    
    async def _create_komposition(
        self,
        intent: CompositionIntent,
        segments: List[Dict[str, Any]],
        effects_tree: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create complete komposition structure"""
        
        total_duration = intent.total_beats * 60 / intent.bpm
        
        komposition = {
            "metadata": {
                "title": intent.title,
                "description": intent.description,
                "bpm": intent.bpm,
                "beatsPerMeasure": intent.beats_per_measure,
                "totalBeats": intent.total_beats,
                "estimatedDuration": total_duration,
                "createdAt": datetime.now().isoformat(),
                "generatedFromDescription": True
            },
            "segments": segments,
            "effects_tree": effects_tree,
            "outputSettings": {
                "resolution": f"{intent.resolution[0]}x{intent.resolution[1]}",
                "aspectRatio": f"{intent.resolution[0]}:{intent.resolution[1]}",
                "fps": 30,
                "videoCodec": "libx264",
                "audioCodec": "aac"
            }
        }
        
        # Add render range if specified
        if intent.render_start_beat is not None and intent.render_end_beat is not None:
            komposition["renderRange"] = {
                "startBeat": intent.render_start_beat,
                "endBeat": intent.render_end_beat
            }
        
        return komposition
    
    async def _save_komposition(self, komposition: Dict[str, Any], title: str) -> Path:
        """Save generated komposition to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        filename = f"generated_{safe_title}_{timestamp}.json"
        
        komposition_file = self.komposition_cache_dir / filename
        
        with open(komposition_file, 'w') as f:
            json.dump(komposition, f, indent=2)
        
        print(f"   💾 Saved: {komposition_file}")
        return komposition_file
    
    def get_available_sources(self) -> List[str]:
        """Get list of available source files"""
        sources = []
        source_dir = Path("/tmp/music/source")
        
        if source_dir.exists():
            for file_path in source_dir.glob("*"):
                if file_path.is_file() and file_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.mp3', '.wav']:
                    sources.append(file_path.name)
        
        return sources
    
    def _extract_mentioned_files(self, description: str, available_sources: List[str]) -> List[str]:
        """Extract video files mentioned in description with intelligent matching"""
        mentioned_files = []
        desc_lower = description.lower()
        
        # Look for explicit filename patterns (like "lookin.mp4" or "panning.mp4")
        filename_pattern = r'\b(\w+(?:\s+\w+)*\.(?:mp4|avi|mov|mkv))\b'
        explicit_files = re.findall(filename_pattern, desc_lower, re.IGNORECASE)
        
        for explicit_file in explicit_files:
            # Try exact match
            exact_match = next((f for f in available_sources if f.lower() == explicit_file.lower()), None)
            if exact_match:
                mentioned_files.append(exact_match)
                continue
            
            # Try fuzzy match for the full filename
            suggestions = self._suggest_similar_files(explicit_file, available_sources)
            if suggestions:
                mentioned_files.append(suggestions[0])
        
        # Look for partial names mentioned (like "lookin" referring to "lookin.mp4")
        video_files = [f for f in available_sources if f.split('.')[-1].lower() in ['mp4', 'avi', 'mov', 'mkv']]
        tokens = re.findall(r'\b\w+\b', desc_lower)
        
        for token in tokens:
            if len(token) < 3:  # Skip very short tokens
                continue
                
            # Find all potential matches for this token
            exact_matches = []
            word_matches = []
            prefix_matches = []
            
            for video_file in video_files:
                base_name = video_file.split('.')[0].lower()
                # Normalize base_name by replacing separators with spaces
                normalized_base = base_name.replace('_', ' ').replace('-', ' ')
                
                # Check for exact match of token to base name
                if token == base_name:
                    exact_matches.append(video_file)
                    continue
                        
                # Check if token is a complete word in the normalized filename  
                words_in_base = normalized_base.split()
                if token in words_in_base:
                    word_matches.append(video_file)
                    continue
                        
                # Check if token matches start of base name and is substantial portion (70%+)
                if base_name.startswith(token) and len(token) >= len(base_name) * 0.7:
                    prefix_matches.append(video_file)
            
            # Add matches in priority order: exact > word > prefix
            # But prefer shorter filenames when multiple matches exist
            for match_list, match_type in [(exact_matches, "Exact"), (word_matches, "Word"), (prefix_matches, "Prefix")]:
                if match_list:
                    # Sort by filename length to prefer shorter, more specific matches
                    match_list.sort(key=lambda f: len(f.split('.')[0]))
                    best_match = match_list[0]
                    if best_match not in mentioned_files:
                        mentioned_files.append(best_match)
                        print(f"   🎯 {match_type} match '{token}' → '{best_match}'")
                        break  # Only take the first (best) match type for this token
        
        return mentioned_files
    
    def _suggest_similar_files(self, user_mentioned: str, available_sources: List[str]) -> List[str]:
        """Suggest similar filenames when exact match fails"""
        suggestions = []
        
        # Use difflib for fuzzy string matching
        close_matches = difflib.get_close_matches(
            user_mentioned.lower(), 
            [f.lower() for f in available_sources], 
            n=3, 
            cutoff=0.4
        )
        
        # Map back to original filenames
        for match in close_matches:
            for original in available_sources:
                if original.lower() == match:
                    suggestions.append(original)
                    break
        
        return suggestions
    
    def _create_file_not_found_error(self, user_mentioned: str, available_sources: List[str]) -> Dict[str, Any]:
        """Create helpful error message when files cannot be found"""
        suggestions = self._suggest_similar_files(user_mentioned, available_sources)
        
        # Filter to only video files for suggestions
        video_files = [f for f in available_sources if f.split('.')[-1].lower() in ['mp4', 'avi', 'mov', 'mkv']]
        
        return {
            "success": False,
            "error": f"Could not find file '{user_mentioned}' in available sources",
            "available_video_files": video_files[:5],  # Limit to 5 for security
            "suggestions": suggestions[:3] if suggestions else [],
            "help": "Try using exact filenames or check the available files list"
        }
