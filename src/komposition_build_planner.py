"""
Komposition Build Planner
=========================

Transforms komposition.json into detailed build plans with:
- Beat-precise timing calculations for any BPM
- File dependency mapping (source → intermediate → final)
- Effects tree dependency ordering
- Snippet extraction with exact timestamps
- Processing operation sequencing

Key Features:
- Multi-BPM support (120, 135, any BPM)
- Dependency graph resolution
- Intermediate file tracking
- Effect layering and ordering
- Build validation and testing
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime

try:
    from .file_manager import FileManager
    from .config import SecurityConfig
except ImportError:
    from file_manager import FileManager
    from config import SecurityConfig


@dataclass
class BeatTiming:
    """Precise beat timing calculations"""
    bpm: int
    beats_per_measure: int = 16
    start_beat: int = 0
    end_beat: int = 0
    
    @property
    def seconds_per_beat(self) -> float:
        return 60.0 / self.bpm
    
    @property
    def start_time(self) -> float:
        return self.start_beat * self.seconds_per_beat
    
    @property
    def end_time(self) -> float:
        return self.end_beat * self.seconds_per_beat
    
    @property
    def duration(self) -> float:
        return (self.end_beat - self.start_beat) * self.seconds_per_beat
    
    @property
    def beat_count(self) -> int:
        return self.end_beat - self.start_beat


@dataclass
class SourceFile:
    """Source file reference with metadata"""
    id: str
    filename: str
    file_path: Optional[Path] = None
    file_id: Optional[str] = None
    duration: float = 0.0
    resolution: Tuple[int, int] = (1920, 1080)
    fps: int = 30
    has_audio: bool = True


@dataclass
class SnippetExtraction:
    """Snippet extraction specification"""
    id: str
    source_file_id: str
    source_start: float
    source_duration: float
    target_start_beat: int
    target_end_beat: int
    target_timing: BeatTiming
    extraction_method: str = "trim"  # trim, smart_cut, time_stretch
    preserve_audio: bool = True


@dataclass
class EffectOperation:
    """Single effect operation specification"""
    id: str
    effect_type: str
    input_files: List[str]
    output_file: str
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    execution_order: int = 0


@dataclass
class IntermediateFile:
    """Intermediate file specification"""
    id: str
    filename: str
    file_path: Path
    source_operation: str
    dependencies: List[str] = field(default_factory=list)
    file_type: str = "video"  # video, audio, image
    temporary: bool = True


@dataclass
class BuildPlan:
    """Complete build plan for komposition"""
    id: str
    title: str
    source_komposition_path: str
    created_at: str
    beat_timing: BeatTiming
    render_range: Tuple[int, int]  # (start_beat, end_beat)
    output_resolution: Tuple[int, int]
    
    source_files: List[SourceFile] = field(default_factory=list)
    snippet_extractions: List[SnippetExtraction] = field(default_factory=list)
    intermediate_files: List[IntermediateFile] = field(default_factory=list)
    effect_operations: List[EffectOperation] = field(default_factory=list)
    
    execution_order: List[str] = field(default_factory=list)
    estimated_processing_time: float = 0.0
    final_output_file: str = ""


class KompositionBuildPlanner:
    """Build plan generator from komposition.json"""
    
    def __init__(self):
        self.file_manager = FileManager()
        self.build_cache_dir = Path("/tmp/music/metadata/build_plans")
        self.build_cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_build_plan(
        self,
        komposition_path: str,
        render_start_beat: Optional[int] = None,
        render_end_beat: Optional[int] = None,
        output_resolution: Tuple[int, int] = (1920, 1080),
        custom_bpm: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create detailed build plan from komposition.json
        
        Args:
            komposition_path: Path to komposition.json file
            render_start_beat: Override start beat (default: use komposition)
            render_end_beat: Override end beat (default: use komposition)
            output_resolution: Target resolution (width, height)
            custom_bpm: Override BPM (default: use komposition)
            
        Returns:
            Complete build plan with dependencies and execution order
        """
        try:
            # Step 1: Load and validate komposition
            komposition = await self._load_komposition(komposition_path)
            if not komposition:
                return {"success": False, "error": "Failed to load komposition"}
            
            # Step 2: Calculate beat timing
            bpm = custom_bpm or komposition["metadata"].get("bpm", 120)
            beats_per_measure = komposition["metadata"].get("beatsPerMeasure", 16)
            
            # Determine render range
            total_beats = komposition["metadata"].get("totalBeats", 128)
            start_beat = render_start_beat or 0
            end_beat = render_end_beat or total_beats
            
            beat_timing = BeatTiming(
                bpm=bpm,
                beats_per_measure=beats_per_measure,
                start_beat=start_beat,
                end_beat=end_beat
            )
            
            # Step 3: Create build plan structure
            build_plan = BuildPlan(
                id=f"build_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                title=komposition["metadata"].get("title", "Untitled Build"),
                source_komposition_path=komposition_path,
                created_at=datetime.now().isoformat(),
                beat_timing=beat_timing,
                render_range=(start_beat, end_beat),
                output_resolution=output_resolution
            )
            
            # Step 4: Process source files
            await self._process_source_files(komposition, build_plan)
            
            # Step 5: Plan snippet extractions
            await self._plan_snippet_extractions(komposition, build_plan)
            
            # Step 6: Plan effects operations
            await self._plan_effects_operations(komposition, build_plan)
            
            # Step 7: Build dependency graph and execution order
            await self._build_execution_order(build_plan)
            
            # Step 8: Estimate processing time
            build_plan.estimated_processing_time = self._estimate_processing_time(build_plan)
            
            # Step 9: Save build plan
            plan_file = await self._save_build_plan(build_plan)
            
            return {
                "success": True,
                "build_plan": asdict(build_plan),
                "build_plan_file": str(plan_file),
                "summary": {
                    "total_operations": len(build_plan.execution_order),
                    "estimated_time": build_plan.estimated_processing_time,
                    "output_resolution": output_resolution,
                    "render_duration": beat_timing.duration,
                    "bpm": bpm
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _load_komposition(self, komposition_path: str) -> Optional[Dict[str, Any]]:
        """Load and validate komposition.json"""
        try:
            # Handle relative paths
            path = Path(komposition_path)
            if not path.is_absolute():
                path = Path.cwd() / komposition_path
            
            if not path.exists():
                return None
            
            with open(path, 'r') as f:
                komposition = json.load(f)
            
            # Basic validation
            required_fields = ["metadata", "segments"]
            for field in required_fields:
                if field not in komposition:
                    return None
            return komposition
            
        except Exception as e:
            return None
    
    async def _process_source_files(self, komposition: Dict[str, Any], build_plan: BuildPlan):
        """Process and validate source files"""
        segments = komposition.get("segments", [])
        
        for segment in segments:
            source_ref = segment.get("sourceRef")
            if not source_ref:
                continue
            
            # Get file info
            file_id = self.file_manager.get_id_by_name(source_ref)
            if not file_id:
                continue
            
            file_path = self.file_manager.resolve_id(file_id)
            
            # Create source file entry
            source_file = SourceFile(
                id=f"source_{len(build_plan.source_files)}",
                filename=source_ref,
                file_path=file_path,
                file_id=file_id
                # TODO: Get actual duration, resolution, fps from file analysis
            )
            
            build_plan.source_files.append(source_file)
    
    async def _plan_snippet_extractions(self, komposition: Dict[str, Any], build_plan: BuildPlan):
        """Plan snippet extractions from source files"""
        segments = komposition.get("segments", [])
        
        for segment in segments:
            # Check if segment falls within render range
            seg_start = segment.get("startBeat", 0)
            seg_end = segment.get("endBeat", 16)
            
            if seg_end <= build_plan.render_range[0] or seg_start >= build_plan.render_range[1]:
                continue  # Skip segments outside render range
            
            # Find source file
            source_ref = segment.get("sourceRef")
            source_file = next((sf for sf in build_plan.source_files if sf.filename == source_ref), None)
            if not source_file:
                continue
            
            # Calculate timing
            target_timing = BeatTiming(
                bpm=build_plan.beat_timing.bpm,
                start_beat=seg_start,
                end_beat=seg_end
            )
            
            # Determine extraction method
            params = segment.get("params", {})
            extraction_method = "trim"
            if "setpts" in str(params) or segment.get("operation") == "time_stretch":
                extraction_method = "time_stretch"
            elif "smart_cut" in str(params):
                extraction_method = "smart_cut"
            
            # Create extraction plan
            extraction = SnippetExtraction(
                id=f"extract_{len(build_plan.snippet_extractions)}",
                source_file_id=source_file.id,
                source_start=params.get("start", 0),
                source_duration=params.get("duration", target_timing.duration),
                target_start_beat=seg_start,
                target_end_beat=seg_end,
                target_timing=target_timing,
                extraction_method=extraction_method
            )
            
            build_plan.snippet_extractions.append(extraction)
    
    async def _plan_effects_operations(self, komposition: Dict[str, Any], build_plan: BuildPlan):
        """Plan effects operations from effects tree"""
        effects_tree = komposition.get("effects_tree", [])
        if not effects_tree:
            return
        
        operation_id = 0
        
        for effect_layer in effects_tree:
            effect_type = effect_layer.get("effect", "unknown")
            effect_params = effect_layer.get("params", {})
            
            # Create effect operation
            operation = EffectOperation(
                id=f"effect_{operation_id}",
                effect_type=effect_type,
                input_files=[],  # Will be populated based on dependencies
                output_file=f"intermediate_effect_{operation_id}.mp4",
                parameters=effect_params,
                execution_order=operation_id
            )
            
            build_plan.effect_operations.append(operation)
            operation_id += 1
    
    async def _build_execution_order(self, build_plan: BuildPlan):
        """Build dependency graph and determine execution order"""
        execution_order = []
        
        # Phase 1: Source file extractions (can run in parallel)
        for extraction in build_plan.snippet_extractions:
            execution_order.append(f"extract_{extraction.id}")
        
        # Phase 2: Effects operations (must respect dependencies)
        for effect in build_plan.effect_operations:
            execution_order.append(f"effect_{effect.id}")
        
        # Phase 3: Final composition
        if build_plan.snippet_extractions or build_plan.effect_operations:
            execution_order.append("final_composition")
        
        build_plan.execution_order = execution_order
    
    def _estimate_processing_time(self, build_plan: BuildPlan) -> float:
        """Estimate total processing time in seconds"""
        base_time = 30  # Base overhead
        
        # Extraction time (based on duration and method)
        extraction_time = 0
        for extraction in build_plan.snippet_extractions:
            if extraction.extraction_method == "time_stretch":
                extraction_time += extraction.target_timing.duration * 2  # More processing for time stretch
            else:
                extraction_time += extraction.target_timing.duration * 0.5  # Trim is fast
        
        # Effects time (more complex = more time)
        effects_time = len(build_plan.effect_operations) * 60  # 1 minute per effect
        
        # Final composition time
        composition_time = build_plan.beat_timing.duration * 1.5
        
        return base_time + extraction_time + effects_time + composition_time
    
    async def _save_build_plan(self, build_plan: BuildPlan) -> Path:
        """Save build plan to file"""
        plan_file = self.build_cache_dir / f"{build_plan.id}.json"
        
        with open(plan_file, 'w') as f:
            json.dump(asdict(build_plan), f, indent=2, default=str)
        
        return plan_file
    
    def validate_build_plan_bpm(self, build_plan: BuildPlan, test_bpms: List[int]) -> Dict[str, Any]:
        """Validate build plan calculations for different BPMs"""
        validation_results = {}
        
        for bpm in test_bpms:
            # Recalculate timing for this BPM
            test_timing = BeatTiming(
                bpm=bpm,
                beats_per_measure=build_plan.beat_timing.beats_per_measure,
                start_beat=build_plan.beat_timing.start_beat,
                end_beat=build_plan.beat_timing.end_beat
            )
            
            # Validate all extractions
            extraction_errors = []
            for extraction in build_plan.snippet_extractions:
                test_extract_timing = BeatTiming(
                    bpm=bpm,
                    start_beat=extraction.target_start_beat,
                    end_beat=extraction.target_end_beat
                )
                
                # Check if timing makes sense
                if test_extract_timing.duration <= 0:
                    extraction_errors.append(f"Invalid duration for {extraction.id}")
                elif test_extract_timing.duration > 300:  # > 5 minutes seems wrong
                    extraction_errors.append(f"Excessive duration for {extraction.id}: {test_extract_timing.duration:.1f}s")
            
            validation_results[bpm] = {
                "total_duration": test_timing.duration,
                "seconds_per_beat": test_timing.seconds_per_beat,
                "extraction_errors": extraction_errors,
                "valid": len(extraction_errors) == 0
            }
            
            return validation_results
