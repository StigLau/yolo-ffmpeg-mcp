"""
Professional Video Effects Processor
Handles FFmpeg-based and OpenCV-based video effects with preset management
"""

import json
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

class EffectProvider(Enum):
    FFMPEG = "ffmpeg"
    OPENCV = "opencv"
    PIL = "pil"

@dataclass
class EffectParameter:
    name: str
    type: str  # "float", "int", "str", "bool"
    default: Union[float, int, str, bool]
    min_value: Optional[Union[float, int]] = None
    max_value: Optional[Union[float, int]] = None
    description: str = ""
    options: Optional[List[str]] = None  # For enum parameters

@dataclass
class EffectDefinition:
    name: str
    provider: EffectProvider
    category: str  # "color", "stylistic", "blur", "distortion", "transition"
    description: str
    parameters: List[EffectParameter]
    filter_chain: Optional[str] = None  # FFmpeg filter chain
    processing_function: Optional[str] = None  # Python function name for non-FFmpeg
    performance_tier: str = "fast"  # "fast", "medium", "slow"
    estimated_time_per_second: float = 0.1  # seconds of processing per second of video

class EffectProcessor:
    """Core video effects processing engine"""
    
    def __init__(self, ffmpeg_wrapper: FFMPEGWrapper, file_manager: FileManager):
        self.ffmpeg = ffmpeg_wrapper
        self.file_manager = file_manager
        self.effects_registry: Dict[str, EffectDefinition] = {}
        self.presets_dir = Path(__file__).parent.parent / "presets"
        self.presets_dir.mkdir(exist_ok=True)
        self._load_effects()
        
    def _load_effects(self):
        """Load effect definitions from presets and built-in definitions"""
        # Load built-in effects
        self._register_builtin_effects()
        
        # Load external presets if available
        effects_file = self.presets_dir / "effects.json"
        if effects_file.exists():
            try:
                with open(effects_file, 'r') as f:
                    external_effects = json.load(f)
                    self._register_external_effects(external_effects)
            except Exception as e:
                logger.warning(f"Failed to load external effects: {e}")
    
    def _register_builtin_effects(self):
        """Register built-in video effects"""
        
        # FFmpeg Color Grading Effects
        self.effects_registry["vintage_color"] = EffectDefinition(
            name="vintage_color",
            provider=EffectProvider.FFMPEG,
            category="color",
            description="Warm vintage film look with reduced saturation",
            parameters=[
                EffectParameter("intensity", "float", 1.0, 0.0, 2.0, "Effect intensity"),
                EffectParameter("warmth", "float", 0.2, -0.5, 0.5, "Color temperature adjustment"),
                EffectParameter("saturation", "float", 0.85, 0.0, 2.0, "Color saturation")
            ],
            filter_chain="eq=saturation={saturation}:contrast=1.1,colorbalance=rs={warmth}:rh={warmth}",
            performance_tier="fast",
            estimated_time_per_second=0.05
        )
        
        self.effects_registry["film_noir"] = EffectDefinition(
            name="film_noir",
            provider=EffectProvider.FFMPEG,
            category="color",
            description="High contrast black and white cinematic look",
            parameters=[
                EffectParameter("contrast", "float", 2.0, 1.0, 3.0, "Contrast intensity"),
                EffectParameter("brightness", "float", -0.1, -0.5, 0.5, "Brightness adjustment")
            ],
            filter_chain="eq=saturation=0.1:contrast={contrast}:brightness={brightness},curves=all='0/0 0.3/0.1 0.7/0.9 1/1'",
            performance_tier="fast",
            estimated_time_per_second=0.08
        )
        
        # FFmpeg Stylistic Effects
        self.effects_registry["vhs_look"] = EffectDefinition(
            name="vhs_look",
            provider=EffectProvider.FFMPEG,
            category="stylistic",
            description="Retro VHS tape aesthetic with analog distortion",
            parameters=[
                EffectParameter("noise_level", "float", 7.0, 0.0, 20.0, "Analog noise intensity"),
                EffectParameter("blur_amount", "float", 0.4, 0.0, 2.0, "Blur softness"),
                EffectParameter("saturation", "float", 0.85, 0.0, 2.0, "Color saturation")
            ],
            filter_chain="scale=640:480,setsar=1,eq=saturation={saturation}:contrast=1.1,noise=alls={noise_level},gblur=sigma={blur_amount}",
            performance_tier="medium",
            estimated_time_per_second=0.2
        )
        
        self.effects_registry["gaussian_blur"] = EffectDefinition(
            name="gaussian_blur",
            provider=EffectProvider.FFMPEG,
            category="blur",
            description="Smooth Gaussian blur effect",
            parameters=[
                EffectParameter("sigma", "float", 5.0, 0.1, 20.0, "Blur radius"),
                EffectParameter("steps", "int", 1, 1, 10, "Processing steps for quality")
            ],
            filter_chain="gblur=sigma={sigma}:steps={steps}",
            performance_tier="fast",
            estimated_time_per_second=0.1
        )
        
        self.effects_registry["vignette"] = EffectDefinition(
            name="vignette",
            provider=EffectProvider.FFMPEG,
            category="stylistic",
            description="Dark vignette around edges for cinematic feel",
            parameters=[
                EffectParameter("angle", "float", 1.57, 0.0, 6.28, "Vignette shape angle"),
                EffectParameter("x0", "float", 0.5, 0.0, 1.0, "Center X position"),
                EffectParameter("y0", "float", 0.5, 0.0, 1.0, "Center Y position"),
                EffectParameter("mode", "str", "forward", description="Vignette mode", 
                             options=["forward", "backward"])
            ],
            filter_chain="vignette=angle={angle}:x0={x0}:y0={y0}:mode={mode}",
            performance_tier="fast",
            estimated_time_per_second=0.03
        )
        
        # OpenCV/PIL Effects (processed via Python)
        self.effects_registry["face_blur"] = EffectDefinition(
            name="face_blur",
            provider=EffectProvider.OPENCV,
            category="privacy",
            description="Automatically detect and blur faces for privacy",
            parameters=[
                EffectParameter("blur_strength", "float", 15.0, 5.0, 50.0, "Blur intensity"),
                EffectParameter("detection_confidence", "float", 0.7, 0.3, 0.95, "Face detection threshold")
            ],
            processing_function="process_face_blur",
            performance_tier="slow",
            estimated_time_per_second=2.0
        )
        
        self.effects_registry["chromatic_aberration"] = EffectDefinition(
            name="chromatic_aberration",
            provider=EffectProvider.PIL,
            category="distortion",
            description="RGB channel separation for glitch/vintage effect",
            parameters=[
                EffectParameter("red_offset_x", "int", 3, -10, 10, "Red channel X offset"),
                EffectParameter("red_offset_y", "int", 0, -10, 10, "Red channel Y offset"),
                EffectParameter("blue_offset_x", "int", -3, -10, 10, "Blue channel X offset"),
                EffectParameter("blue_offset_y", "int", 0, -10, 10, "Blue channel Y offset"),
                EffectParameter("intensity", "float", 1.0, 0.0, 2.0, "Overall effect intensity")
            ],
            processing_function="process_chromatic_aberration",
            performance_tier="medium",
            estimated_time_per_second=0.5
        )
        
        # Additional effects to match API
        self.effects_registry["social_media_pack"] = EffectDefinition(
            name="social_media_pack",
            provider=EffectProvider.FFMPEG,
            category="stylistic",
            description="Optimized effects pack for social media content with increased saturation and contrast",
            parameters=[
                EffectParameter("saturation", "float", 1.3, 0.5, 2.0, "Color saturation boost"),
                EffectParameter("contrast", "float", 1.2, 0.8, 2.0, "Contrast enhancement"),
                EffectParameter("brightness", "float", 0.05, -0.2, 0.2, "Brightness adjustment"),
                EffectParameter("sharpness", "float", 0.8, 0.0, 2.0, "Sharpening intensity")
            ],
            filter_chain="eq=saturation={saturation}:contrast={contrast}:brightness={brightness},unsharp=5:5:{sharpness}:5:5:0.0",
            performance_tier="fast",
            estimated_time_per_second=0.1
        )
        
        self.effects_registry["warm_cinematic"] = EffectDefinition(
            name="warm_cinematic",
            provider=EffectProvider.FFMPEG,
            category="color",
            description="Warm cinematic look with orange/teal color grading",
            parameters=[
                EffectParameter("orange_push", "float", 0.1, -0.3, 0.3, "Orange tint in shadows"),
                EffectParameter("midtone_warmth", "float", 0.05, -0.2, 0.2, "Midtone warmth"),
                EffectParameter("highlight_cool", "float", -0.05, -0.2, 0.2, "Cool highlights"),
                EffectParameter("saturation", "float", 1.1, 0.0, 2.0, "Overall saturation"),
                EffectParameter("contrast", "float", 1.05, 0.5, 2.0, "Contrast adjustment")
            ],
            filter_chain="eq=saturation={saturation}:contrast={contrast},colorbalance=rs={orange_push}:rm={midtone_warmth}:rh={highlight_cool}",
            performance_tier="fast",
            estimated_time_per_second=0.08
        )
        
        self.effects_registry["glitch_aesthetic"] = EffectDefinition(
            name="glitch_aesthetic",
            provider=EffectProvider.FFMPEG,
            category="distortion",
            description="Digital glitch effect with noise and RGB separation",
            parameters=[
                EffectParameter("noise_strength", "float", 15.0, 0.0, 50.0, "Digital noise intensity"),
                EffectParameter("red_shift", "int", 3, -10, 10, "Red channel horizontal shift"),
                EffectParameter("blue_shift", "int", -3, -10, 10, "Blue channel horizontal shift")
            ],
            filter_chain="noise=alls={noise_strength},rgbashift=rh={red_shift}:bh={blue_shift}",
            performance_tier="medium",
            estimated_time_per_second=0.3
        )
        
        self.effects_registry["dreamy_soft"] = EffectDefinition(
            name="dreamy_soft",
            provider=EffectProvider.FFMPEG,
            category="stylistic",
            description="Soft dreamy effect with gentle blur and brightness",
            parameters=[
                EffectParameter("blur_sigma", "float", 1.5, 0.1, 5.0, "Soft blur amount"),
                EffectParameter("brightness", "float", 0.1, -0.3, 0.3, "Dreamy brightness boost"),
                EffectParameter("saturation", "float", 0.9, 0.0, 2.0, "Subtle desaturation"),
                EffectParameter("negative_sharpen", "float", -0.3, -1.0, 1.0, "Reverse sharpening for softness")
            ],
            filter_chain="gblur=sigma={blur_sigma},eq=saturation={saturation}:brightness={brightness},unsharp=5:5:{negative_sharpen}:5:5:0.0",
            performance_tier="medium",
            estimated_time_per_second=0.2
        )
        
        self.effects_registry["horror_desaturated"] = EffectDefinition(
            name="horror_desaturated",
            provider=EffectProvider.FFMPEG,
            category="color",
            description="Horror movie aesthetic with desaturation and cool tones",
            parameters=[
                EffectParameter("saturation", "float", 0.3, 0.0, 1.0, "Heavy desaturation"),
                EffectParameter("contrast", "float", 1.4, 1.0, 2.5, "High contrast"),
                EffectParameter("brightness", "float", -0.1, -0.5, 0.0, "Darker overall tone"),
                EffectParameter("shadow_cool", "float", -0.1, -0.3, 0.0, "Cool shadows"),
                EffectParameter("midtone_cool", "float", -0.05, -0.2, 0.0, "Cool midtones"),
                EffectParameter("highlight_cool", "float", -0.03, -0.2, 0.0, "Cool highlights")
            ],
            filter_chain="eq=saturation={saturation}:contrast={contrast}:brightness={brightness},colorbalance=rs={shadow_cool}:rm={midtone_cool}:rh={highlight_cool}",
            performance_tier="fast",
            estimated_time_per_second=0.12
        )
    
    def _register_external_effects(self, effects_data: Dict[str, Any]):
        """Register effects from external JSON configuration"""
        for effect_name, effect_config in effects_data.items():
            try:
                parameters = []
                for param_name, param_config in effect_config.get("parameters", {}).items():
                    parameters.append(EffectParameter(
                        name=param_name,
                        type=param_config.get("type", "float"),
                        default=param_config.get("default", 1.0),
                        min_value=param_config.get("min"),
                        max_value=param_config.get("max"),
                        description=param_config.get("description", ""),
                        options=param_config.get("options")
                    ))
                
                self.effects_registry[effect_name] = EffectDefinition(
                    name=effect_name,
                    provider=EffectProvider(effect_config.get("provider", "ffmpeg")),
                    category=effect_config.get("category", "stylistic"),
                    description=effect_config.get("description", ""),
                    parameters=parameters,
                    filter_chain=effect_config.get("filter_chain"),
                    processing_function=effect_config.get("processing_function"),
                    performance_tier=effect_config.get("performance_tier", "medium"),
                    estimated_time_per_second=effect_config.get("estimated_time_per_second", 0.1)
                )
            except Exception as e:
                logger.warning(f"Failed to register effect {effect_name}: {e}")
    
    def get_available_effects(self, category: Optional[str] = None, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get list of available effects with their parameters"""
        effects = {}
        
        for name, effect in self.effects_registry.items():
            # Filter by category if specified
            if category and effect.category != category:
                continue
                
            # Filter by provider if specified
            if provider and effect.provider.value != provider:
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
            "categories": list(set(effect.category for effect in self.effects_registry.values())),
            "providers": list(set(effect.provider.value for effect in self.effects_registry.values()))
        }
    
    async def apply_effect(self, file_id: str, effect_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Apply a single effect to a video file"""
        if effect_name not in self.effects_registry:
            return {
                "success": False,
                "error": f"Effect '{effect_name}' not found",
                "available_effects": list(self.effects_registry.keys())
            }
        
        effect = self.effects_registry[effect_name]
        parameters = parameters or {}
        
        # Validate and set default parameters
        validated_params = self._validate_parameters(effect, parameters)
        if "error" in validated_params:
            return {"success": False, **validated_params}
        
        try:
            if effect.provider == EffectProvider.FFMPEG:
                return await self._apply_ffmpeg_effect(file_id, effect, validated_params["parameters"])
            elif effect.provider in [EffectProvider.OPENCV, EffectProvider.PIL]:
                return await self._apply_python_effect(file_id, effect, validated_params["parameters"])
            else:
                return {"success": False, "error": f"Unsupported provider: {effect.provider.value}"}
                
        except Exception as e:
            logger.error(f"Error applying effect {effect_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def apply_effect_chain(self, file_id: str, effects_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply multiple effects in sequence"""
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
    
    def _validate_parameters(self, effect: EffectDefinition, parameters: Dict[str, Any]) -> Dict[str, Any]:
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
            
            elif param.type == "str":
                if param.options and value not in param.options:
                    return {"error": f"Invalid option for parameter '{param.name}': {value}. Options: {param.options}"}
            
            elif param.type == "bool":
                value = bool(value)
            
            validated[param.name] = value
        
        return {"parameters": validated}
    
    async def _apply_ffmpeg_effect(self, file_id: str, effect: EffectDefinition, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply FFmpeg-based effect"""
        # Get source file path
        source_path = self.file_manager.resolve_id(file_id)
        if not source_path:
            return {"success": False, "error": f"File not found: {file_id}"}
        
        # Generate output file
        output_path = SecurityConfig.TEMP_DIR / f"effect_{effect.name}_{file_id}_{hash(str(parameters))}.mp4"
        
        # Build filter chain with parameters
        filter_chain = effect.filter_chain
        for param_name, param_value in parameters.items():
            filter_chain = filter_chain.replace(f"{{{param_name}}}", str(param_value))
        
        # Execute FFmpeg command
        command = [
            self.ffmpeg.ffmpeg_path,
            "-i", str(source_path),
            "-vf", filter_chain,
            "-c:a", "copy",  # Copy audio stream unchanged
            "-y",
            str(output_path)
        ]
        result = await self.ffmpeg.execute_command(command)
        
        if result["success"]:
            # Register output file
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
    
    async def _apply_python_effect(self, file_id: str, effect: EffectDefinition, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Python-based effect (OpenCV/PIL)"""
        if not effect.processing_function:
            return {"success": False, "error": f"No processing function defined for effect {effect.name}"}
        
        # Get processing function
        processing_func = getattr(self, effect.processing_function, None)
        if not processing_func:
            return {"success": False, "error": f"Processing function not found: {effect.processing_function}"}
        
        try:
            result = await processing_func(file_id, parameters)
            return result
        except Exception as e:
            logger.error(f"Error in Python effect processing: {e}")
            return {"success": False, "error": str(e)}
    
    async def process_face_blur(self, file_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """OpenCV-based face detection and blurring"""
        try:
            import cv2
            import numpy as np
        except ImportError:
            return {"success": False, "error": "OpenCV not available. Install with: pip install opencv-python"}
        
        source_path = self.file_manager.resolve_id(file_id)
        if not source_path:
            return {"success": False, "error": f"File not found: {file_id}"}
        
        output_path = SecurityConfig.TEMP_DIR / f"face_blur_{file_id}.mp4"
        
        # Load face cascade classifier
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Open video
        cap = cv2.VideoCapture(str(source_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        blur_strength = int(parameters.get("blur_strength", 15))
        confidence = parameters.get("detection_confidence", 0.7)
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            # Blur detected faces
            for (x, y, w, h) in faces:
                # Extract face region
                face_region = frame[y:y+h, x:x+w]
                # Apply blur
                blurred_face = cv2.GaussianBlur(face_region, (blur_strength, blur_strength), 0)
                # Replace face region with blurred version
                frame[y:y+h, x:x+w] = blurred_face
            
            out.write(frame)
            frame_count += 1
        
        cap.release()
        out.release()
        
        # Register output file
        output_file_id = self.file_manager.register_file(output_path)
        
        return {
            "success": True,
            "input_file_id": file_id,
            "output_file_id": output_file_id,
            "effect_name": "face_blur",
            "parameters": parameters,
            "output_path": str(output_path),
            "faces_detected": len(faces) if 'faces' in locals() else 0,
            "frames_processed": frame_count
        }
    
    async def process_chromatic_aberration(self, file_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """PIL-based chromatic aberration effect"""
        try:
            from PIL import Image, ImageChops
            import cv2
            import numpy as np
        except ImportError:
            return {"success": False, "error": "PIL or OpenCV not available"}
        
        source_path = self.file_manager.resolve_id(file_id)
        if not source_path:
            return {"success": False, "error": f"File not found: {file_id}"}
        
        output_path = SecurityConfig.TEMP_DIR / f"chromatic_{file_id}.mp4"
        
        # Open video with OpenCV
        cap = cv2.VideoCapture(str(source_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        # Get parameters
        red_offset_x = parameters.get("red_offset_x", 3)
        red_offset_y = parameters.get("red_offset_y", 0) 
        blue_offset_x = parameters.get("blue_offset_x", -3)
        blue_offset_y = parameters.get("blue_offset_y", 0)
        intensity = parameters.get("intensity", 1.0)
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert BGR to RGB for PIL
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            
            # Split into RGB channels
            r, g, b = pil_image.split()
            
            # Create shifted channels
            r_shifted = ImageChops.offset(r, int(red_offset_x * intensity), int(red_offset_y * intensity))
            b_shifted = ImageChops.offset(b, int(blue_offset_x * intensity), int(blue_offset_y * intensity))
            
            # Merge channels back
            aberrated = Image.merge('RGB', (r_shifted, g, b_shifted))
            
            # Convert back to BGR for OpenCV
            frame_aberrated = cv2.cvtColor(np.array(aberrated), cv2.COLOR_RGB2BGR)
            
            out.write(frame_aberrated)
            frame_count += 1
        
        cap.release()
        out.release()
        
        # Register output file
        output_file_id = self.file_manager.register_file(output_path)
        
        return {
            "success": True,
            "input_file_id": file_id,
            "output_file_id": output_file_id,
            "effect_name": "chromatic_aberration",
            "parameters": parameters,
            "output_path": str(output_path),
            "frames_processed": frame_count
        }

    def estimate_processing_time(self, file_id: str, effects_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate total processing time for effects chain"""
        # Get video duration
        source_path = self.file_manager.resolve_id(file_id)
        if not source_path:
            return {"success": False, "error": f"File not found: {file_id}"}
        
        try:
            import subprocess
            result = subprocess.run([
                "ffprobe", "-v", "quiet", "-print_format", "json", "-show_format",
                str(source_path)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                import json
                metadata = json.loads(result.stdout)
                duration = float(metadata["format"]["duration"])
            else:
                duration = 30.0  # Default estimate
        except:
            duration = 30.0
        
        total_time = 0.0
        effect_estimates = []
        
        for effect_step in effects_chain:
            effect_name = effect_step.get("effect")
            if effect_name in self.effects_registry:
                effect = self.effects_registry[effect_name]
                processing_time = duration * effect.estimated_time_per_second
                total_time += processing_time
                
                effect_estimates.append({
                    "effect": effect_name,
                    "estimated_seconds": processing_time,
                    "performance_tier": effect.performance_tier
                })
        
        return {
            "success": True,
            "video_duration": duration,
            "total_estimated_time": total_time,
            "effect_estimates": effect_estimates,
            "time_per_effect": total_time / len(effects_chain) if effects_chain else 0
        }