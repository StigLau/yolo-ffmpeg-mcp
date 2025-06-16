"""
Professional Audio Effects Processor
Handles FFmpeg-based audio mastering and effects processing with template support
"""

import json
import yaml
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from .ffmpeg_wrapper import FFMPEGWrapper
    from .config import SecurityConfig
    from .file_manager import FileManager
except ImportError:
    from ffmpeg_wrapper import FFMPEGWrapper
    from config import SecurityConfig
    from file_manager import FileManager

logger = logging.getLogger(__name__)

class AudioEffectProvider(Enum):
    FFMPEG = "ffmpeg"
    PYTHON = "python"

@dataclass
class AudioEffectParameter:
    name: str
    type: str  # "float", "int", "str", "bool", "list"
    default: Union[float, int, str, bool, List]
    min_value: Optional[Union[float, int]] = None
    max_value: Optional[Union[float, int]] = None
    description: str = ""
    options: Optional[List[str]] = None

@dataclass
class AudioEffectDefinition:
    name: str
    provider: AudioEffectProvider
    category: str  # "eq", "dynamics", "loudness", "spatial", "filter"
    description: str
    parameters: List[AudioEffectParameter]
    filter_chain: Optional[str] = None  # FFmpeg filter chain
    processing_function: Optional[str] = None  # Python function name
    performance_tier: str = "fast"  # "fast", "medium", "slow"
    estimated_time_per_second: float = 0.05

class AudioEffectProcessor:
    """Core audio effects processing engine with template support"""
    
    def __init__(self, ffmpeg_wrapper: FFMPEGWrapper, file_manager: FileManager):
        self.ffmpeg = ffmpeg_wrapper
        self.file_manager = file_manager
        self.effects_registry: Dict[str, AudioEffectDefinition] = {}
        
        # Template directories
        self.predefined_templates_dir = Path(__file__).parent.parent / "examples" / "effect-templates" / "audio"
        self.user_templates_dir = Path("/tmp/music/effect-templates/audio")
        self.user_templates_dir.mkdir(parents=True, exist_ok=True)
        
        self._load_effects()
        
    def _load_effects(self):
        """Load effect definitions and templates"""
        self._register_builtin_audio_effects()
        
    def _register_builtin_audio_effects(self):
        """Register built-in audio effects"""
        
        # Core Audio Filters
        self.effects_registry["high_pass_filter"] = AudioEffectDefinition(
            name="high_pass_filter",
            provider=AudioEffectProvider.FFMPEG,
            category="filter",
            description="High-pass filter to remove low-frequency content",
            parameters=[
                AudioEffectParameter("frequency", "float", 80.0, 10.0, 1000.0, "Cutoff frequency in Hz"),
                AudioEffectParameter("rolloff", "int", 12, 6, 48, "Filter rolloff in dB/octave")
            ],
            filter_chain="highpass=f={frequency}:p={rolloff}",
            performance_tier="fast",
            estimated_time_per_second=0.02
        )
        
        self.effects_registry["equalizer"] = AudioEffectDefinition(
            name="equalizer",
            provider=AudioEffectProvider.FFMPEG,
            category="eq",
            description="Parametric equalizer with multiple bands",
            parameters=[
                AudioEffectParameter("bands", "list", [], description="List of EQ bands with frequency, gain, q")
            ],
            processing_function="process_parametric_eq",
            performance_tier="fast",
            estimated_time_per_second=0.03
        )
        
        self.effects_registry["compressor"] = AudioEffectDefinition(
            name="compressor",
            provider=AudioEffectProvider.FFMPEG,
            category="dynamics",
            description="Dynamic range compressor",
            parameters=[
                AudioEffectParameter("threshold", "float", -18.0, -60.0, 0.0, "Compression threshold in dB"),
                AudioEffectParameter("ratio", "float", 3.0, 1.0, 20.0, "Compression ratio"),
                AudioEffectParameter("attack", "float", 20.0, 0.1, 1000.0, "Attack time in ms"),
                AudioEffectParameter("release", "float", 150.0, 1.0, 5000.0, "Release time in ms"),
                AudioEffectParameter("knee", "float", 2.0, 0.0, 10.0, "Knee softness in dB")
            ],
            filter_chain="acompressor=threshold={threshold}dB:ratio={ratio}:attack={attack}:release={release}:knee={knee}",
            performance_tier="fast",
            estimated_time_per_second=0.04
        )
        
        self.effects_registry["loudness_normalize"] = AudioEffectDefinition(
            name="loudness_normalize",
            provider=AudioEffectProvider.FFMPEG,
            category="loudness",
            description="EBU R128 loudness normalization",
            parameters=[
                AudioEffectParameter("target_lufs", "float", -16.0, -30.0, -6.0, "Target integrated loudness in LUFS"),
                AudioEffectParameter("true_peak", "float", -1.0, -3.0, 0.0, "True peak ceiling in dBTP"),
                AudioEffectParameter("lra", "float", 7.0, 1.0, 20.0, "Loudness range in LU")
            ],
            processing_function="process_loudness_normalize",
            performance_tier="medium",
            estimated_time_per_second=0.15
        )
        
        self.effects_registry["limiter"] = AudioEffectDefinition(
            name="limiter",
            provider=AudioEffectProvider.FFMPEG,
            category="dynamics",
            description="Peak limiter for final output control",
            parameters=[
                AudioEffectParameter("ceiling", "float", -1.0, -3.0, 0.0, "Output ceiling in dBTP"),
                AudioEffectParameter("release", "float", 50.0, 1.0, 1000.0, "Release time in ms"),
                AudioEffectParameter("target_lufs", "float", -14.0, -30.0, -6.0, "Optional LUFS target")
            ],
            filter_chain="alimiter=level_in=1:level_out={ceiling}dB:release={release}",
            performance_tier="fast",
            estimated_time_per_second=0.03
        )
        
        self.effects_registry["de_esser"] = AudioEffectDefinition(
            name="de_esser",
            provider=AudioEffectProvider.FFMPEG,
            category="dynamics",
            description="Frequency-specific compressor for sibilance control",
            parameters=[
                AudioEffectParameter("frequency", "float", 6500.0, 2000.0, 12000.0, "Target frequency in Hz"),
                AudioEffectParameter("threshold", "float", -25.0, -50.0, -10.0, "Threshold in dB"),
                AudioEffectParameter("ratio", "float", 3.0, 1.0, 10.0, "Compression ratio"),
                AudioEffectParameter("attack", "float", 1.0, 0.1, 10.0, "Attack time in ms"),
                AudioEffectParameter("release", "float", 100.0, 10.0, 1000.0, "Release time in ms")
            ],
            processing_function="process_de_esser",
            performance_tier="medium",
            estimated_time_per_second=0.08
        )
        
        self.effects_registry["stereo_widener"] = AudioEffectDefinition(
            name="stereo_widener",
            provider=AudioEffectProvider.FFMPEG,
            category="spatial",
            description="Stereo field width control",
            parameters=[
                AudioEffectParameter("width", "float", 1.2, 0.0, 2.0, "Stereo width multiplier"),
                AudioEffectParameter("frequency_range", "list", [200, 20000], description="Frequency range to affect [low, high]")
            ],
            processing_function="process_stereo_widener",
            performance_tier="fast",
            estimated_time_per_second=0.02
        )
        
        self.effects_registry["mono_bass"] = AudioEffectDefinition(
            name="mono_bass",
            provider=AudioEffectProvider.FFMPEG,
            category="spatial",
            description="Make low frequencies mono for club compatibility",
            parameters=[
                AudioEffectParameter("frequency", "float", 120.0, 50.0, 300.0, "Mono cutoff frequency in Hz")
            ],
            processing_function="process_mono_bass",
            performance_tier="fast",
            estimated_time_per_second=0.02
        )
        
        self.effects_registry["noise_gate"] = AudioEffectDefinition(
            name="noise_gate",
            provider=AudioEffectProvider.FFMPEG,
            category="dynamics",
            description="Noise gate for background noise removal",
            parameters=[
                AudioEffectParameter("threshold", "float", -50.0, -80.0, -20.0, "Gate threshold in dB"),
                AudioEffectParameter("ratio", "float", 10.0, 2.0, 20.0, "Gate ratio"),
                AudioEffectParameter("attack", "float", 5.0, 0.1, 100.0, "Attack time in ms"),
                AudioEffectParameter("release", "float", 200.0, 10.0, 2000.0, "Release time in ms")
            ],
            filter_chain="agate=threshold={threshold}dB:ratio={ratio}:attack={attack}:release={release}",
            performance_tier="fast",
            estimated_time_per_second=0.03
        )
    
    def load_effect_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Load an effect template from YAML file"""
        # Check user templates first
        user_template_path = self.user_templates_dir / f"{template_name}.yaml"
        predefined_template_path = self.predefined_templates_dir / f"{template_name}.yaml"
        
        template_path = user_template_path if user_template_path.exists() else predefined_template_path
        
        if not template_path.exists():
            return None
            
        try:
            with open(template_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load template {template_name}: {e}")
            return None
    
    def list_effect_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all available effect templates"""
        templates = {"predefined": [], "user": []}
        
        # Load predefined templates
        if self.predefined_templates_dir.exists():
            for template_file in self.predefined_templates_dir.glob("*.yaml"):
                try:
                    with open(template_file, 'r') as f:
                        template = yaml.safe_load(f)
                        template["template_id"] = template_file.stem
                        templates["predefined"].append(template)
                except Exception as e:
                    logger.warning(f"Failed to load predefined template {template_file}: {e}")
        
        # Load user templates  
        for template_file in self.user_templates_dir.glob("*.yaml"):
            try:
                with open(template_file, 'r') as f:
                    template = yaml.safe_load(f)
                    template["template_id"] = template_file.stem
                    templates["user"].append(template)
            except Exception as e:
                logger.warning(f"Failed to load user template {template_file}: {e}")
        
        return templates
    
    def save_effect_template(self, template_name: str, template_data: Dict[str, Any]) -> bool:
        """Save an effect template to user directory"""
        try:
            template_path = self.user_templates_dir / f"{template_name}.yaml"
            with open(template_path, 'w') as f:
                yaml.dump(template_data, f, default_flow_style=False, sort_keys=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save template {template_name}: {e}")
            return False
    
    async def apply_effect_template(self, file_id: str, template_name: str) -> Dict[str, Any]:
        """Apply a complete effect template to an audio file"""
        template = self.load_effect_template(template_name)
        if not template:
            return {"success": False, "error": f"Template '{template_name}' not found"}
        
        effects_chain = template.get("effects_chain", [])
        if not effects_chain:
            return {"success": False, "error": f"Template '{template_name}' has no effects chain"}
        
        return await self.apply_effect_chain(file_id, effects_chain)
    
    async def apply_effect_chain(self, file_id: str, effects_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply multiple audio effects in sequence"""
        current_file_id = file_id
        applied_effects = []
        
        for step_idx, effect_step in enumerate(effects_chain):
            effect_name = effect_step.get("effect")
            parameters = effect_step.get("parameters", {})
            
            if not effect_name:
                return {
                    "success": False,
                    "error": f"Missing effect name in step {step_idx}",
                    "applied_effects": applied_effects
                }
            
            result = await self.apply_effect(current_file_id, effect_name, parameters)
            
            if not result.get("success"):
                return {
                    "success": False,
                    "error": f"Failed at step {step_idx}: {result.get('error')}",
                    "applied_effects": applied_effects,
                    "failed_step": effect_step
                }
            
            current_file_id = result["output_file_id"]
            applied_effects.append({
                "step": step_idx,
                "effect": effect_name,
                "parameters": parameters,
                "output_file_id": current_file_id
            })
        
        return {
            "success": True,
            "input_file_id": file_id,
            "final_output_file_id": current_file_id,
            "applied_effects": applied_effects,
            "total_steps": len(effects_chain)
        }
    
    async def apply_effect(self, file_id: str, effect_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Apply a single audio effect to a file"""
        if effect_name not in self.effects_registry:
            return {
                "success": False,
                "error": f"Audio effect '{effect_name}' not found",
                "available_effects": list(self.effects_registry.keys())
            }
        
        effect = self.effects_registry[effect_name]
        parameters = parameters or {}
        
        # Validate and set default parameters
        validated_params = self._validate_parameters(effect, parameters)
        if "error" in validated_params:
            return {"success": False, **validated_params}
        
        try:
            if effect.provider == AudioEffectProvider.FFMPEG:
                if effect.filter_chain:
                    return await self._apply_ffmpeg_audio_effect(file_id, effect, validated_params["parameters"])
                else:
                    return await self._apply_python_audio_effect(file_id, effect, validated_params["parameters"])
            else:
                return await self._apply_python_audio_effect(file_id, effect, validated_params["parameters"])
                
        except Exception as e:
            logger.error(f"Error applying audio effect {effect_name}: {e}")
            return {"success": False, "error": str(e)}
    
    def _validate_parameters(self, effect: AudioEffectDefinition, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and set default values for effect parameters"""
        validated = {}
        
        for param in effect.parameters:
            value = parameters.get(param.name, param.default)
            
            # Type validation
            if param.type == "float":
                try:
                    value = float(value)
                    if param.min_value is not None and value < param.min_value:
                        value = param.min_value
                    if param.max_value is not None and value > param.max_value:
                        value = param.max_value
                except (ValueError, TypeError):
                    return {"error": f"Invalid float value for parameter '{param.name}': {value}"}
            
            elif param.type == "int":
                try:
                    value = int(value)
                    if param.min_value is not None and value < param.min_value:
                        value = param.min_value
                    if param.max_value is not None and value > param.max_value:
                        value = param.max_value
                except (ValueError, TypeError):
                    return {"error": f"Invalid int value for parameter '{param.name}': {value}"}
            
            elif param.type == "list":
                if not isinstance(value, list):
                    return {"error": f"Parameter '{param.name}' must be a list"}
            
            validated[param.name] = value
        
        return {"parameters": validated}
    
    async def _apply_ffmpeg_audio_effect(self, file_id: str, effect: AudioEffectDefinition, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply FFmpeg-based audio effect"""
        source_path = self.file_manager.resolve_id(file_id)
        if not source_path:
            return {"success": False, "error": f"File not found: {file_id}"}
        
        # Generate output file
        output_path = SecurityConfig.TEMP_DIR / f"audio_effect_{effect.name}_{file_id}_{hash(str(parameters))}.wav"
        
        # Build filter chain with parameters
        filter_chain = effect.filter_chain
        for param_name, param_value in parameters.items():
            filter_chain = filter_chain.replace(f"{{{param_name}}}", str(param_value))
        
        # Execute FFmpeg command
        command = [
            self.ffmpeg.ffmpeg_path,
            "-i", str(source_path),
            "-af", filter_chain,
            "-y",
            str(output_path)
        ]
        result = await self.ffmpeg.execute_command(command)
        
        if result["success"]:
            output_file_id = self.file_manager.register_file(output_path)
            return {
                "success": True,
                "input_file_id": file_id,
                "output_file_id": output_file_id,
                "effect_name": effect.name,
                "parameters": parameters,
                "output_path": str(output_path),
                "processing_time": result.get("processing_time", 0)
            }
        else:
            return {"success": False, "error": result.get("error", "FFmpeg processing failed")}
    
    async def _apply_python_audio_effect(self, file_id: str, effect: AudioEffectDefinition, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Python-based audio effect"""
        if not effect.processing_function:
            return {"success": False, "error": f"No processing function defined for effect {effect.name}"}
        
        processing_func = getattr(self, effect.processing_function, None)
        if not processing_func:
            return {"success": False, "error": f"Processing function not found: {effect.processing_function}"}
        
        try:
            result = await processing_func(file_id, parameters)
            return result
        except Exception as e:
            logger.error(f"Error in Python audio effect processing: {e}")
            return {"success": False, "error": str(e)}
    
    # Processing functions for complex effects
    
    async def process_parametric_eq(self, file_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process parametric EQ with multiple bands"""
        bands = parameters.get("bands", [])
        if not bands:
            return {"success": False, "error": "No EQ bands specified"}
        
        source_path = self.file_manager.resolve_id(file_id)
        if not source_path:
            return {"success": False, "error": f"File not found: {file_id}"}
        
        output_path = SecurityConfig.TEMP_DIR / f"audio_eq_{file_id}_{hash(str(parameters))}.wav"
        
        # Build EQ filter chain
        eq_filters = []
        for band in bands:
            freq = band.get("frequency", 1000)
            gain = band.get("gain", 0)
            q = band.get("q", 1.0)
            eq_filters.append(f"equalizer=f={freq}:g={gain}:q={q}")
        
        filter_chain = ",".join(eq_filters)
        
        command = [
            self.ffmpeg.ffmpeg_path,
            "-i", str(source_path),
            "-af", filter_chain,
            "-y",
            str(output_path)
        ]
        
        result = await self.ffmpeg.execute_command(command)
        
        if result["success"]:
            output_file_id = self.file_manager.register_file(output_path)
            return {
                "success": True,
                "input_file_id": file_id,
                "output_file_id": output_file_id,
                "effect_name": "equalizer",
                "parameters": parameters,
                "output_path": str(output_path),
                "bands_applied": len(bands)
            }
        else:
            return {"success": False, "error": result.get("error", "EQ processing failed")}
    
    async def process_loudness_normalize(self, file_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process loudness normalization (two-pass EBU R128)"""
        target_lufs = parameters.get("target_lufs", -16.0)
        true_peak = parameters.get("true_peak", -1.0)
        lra = parameters.get("lra", 7.0)
        
        source_path = self.file_manager.resolve_id(file_id)
        if not source_path:
            return {"success": False, "error": f"File not found: {file_id}"}
        
        output_path = SecurityConfig.TEMP_DIR / f"audio_loudnorm_{file_id}_{hash(str(parameters))}.wav"
        
        # Two-pass loudnorm for best results
        # Pass 1: Analysis
        analysis_command = [
            self.ffmpeg.ffmpeg_path,
            "-i", str(source_path),
            "-af", f"loudnorm=I={target_lufs}:TP={true_peak}:LRA={lra}:print_format=json",
            "-f", "null",
            "-"
        ]
        
        analysis_result = await self.ffmpeg.execute_command(analysis_command)
        
        if not analysis_result["success"]:
            return {"success": False, "error": "Loudness analysis failed"}
        
        # Parse analysis results (simplified for now)
        # In production, we'd parse the JSON output for precise normalization
        
        # Pass 2: Apply normalization
        normalize_command = [
            self.ffmpeg.ffmpeg_path,
            "-i", str(source_path),
            "-af", f"loudnorm=I={target_lufs}:TP={true_peak}:LRA={lra}",
            "-y",
            str(output_path)
        ]
        
        result = await self.ffmpeg.execute_command(normalize_command)
        
        if result["success"]:
            output_file_id = self.file_manager.register_file(output_path)
            return {
                "success": True,
                "input_file_id": file_id,
                "output_file_id": output_file_id,
                "effect_name": "loudness_normalize",
                "parameters": parameters,
                "output_path": str(output_path),
                "target_lufs": target_lufs,
                "true_peak_ceiling": true_peak
            }
        else:
            return {"success": False, "error": result.get("error", "Loudness normalization failed")}
    
    def get_available_effects(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get list of available audio effects"""
        effects = {}
        
        for name, effect in self.effects_registry.items():
            if category and effect.category != category:
                continue
            
            effects[name] = {
                "name": effect.name,
                "provider": effect.provider.value,
                "category": effect.category,
                "description": effect.description,
                "parameters": [asdict(param) for param in effect.parameters],
                "performance_tier": effect.performance_tier,
                "estimated_time_per_second": effect.estimated_time_per_second
            }
        
        return {
            "success": True,
            "effects_count": len(effects),
            "effects": effects,
            "categories": list(set(effect.category for effect in self.effects_registry.values()))
        }