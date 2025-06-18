from pathlib import Path
from typing import Dict, Any, Optional, List
import time

from .config import SecurityConfig
from .models import ProcessResult
from .analytics_service import get_analytics

# Forward declaration for type hints if FileManager/FFMPEGWrapper are passed as instances
# This helps with static analysis without creating circular imports at runtime.
try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from .file_manager import FileManager
    from .ffmpeg_wrapper import FFMPEGWrapper


async def execute_core_processing(
    input_file_id: str,
    operation: str,
    output_extension: str,
    params_str: str,
    file_manager: 'FileManager',
    ffmpeg: 'FFMPEGWrapper',
    user_id: str = "anonymous",
) -> ProcessResult:
    """Core logic for processing a file, extracted from the original process_file MCP tool."""
    input_path = file_manager.resolve_id(input_file_id)
    if not input_path:
        return ProcessResult(
            success=False,
            message=f"Input file ID '{input_file_id}' not found"
        )
        
    if not input_path.exists():
        return ProcessResult(
            success=False,
            message=f"Input file no longer exists: {input_path.name}"
        )
    
    if not SecurityConfig.validate_file_size(input_path):
        return ProcessResult(
            success=False,
            message=f"File too large (max {SecurityConfig.MAX_FILE_SIZE} bytes)"
        )
    
    output_file_id = None # Initialize to ensure it's always defined
    output_path = None    # Initialize to ensure it's always defined

    try:
        required_params = {
            'trim': ['start', 'duration'],
            'resize': ['width', 'height'],
            'replace_audio': ['audio_file'],
            'concatenate_simple': ['second_video'],
            'trim_and_replace_audio': ['start', 'duration', 'audio_file'],
            'image_to_video': ['duration']
        }
        
        parsed_params = {}
        if params_str:
            for param_item in params_str.split():
                if '=' in param_item:
                    key, value = param_item.split('=', 1)
                    if value.startswith('file_') and key in ['audio_file', 'second_video']:
                        file_path_resolved = file_manager.resolve_id(value)
                        if file_path_resolved and file_path_resolved.exists():
                            parsed_params[key] = str(file_path_resolved)
                        else:
                            return ProcessResult(
                                success=False,
                                message=f"File ID '{value}' not found or file does not exist"
                            )
                    else:
                        parsed_params[key] = value
        
        if operation in required_params:
            missing = [p for p in required_params[operation] if p not in parsed_params]
            if missing:
                examples = {
                    'trim': 'start=10 duration=15',
                    'resize': 'width=1280 height=720', 
                    'replace_audio': 'audio_file=file_12345678',
                    'concatenate_simple': 'second_video=file_87654321',
                    'trim_and_replace_audio': 'start=10 duration=15 audio_file=file_12345678',
                    'image_to_video': 'duration=2'
                }
                return ProcessResult(
                    success=False,
                    message=f"Missing required parameters: {missing}. Example: {examples.get(operation, '')}"
                )
        
        output_file_id, output_path = file_manager.create_temp_file(output_extension)
        
        if operation == 'concatenate_simple':
            second_video_path = Path(parsed_params['second_video'])
            command = await ffmpeg.build_smart_concat_command(input_path, second_video_path, output_path, file_manager)
        else:
            command = ffmpeg.build_command(operation, input_path, output_path, **parsed_params)
        
        # Track analytics - start timing
        start_time = time.time()
        
        ffmpeg_result = await ffmpeg.execute_command(command, SecurityConfig.PROCESS_TIMEOUT)
        
        # Track analytics - capture results
        processing_time_ms = int((time.time() - start_time) * 1000)
        analytics = get_analytics()
        if analytics:
            await analytics.track_ffmpeg_operation(
                user_id=user_id,
                operation_type=operation,
                parameters=parsed_params,
                input_path=input_path,
                output_path=output_path,
                success=ffmpeg_result["success"],
                processing_time_ms=processing_time_ms,
                error_message=ffmpeg_result.get("error") if not ffmpeg_result["success"] else None,
                platform="mcp"
            )
        
        if ffmpeg_result["success"]:
            return ProcessResult(
                success=True,
                message=f"Successfully processed {input_path.name}",
                output_file_id=output_file_id,
                logs=ffmpeg_result.get("stderr", "")
            )
        else:
            if output_path and output_path.exists(): # Check if output_path was set
                output_path.unlink(missing_ok=True)
            if output_file_id: # Check if output_file_id was set
                file_manager.invalidate_file_id(output_file_id)
            return ProcessResult(
                success=False,
                message=f"FFMPEG failed: {ffmpeg_result.get('error', 'Unknown error')}",
                logs=ffmpeg_result.get("stderr", "")
            )
            
    except ValueError as e:
        return ProcessResult(
            success=False,
            message=f"Invalid operation or parameters: {str(e)}"
        )
    except Exception as e:
        if output_path and output_path.exists():
             output_path.unlink(missing_ok=True)
        if output_file_id:
            file_manager.invalidate_file_id(output_file_id)
        return ProcessResult(
            success=False,
            message=f"Unexpected error in core processing: {str(e)}"
        )

async def process_file_internal(
    input_file_id: str,
    operation: str,
    output_extension: str,
    params_str: str,
    file_manager: 'FileManager',
    ffmpeg: 'FFMPEGWrapper',
    user_id: str = "internal"
) -> str:
    """Internal helper for processors to use core processing logic, returning file_id or raising error."""
    result_obj = await execute_core_processing(
        input_file_id, operation, output_extension, params_str, file_manager, ffmpeg, user_id
    )
    
    if result_obj.success:
        if result_obj.output_file_id is None:
             raise Exception(f"Operation {operation} succeeded but returned no output_file_id")
        return result_obj.output_file_id
    else:
        error_message = f"Operation '{operation}' failed on file '{input_file_id}'. Reason: {result_obj.message}."
        if result_obj.logs:
            error_message += f" Logs: {result_obj.logs}"
        raise Exception(error_message)

async def process_file_as_finished(
    input_file_id: str,
    operation: str,
    output_extension: str,
    params_str: str,
    file_manager: 'FileManager',
    ffmpeg: 'FFMPEGWrapper',
    title: Optional[str] = None
) -> str:
    """Process file and create output in finished directory instead of temp, returning file_id or raising error."""
    input_path = file_manager.resolve_id(input_file_id)
    if not input_path:
        raise Exception(f"Input file ID '{input_file_id}' not found")
        
    if not input_path.exists():
        raise Exception(f"Input file no longer exists: {input_path.name}")
    
    if not SecurityConfig.validate_file_size(input_path):
        raise Exception(f"File too large (max {SecurityConfig.MAX_FILE_SIZE} bytes)")
    
    parsed_params = {}
    if params_str:
        for param_item in params_str.split():
            if "=" in param_item:
                key, value = param_item.split("=", 1)
                if key in ['second_video', 'audio_file'] and value.startswith('file_'):
                    file_path_resolved = file_manager.resolve_id(value)
                    if file_path_resolved and file_path_resolved.exists():
                        parsed_params[key] = str(file_path_resolved)
                    else:
                        raise Exception(f"File ID '{value}' not found or file does not exist")
                else:
                    parsed_params[key] = value
    
    output_file_id, output_path = file_manager.create_finished_file(output_extension, title)
    
    try:
        if operation == 'concatenate_simple':
            second_video_path = Path(parsed_params['second_video'])
            command = await ffmpeg.build_smart_concat_command(input_path, second_video_path, output_path, file_manager)
        else:
            command = ffmpeg.build_command(operation, input_path, output_path, **parsed_params)
        
        ffmpeg_result = await ffmpeg.execute_command(command, SecurityConfig.PROCESS_TIMEOUT)
        
        if ffmpeg_result["success"]:
            return output_file_id
        else:
            if output_path.exists():
                output_path.unlink(missing_ok=True)
            file_manager.invalidate_file_id(output_file_id)
            error_message = f"Operation failed: {ffmpeg_result.get('message', ffmpeg_result.get('error', 'Unknown error'))}."
            if ffmpeg_result.get("stderr"):
                 error_message += f" Logs: {ffmpeg_result.get('stderr')}"
            raise Exception(error_message)
    except Exception as e:
        if output_path.exists():
            output_path.unlink(missing_ok=True)
        file_manager.invalidate_file_id(output_file_id)
        raise Exception(f"Processing file as finished failed: {str(e)}")
