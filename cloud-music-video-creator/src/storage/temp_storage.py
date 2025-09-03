"""
Temporary Storage Backend for Cloud Music Video Creator
Simple local file storage implementation
"""

import json
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path


class TempStorageBackend:
    """Simple local temporary storage backend"""
    
    def __init__(self, base_path: str = "/tmp/music-video-creator"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def ensure_directory(self, path: str) -> None:
        """Ensure directory exists within storage"""
        dir_path = self.base_path / path
        dir_path.mkdir(parents=True, exist_ok=True)
    
    async def write_json(self, path: str, data: Dict[str, Any]) -> None:
        """Write JSON data to file"""
        file_path = self.base_path / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use asyncio to write file (simulating async operation)
        await asyncio.sleep(0)  # Yield control
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    async def read_json(self, path: str) -> Optional[Dict[str, Any]]:
        """Read JSON data from file"""
        file_path = self.base_path / path
        
        if not file_path.exists():
            return None
        
        # Use asyncio to read file (simulating async operation)
        await asyncio.sleep(0)  # Yield control
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading JSON file {file_path}: {e}")
            return None
    
    async def delete_file(self, path: str) -> bool:
        """Delete file"""
        file_path = self.base_path / path
        
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            return False
    
    async def list_files(self, path: str) -> list:
        """List files in directory"""
        dir_path = self.base_path / path
        
        if not dir_path.exists():
            return []
        
        try:
            return [f.name for f in dir_path.iterdir() if f.is_file()]
        except Exception as e:
            print(f"Error listing files in {dir_path}: {e}")
            return []
    
    def get_full_path(self, path: str) -> str:
        """Get full filesystem path"""
        return str(self.base_path / path)