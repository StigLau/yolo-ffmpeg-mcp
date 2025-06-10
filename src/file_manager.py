from pathlib import Path
from typing import Dict, Optional
import uuid
import os


class FileManager:
    def __init__(self):
        self.file_map: Dict[str, Path] = {}
        self.source_dir = Path("/tmp/music/source")
        self.temp_dir = Path("/tmp/music/temp")
        
        # Create directories if they don't exist
        self.source_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
    def register_file(self, file_path: str | Path) -> str:
        """Register a file and return its ID reference"""
        file_path = Path(file_path)
        
        # Validate file exists
        if not file_path.exists():
            raise ValueError(f"File does not exist: {file_path}")
            
        # Validate file is in allowed directory
        if not self._is_path_allowed(file_path):
            raise ValueError(f"File path not allowed: {file_path}")
            
        # Generate unique ID
        file_id = f"file_{uuid.uuid4().hex[:8]}"
        
        # Add to mapping
        self.file_map[file_id] = file_path.resolve()
        
        return file_id
        
    def resolve_id(self, file_id: str) -> Optional[Path]:
        """Convert ID reference to actual path"""
        return self.file_map.get(file_id)
        
    def create_temp_file(self, extension: str) -> tuple[str, Path]:
        """Create temporary file and return (id, path)"""
        if not extension.startswith('.'):
            extension = f'.{extension}'
            
        temp_filename = f"temp_{uuid.uuid4().hex[:8]}{extension}"
        temp_path = self.temp_dir / temp_filename
        
        # Create empty file
        temp_path.touch()
        
        # Register and return
        file_id = self.register_file(temp_path)
        return file_id, temp_path
        
    def _is_path_allowed(self, file_path: Path) -> bool:
        """Check if file path is within allowed directories"""
        try:
            resolved_path = file_path.resolve()
            allowed_dirs = [self.source_dir.resolve(), self.temp_dir.resolve()]
            
            return any(
                resolved_path.is_relative_to(allowed_dir) 
                for allowed_dir in allowed_dirs
            )
        except Exception:
            return False
            
    def validate_file_extension(self, file_path: Path) -> bool:
        """Validate file has allowed extension"""
        allowed_extensions = {'.mp3', '.mp4', '.wav', '.flac', '.m4a', '.avi', '.mkv', '.mov', '.webm'}
        return file_path.suffix.lower() in allowed_extensions
        
    def cleanup_temp_files(self):
        """Remove all temporary files"""
        for file_id, path in list(self.file_map.items()):
            if path.parent == self.temp_dir:
                try:
                    path.unlink(missing_ok=True)
                    del self.file_map[file_id]
                except Exception:
                    pass