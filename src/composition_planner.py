"""
Intelligent Composition Planner
==============================

Advanced engine for creating intelligent video composition plans:
- Multi-source analysis and strategy selection
- Automatic time allocation with speech preservation
- Beat-synchronized planning with BPM awareness
- Effects chain optimization
- Audio-visual synchronization planning

Key Features:
- Speech-aware cutting strategies
- Intelligent time slot allocation
- Multi-modal optimization (video quality + speech preservation + timing)
- Komposition-plan JSON generation
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    from .enhanced_speech_analyzer import EnhancedSpeechAnalyzer
    from .content_analyzer import VideoContentAnalyzer
    from .file_manager import FileManager
except ImportError:
    from enhanced_speech_analyzer import EnhancedSpeechAnalyzer
    from content_analyzer import VideoContentAnalyzer
    from file_manager import FileManager


@dataclass
class CompositionSource:
    """Source file with analysis results"""
    id: str
    file: str
    file_path: Path
    duration: float
    has_speech: bool
    speech_analysis: Dict[str, Any]
    content_analysis: Dict[str, Any]
    recommended_strategy: str
    priority_score: float


@dataclass
class TimeSlot:
    """Time slot allocation in composition"""
    start: float
    end: float
    duration: float
    beat_start: int
    beat_end: int
    allocated_source: Optional[str] = None
    strategy: Optional[str] = None


@dataclass
class CompositionSegment:
    """Complete segment definition for composition"""
    id: str
    time_slot: TimeSlot
    source: CompositionSource
    strategy: Dict[str, Any]
    cutting: Dict[str, Any]
    audio_handling: Dict[str, Any]
    effects: List[Dict[str, Any]]
    quality_score: float


class CompositionPlanner:
    """Intelligent composition planning engine"""
    
    def __init__(self):
        self.speech_analyzer = EnhancedSpeechAnalyzer()
        self.content_analyzer = VideoContentAnalyzer()
        self.file_manager = FileManager()
        self.cache_dir = Path("/tmp/music/metadata/compositions")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_composition_plan(
        self,
        sources: List[str],  # List of filenames
        background_music: str,
        total_duration: float,
        bpm: int = 120,
        beats_per_measure: int = 16,
        composition_title: str = "Intelligent Composition",
        force_reanalysis: bool = False
    ) -> Dict[str, Any]:
        """
        Create comprehensive composition plan
        
        Args:
            sources: List of source video filenames
            background_music: Background music filename
            total_duration: Total composition duration
            bpm: Beats per minute for synchronization
            beats_per_measure: Beats per measure
            composition_title: Title for the composition
            force_reanalysis: Force fresh analysis of sources
            
        Returns:
            Complete komposition-plan JSON
        """
        print(f"🎬 CREATING INTELLIGENT COMPOSITION PLAN")
        print(f"   📊 Sources: {len(sources)} videos")
        print(f"   🎵 Duration: {total_duration}s @ {bpm} BPM")
        print(f"=" * 60)
        
        try:
            # Step 1: Analyze all sources
            print(f"\n🔍 STEP 1: ANALYZING SOURCES")
            analyzed_sources = await self._analyze_all_sources(sources, force_reanalysis)
            
            if not analyzed_sources:
                return {"success": False, "error": "No valid sources analyzed"}
            
            # Step 2: Create time slot allocation
            print(f"\n⏰ STEP 2: CREATING TIME ALLOCATION")
            time_slots = self._create_time_slots(total_duration, len(sources), bpm, beats_per_measure)
            
            # Step 3: Optimize source-to-slot assignment
            print(f"\n🎯 STEP 3: OPTIMIZING ASSIGNMENTS")
            segment_assignments = await self._optimize_assignments(analyzed_sources, time_slots)
            
            # Step 4: Generate cutting strategies
            print(f"\n✂️ STEP 4: GENERATING CUTTING STRATEGIES")
            composition_segments = await self._generate_segments(segment_assignments)
            
            # Step 5: Plan audio handling
            print(f"\n🎤 STEP 5: PLANNING AUDIO HANDLING")
            audio_plan = await self._plan_audio_handling(composition_segments, background_music)
            
            # Step 6: Create effects chain
            print(f"\n✨ STEP 6: CREATING EFFECTS CHAIN")
            effects_plan = await self._plan_effects_chain(composition_segments)
            
            # Step 7: Assemble final plan
            print(f"\n📋 STEP 7: ASSEMBLING COMPOSITION PLAN")
            composition_plan = self._assemble_composition_plan(
                composition_title, total_duration, bpm, beats_per_measure,
                analyzed_sources, composition_segments, audio_plan, effects_plan
            )
            
            # Cache the plan
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plan_file = self.cache_dir / f"composition_plan_{timestamp}.json"
            with open(plan_file, 'w') as f:
                json.dump(composition_plan, f, indent=2)
            
            print(f"\n🎉 COMPOSITION PLAN COMPLETE!")
            print(f"📂 Plan saved: {plan_file}")
            print(f"📊 Segments: {len(composition_segments)}")
            print(f"🎤 Speech segments: {sum(1 for s in composition_segments if s.source.has_speech)}")
            
            return composition_plan
            
        except Exception as e:
            print(f"❌ Composition planning failed: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    async def _analyze_all_sources(
        self, 
        source_filenames: List[str], 
        force_reanalysis: bool
    ) -> List[CompositionSource]:
        """Analyze all source files comprehensively"""
        analyzed_sources = []
        
        for i, filename in enumerate(source_filenames):
            print(f"   📹 Analyzing source {i+1}/{len(source_filenames)}: {filename}")
            
            # Get file ID and path
            file_id = self.file_manager.get_id_by_name(filename)
            if not file_id:
                print(f"      ❌ File not found: {filename}")
                continue
            
            file_path = self.file_manager.resolve_id(file_id)
            
            # Enhanced speech analysis
            speech_analysis = await self.speech_analyzer.analyze_video_for_composition(
                file_path, force_reanalysis=force_reanalysis
            )
            
            if not speech_analysis["success"]:
                print(f"      ❌ Speech analysis failed: {filename}")
                continue
            
            # Content analysis
            content_analysis = await self.content_analyzer.analyze_video_content(file_id)
            
            # Determine recommended strategy
            recommended_strategy = self._determine_strategy(speech_analysis, content_analysis)
            
            # Calculate priority score
            priority_score = self._calculate_priority_score(speech_analysis, content_analysis)
            
            source = CompositionSource(
                id=f"source_{i+1}",
                file=filename,
                file_path=file_path,
                duration=speech_analysis["video_duration"],
                has_speech=speech_analysis["has_speech"],
                speech_analysis=speech_analysis,
                content_analysis=content_analysis,
                recommended_strategy=recommended_strategy,
                priority_score=priority_score
            )
            
            analyzed_sources.append(source)
            
            print(f"      ✅ Strategy: {recommended_strategy}, Priority: {priority_score:.2f}")
        
        # Sort by priority score (highest first)
        analyzed_sources.sort(key=lambda s: s.priority_score, reverse=True)
        
        return analyzed_sources
    
    def _create_time_slots(
        self, 
        total_duration: float, 
        num_sources: int, 
        bpm: int, 
        beats_per_measure: int
    ) -> List[TimeSlot]:
        """Create time slot allocation based on BPM and measures"""
        seconds_per_beat = 60.0 / bpm
        slot_duration = seconds_per_beat * beats_per_measure
        
        time_slots = []
        current_time = 0.0
        current_beat = 0
        
        for i in range(num_sources):
            slot = TimeSlot(
                start=current_time,
                end=current_time + slot_duration,
                duration=slot_duration,
                beat_start=current_beat,
                beat_end=current_beat + beats_per_measure
            )
            
            time_slots.append(slot)
            current_time += slot_duration
            current_beat += beats_per_measure
            
            if current_time >= total_duration:
                # Adjust last slot to fit exactly
                slot.end = total_duration
                slot.duration = total_duration - slot.start
                break
        
        return time_slots
    
    async def _optimize_assignments(
        self, 
        sources: List[CompositionSource], 
        time_slots: List[TimeSlot]
    ) -> List[Tuple[CompositionSource, TimeSlot]]:
        """Optimize assignment of sources to time slots"""
        assignments = []
        
        # Simple assignment: prioritized sources to slots in order
        for i, (source, slot) in enumerate(zip(sources, time_slots)):
            slot.allocated_source = source.id
            slot.strategy = source.recommended_strategy
            assignments.append((source, slot))
            
            print(f"   🎯 Slot {i+1}: {source.file} ({source.recommended_strategy})")
        
        return assignments
    
    async def _generate_segments(
        self, 
        assignments: List[Tuple[CompositionSource, TimeSlot]]
    ) -> List[CompositionSegment]:
        """Generate detailed segments with cutting strategies"""
        segments = []
        
        for i, (source, time_slot) in enumerate(assignments):
            print(f"   ✂️ Generating segment {i+1}: {source.file}")
            
            # Generate cutting strategy
            target_duration = time_slot.duration
            cut_strategies = source.speech_analysis.get("cut_strategies", [])
            
            if not cut_strategies:
                # Generate strategies for this target duration
                cut_strategies = await self.speech_analyzer._generate_cut_strategies(
                    source.speech_analysis, target_duration
                )
            
            # Select best strategy
            best_strategy = cut_strategies[0] if cut_strategies else self._default_strategy(source, target_duration)
            
            # Create cutting plan
            cutting_plan = {
                "source_start": best_strategy.get("cut_start", 0.0),
                "source_end": best_strategy.get("cut_end", source.duration),
                "method": best_strategy.get("name", "time_stretch"),
                "resulting_duration": best_strategy.get("resulting_duration", target_duration),
                "fit_strategy": best_strategy.get("fit_method", "time_stretch")
            }
            
            # Create strategy plan
            strategy_plan = {
                "type": source.recommended_strategy,
                "reason": f"Best fit for {source.file}",
                "stretch_factor": best_strategy.get("stretch_factor", 1.0),
                "preserve_speech_pitch": source.has_speech and source.speech_analysis["quality_metrics"]["overall_quality"] > 0.5
            }
            
            # Create audio handling plan
            audio_plan = {
                "preserve_original": source.has_speech and strategy_plan["preserve_speech_pitch"],
                "background_music": True,
                "extracted_audio": None
            }
            
            if source.has_speech and audio_plan["preserve_original"]:
                audio_plan["extracted_audio"] = {
                    "file": f"extracted_speech_segment_{i+1}.wav",
                    "insert_at": time_slot.start + (time_slot.duration - cutting_plan["resulting_duration"]) / 2,
                    "duration": cutting_plan["resulting_duration"],
                    "volume": 0.9,
                    "fade_in": 0.2,
                    "fade_out": 0.2
                }
            
            # Create segment
            segment = CompositionSegment(
                id=f"segment_{i+1}",
                time_slot=time_slot,
                source=source,
                strategy=strategy_plan,
                cutting=cutting_plan,
                audio_handling=audio_plan,
                effects=[],
                quality_score=best_strategy.get("overall_score", 0.5)
            )
            
            segments.append(segment)
            
            print(f"      ✅ Method: {cutting_plan['method']}, Duration: {cutting_plan['resulting_duration']:.1f}s")
        
        return segments
    
    async def _plan_audio_handling(
        self, 
        segments: List[CompositionSegment], 
        background_music: str
    ) -> Dict[str, Any]:
        """Plan comprehensive audio handling"""
        audio_tracks = {
            "background": [],
            "speech": []
        }
        
        # Background music track
        total_duration = max(seg.time_slot.end for seg in segments)
        audio_tracks["background"].append({
            "start": 0.0,
            "end": total_duration,
            "source": background_music,
            "volume": 0.5
        })
        
        # Speech tracks
        for segment in segments:
            if segment.audio_handling.get("extracted_audio"):
                speech_info = segment.audio_handling["extracted_audio"]
                audio_tracks["speech"].append({
                    "start": speech_info["insert_at"],
                    "end": speech_info["insert_at"] + speech_info["duration"],
                    "source": speech_info["file"],
                    "volume": speech_info["volume"],
                    "fade_in": speech_info["fade_in"],
                    "fade_out": speech_info["fade_out"]
                })
        
        return {
            "background_music": {
                "file": background_music,
                "start_offset": 0.0,
                "volume": 0.5,
                "fade_in": 1.0,
                "fade_out": 2.0
            },
            "speech_overlays": [track for track in audio_tracks["speech"]],
            "audio_tracks": audio_tracks
        }
    
    async def _plan_effects_chain(
        self, 
        segments: List[CompositionSegment]
    ) -> Dict[str, Any]:
        """Plan effects chain for segments"""
        global_effects = [
            {
                "type": "background_music",
                "params": {
                    "volume": 0.5,
                    "fade_in": 1.0,
                    "fade_out": 2.0
                }
            }
        ]
        
        per_segment_effects = {}
        
        for segment in segments:
            segment_effects = []
            
            # Add stabilization for shaky content
            if segment.source.content_analysis.get("camera_motion", "stable") == "shaky":
                segment_effects.append({
                    "type": "video_stabilization",
                    "params": {"strength": 0.3}
                })
            
            # Add audio mixing for speech segments
            if segment.audio_handling.get("extracted_audio"):
                segment_effects.append({
                    "type": "audio_mix",
                    "params": {
                        "speech_volume": 0.9,
                        "music_volume": 0.2,
                        "crossfade_duration": 0.5
                    }
                })
            
            per_segment_effects[segment.id] = segment_effects
        
        return {
            "global": global_effects,
            "per_segment": per_segment_effects
        }
    
    def _assemble_composition_plan(
        self,
        title: str,
        total_duration: float,
        bpm: int,
        beats_per_measure: int,
        sources: List[CompositionSource],
        segments: List[CompositionSegment],
        audio_plan: Dict[str, Any],
        effects_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assemble the complete composition plan"""
        
        return {
            "metadata": {
                "title": title,
                "description": "Intelligent speech-aware video composition",
                "version": "2.0",
                "created_at": datetime.now().isoformat(),
                "total_duration": total_duration,
                "bpm": bpm,
                "beats_per_measure": beats_per_measure,
                "total_beats": int(total_duration * bpm / 60),
                "estimated_duration": total_duration
            },
            
            "sources": {
                "videos": [
                    {
                        "id": source.id,
                        "file": source.file,
                        "duration": source.duration,
                        "has_speech": source.has_speech,
                        "priority_score": source.priority_score,
                        "recommended_strategy": source.recommended_strategy,
                        "analysis_results": {
                            "speech_segments": source.speech_analysis.get("speech_segments", []),
                            "cut_points": source.speech_analysis.get("cut_points", []),
                            "quality_metrics": source.speech_analysis.get("quality_metrics", {}),
                            "content_score": source.content_analysis.get("overall_score", 0.5)
                        }
                    }
                    for source in sources
                ],
                "audio": [
                    {
                        "id": "background_music",
                        "file": audio_plan["background_music"]["file"],
                        "type": "background_music",
                        "bpm": bpm
                    }
                ]
            },
            
            "composition": {
                "segments": [
                    {
                        "id": segment.id,
                        "time_slot": {
                            "start": segment.time_slot.start,
                            "end": segment.time_slot.end,
                            "duration": segment.time_slot.duration,
                            "beat_start": segment.time_slot.beat_start,
                            "beat_end": segment.time_slot.beat_end
                        },
                        "source_id": segment.source.id,
                        "strategy": segment.strategy,
                        "cutting": segment.cutting,
                        "audio_handling": segment.audio_handling,
                        "quality_score": segment.quality_score
                    }
                    for segment in segments
                ]
            },
            
            "audio_plan": audio_plan,
            "effects": effects_plan,
            
            "timeline": {
                "audio_tracks": audio_plan["audio_tracks"],
                "video_segments": [
                    {
                        "start": segment.time_slot.start,
                        "end": segment.time_slot.end,
                        "source": segment.source.file,
                        "processing": segment.strategy["type"]
                    }
                    for segment in segments
                ]
            },
            
            "processing": {
                "quality": "high",
                "resolution": "1920x1080",
                "fps": 30,
                "audio_sample_rate": 44100,
                "estimated_processing_time": len(segments) * 60,
                "output_files": {
                    "final_video": "INTELLIGENT_COMPOSITION.mp4",
                    "audio_manifest": "AUDIO_TIMING_MANIFEST.json",
                    "intermediate_files": [
                        f"processed_{segment.id}.mp4" for segment in segments
                    ] + [
                        seg.audio_handling["extracted_audio"]["file"] 
                        for seg in segments 
                        if seg.audio_handling.get("extracted_audio")
                    ]
                }
            },
            
            "success": True
        }
    
    def _determine_strategy(
        self, 
        speech_analysis: Dict[str, Any], 
        content_analysis: Dict[str, Any]
    ) -> str:
        """Determine recommended processing strategy"""
        has_speech = speech_analysis["has_speech"]
        quality = speech_analysis["quality_metrics"]["overall_quality"]
        
        if not has_speech:
            return "time_stretch"
        elif quality > 0.8:
            return "smart_cut"
        elif quality > 0.5:
            return "hybrid"
        else:
            return "minimal_stretch"
    
    def _calculate_priority_score(
        self, 
        speech_analysis: Dict[str, Any], 
        content_analysis: Dict[str, Any]
    ) -> float:
        """Calculate priority score for source ordering"""
        base_score = 0.5
        
        # Boost for high-quality speech
        if speech_analysis["has_speech"]:
            speech_quality = speech_analysis["quality_metrics"]["overall_quality"]
            base_score += speech_quality * 0.3
        
        # Boost for good visual content
        content_score = content_analysis.get("overall_score", 0.5)
        base_score += content_score * 0.2
        
        return min(1.0, base_score)
    
    def _default_strategy(
        self, 
        source: CompositionSource, 
        target_duration: float
    ) -> Dict[str, Any]:
        """Generate default strategy when no cut strategies available"""
        stretch_factor = target_duration / source.duration
        
        return {
            "name": "time_stretch",
            "cut_start": 0.0,
            "cut_end": source.duration,
            "resulting_duration": target_duration,
            "stretch_factor": stretch_factor,
            "fit_method": "time_stretch",
            "overall_score": 0.5
        }