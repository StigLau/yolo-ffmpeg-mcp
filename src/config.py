from pathlib import Path
import os


class SecurityConfig:
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        # Video formats
        '.mp4', '.avi', '.mkv', '.mov', '.webm', '.wmv', '.flv', '.m4v',
        # Audio formats  
        '.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac', '.wma',
        # Image formats
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'
    }
    
    # Maximum file size (500MB)
    MAX_FILE_SIZE = 500 * 1024 * 1024
    
    # Process timeout (5 minutes)
    PROCESS_TIMEOUT = 300
    
    # Resource limits
    MEMORY_LIMIT = "512M"
    CPU_LIMIT = "1.0"
    
    # Directory configuration
    SOURCE_DIR = Path(os.getenv("FFMPEG_SOURCE_DIR", "/tmp/music/source"))
    TEMP_DIR = Path(os.getenv("FFMPEG_TEMP_DIR", "/tmp/music/temp"))
    FINISHED_DIR = Path(os.getenv("FFMPEG_FINISHED_DIR", "/tmp/music/finished"))
    SCREENSHOTS_DIR = Path(os.getenv("FFMPEG_SCREENSHOTS_DIR", "/tmp/music/screenshots"))
    METADATA_DIR = Path(os.getenv("FFMPEG_METADATA_DIR", "/tmp/music/metadata"))
    
    # Screenshot URL configuration
    SCREENSHOTS_BASE_URL = os.getenv("SCREENSHOTS_BASE_URL", "https://kompo.st/screenshots")
    
    # FFMPEG binary path
    FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")
    
    @classmethod
    def validate_file_size(cls, file_path: Path) -> bool:
        """Check if file size is within limits"""
        try:
            return file_path.stat().st_size <= cls.MAX_FILE_SIZE
        except Exception:
            return False
            
    @classmethod
    def validate_extension(cls, file_path: Path) -> bool:
        """Check if file extension is allowed"""
        return file_path.suffix.lower() in cls.ALLOWED_EXTENSIONS