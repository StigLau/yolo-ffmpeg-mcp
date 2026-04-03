import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_compatibility():
    from src.video_operations import process_file_as_finished
    from src.file_manager import FileManager  
    from src.ffmpeg_wrapper import FFMPEGWrapper
    
    file_manager = FileManager()
    ffmpeg_wrapper = FFMPEGWrapper(file_manager)
    
    # Test with our known file
    result = await process_file_as_finished(
        input_file_id="file_6f108044",  # test_video.mp4
        operation="youtube_recommended_encode", 
        output_extension="mp4",
        params_str="",
        file_manager=file_manager,
        ffmpeg=ffmpeg_wrapper,
        title="compatibility_test"
    )
    
    print(f"✅ Compatibility encoding result: {result}")
    return result

if __name__ == "__main__":
    result = asyncio.run(test_compatibility())
