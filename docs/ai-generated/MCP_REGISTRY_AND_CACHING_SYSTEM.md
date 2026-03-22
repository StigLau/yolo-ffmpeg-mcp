# MCP Registry and Caching System Design

**Purpose**: Define the comprehensive registry and caching system for the FFMPEG MCP server, establishing proper LLM interaction patterns and cache management protocols.

**Status**: DESIGN SPECIFICATION - For implementation and LLM guidance

**Date**: July 27, 2025

## 🎯 **Core Principles**

### **1. Registry as Single Source of Truth**
The MCP server maintains an authoritative registry of all files it manages, accessible only through MCP tools. LLMs should NEVER directly access filesystem paths.

### **2. Abstraction Layer Enforcement**
LLMs interact with files through:
- **File IDs** (not paths): `src_video_abc123`, `temp_output_def456`
- **MCP Tools** (not filesystem): `list_files()`, `get_file_info()`
- **Registry Queries** (not directory scans): Server handles all file discovery

### **3. Cache Awareness Without Cache Access**
LLMs understand caching exists but never interact with cache storage directly.

## 🗂️ **Registry System Architecture**

### **Registry Database Structure**
```json
{
  "registry_version": "1.0",
  "last_scan": "2025-07-27T10:30:00Z",
  "source_files": {
    "src_jjvtt947ffi_136_mp4": {
      "original_name": "JJVtt947FfI_136.mp4",
      "path": "/tmp/music/source/JJVtt947FfI_136.mp4",
      "size": 17238807,
      "checksum": "sha256:abc123...",
      "added_date": "2025-07-26T21:18:00Z",
      "metadata": {
        "duration": 223.88,
        "resolution": "1280x720",
        "format": "mp4",
        "codec": "h264"
      }
    }
  },
  "generated_files": {
    "temp_4f05849a_mp4": {
      "original_name": "music_video_output.mp4",
      "path": "/tmp/music/temp/temp_4f05849a.mp4",
      "size": 5700000,
      "parent_operations": ["trim", "concatenate_simple"],
      "source_file_ids": ["src_jjvtt947ffi_136_mp4", "src_wz5hof5txy_136_mp4"],
      "created_date": "2025-07-26T22:45:00Z",
      "workflow_context": {
        "type": "music_video",
        "bpm": 120,
        "duration": 64.0
      }
    }
  },
  "operation_history": {
    "op_12345": {
      "operation": "concatenate_simple",
      "input_file_ids": ["src_jjvtt947ffi_136_mp4", "src_wz5hof5txy_136_mp4"],
      "output_file_id": "temp_4f05849a_mp4",
      "timestamp": "2025-07-26T22:45:00Z",
      "success": true,
      "processing_time_ms": 2500
    }
  },
  "cache_metadata": {
    "total_source_files": 5,
    "total_generated_files": 6,
    "total_storage_used": 45000000,
    "orphaned_files": [],
    "last_cleanup": "2025-07-27T09:00:00Z"
  }
}
```

### **Registry Locations**
- **Primary Registry**: `/tmp/music/metadata/file_registry.json`
- **Backup Registry**: `/tmp/music/metadata/file_registry.backup.json`
- **Operation Logs**: `/tmp/music/metadata/operation_history/`
- **Cache Manifests**: `/tmp/music/metadata/cache_manifests/`

## 🔄 **Startup and Rescan Functionality**

### **Server Startup Sequence**
```python
async def initialize_registry_system():
    """Complete registry initialization on server startup"""
    
    # 1. Load existing registry
    registry = await load_registry_database()
    
    # 2. Perform filesystem rescan
    scan_results = await rescan_managed_directories()
    
    # 3. Reconcile registry with filesystem
    reconciliation = await reconcile_registry_with_filesystem(registry, scan_results)
    
    # 4. Handle cache misses and orphaned files
    await handle_cache_misses(reconciliation.missing_files)
    await handle_orphaned_files(reconciliation.orphaned_files)
    
    # 5. Update registry with current state
    await update_registry_database(reconciliation.updated_registry)
    
    # 6. Initialize MCP tools with clean registry
    await initialize_mcp_tools_with_registry()
```

### **Rescan Directories**
```python
async def rescan_managed_directories():
    """Scan all managed directories for current file state"""
    
    managed_directories = [
        "/tmp/music/source/",      # Source video files
        "/tmp/music/temp/",        # Generated/processed files  
        "/tmp/music/finished/",    # Completed workflows
        "/tmp/music/screenshots/", # Generated screenshots
        "/tmp/music/cache/"        # Cached analysis results
    ]
    
    filesystem_state = {}
    
    for directory in managed_directories:
        if os.path.exists(directory):
            files = await scan_directory_with_metadata(directory)
            filesystem_state[directory] = files
    
    return filesystem_state
```

### **Cache Miss Handling**
```python
async def handle_cache_misses(missing_files: List[str]):
    """Handle files that exist in registry but not on filesystem"""
    
    for file_id in missing_files:
        registry_entry = registry.get_file_entry(file_id)
        
        # Log cache miss
        logger.warning(f"Cache miss detected: {file_id} - {registry_entry.original_name}")
        
        # Mark file as missing in registry
        registry.mark_file_missing(file_id, timestamp=datetime.now())
        
        # Invalidate dependent operations
        dependent_operations = registry.get_dependent_operations(file_id)
        for op_id in dependent_operations:
            registry.invalidate_operation(op_id, reason="source_file_missing")
        
        # Clean up broken dependency chains
        await cleanup_broken_dependencies(file_id)
```

### **Orphaned File Recovery**
```python
async def handle_orphaned_files(orphaned_files: List[str]):
    """Handle files that exist on filesystem but not in registry"""
    
    for file_path in orphaned_files:
        # Attempt to recover file metadata
        metadata = await extract_file_metadata(file_path)
        
        # Try to match with operation history
        possible_operation = await match_orphaned_file_to_operation(file_path, metadata)
        
        if possible_operation:
            # Restore file to registry
            file_id = await restore_file_to_registry(file_path, metadata, possible_operation)
            logger.info(f"Recovered orphaned file: {file_id}")
        else:
            # Create new registry entry for unknown file
            file_id = await create_registry_entry_for_orphaned_file(file_path, metadata)
            logger.info(f"Registered unknown file: {file_id}")
```

## 🛠️ **MCP Tools for Registry Interaction**

### **Core Registry Tools**
```python
@mcp.tool()
async def list_files(file_type: Optional[str] = None) -> Dict[str, Any]:
    """
    🗂️ LIST FILES - Get all files known to the MCP server
    
    LLM Usage: "What files do you have available?"
    Returns: File IDs, names, metadata - NEVER file paths
    """

@mcp.tool()
async def get_file_info(file_id: str) -> Dict[str, Any]:
    """
    📋 FILE INFO - Get detailed information about a specific file
    
    LLM Usage: "Tell me about file src_video_abc123"
    Returns: Metadata, processing history, dependencies
    """

@mcp.tool()  
async def get_registry_status() -> Dict[str, Any]:
    """
    📊 REGISTRY STATUS - Get overall registry health and statistics
    
    LLM Usage: "How is your file registry doing?"
    Returns: File counts, storage usage, cache health, orphaned files
    """

@mcp.tool()
async def search_files(query: str, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    🔍 SEARCH FILES - Find files by name, metadata, or content
    
    LLM Usage: "Find videos with 'music' in the name"
    Returns: Matching file IDs and metadata
    """

@mcp.tool()
async def get_file_history(file_id: str) -> Dict[str, Any]:
    """
    📜 FILE HISTORY - Get complete processing history for a file
    
    LLM Usage: "What operations were performed on this file?"
    Returns: Operation chain, dependencies, derivation tree
    """
```

### **Cache Management Tools**
```python
@mcp.tool()
async def trigger_registry_rescan() -> Dict[str, Any]:
    """
    🔄 RESCAN REGISTRY - Force a complete rescan of managed directories
    
    LLM Usage: "Please rescan your file registry"
    Returns: Scan results, recovered files, cache miss report
    """

@mcp.tool()
async def cleanup_orphaned_files() -> Dict[str, Any]:
    """
    🧹 CLEANUP ORPHANED - Remove or register orphaned files
    
    LLM Usage: "Clean up any orphaned files"
    Returns: Cleanup summary, recovered files, removed files
    """

@mcp.tool()
async def validate_registry_integrity() -> Dict[str, Any]:
    """
    ✅ VALIDATE REGISTRY - Check registry consistency and health
    
    LLM Usage: "Check if your file registry is healthy"
    Returns: Validation report, integrity score, issues found
    """
```

## 🤖 **LLM Interaction Guidelines**

### **✅ PROPER LLM Behavior**

**File Discovery:**
```
❌ "Let me check /tmp/music/source/ for videos"
✅ "What video files do you have available?"
```

**File Information:**  
```
❌ "Let me run ffprobe on /path/to/video.mp4"
✅ "Can you tell me about file src_video_abc123?"
```

**File Processing:**
```
❌ "I'll process /tmp/music/temp/output.mp4"
✅ "Process file temp_output_def456 with trim operation"
```

**Registry Health:**
```
❌ "Let me scan your temp directory"
✅ "How is your file registry doing? Any orphaned files?"
```

### **🚫 FORBIDDEN LLM Behavior**

**Direct Filesystem Access:**
- Never use `ls`, `find`, `ffprobe` on MCP server paths
- Never read/write files in `/tmp/music/` directly
- Never access registry JSON files directly
- Never scan directories for file discovery

**Cache Manipulation:**
- Never delete files from temp directories
- Never modify registry database files
- Never move files between MCP server directories
- Never bypass MCP tools for file operations

### **🛠️ DEVELOPMENT/DEBUG Mode Exception**

**When explicitly in development/debug mode:**
```python
@mcp.tool()
async def debug_filesystem_state() -> Dict[str, Any]:
    """
    🔧 DEBUG ONLY - Direct filesystem inspection for development
    
    WARNING: Only for development/debugging. Do not use in normal operation.
    """
```

**Development mode allows:**
- Direct filesystem inspection for verification
- Registry database examination
- Cache directory analysis
- File system consistency checking

## 📋 **Registry Maintenance Protocols**

### **Automatic Maintenance**
- **Daily**: Registry validation and integrity checks
- **Weekly**: Cleanup of old temporary files (>7 days)
- **Monthly**: Registry optimization and defragmentation
- **On restart**: Complete rescan and reconciliation

### **Cache Eviction Policies**
```python
class CacheEvictionPolicy:
    """Policies for managing cache storage limits"""
    
    MAX_CACHE_SIZE = 10_000_000_000  # 10GB
    MAX_TEMP_FILE_AGE = 7 * 24 * 3600  # 7 days
    MAX_REGISTRY_ENTRIES = 10000
    
    async def evict_old_files(self):
        """Remove files older than MAX_TEMP_FILE_AGE"""
    
    async def evict_large_cache(self):
        """Remove oldest files when cache exceeds MAX_CACHE_SIZE"""
    
    async def cleanup_broken_operations(self):
        """Remove operations with missing dependencies"""
```

### **Registry Backup Strategy**
- **Real-time**: Registry changes logged to operation history
- **Hourly**: Automatic registry backup creation
- **Daily**: Registry export to external backup location
- **On shutdown**: Complete registry state preservation

## 🎯 **Implementation Status**

### **Current State**
- ✅ **Basic file tracking**: Source files properly registered
- ⚠️ **Generated file tracking**: Files exist but registry disconnected
- ✅ **Directory structure**: Proper organization in place
- ⚠️ **Rescan functionality**: Infrastructure exists, needs activation
- ❌ **Cache miss handling**: Not implemented
- ❌ **Orphaned file recovery**: Not implemented

### **Priority Implementation Tasks**
1. **Registry reconciliation system**: Reconnect orphaned files
2. **Startup rescan functionality**: Complete directory scan on startup
3. **Cache miss handling**: Graceful handling of missing files
4. **MCP tool enhancement**: Expose registry functionality to LLMs
5. **Documentation integration**: Add registry awareness to existing tools

### **Success Metrics**
- **Zero orphaned files**: All generated files tracked in registry
- **100% cache hit rate**: No missing files in registry
- **Sub-second registry queries**: Fast MCP tool responses
- **Complete operation history**: Full provenance tracking for all files

## 📖 **LLM Quick Reference**

### **Registry Interaction Pattern**
1. **Discovery**: `list_files()` - What's available?
2. **Investigation**: `get_file_info(file_id)` - What are the details?
3. **Processing**: `process_file(file_id, operation, params)` - Work with files
4. **Tracking**: `get_file_history(file_id)` - What happened to this file?
5. **Health Check**: `get_registry_status()` - Is everything working?

### **Cache Awareness**
- **Understand**: Files may exist in multiple locations (source, temp, finished)
- **Trust**: Registry is authoritative - don't verify with filesystem
- **Request**: Use `trigger_registry_rescan()` if concerned about cache misses
- **Avoid**: Never directly access `/tmp/music/` paths

### **Error Handling**
- **File not found**: File may have been evicted - check registry status
- **Processing failures**: May indicate cache misses - trigger rescan
- **Slow responses**: Registry may need maintenance - check health

---

**This document establishes the contract between the MCP server's registry system and LLM clients. Following these guidelines ensures proper abstraction, cache management, and system reliability.**