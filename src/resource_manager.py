"""
Resource Manager for FFMPEG MCP Server

Comprehensive resource tracking, caching, and recovery system that maintains
file mappings across server restarts and provides intelligent cache invalidation.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime, timedelta
import os
import time
from dataclasses import dataclass, asdict
from collections import defaultdict

try:
    from .deterministic_id_generator import DeterministicIDGenerator, CacheKeyGenerator
except ImportError:
    from deterministic_id_generator import DeterministicIDGenerator, CacheKeyGenerator


@dataclass
class FileResource:
    """Represents a tracked file resource"""
    file_id: str
    path: str
    type: str  # 'source', 'generated', 'metadata', 'screenshot'
    size: int
    created: float
    modified: float
    checksum: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


@dataclass
class OperationRecord:
    """Represents a completed operation"""
    operation_id: str
    operation: str
    input_files: List[str]
    output_file: str
    parameters: Dict[str, Any]
    timestamp: float
    duration: float


class ResourceRegistry:
    """Persistent file registry with dependency tracking"""
    
    def __init__(self, registry_path: str = "/tmp/music/metadata/file_registry.json"):
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.source_files: Dict[str, FileResource] = {}
        self.generated_files: Dict[str, FileResource] = {}
        self.metadata_files: Dict[str, FileResource] = {}
        self.dependencies: Dict[str, List[str]] = {}  # file_id -> [parent_file_ids]
        self.operations: Dict[str, OperationRecord] = {}
        
        self.load_registry()
    
    def load_registry(self):
        """Load registry from disk"""
        if not self.registry_path.exists():
            return
        
        try:
            with open(self.registry_path, 'r') as f:
                data = json.load(f)
            
            # Load file resources
            for file_id, file_data in data.get('source_files', {}).items():
                self.source_files[file_id] = FileResource(**file_data)
            
            for file_id, file_data in data.get('generated_files', {}).items():
                self.generated_files[file_id] = FileResource(**file_data)
                
            for file_id, file_data in data.get('metadata_files', {}).items():
                self.metadata_files[file_id] = FileResource(**file_data)
            
            # Load dependencies and operations
            self.dependencies = data.get('dependencies', {})
            
            for op_id, op_data in data.get('operations', {}).items():
                self.operations[op_id] = OperationRecord(**op_data)
                
        except Exception as e:
            print(f"Warning: Failed to load registry: {e}")
    
    def save_registry(self):
        """Save registry to disk"""
        data = {
            'version': '1.0',
            'last_updated': datetime.now().isoformat(),
            'source_files': {fid: asdict(f) for fid, f in self.source_files.items()},
            'generated_files': {fid: asdict(f) for fid, f in self.generated_files.items()},
            'metadata_files': {fid: asdict(f) for fid, f in self.metadata_files.items()},
            'dependencies': self.dependencies,
            'operations': {oid: asdict(op) for oid, op in self.operations.items()}
        }
        
        # Atomic write
        temp_path = self.registry_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=2)
        temp_path.replace(self.registry_path)
    
    def register_source_file(self, filename: str, path: Path) -> str:
        """Register a source file and return its deterministic ID"""
        file_id = DeterministicIDGenerator.source_file_id(filename)
        
        file_stat = path.stat()
        resource = FileResource(
            file_id=file_id,
            path=str(path),
            type='source',
            size=file_stat.st_size,
            created=file_stat.st_ctime,
            modified=file_stat.st_mtime
        )
        
        self.source_files[file_id] = resource
        self.save_registry()
        return file_id
    
    def register_generated_file(self, file_id: str, path: Path, operation: str, 
                              input_files: List[str], parameters: Dict[str, Any]) -> str:
        """Register a generated file with its operation history"""
        file_stat = path.stat()
        resource = FileResource(
            file_id=file_id,
            path=str(path),
            type='generated',
            size=file_stat.st_size,
            created=file_stat.st_ctime,
            modified=file_stat.st_mtime
        )
        
        self.generated_files[file_id] = resource
        self.dependencies[file_id] = input_files
        
        # Record operation
        operation_record = OperationRecord(
            operation_id=f"op_{int(time.time())}_{file_id}",
            operation=operation,
            input_files=input_files,
            output_file=file_id,
            parameters=parameters,
            timestamp=time.time(),
            duration=0.0  # TODO: Track actual duration
        )
        self.operations[operation_record.operation_id] = operation_record
        
        self.save_registry()
        return file_id
    
    def get_file_resource(self, file_id: str) -> Optional[FileResource]:
        """Get file resource by ID"""
        return (self.source_files.get(file_id) or 
                self.generated_files.get(file_id) or 
                self.metadata_files.get(file_id))
    
    def get_dependencies(self, file_id: str) -> List[str]:
        """Get all files that this file depends on"""
        return self.dependencies.get(file_id, [])
    
    def get_dependents(self, file_id: str) -> List[str]:
        """Get all files that depend on this file"""
        dependents = []
        for dependent_id, deps in self.dependencies.items():
            if file_id in deps:
                dependents.append(dependent_id)
        return dependents
    
    def check_effect_cache(self, input_ids: List[str], operation: str, 
                          parameters: Dict[str, Any]) -> Optional[str]:
        """Check if identical effect operation result exists"""
        effect_id = DeterministicIDGenerator.effect_file_id(input_ids, operation, parameters)
        
        if effect_id in self.generated_files:
            resource = self.generated_files[effect_id]
            # Verify file still exists on disk
            if Path(resource.path).exists():
                # Verify input files haven't changed
                if self._verify_input_integrity(input_ids):
                    return effect_id
            else:
                # File missing - remove from registry
                self.remove_generated_file(effect_id)
        
        return None
    
    def _verify_input_integrity(self, input_ids: List[str]) -> bool:
        """Verify that input files haven't changed since cached result was created"""
        for input_id in input_ids:
            resource = self.get_file_resource(input_id)
            if not resource:
                return False
            
            path = Path(resource.path)
            if not path.exists():
                return False
            
            # Check if file has been modified
            current_mtime = path.stat().st_mtime
            if current_mtime > resource.modified:
                return False
        
        return True
    
    def remove_generated_file(self, file_id: str):
        """Remove generated file from registry"""
        if file_id in self.generated_files:
            del self.generated_files[file_id]
        if file_id in self.dependencies:
            del self.dependencies[file_id]
        
        # Remove operations that produced this file
        ops_to_remove = [op_id for op_id, op in self.operations.items() 
                        if op.output_file == file_id]
        for op_id in ops_to_remove:
            del self.operations[op_id]
        
        self.save_registry()


class CacheManager:
    """Manages caching and invalidation across the resource system"""
    
    def __init__(self, registry: ResourceRegistry):
        self.registry = registry
        self.memory_cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, float] = {}
        self.cache_ttl = 300  # 5 minutes
    
    def invalidate_dependent_files(self, source_file_id: str):
        """Invalidate all files that depend on a changed source file"""
        to_invalidate = set()
        self._collect_dependents(source_file_id, to_invalidate)
        
        for file_id in to_invalidate:
            self.registry.remove_generated_file(file_id)
            # Also remove from memory cache
            cache_keys_to_remove = [key for key in self.memory_cache.keys() 
                                  if file_id in key]
            for key in cache_keys_to_remove:
                del self.memory_cache[key]
                del self.cache_timestamps[key]
    
    def _collect_dependents(self, file_id: str, collected: Set[str]):
        """Recursively collect all dependent files"""
        dependents = self.registry.get_dependents(file_id)
        for dependent in dependents:
            if dependent not in collected:
                collected.add(dependent)
                self._collect_dependents(dependent, collected)
    
    def check_source_file_changes(self):
        """Check all source files for changes and invalidate dependents"""
        for file_id, resource in self.registry.source_files.items():
            path = Path(resource.path)
            if path.exists():
                current_mtime = path.stat().st_mtime
                if current_mtime > resource.modified:
                    print(f"Source file changed: {file_id}")
                    self.invalidate_dependent_files(file_id)
                    # Update the resource record
                    resource.modified = current_mtime
                    self.registry.save_registry()
    
    def cleanup_stale_files(self, max_age_days: int = 7):
        """Remove generated files older than specified age"""
        cutoff_time = time.time() - (max_age_days * 24 * 3600)
        
        files_to_remove = []
        for file_id, resource in self.registry.generated_files.items():
            if resource.created < cutoff_time:
                # Check if file is still being used (has dependents)
                if not self.registry.get_dependents(file_id):
                    files_to_remove.append(file_id)
        
        for file_id in files_to_remove:
            resource = self.registry.generated_files[file_id]
            path = Path(resource.path)
            if path.exists():
                path.unlink()
            self.registry.remove_generated_file(file_id)
            print(f"Cleaned up stale file: {file_id}")


class ResourceRecovery:
    """Handles recovery and validation of resource state"""
    
    def __init__(self, registry: ResourceRegistry):
        self.registry = registry
    
    def scan_and_rebuild_registry(self):
        """Rebuild file registry from existing files on disk"""
        print("Scanning filesystem to rebuild registry...")
        
        # Scan source directory
        source_dir = Path("/tmp/music/source")
        if source_dir.exists():
            for source_file in source_dir.iterdir():
                if source_file.is_file():
                    file_id = self.registry.register_source_file(source_file.name, source_file)
                    print(f"Registered source file: {file_id} -> {source_file.name}")
        
        # Scan for existing metadata files
        metadata_dir = Path("/tmp/music/metadata")
        if metadata_dir.exists():
            for metadata_file in metadata_dir.glob("*.json"):
                if metadata_file.name != "file_registry.json":
                    # Try to associate with source files
                    self._recover_metadata_file(metadata_file)
        
        print("Registry rebuild complete")
    
    def _recover_metadata_file(self, metadata_path: Path):
        """Attempt to recover metadata file associations"""
        # Try to extract file_id from metadata filename patterns
        name = metadata_path.stem
        
        # Pattern: {file_id}_analysis.json, {file_id}_speech.json, etc.
        if '_' in name:
            potential_file_id = name.split('_')[0]
            if potential_file_id in self.registry.source_files:
                print(f"Recovered metadata: {name} -> {potential_file_id}")
    
    def validate_resource_integrity(self) -> Dict[str, List[str]]:
        """Validate all tracked resources exist and are accessible"""
        missing_resources = {
            'source_files': [],
            'generated_files': [],
            'metadata_files': []
        }
        
        # Check source files
        for file_id, resource in self.registry.source_files.items():
            if not Path(resource.path).exists():
                missing_resources['source_files'].append(file_id)
        
        # Check generated files
        for file_id, resource in self.registry.generated_files.items():
            if not Path(resource.path).exists():
                missing_resources['generated_files'].append(file_id)
                self.registry.remove_generated_file(file_id)
        
        # Check metadata files
        for file_id, resource in self.registry.metadata_files.items():
            if not Path(resource.path).exists():
                missing_resources['metadata_files'].append(file_id)
        
        return missing_resources
    
    def repair_broken_dependencies(self):
        """Remove dependencies to files that no longer exist"""
        files_to_remove = []
        
        for file_id, deps in self.registry.dependencies.items():
            valid_deps = []
            for dep_id in deps:
                if self.registry.get_file_resource(dep_id):
                    valid_deps.append(dep_id)
            
            if len(valid_deps) != len(deps):
                if valid_deps:
                    self.registry.dependencies[file_id] = valid_deps
                else:
                    # No valid dependencies - remove the file
                    files_to_remove.append(file_id)
        
        for file_id in files_to_remove:
            self.registry.remove_generated_file(file_id)
        
        if files_to_remove:
            self.registry.save_registry()


# Example usage
if __name__ == "__main__":
    # Initialize resource management system
    registry = ResourceRegistry()
    cache_manager = CacheManager(registry)
    recovery = ResourceRecovery(registry)
    
    # Validate current state
    print("Validating resource integrity...")
    missing = recovery.validate_resource_integrity()
    
    for category, files in missing.items():
        if files:
            print(f"Missing {category}: {files}")
    
    # Check for source file changes
    print("Checking for source file changes...")
    cache_manager.check_source_file_changes()
    
    print(f"Registry contains:")
    print(f"  Source files: {len(registry.source_files)}")
    print(f"  Generated files: {len(registry.generated_files)}")
    print(f"  Operations: {len(registry.operations)}")