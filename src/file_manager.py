from pathlib import Path
from typing import Dict, Optional, Any
import uuid
import os
import time


class FileManager:
    def __init__(self):
        self.file_map: Dict[str, Path] = {}
        self.property_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamps: Dict[str, float] = {}
        self.cache_ttl = 300  # 5 minutes cache TTL
        self.source_dir = Path("/tmp/music/source")
        self.temp_dir = Path("/tmp/music/temp")
        self.finished_dir = Path("/tmp/music/finished")
        
        # Create directories if they don't exist
        self.source_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.finished_dir.mkdir(parents=True, exist_ok=True)
        
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
        
    def create_finished_file(self, extension: str, title: str = None) -> tuple[str, Path]:
        """Create finished file and return (id, path)"""
        if not extension.startswith('.'):
            extension = f'.{extension}'
            
        if title:
            # Sanitize title for filename
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')
            finished_filename = f"{safe_title}_{uuid.uuid4().hex[:8]}{extension}"
        else:
            finished_filename = f"finished_{uuid.uuid4().hex[:8]}{extension}"
            
        finished_path = self.finished_dir / finished_filename
        
        # Create empty file
        finished_path.touch()
        
        # Register and return
        file_id = self.register_file(finished_path)
        return file_id, finished_path
        
    def _is_path_allowed(self, file_path: Path) -> bool:
        """Check if file path is within allowed directories"""
        try:
            resolved_path = file_path.resolve()
            allowed_dirs = [self.source_dir.resolve(), self.temp_dir.resolve(), self.finished_dir.resolve()]
            
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
        
    def cache_file_properties(self, file_id: str, properties: Dict[str, Any]):
        """Cache video properties for a file"""
        self.property_cache[file_id] = properties
        self.cache_timestamps[file_id] = time.time()
        
    def get_cached_properties(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get cached properties if still valid"""
        if file_id not in self.property_cache:
            return None
            
        # Check if cache is still valid
        cache_time = self.cache_timestamps.get(file_id, 0)
        if time.time() - cache_time > self.cache_ttl:
            # Cache expired, remove it
            self.property_cache.pop(file_id, None)
            self.cache_timestamps.pop(file_id, None)
            return None
            
        return self.property_cache[file_id]
        
    def invalidate_cache(self, file_id: str):
        """Remove cached properties for a file"""
        self.property_cache.pop(file_id, None)
        self.cache_timestamps.pop(file_id, None)

    def invalidate_file_id(self, file_id: str):
        """Remove a file_id from the map, typically if its creation failed or file is removed."""
        if file_id in self.file_map:
            del self.file_map[file_id]
        # Also remove from property cache if it exists
        self.property_cache.pop(file_id, None)
        self.cache_timestamps.pop(file_id, None)
        
    def cleanup_temp_files(self):
        """Remove all temporary files and their cache entries"""
        for file_id, path in list(self.file_map.items()):
            if path.parent == self.temp_dir:
                try:
                    path.unlink(missing_ok=True)
                    del self.file_map[file_id]
                    # Also clean up cache entries
                    self.invalidate_cache(file_id)
                except Exception:
                    pass
    
    def get_id_by_name(self, filename: str) -> Optional[str]:
        """Find file ID by filename in source directory"""
        try:
            # Look for file in source directory
            file_path = self.source_dir / filename
            if file_path.exists():
                # Check if already registered
                for file_id, registered_path in self.file_map.items():
                    if registered_path.samefile(file_path):
                        return file_id
                
                # Register new file
                return self.register_file(file_path)
            
            return None
        except Exception:
            return None
    
    def add_temp_file(self, file_path: Path) -> str:
        """Add temporary file to manager and return ID"""
        file_id = f"file_{uuid.uuid4().hex[:8]}"
        self.file_map[file_id] = file_path.resolve()
        return file_id
