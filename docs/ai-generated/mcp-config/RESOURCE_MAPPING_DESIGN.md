# Resource Mapping System Design

## Overview

This document outlines a comprehensive resource mapping system for the FFMPEG MCP server that addresses cache persistence, file dependency tracking, and deterministic naming for effect operations.

## Current State Analysis

### ✅ Strengths
- Secure path validation and directory structure
- Persistent content analysis cache (`/tmp/music/metadata/`)
- Organized screenshot storage by video name
- Multiple specialized metadata directories

### ❌ Critical Gaps
- File IDs regenerate on restart (ephemeral `uuid.uuid4().hex[:8]`)
- No dependency tracking between operations
- Memory-only property cache loses performance benefits
- Cannot resume interrupted workflows
- No deterministic naming for effect operations

## Proposed Resource Mapping Architecture

### 1. Persistent File Registry

**Location**: `/tmp/music/metadata/file_registry.json`

```json
{
  "version": "1.0",
  "last_updated": "2025-06-14T09:37:01.123Z",
  "source_files": {
    "lookin.mp4": {
      "file_id": "src_lookin_mp4",
      "path": "/tmp/music/source/lookin.mp4",
      "size": 14555204,
      "modified": 1749891440.698,
      "checksum": "sha256_hash_here",
      "properties": {
        "duration": 5.800567,
        "resolution": "1920x1080",
        "codec": "hevc"
      }
    }
  },
  "generated_files": {
    "effect_trim_1a2b3c4d": {
      "file_id": "effect_trim_1a2b3c4d",
      "path": "/tmp/music/temp/trim_lookin_0s_4s.mp4",
      "created": 1749891440.698,
      "derived_from": ["src_lookin_mp4"],
      "operation": "trim",
      "parameters": {"start": 0, "duration": 4},
      "deterministic_id": true
    }
  }
}
```

### 2. Deterministic File ID Generation

**Strategy**: Replace random UUIDs with deterministic, content-based IDs

```python
class DeterministicIDGenerator:
    @staticmethod
    def source_file_id(filename: str) -> str:
        """Generate ID for source files based on filename"""
        # Remove extension, normalize, prefix with src_
        base = filename.replace('.', '_').lower()
        return f"src_{base}"
    
    @staticmethod
    def effect_file_id(input_ids: List[str], operation: str, params: Dict) -> str:
        """Generate deterministic ID for effect operations"""
        # Sort inputs and params for consistency
        sorted_inputs = sorted(input_ids)
        sorted_params = sorted(params.items())
        
        # Create content hash
        content = f"{sorted_inputs}_{operation}_{sorted_params}"
        hash_hex = hashlib.sha256(content.encode()).hexdigest()[:8]
        
        return f"effect_{operation}_{hash_hex}"
    
    @staticmethod
    def temp_file_path(file_id: str, operation: str, params: Dict) -> str:
        """Generate predictable temp file paths"""
        # Create descriptive filename from operation and params
        param_str = "_".join(f"{k}{v}" for k, v in sorted(params.items()))
        return f"/tmp/music/temp/{operation}_{file_id}_{param_str}.mp4"
```

### 3. Dependency Graph System

**Location**: `/tmp/music/metadata/dependency_graph.json`

```json
{
  "nodes": {
    "src_lookin_mp4": {
      "type": "source",
      "path": "/tmp/music/source/lookin.mp4",
      "metadata_files": [
        "/tmp/music/metadata/src_lookin_mp4_analysis.json",
        "/tmp/music/screenshots/lookin/"
      ]
    },
    "effect_trim_1a2b3c4d": {
      "type": "generated",
      "path": "/tmp/music/temp/trim_lookin_0s_4s.mp4",
      "operation": "trim",
      "parameters": {"start": 0, "duration": 4},
      "derived_from": ["src_lookin_mp4"],
      "created": 1749891440.698
    }
  },
  "edges": [
    {
      "from": "src_lookin_mp4",
      "to": "effect_trim_1a2b3c4d",
      "operation": "trim",
      "timestamp": 1749891440.698
    }
  ]
}
```

### 4. Resource Type Mapping

```json
{
  "resource_types": {
    "source_files": {
      "location": "/tmp/music/source/",
      "pattern": "*.{mp4,mp3,flac,wav,jpeg,png}",
      "persistent": true,
      "tracked_in": "file_registry.source_files"
    },
    "temp_files": {
      "location": "/tmp/music/temp/",
      "pattern": "*.{mp4,mp3,wav}",
      "persistent": false,
      "cleanup_policy": "age > 7 days",
      "tracked_in": "file_registry.generated_files"
    },
    "metadata_cache": {
      "location": "/tmp/music/metadata/",
      "pattern": "*_analysis.json",
      "persistent": true,
      "linked_to": "source_files"
    },
    "screenshots": {
      "location": "/tmp/music/screenshots/",
      "pattern": "*/scene_*.jpg",
      "persistent": true,
      "organized_by": "source_filename",
      "linked_to": "content_analysis"
    },
    "kompositions": {
      "location": "/tmp/music/metadata/generated_kompositions/",
      "pattern": "*.json",
      "persistent": true,
      "versioned": true
    }
  }
}
```

### 5. Cache Invalidation Strategy

```python
class ResourceCache:
    def invalidate_if_source_changed(self, source_file_id: str):
        """Invalidate all derived resources if source file changes"""
        source_info = self.registry.get_source_file(source_file_id)
        current_mtime = os.path.getmtime(source_info.path)
        
        if current_mtime > source_info.modified:
            # Source file changed - invalidate all derived resources
            derived_files = self.dependency_graph.get_derived_files(source_file_id)
            for derived_id in derived_files:
                self.mark_for_cleanup(derived_id)
                self.registry.remove_generated_file(derived_id)
    
    def check_effect_cache(self, input_ids: List[str], operation: str, params: Dict) -> Optional[str]:
        """Check if identical effect operation result exists"""
        deterministic_id = DeterministicIDGenerator.effect_file_id(input_ids, operation, params)
        
        if self.registry.has_generated_file(deterministic_id):
            # Verify all input files haven't changed
            if self.verify_input_integrity(input_ids):
                return deterministic_id
        
        return None
```

### 6. Recovery and Validation System

```python
class ResourceRecovery:
    def scan_and_rebuild_registry(self):
        """Rebuild file registry from existing files on disk"""
        # Scan source directory
        for source_file in Path("/tmp/music/source").glob("*"):
            file_id = DeterministicIDGenerator.source_file_id(source_file.name)
            self.registry.register_source_file(file_id, source_file)
        
        # Scan temp directory and attempt to reverse-engineer operations
        for temp_file in Path("/tmp/music/temp").glob("*"):
            self.attempt_operation_recovery(temp_file)
    
    def validate_resource_integrity(self):
        """Validate all tracked resources exist and are accessible"""
        missing_resources = []
        
        for file_id, info in self.registry.all_files():
            if not info.path.exists():
                missing_resources.append(file_id)
                self.mark_for_cleanup(file_id)
        
        return missing_resources
```

## Implementation Benefits

### ✅ Cache Persistence Across Restarts
- File IDs remain consistent between server sessions
- Completed operations can be found and reused
- Workflow state survives interruptions

### ✅ Deterministic Effect Operations
- Identical operations with same parameters produce same file IDs
- Automatic cache reuse for expensive operations
- Reduced redundant processing

### ✅ Resource Dependency Tracking
- Complete lineage from source to final output
- Impact analysis for source file changes
- Intelligent cache invalidation

### ✅ Robust Error Recovery
- Scan and rebuild registry from disk state
- Validate resource integrity on startup
- Handle missing files gracefully

## Migration Strategy

1. **Phase 1**: Implement `DeterministicIDGenerator` alongside existing system
2. **Phase 2**: Add `file_registry.json` persistence with backward compatibility
3. **Phase 3**: Implement dependency graph tracking for new operations
4. **Phase 4**: Add cache validation and recovery systems
5. **Phase 5**: Remove legacy random ID generation

## File Naming Convention

```
# Source files
src_{normalized_filename}

# Effect operations
effect_{operation}_{8char_hash}

# Temp file paths
{operation}_{source_id}_{params}.{ext}

# Examples
src_lookin_mp4                    # lookin.mp4
effect_trim_1a2b3c4d             # trim operation with specific params
trim_src_lookin_mp4_start0_dur4.mp4  # actual file path
```

This design ensures **deterministic, persistent, and recoverable** resource management while maintaining the existing security model and directory structure.