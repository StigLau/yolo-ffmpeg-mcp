"""
Komposition Processor Service
Handles komposition creation, validation, and processing orchestration
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from ..models.komposition import Komposition, KompositionSpec, Segment, Effect, EffectType, ProcessingStatus
from ..models.media import MediaReference, MediaType
from ..registry.media_registry import MediaRegistry
from ..llm.processing_llm import ProcessingLLM


class KompositionProcessor:
    """Service for processing komposition creation and management"""
    
    def __init__(self, processing_llm: ProcessingLLM, media_registry: MediaRegistry):
        self.processing_llm = processing_llm
        self.media_registry = media_registry
    
    async def create_from_spec(self, spec: KompositionSpec, user_id: str) -> Komposition:
        """Create komposition from specification"""
        komposition_id = f"komp_{uuid.uuid4().hex[:8]}"
        
        # Create base komposition
        komposition = Komposition(
            id=komposition_id,
            title=spec.title,
            description=spec.description,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            bpm=spec.bpm,
            total_beats=(spec.bpm * spec.duration_seconds) / 60.0,
            duration_seconds=spec.duration_seconds,
            resolution=spec.resolution,
            status=ProcessingStatus.DRAFT
        )
        
        # Process audio file if provided
        if spec.audio_file_path:
            await self._process_audio_track(komposition, spec.audio_file_path)
        
        # Generate initial segments based on visual concept
        await self._generate_initial_segments(komposition, spec)
        
        return komposition
    
    async def _process_audio_track(self, komposition: Komposition, audio_file_path: str) -> None:
        """Process and register audio track"""
        from ..models.media import MediaMetadata
        from ..models.komposition import AudioTrack
        
        # Register audio file in media registry
        audio_metadata = MediaMetadata(
            type=MediaType.AUDIO,
            filename=audio_file_path.split('/')[-1],
            file_size_bytes=0  # Will be calculated by registry
        )
        
        try:
            audio_ref = await self.media_registry.register_file(audio_file_path, audio_metadata)
            
            # Create AudioTrack
            audio_track = AudioTrack(
                source=audio_ref,
                bpm=komposition.bpm,
                duration_seconds=komposition.duration_seconds
            )
            
            komposition.audio_track = audio_track
            
        except Exception as e:
            print(f"Warning: Could not process audio file {audio_file_path}: {e}")
    
    async def _generate_initial_segments(self, komposition: Komposition, spec: KompositionSpec) -> None:
        """Generate initial video segments for komposition"""
        
        # Calculate basic segment structure
        num_segments = max(2, min(8, int(komposition.duration_seconds / 4)))  # 4-second segments on average
        segment_duration = komposition.duration_seconds / num_segments
        
        segments = []
        
        for i in range(num_segments):
            segment_id = f"seg_{uuid.uuid4().hex[:8]}"
            start_seconds = i * segment_duration
            
            # Determine effects based on visual concept and segment position
            effects = await self._suggest_effects_for_segment(
                spec.visual_concept, 
                i, 
                num_segments, 
                spec.preferred_effects
            )
            
            segment = Segment(
                id=segment_id,
                name=f"Segment {i+1}",
                start_beat=(komposition.bpm * start_seconds) / 60.0,
                duration_beats=(komposition.bpm * segment_duration) / 60.0,
                start_seconds=start_seconds,
                duration_seconds=segment_duration,
                source_media=None,  # Will be populated when user provides source videos
                effects=effects,
                visual_score=0.7  # Default decent score
            )
            
            segments.append(segment)
        
        komposition.segments = segments
    
    async def _suggest_effects_for_segment(self, 
                                         visual_concept: Optional[str], 
                                         segment_index: int, 
                                         total_segments: int,
                                         preferred_effects: Optional[List[EffectType]]) -> List[Effect]:
        """Suggest effects based on visual concept and segment position"""
        effects = []
        
        # Base effects based on visual concept
        if visual_concept:
            concept_lower = visual_concept.lower()
            
            if "vintage" in concept_lower or "old" in concept_lower or "retro" in concept_lower:
                effects.append(Effect(
                    type=EffectType.VINTAGE,
                    name="Vintage Style",
                    intensity=0.8
                ))
                effects.append(Effect(
                    type=EffectType.VIGNETTE,
                    name="Vintage Vignette",
                    intensity=0.6
                ))
            
            elif "blur" in concept_lower or "dreamy" in concept_lower:
                effects.append(Effect(
                    type=EffectType.BLUR,
                    name="Soft Blur",
                    intensity=0.5
                ))
            
            elif "8bit" in concept_lower or "pixel" in concept_lower:
                effects.append(Effect(
                    type=EffectType.EIGHT_BIT,
                    name="8-bit Style",
                    intensity=1.0,
                    parameters={"resolution_scale": 4, "color_depth": 16}
                ))
        
        # Add preferred effects if specified
        if preferred_effects:
            for effect_type in preferred_effects[:2]:  # Limit to 2 preferred effects
                effects.append(Effect(
                    type=effect_type,
                    name=f"{effect_type.value.title()} Effect",
                    intensity=0.7
                ))
        
        # Position-based effects (beginning and end segments)
        if segment_index == 0:
            # First segment - fade in
            effects.append(Effect(
                type=EffectType.FADE_IN,
                name="Opening Fade In",
                duration=1.0,
                intensity=1.0
            ))
        
        elif segment_index == total_segments - 1:
            # Last segment - fade out
            effects.append(Effect(
                type=EffectType.FADE_OUT,
                name="Closing Fade Out", 
                duration=1.0,
                intensity=1.0
            ))
        
        else:
            # Middle segments - crossfade transitions
            effects.append(Effect(
                type=EffectType.CROSSFADE,
                name="Segment Transition",
                duration=0.5,
                intensity=0.8
            ))
        
        return effects
    
    async def add_source_media_to_segments(self, komposition: Komposition, media_files: List[str]) -> None:
        """Add source media files to komposition segments"""
        
        # Register all media files
        media_refs = []
        for file_path in media_files:
            try:
                from ..models.media import MediaMetadata
                
                metadata = MediaMetadata(
                    type=MediaType.VIDEO,
                    filename=file_path.split('/')[-1],
                    file_size_bytes=0
                )
                
                media_ref = await self.media_registry.register_file(file_path, metadata)
                media_refs.append(media_ref)
                
            except Exception as e:
                print(f"Warning: Could not register media file {file_path}: {e}")
                continue
        
        # Assign media to segments
        if media_refs and komposition.segments:
            # Distribute media files across segments
            for i, segment in enumerate(komposition.segments):
                media_index = i % len(media_refs)
                segment.source_media = media_refs[media_index]
        
        komposition.updated_at = datetime.utcnow()
    
    async def validate_for_processing(self, komposition: Komposition) -> Dict[str, Any]:
        """Validate komposition is ready for video processing"""
        issues = []
        warnings = []
        
        # Check audio track
        if not komposition.audio_track:
            warnings.append("No audio track provided - video will be silent")
        
        # Check segments have source media
        segments_without_media = [s for s in komposition.segments if not s.source_media]
        if segments_without_media:
            issues.append(f"{len(segments_without_media)} segments missing source media")
        
        # Check segment timing
        total_segment_time = sum(s.duration_seconds for s in komposition.segments)
        if abs(total_segment_time - komposition.duration_seconds) > 0.5:
            warnings.append(f"Segment timing ({total_segment_time}s) doesn't match total duration ({komposition.duration_seconds}s)")
        
        # Check for complex effects that might increase processing cost
        complex_effects = []
        for segment in komposition.segments:
            for effect in segment.effects:
                if effect.type in [EffectType.EIGHT_BIT, EffectType.LEICA, EffectType.COLOR_GRADE]:
                    complex_effects.append(effect.type)
        
        if complex_effects:
            warnings.append(f"Complex effects detected: {complex_effects} (may increase processing cost)")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "estimated_cost": komposition.estimated_processing_cost,
            "ready_for_processing": komposition.is_ready_for_processing
        }