"""Composition planning and processing tools."""
import json
from pathlib import Path
from typing import Dict, List, Any

from ..server_deps import timing_decorator


def register(mcp, deps):
    file_manager = deps.file_manager
    content_analyzer = deps.content_analyzer
    enhanced_speech_analyzer = deps.enhanced_speech_analyzer
    composition_planner = deps.composition_planner

    @mcp.tool()
    @timing_decorator
    async def analyze_composition_sources(source_filenames: List[str], force_reanalysis: bool = False) -> Dict[str, Any]:
        """Analyze multiple video sources for intelligent composition planning.

        Args:
            source_filenames: List of video filenames to analyze
            force_reanalysis: Force fresh analysis, ignore cache (default: False)

        Returns:
            Dictionary with analyzed sources, recommendations, and priority order
        """
        try:
            analyzed_sources = []

            for i, filename in enumerate(source_filenames):
                file_id = file_manager.get_id_by_name(filename)
                if not file_id:
                    continue

                file_path = file_manager.resolve_id(file_id)

                speech_analysis = await enhanced_speech_analyzer.analyze_video_for_composition(
                    file_path, force_reanalysis=force_reanalysis
                )

                if not speech_analysis["success"]:
                    continue

                content_analysis = await content_analyzer.analyze_video_content(file_id)

                has_speech = speech_analysis["has_speech"]
                speech_quality = speech_analysis["quality_metrics"]["overall_quality"]

                if not has_speech:
                    strategy = "time_stretch"
                elif speech_quality > 0.8:
                    strategy = "smart_cut"
                elif speech_quality > 0.5:
                    strategy = "hybrid"
                else:
                    strategy = "minimal_stretch"

                priority_score = 0.5
                if has_speech:
                    priority_score += speech_quality * 0.3
                priority_score += content_analysis.get("overall_score", 0.5) * 0.2
                priority_score = min(1.0, priority_score)

                source_result = {
                    "filename": filename,
                    "file_id": file_id,
                    "duration": speech_analysis["video_duration"],
                    "has_speech": has_speech,
                    "speech_quality": speech_quality if has_speech else 0.0,
                    "content_score": content_analysis.get("overall_score", 0.5),
                    "recommended_strategy": strategy,
                    "priority_score": priority_score,
                    "speech_segments": speech_analysis.get("speech_segments", []),
                    "cut_points": speech_analysis.get("cut_points", []),
                    "cut_strategies": speech_analysis.get("cut_strategies", [])
                }

                analyzed_sources.append(source_result)

            analyzed_sources.sort(key=lambda s: s["priority_score"], reverse=True)

            recommendations = {
                "total_sources": len(analyzed_sources),
                "sources_with_speech": sum(1 for s in analyzed_sources if s["has_speech"]),
                "high_priority_sources": sum(1 for s in analyzed_sources if s["priority_score"] > 0.8),
                "suggested_composition_order": [s["filename"] for s in analyzed_sources],
                "processing_strategies": {
                    s["filename"]: s["recommended_strategy"] for s in analyzed_sources
                }
            }

            return {
                "success": True,
                "analyzed_sources": analyzed_sources,
                "recommendations": recommendations,
                "priority_order": [s["filename"] for s in analyzed_sources]
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    @timing_decorator
    async def generate_composition_plan(
        source_filenames: List[str],
        background_music: str,
        total_duration: float = 24.0,
        bpm: int = 120,
        composition_title: str = "Intelligent Composition",
        force_reanalysis: bool = False
    ) -> Dict[str, Any]:
        """Generate intelligent composition plan with speech-aware processing strategies.

        Args:
            source_filenames: List of video filenames for composition
            background_music: Background music filename
            total_duration: Total composition duration in seconds (default: 24.0)
            bpm: Beats per minute for synchronization (default: 120)
            composition_title: Title for the composition
            force_reanalysis: Force fresh analysis of sources (default: False)

        Returns:
            Dictionary with composition plan, file path, and processing summary
        """
        try:
            composition_plan = await composition_planner.create_composition_plan(
                sources=source_filenames,
                background_music=background_music,
                total_duration=total_duration,
                bpm=bpm,
                composition_title=composition_title,
                force_reanalysis=force_reanalysis
            )

            if not composition_plan.get("success", False):
                return composition_plan

            segments = composition_plan.get("composition", {}).get("segments", [])
            processing_summary = {
                "total_segments": len(segments),
                "speech_segments": sum(1 for s in segments if s.get("strategy", {}).get("preserve_speech_pitch", False)),
                "time_stretch_segments": sum(1 for s in segments if s.get("strategy", {}).get("type") == "time_stretch"),
                "smart_cut_segments": sum(1 for s in segments if s.get("strategy", {}).get("type") == "smart_cut"),
                "estimated_processing_time": len(segments) * 60,
                "audio_overlays": len([s for s in segments if s.get("audio_handling", {}).get("extracted_audio")])
            }

            return {
                "success": True,
                "composition_plan": composition_plan,
                "plan_file_path": str(composition_planner.cache_dir / f"composition_plan_latest.json"),
                "processing_summary": processing_summary
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate composition plan: {str(e)}"
            }

    @mcp.tool()
    @timing_decorator
    async def process_composition_plan(plan_file_path: str) -> Dict[str, Any]:
        """Execute an intelligent composition plan with speech-aware processing.

        Args:
            plan_file_path: Path to komposition-plan.json file

        Returns:
            Dictionary with output files, audio manifest, and processing log
        """
        try:
            print(f"🎬 PROCESSING INTELLIGENT COMPOSITION PLAN")

            plan_path = Path(plan_file_path)
            if not plan_path.is_absolute():
                plan_path = composition_planner.cache_dir / plan_file_path

            if not plan_path.exists():
                return {
                    "success": False,
                    "error": f"Plan file not found: {plan_file_path}"
                }

            with open(plan_path, 'r') as f:
                plan = json.load(f)

            if not plan.get("success", False):
                return {
                    "success": False,
                    "error": "Invalid composition plan"
                }

            segments = plan.get("composition", {}).get("segments", [])
            sources = plan.get("sources", {}).get("videos", [])
            audio_plan = plan.get("audio_plan", {})

            print(f"   📊 Processing {len(segments)} segments")

            processing_log = []
            output_files = []

            for i, segment in enumerate(segments):
                segment_id = segment["id"]
                source_id = segment["source_id"]
                strategy = segment["strategy"]
                cutting = segment["cutting"]
                audio_handling = segment["audio_handling"]

                print(f"\n   🎬 Processing {segment_id} ({strategy['type']})")

                source_file = None
                for src in sources:
                    if src["id"] == source_id:
                        source_file = src["file"]
                        break

                if not source_file:
                    processing_log.append({"segment": segment_id, "error": f"Source file not found for {source_id}"})
                    continue

                file_id = file_manager.get_id_by_name(source_file)
                if not file_id:
                    processing_log.append({"segment": segment_id, "error": f"File ID not found for {source_file}"})
                    continue

                try:
                    if strategy["type"] == "time_stretch":
                        target_duration = cutting["resulting_duration"]

                        result = await mcp.call_tool('process_file', {
                            'input_file_id': file_id,
                            'operation': 'trim',
                            'output_extension': 'mp4',
                            'params': f"start={cutting['source_start']} duration={target_duration}"
                        })

                        result_data = json.loads(result[0].text) if result and len(result) > 0 else {}

                        if result_data.get("success"):
                            segment_file_id = result_data["output_file_id"]
                            output_files.append({
                                "file_id": segment_file_id,
                                "description": f"Time-stretched segment: {segment_id}",
                                "type": "video_segment"
                            })
                            processing_log.append({
                                "segment": segment_id,
                                "operation": "time_stretch",
                                "success": True,
                                "output_file_id": segment_file_id
                            })

                    elif strategy["type"] == "smart_cut":
                        cut_start = cutting["source_start"]
                        cut_end = cutting["source_end"]
                        duration = cut_end - cut_start

                        result = await mcp.call_tool('process_file', {
                            'input_file_id': file_id,
                            'operation': 'trim',
                            'output_extension': 'mp4',
                            'params': f"start={cut_start} duration={duration}"
                        })

                        result_data = json.loads(result[0].text) if result and len(result) > 0 else {}

                        if result_data.get("success"):
                            segment_file_id = result_data["output_file_id"]
                            output_files.append({
                                "file_id": segment_file_id,
                                "description": f"Smart-cut segment: {segment_id} (speech preserved)",
                                "type": "video_segment"
                            })

                            if audio_handling.get("extracted_audio"):
                                speech_result = await mcp.call_tool('process_file', {
                                    'input_file_id': segment_file_id,
                                    'operation': 'extract_audio',
                                    'output_extension': 'wav',
                                    'params': ''
                                })

                                speech_data = json.loads(speech_result[0].text) if speech_result and len(speech_result) > 0 else {}

                                if speech_data.get("success"):
                                    output_files.append({
                                        "file_id": speech_data["output_file_id"],
                                        "description": f"Extracted speech: {segment_id}",
                                        "type": "speech_audio"
                                    })

                            processing_log.append({
                                "segment": segment_id,
                                "operation": "smart_cut",
                                "success": True,
                                "output_file_id": segment_file_id,
                                "speech_preserved": True
                            })

                except Exception as e:
                    processing_log.append({
                        "segment": segment_id,
                        "error": str(e),
                        "success": False
                    })
                    continue

            audio_manifest = {
                "background_music": audio_plan.get("background_music", {}),
                "speech_overlays": audio_plan.get("speech_overlays", []),
                "timeline": plan.get("timeline", {}),
                "instructions": [
                    "1. Load background music for full duration",
                    "2. Insert speech overlays at specified times",
                    "3. Mix with specified volume levels",
                    "4. Export final audio track"
                ]
            }

            success_count = sum(1 for log in processing_log if log.get("success", False))

            print(f"\n✅ PROCESSING COMPLETE: {success_count}/{len(segments)} segments successful")

            return {
                "success": success_count > 0,
                "output_files": output_files,
                "audio_manifest": audio_manifest,
                "processing_log": processing_log,
                "segments_processed": success_count,
                "total_segments": len(segments)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process composition plan: {str(e)}"
            }

    @mcp.tool()
    @timing_decorator
    async def preview_composition_timing(
        source_filenames: List[str],
        total_duration: float = 24.0,
        bpm: int = 120
    ) -> Dict[str, Any]:
        """Preview timing allocation for composition without full processing.

        Args:
            source_filenames: List of video filenames
            total_duration: Total composition duration in seconds (default: 24.0)
            bpm: Beats per minute for synchronization (default: 120)

        Returns:
            Dictionary with timing preview, recommendations, and estimated processing time
        """
        try:
            print(f"⏰ PREVIEWING COMPOSITION TIMING")

            seconds_per_beat = 60.0 / bpm
            beats_per_measure = 16
            slot_duration = seconds_per_beat * beats_per_measure

            time_slots = []
            current_time = 0.0

            for i in range(len(source_filenames)):
                if current_time >= total_duration:
                    break

                end_time = min(current_time + slot_duration, total_duration)

                time_slots.append({
                    "slot_number": i + 1,
                    "source_file": source_filenames[i] if i < len(source_filenames) else None,
                    "start_time": current_time,
                    "end_time": end_time,
                    "duration": end_time - current_time,
                    "beat_start": int(current_time / seconds_per_beat),
                    "beat_end": int(end_time / seconds_per_beat)
                })

                current_time = end_time

            timing_preview = []
            total_processing_estimate = 0

            for slot in time_slots:
                if not slot["source_file"]:
                    continue

                file_id = file_manager.get_id_by_name(slot["source_file"])
                if not file_id:
                    slot_info = {
                        **slot,
                        "strategy": "unknown",
                        "issue": "File not found",
                        "processing_time_estimate": 0
                    }
                else:
                    if "speech" in slot["source_file"].lower() or "talk" in slot["source_file"].lower():
                        strategy = "smart_cut"
                        processing_time = 120
                    else:
                        strategy = "time_stretch"
                        processing_time = 60

                    slot_info = {
                        **slot,
                        "strategy": strategy,
                        "processing_time_estimate": processing_time,
                        "note": f"Will use {strategy} processing"
                    }

                    total_processing_estimate += processing_time

                timing_preview.append(slot_info)

            recommendations = []

            if len(source_filenames) > len(time_slots):
                recommendations.append({
                    "type": "warning",
                    "message": f"Too many sources ({len(source_filenames)}) for duration ({total_duration}s). Only first {len(time_slots)} will be used."
                })

            if total_processing_estimate > 300:
                recommendations.append({
                    "type": "info",
                    "message": f"Estimated processing time: {total_processing_estimate/60:.1f} minutes. Consider processing in smaller batches."
                })

            speech_sources = sum(1 for slot in timing_preview if slot.get("strategy") == "smart_cut")
            if speech_sources > 0:
                recommendations.append({
                    "type": "info",
                    "message": f"{speech_sources} sources detected as speech content. These will preserve natural pitch."
                })

            print(f"✅ TIMING PREVIEW COMPLETE: {len(timing_preview)} slots allocated")

            return {
                "success": True,
                "timing_preview": timing_preview,
                "recommendations": recommendations,
                "estimated_processing_time": total_processing_estimate,
                "total_duration": total_duration,
                "beats_per_minute": bpm,
                "slot_duration": slot_duration
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to preview composition timing: {str(e)}"
            }
