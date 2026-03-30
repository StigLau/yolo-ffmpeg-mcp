#!/usr/bin/env python3
"""
Komposition Processor
Handles the conversion from komposition formats to FFMPEG commands
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Segment:
    """Represents a video segment with timing and effects"""
    id: str
    source: str
    start_time: float
    duration: float
    effects: List[str]
    transitions: List[str]


@dataclass 
class KompositionConfig:
    """Video configuration settings"""
    width: int = 1280
    height: int = 720
    framerate: int = 24
    extension: str = "mp4"
    bpm: int = 120


class KompositionProcessor:
    """Processes komposition files and generates FFMPEG commands"""
    
    def __init__(self):
        self.file_registry = {
            "JJVtt947FfI_136.mp4": "/tmp/music/source/JJVtt947FfI_136.mp4",
            "Subnautic Measures.flac": "/tmp/music/source/Subnautic Measures.flac"
        }
        
        self.effect_presets = {
            "8-bit retro": "scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10",
            "leica film": "colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4",
            "fade in": "fade=t=in:st=0:d=0.3",
            "fade out": "fade=t=out:st=2.7:d=0.3"
        }
    
    def parse_md_komposition(self, md_content: str) -> Tuple[KompositionConfig, List[Segment], Dict[str, str]]:
        """Parse markdown komposition and extract segments"""
        
        config = KompositionConfig()
        segments = []
        sources = {}
        
        lines = md_content.split('\n')
        current_segment = None
        
        for line in lines:
            line = line.strip()
            
            # Parse configuration
            if '**Resolution**:' in line:
                res_match = re.search(r'(\d+)x(\d+)', line)
                if res_match:
                    config.width = int(res_match.group(1))
                    config.height = int(res_match.group(2))
                    
            if '**Frame Rate**:' in line:
                fps_match = re.search(r'(\d+)\s*fps', line)
                if fps_match:
                    config.framerate = int(fps_match.group(1))
                    
            if '**BPM**:' in line:
                bpm_match = re.search(r'\*\*BPM\*\*:\s*(\d+)', line)
                if bpm_match:
                    config.bpm = int(bpm_match.group(1))
            
            # Parse segments
            if line.startswith('### Segment '):
                seg_match = re.search(r'### Segment \d+: "([^"]+)"', line)
                if seg_match:
                    segment_id = seg_match.group(1)
                    current_segment = {
                        'id': segment_id,
                        'source': '',
                        'start_time': 0.0,
                        'duration': 3.0,
                        'effects': [],
                        'transitions': []
                    }
                    
            # Parse segment details
            if current_segment:
                if line.startswith('- **Source**:'):
                    source_match = re.search(r'`([^`]+)`', line)
                    if source_match:
                        current_segment['source'] = source_match.group(1)
                        
                if line.startswith('- **Duration**:'):
                    dur_match = re.search(r'(\d+\.?\d*)\s*seconds', line)
                    if dur_match:
                        current_segment['duration'] = float(dur_match.group(1))
                        
                if 'Extract from' in line:
                    time_match = re.search(r'(\d+\.?\d*)s', line)
                    if time_match:
                        current_segment['start_time'] = float(time_match.group(1))
                        
                if line.startswith('  - ') and 'effect' in line.lower():
                    current_segment['effects'].append(line[4:].strip())
                    
                if line.startswith('- **Transitions**:'):
                    trans_match = re.search(r'Fade ([^(]+)', line)
                    if trans_match:
                        current_segment['transitions'].append(trans_match.group(1).strip())
                        
                # End of segment
                if line.startswith('### ') and current_segment['id']:
                    segment = Segment(
                        id=current_segment['id'],
                        source=current_segment['source'],
                        start_time=current_segment['start_time'],
                        duration=current_segment['duration'],
                        effects=current_segment['effects'],
                        transitions=current_segment['transitions']
                    )
                    segments.append(segment)
                    current_segment = None
        
        # Add last segment if exists
        if current_segment and current_segment['id']:
            segment = Segment(
                id=current_segment['id'],
                source=current_segment['source'],
                start_time=current_segment['start_time'],
                duration=current_segment['duration'],
                effects=current_segment['effects'],
                transitions=current_segment['transitions']
            )
            segments.append(segment)
        
        return config, segments, sources
    
    def generate_ffmpeg_command(self, config: KompositionConfig, segments: List[Segment], 
                               output_file: str, audio_source: str = None) -> str:
        """Generate FFMPEG command from komposition"""
        
        if not segments:
            raise ValueError("No segments found in komposition")
            
        # Resolve file paths
        video_input = self.file_registry.get(segments[0].source, segments[0].source)
        audio_input = audio_source or self.file_registry.get("Subnautic Measures.flac", "")
        
        if not audio_input:
            raise ValueError("No audio source specified")
            
        # Build filter_complex
        filter_parts = []
        segment_labels = []
        
        for i, segment in enumerate(segments):
            label = f"seg{i}"
            segment_labels.append(label)
            
            # Base segment extraction
            filter_part = f"[0:v]trim=start={segment.start_time}:duration={segment.duration},setpts=PTS-STARTPTS"
            
            # Add effects
            for effect in segment.effects:
                if "8-bit" in effect.lower():
                    filter_part += "," + self.effect_presets["8-bit retro"]
                elif "leica" in effect.lower():
                    filter_part += "," + self.effect_presets["leica film"]
                    
            # Add transitions
            for transition in segment.transitions:
                if "fade out" in transition.lower() or (i == len(segments) - 1):
                    filter_part += "," + self.effect_presets["fade out"]
                elif "fade in" in transition.lower() or (i > 0):
                    filter_part += "," + self.effect_presets["fade in"]
                    
            filter_part += f"[{label}]"
            filter_parts.append(filter_part)
        
        # Concatenation
        concat_inputs = "".join(f"[{label}]" for label in segment_labels)
        concat_filter = f"{concat_inputs}concat=n={len(segments)}:v=1:a=0[finalvideo]"
        filter_parts.append(concat_filter)
        
        # Audio processing
        total_duration = sum(seg.duration for seg in segments)
        audio_filter = f"[1:a]atrim=duration={total_duration}[finalaudio]"
        filter_parts.append(audio_filter)
        
        # Combine all filters
        filter_complex = ";".join(filter_parts)
        
        # Build complete command
        command = f'ffmpeg -y -i "{video_input}" -i "{audio_input}" -filter_complex "{filter_complex}" -map "[finalvideo]" -map "[finalaudio]" -c:v libx264 -preset medium -c:a aac -b:a 128k -pix_fmt yuv420p "{output_file}"'
        
        return command
    
    def process_komposition_file(self, komposition_file: str, output_file: str) -> str:
        """Process a komposition file and generate FFMPEG command"""
        
        komposition_path = Path(komposition_file)
        if not komposition_path.exists():
            raise FileNotFoundError(f"Komposition file not found: {komposition_file}")
            
        md_content = komposition_path.read_text(encoding='utf-8')
        config, segments, sources = self.parse_md_komposition(md_content)
        
        if not segments:
            raise ValueError("No segments found in komposition file")
            
        return self.generate_ffmpeg_command(config, segments, output_file)
    
    def validate_komposition(self, komposition_file: str) -> Dict[str, Any]:
        """Validate komposition file and return analysis"""
        
        komposition_path = Path(komposition_file)
        if not komposition_path.exists():
            return {"valid": False, "error": f"File not found: {komposition_file}"}
            
        try:
            md_content = komposition_path.read_text(encoding='utf-8')
            config, segments, sources = self.parse_md_komposition(md_content)
            
            issues = []
            warnings = []
            
            # Check segments
            if not segments:
                issues.append("No segments defined")
            else:
                total_duration = sum(seg.duration for seg in segments)
                if total_duration < 1.0:
                    warnings.append(f"Very short total duration: {total_duration}s")
                elif total_duration > 300.0:
                    warnings.append(f"Very long total duration: {total_duration}s")
                    
            # Check sources
            missing_sources = []
            for segment in segments:
                if segment.source and segment.source not in self.file_registry:
                    missing_sources.append(segment.source)
                    
            if missing_sources:
                issues.append(f"Missing sources: {', '.join(missing_sources)}")
                
            return {
                "valid": len(issues) == 0,
                "segments": len(segments),
                "total_duration": sum(seg.duration for seg in segments),
                "config": {
                    "resolution": f"{config.width}x{config.height}",
                    "framerate": config.framerate,
                    "bpm": config.bpm
                },
                "issues": issues,
                "warnings": warnings
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}