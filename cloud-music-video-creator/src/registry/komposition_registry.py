"""
Komposition Registry for Cloud Music Video Creator
Manages komposition lifecycle, storage, and retrieval
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..models.komposition import Komposition, KompositionSpec, ProcessingStatus
from ..storage.temp_storage import TempStorageBackend


class KompositionRegistry:
    """Registry for managing kompositions with storage backend"""
    
    def __init__(self, storage_backend: TempStorageBackend):
        self.storage = storage_backend
        self.registry_path = "kompositions"
        
        # Ensure registry directory exists
        self.storage.ensure_directory(self.registry_path)
    
    async def create(self, spec: KompositionSpec, user_id: str) -> Komposition:
        """Create new komposition from specification"""
        komposition_id = f"komp_{uuid.uuid4().hex[:8]}"
        
        komposition = Komposition(
            id=komposition_id,
            title=spec.title,
            description=spec.description,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            bpm=spec.bpm,
            total_beats=(spec.bpm * spec.duration_seconds) / 60.0,
            duration_seconds=spec.duration_seconds,
            resolution=spec.resolution,
            status=ProcessingStatus.DRAFT,
            segments=[],
            generated_videos=[]
        )
        
        # Store komposition
        await self._save_komposition(komposition)
        
        return komposition
    
    async def get(self, komposition_id: str) -> Optional[Komposition]:
        """Retrieve komposition by ID"""
        try:
            komposition_path = f"{self.registry_path}/{komposition_id}.json"
            data = await self.storage.read_json(komposition_path)
            
            if data:
                # Update last accessed time
                komposition = Komposition.parse_obj(data)
                return komposition
            
            return None
            
        except Exception as e:
            print(f"Error retrieving komposition {komposition_id}: {e}")
            return None
    
    async def update(self, komposition_id: str, updates: Dict[str, Any]) -> Komposition:
        """Update existing komposition"""
        komposition = await self.get(komposition_id)
        
        if not komposition:
            raise ValueError(f"Komposition {komposition_id} not found")
        
        # Update fields
        for field, value in updates.items():
            if hasattr(komposition, field):
                setattr(komposition, field, value)
        
        komposition.updated_at = datetime.utcnow()
        
        # Save updated komposition
        await self._save_komposition(komposition)
        
        return komposition
    
    async def list_user_kompositions(self, user_id: str) -> List[Komposition]:
        """List all kompositions for a user"""
        kompositions = []
        
        # List all komposition files
        registry_dir = Path(self.storage.base_path) / self.registry_path
        
        if registry_dir.exists():
            for json_file in registry_dir.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    if data.get('user_id') == user_id:
                        komposition = Komposition.parse_obj(data)
                        kompositions.append(komposition)
                        
                except Exception as e:
                    print(f"Error reading komposition file {json_file}: {e}")
                    continue
        
        # Sort by created_at descending
        kompositions.sort(key=lambda k: k.created_at, reverse=True)
        
        return kompositions
    
    async def delete(self, komposition_id: str) -> bool:
        """Delete komposition"""
        try:
            komposition_path = f"{self.registry_path}/{komposition_id}.json"
            return await self.storage.delete_file(komposition_path)
            
        except Exception as e:
            print(f"Error deleting komposition {komposition_id}: {e}")
            return False
    
    async def count(self) -> int:
        """Count total kompositions"""
        registry_dir = Path(self.storage.base_path) / self.registry_path
        
        if registry_dir.exists():
            return len(list(registry_dir.glob("*.json")))
        
        return 0
    
    async def _save_komposition(self, komposition: Komposition) -> None:
        """Save komposition to storage"""
        komposition_path = f"{self.registry_path}/{komposition.id}.json"
        
        # Convert to dict and save
        data = komposition.dict()
        
        # Handle datetime serialization
        data['created_at'] = komposition.created_at.isoformat()
        data['updated_at'] = komposition.updated_at.isoformat()
        
        await self.storage.write_json(komposition_path, data)
    
    async def cleanup_expired(self, hours: int = 24) -> int:
        """Clean up old kompositions"""
        # For temp storage, clean up old draft kompositions
        cleaned_count = 0
        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
        
        registry_dir = Path(self.storage.base_path) / self.registry_path
        
        if registry_dir.exists():
            for json_file in registry_dir.glob("*.json"):
                try:
                    # Check file modification time
                    if json_file.stat().st_mtime < cutoff_time:
                        # Load and check if it's a draft
                        with open(json_file, 'r') as f:
                            data = json.load(f)
                        
                        if data.get('status') == ProcessingStatus.DRAFT:
                            json_file.unlink()
                            cleaned_count += 1
                            
                except Exception as e:
                    print(f"Error during cleanup of {json_file}: {e}")
                    continue
        
        return cleaned_count