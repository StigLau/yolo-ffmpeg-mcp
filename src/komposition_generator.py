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

try:
    from .file_manager import FileManager
    from .config import SecurityConfig
except ImportError:
    from file_manager import FileManager
    from config import SecurityConfig


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
    
    # Render specifications
    render_start_beat: Optional[int] = None
    render_end_beat: Optional[int] = None
    
    def __post_init__(self):
        if self.video_sources is None:
            self.video_sources = []
        if self.audio_sources is None:
            self.audio_sources = []
        if self.segment_descriptions is None:
            self.segment_descriptions = []
        if self.effects_requests is None:
            self.effects_requests = []


class KompositionGenerator:
    """Generate komposition.json from text descriptions"""
    
    def __init__(self):
        self.file_manager = FileManager()
        self.komposition_cache_dir = Path("/tmp/music/metadata/generated_kompositions")
        self.komposition_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Common video file patterns for matching
        self.video_patterns = {
            "intro": ["intro", "opening", "start", "beginning"],
            "speech": ["speech", "talk", "voice", "speaking", "lookin"],
            "action": ["action", "movement", "panning", "motion"],
            "outro": ["outro", "ending", "close", "final"],
            "music": ["music", "audio", "song", "track"]
        }
        
        # Common effects patterns
        self.effects_patterns = {
            "transition": ["transition", "fade", "crossfade", "wipe"],
            "speed": ["slow", "fast", "time", "stretch"],
            "visual": ["filter", "color", "brightness", "contrast"],
            "audio": ["volume", "normalize", "mix"]
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
            matched_sources = await self._match_source_files(intent)
            
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
        
        # Extract mentioned video sources
        if available_sources:
            for source in available_sources:
                if source.lower() in description.lower() or any(part in description.lower() for part in source.lower().split('.')):
                    intent.video_sources.append(source)
        
        # Parse segment descriptions
        segment_keywords = ["intro", "opening", "start", "speech", "talk", "action", "outro", "ending"]
        for keyword in segment_keywords:
            if keyword in description.lower():
                intent.segment_descriptions.append(f"Segment with {keyword}")
        
        # Parse effects requests
        effects_keywords = ["fade", "transition", "slow", "fast", "filter", "crop"]
        for keyword in effects_keywords:
            if keyword in description.lower():
                intent.effects_requests.append(keyword)
        
        print(f"   🎯 Parsed intent: {intent.bpm} BPM, {intent.resolution}, {len(intent.video_sources)} sources")
        return intent
    
    async def _match_source_files(self, intent: CompositionIntent) -> Dict[str, str]:
        """Match intent requirements to available source files"""
        matched_sources = {}
        
        # Get all available files
        all_files = []
        for source_file in Path("/tmp/music/source").glob("*"):
            if source_file.is_file() and source_file.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
                all_files.append(source_file.name)
        
        # If specific sources mentioned, try to match them
        for mentioned_source in intent.video_sources:
            for available_file in all_files:
                if mentioned_source.lower() in available_file.lower():
                    matched_sources[mentioned_source] = available_file
                    break
        
        # Auto-match based on patterns if no specific sources
        if not matched_sources and all_files:
            for category, patterns in self.video_patterns.items():
                for pattern in patterns:
                    for available_file in all_files:
                        if pattern in available_file.lower() and category not in matched_sources:
                            matched_sources[category] = available_file
                            break
        
        # Fallback: use first available files
        if not matched_sources and all_files:
            for i, file in enumerate(all_files[:3]):  # Use first 3 files
                matched_sources[f"segment_{i+1}"] = file
        
        print(f"   📂 Matched sources: {len(matched_sources)} files")
        for category, filename in matched_sources.items():
            print(f"      {category}: {filename}")
        
        return matched_sources
    
    async def _generate_segments(
        self, 
        intent: CompositionIntent, 
        matched_sources: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Generate segments based on intent and matched sources"""
        segments = []
        
        # Calculate segment timing
        beats_per_segment = intent.beats_per_measure
        current_beat = intent.render_start_beat or 0
        max_beat = intent.render_end_beat or intent.total_beats
        
        segment_id = 0
        for category, source_file in matched_sources.items():
            if current_beat >= max_beat:
                break
            
            end_beat = min(current_beat + beats_per_segment, max_beat)
            
            # Get file ID
            file_id = self.file_manager.get_id_by_name(source_file)
            if not file_id:
                print(f"   ⚠️ Could not get file ID for: {source_file}")
                continue
            
            # Create segment
            segment = {
                "id": f"segment_{segment_id}",
                "sourceRef": source_file,
                "startBeat": current_beat,
                "endBeat": end_beat,
                "operation": self._determine_operation(category, intent),
                "params": self._determine_params(category, intent, current_beat, end_beat),
                "description": f"{category.title()} segment using {source_file}"
            }
            
            segments.append(segment)
            segment_id += 1
            current_beat = end_beat
            
            print(f"   🎬 Segment {segment_id}: {source_file} (beat {segment['startBeat']}-{segment['endBeat']})")
        
        return segments
    
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
        """Generate effects tree based on intent"""
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
        
        # Add transitions if requested
        if "fade" in intent.effects_requests or "transition" in intent.effects_requests:
            effects_tree.append({
                "effect": "crossfade_transition",
                "params": {
                    "duration": 0.5,
                    "method": "crossfade"
                }
            })
        
        # Add audio normalization
        effects_tree.append({
            "effect": "audio_normalize",
            "params": {
                "target_level": -12
            }
        })
        
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