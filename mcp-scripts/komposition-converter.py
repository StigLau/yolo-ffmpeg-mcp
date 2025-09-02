#!/usr/bin/env python3
"""
Komposition Format Converter
Converts between .md (human/LLM-friendly) and .json (Komposteur-compatible) formats
"""

import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional


class KompositionConverter:
    
    def __init__(self):
        self.beat_to_time_ratio = 0.5  # Default: 120 BPM = 0.5s per beat
        
    def md_to_json(self, md_content: str) -> Dict[str, Any]:
        """Convert markdown komposition to JSON format"""
        
        komposition = {
            "_id": "",
            "type": "Komposition",
            "bpm": 120,
            "config": {
                "width": 1280,
                "height": 720,
                "framerate": 24,
                "extension": "mp4"
            },
            "beatpattern": {
                "frombeat": 0,
                "tobeat": 64,
                "masterbpm": 120
            },
            "segments": [],
            "sources": []
        }
        
        lines = md_content.split('\n')
        current_segment = None
        
        for line in lines:
            line = line.strip()
            
            # Extract title
            if line.startswith('# ') and not komposition["_id"]:
                komposition["_id"] = line[2:].strip()
                
            # Extract BPM
            if '**BPM**:' in line:
                bpm_match = re.search(r'\*\*BPM\*\*:\s*(\d+)', line)
                if bmp_match:
                    bpm = int(bpm_match.group(1))
                    komposition["bpm"] = bmp
                    komposition["beatpattern"]["masterbpm"] = bmp
                    self.beat_to_time_ratio = 60.0 / bmp
                    
            # Extract resolution
            if '**Resolution**:' in line:
                res_match = re.search(r'(\d+)x(\d+)', line)
                if res_match:
                    komposition["config"]["width"] = int(res_match.group(1))
                    komposition["config"]["height"] = int(res_match.group(2))
                    
            # Extract frame rate
            if '**Frame Rate**:' in line:
                fps_match = re.search(r'(\d+)\s*fps', line)
                if fps_match:
                    komposition["config"]["framerate"] = int(fps_match.group(1))
                    
            # Parse segments
            if line.startswith('### Segment '):
                # Extract segment info: ### Segment 1: "Title" (0-8 beats)
                seg_match = re.search(r'### Segment \d+: "([^"]+)"\s*\((\d+)-(\d+) beats\)', line)
                if seg_match:
                    title = seg_match.group(1)
                    start_beat = int(seg_match.group(2))
                    end_beat = int(seg_match.group(3))
                    duration_beats = end_beat - start_beat
                    
                    current_segment = {
                        "id": title,
                        "sourceid": "",
                        "start": start_beat,
                        "duration": duration_beats,
                        "end": end_beat
                    }
                    komposition["segments"].append(current_segment)
                    
            # Extract source info from segments
            if current_segment and line.startswith('- **Source**:'):
                source_match = re.search(r'\*\*Source\*\*:\s*`([^`]+)`', line)
                if source_match:
                    current_segment["sourceid"] = source_match.group(1)
                    
        # Update total beats
        if komposition["segments"]:
            max_end = max(seg["end"] for seg in komposition["segments"])
            komposition["beatpattern"]["tobeat"] = max_end
            
        return komposition
    
    def json_to_md(self, json_data: Dict[str, Any]) -> str:
        """Convert JSON komposition to markdown format"""
        
        # Handle both direct komposition and CouchDB document wrapper
        if "doc" in json_data:
            kompo = json_data["doc"]
        else:
            kompo = json_data
            
        title = kompo.get("_id", "Untitled Komposition")
        bpm = kompo.get("bmp", kompo.get("beatpattern", {}).get("masterbpm", 120))
        config = kompo.get("config", {})
        segments = kompo.get("segments", [])
        sources = kompo.get("sources", [])
        
        md_content = f"""# {title}

> **Type**: Komposition  
> **BPM**: {bpm}  
> **Duration**: {kompo.get("beatpattern", {}).get("tobeat", 0)} beats  
> **Created**: Converted from JSON komposition

## 🎬 Video Configuration

- **Resolution**: {config.get("width", 1280)}x{config.get("height", 720)}
- **Frame Rate**: {config.get("framerate", 24)} fps  
- **Format**: {config.get("extension", "mp4").upper()}
- **Quality**: High (libx264, medium preset)

## 🎵 Audio Setup

- **Master BPM**: {bpm}
- **Beat Pattern**: {kompo.get("beatpattern", {}).get("frombeat", 0)}-{kompo.get("beatpattern", {}).get("tobeat", 0)} beats
- **Audio Processing**: Trim to video duration, crossfades

## 🎞️ Segment Sequence

"""
        
        # Add segments
        for i, segment in enumerate(segments, 1):
            duration_seconds = segment["duration"] * (60.0 / bmp) if bmp else segment["duration"] * 0.5
            
            md_content += f"""### Segment {i}: "{segment["id"]}" ({segment["start"]}-{segment["end"]} beats)
- **Source**: `{segment.get("sourceid", "")}`
- **Duration**: {duration_seconds:.1f} seconds ({segment["duration"]} beats at {bmp} BPM)
- **Video Effects**: 
  - [Effects to be defined based on segment position/style]
- **Transitions**: [Fade configuration based on position in sequence]

"""
        
        # Add sources section
        if sources:
            md_content += """## 📋 Source Registry

### Media Sources
"""
            for source in sources:
                md_content += f"""- **{source["id"]}**
  - URL: `{source.get("url", "")}`
  - Format: {source.get("extension", "").upper()} {source.get("mediatype", "").title()}
  - Checksum: {source.get("checksums", "N/A")}

"""
        
        md_content += """## 🔄 Processing Workflow

1. **Parse Komposition**: Extract segments, effects, timing
2. **Registry Resolution**: Convert file IDs to actual media paths
3. **FFMPEG Generation**: Create filter_complex command with all effects
4. **Model-Specific Fixes**: Apply LLM-specific syntax corrections
5. **Execution**: Run FFMPEG with proper -map parameters
6. **Quality Check**: Validate output duration, format, and quality

---

*Converted from JSON komposition format*"""
        
        return md_content
    
    def convert_file(self, input_file: str, output_file: str = None):
        """Convert file between formats"""
        
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
            
        if output_file is None:
            if input_path.suffix == '.md':
                output_file = input_path.with_suffix('.json')
            elif input_path.suffix == '.json':
                output_file = input_path.with_suffix('.md')
            else:
                raise ValueError("Input file must be .md or .json")
                
        output_path = Path(output_file)
        
        if input_path.suffix == '.md':
            # MD to JSON
            md_content = input_path.read_text(encoding='utf-8')
            json_data = self.md_to_json(md_content)
            output_path.write_text(json.dumps(json_data, indent=2), encoding='utf-8')
            print(f"✅ Converted MD to JSON: {input_file} → {output_file}")
            
        elif input_path.suffix == '.json':
            # JSON to MD
            json_data = json.loads(input_path.read_text(encoding='utf-8'))
            md_content = self.json_to_md(json_data)
            output_path.write_text(md_content, encoding='utf-8')
            print(f"✅ Converted JSON to MD: {input_file} → {output_file}")
            
        else:
            raise ValueError("Input file must be .md or .json")


def main():
    parser = argparse.ArgumentParser(description='Convert between Komposition MD and JSON formats')
    parser.add_argument('input', help='Input file (.md or .json)')
    parser.add_argument('-o', '--output', help='Output file (auto-detected if not specified)')
    parser.add_argument('--test', action='store_true', help='Run test conversion on example')
    
    args = parser.parse_args()
    
    converter = KompositionConverter()
    
    if args.test:
        # Test with the example file
        example_md = Path(__file__).parent.parent / "komposition-example.md"
        if example_md.exists():
            print("🧪 Testing conversion with example file...")
            converter.convert_file(str(example_md), "test-output.json")
            converter.convert_file("test-output.json", "test-roundtrip.md")
            print("✅ Test completed: komposition-example.md → test-output.json → test-roundtrip.md")
        else:
            print("❌ Example file not found for testing")
    else:
        converter.convert_file(args.input, args.output)


if __name__ == "__main__":
    main()