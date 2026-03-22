# Zombie Process Management - Enhanced MCP Implementation

**Status:** ✅ **IMPLEMENTED AND EMBEDDED**  
**Location:** FFMPEG MCP Server (`src/server.py`)  
**Implementation Date:** 2025-08-07

## Overview

Enhanced zombie process detection and elimination system embedded within the FFMPEG MCP server. Provides intelligent process classification and safe killing capabilities while protecting critical services.

## What Are "Spawned Processes" We're Detecting?

### **Spawn Process Origins**
The processes we detect come from **Python's multiprocessing module** using the **spawn method**:

```python
# When Python code does this:
import multiprocessing
process = multiprocessing.Process(target=some_function)
process.start()
# Creates: python -c "from multiprocessing.spawn import spawn_main; spawn_main(...)"
```

### **In Our FFMPEG MCP Context:**
1. **FFMPEG subprocess operations** - async video processing tasks
2. **Parallel video analysis** - content analysis, speech detection  
3. **Background media validation** - format checking, metadata extraction
4. **Concurrent file operations** - batch processing, format conversion

### **Why They Become Zombies:**
- **Parent process crashes** without cleanup
- **Async timeouts** don't properly terminate children
- **Exception handling gaps** leave processes running
- **Resource exhaustion** prevents proper cleanup

## New MCP Tools

### **1. `scan_zombie_processes()`** 🔍
Enhanced process classification and safety analysis.

```python
result = await scan_zombie_processes()
```

**Returns classified processes:**
- **🚨 Safe to Kill:** Python spawn zombies, hung FFMPEG processes
- **⚠️ Caution:** Firebase services, development servers
- **❌ Do Not Kill:** MCP servers, critical services

### **2. `kill_zombie_processes(pids, force=False)`** ⚠️
Kill specific processes with safety verification.

```python
# Kill specific PIDs (with safety checks)
result = await kill_zombie_processes([81886, 82024])

# Force kill with SIGKILL (-9)
result = await kill_zombie_processes([12345], force=True)
```

**Safety Features:**
- Verifies PIDs are classified as 'safe_to_kill' before killing
- Blocks killing of MCP servers and protected services
- Uses SIGTERM (-15) by default, SIGKILL (-9) with force=True
- Returns detailed results for each PID

### **3. `kill_all_safe_zombies(force=False)`** ⚠️🤖
Automatically kill all safe zombie processes.

```python
# Auto-kill all safe zombies
result = await kill_all_safe_zombies()

# Force kill all safe zombies  
result = await kill_all_safe_zombies(force=True)
```

**Workflow:**
1. Scans for all zombie processes
2. Identifies processes classified as 'safe_to_kill'
3. Kills all safe processes automatically
4. Protects MCP servers and critical services

## Process Classification System

### **🚨 Safe to Kill** (`safety_level: 'safe_to_kill'`)
- **Python spawn zombies** - leftover multiprocessing processes
- **Hung FFMPEG processes** - video processing tasks running >2 hours
- **Old media processing tasks** - abandoned background operations

### **❌ Do Not Kill** (`safety_level: 'do_not_kill'`)
- **MCP servers** - detected by uvicorn + mcp patterns or port :809x
- **Essential system services**

### **⚠️ Caution** (`safety_level: 'caution'`)
- **Firebase emulators** - development services
- **Web servers** - non-MCP uvicorn instances
- **Java services** - Komposteur, processing services

## Example Usage Scenarios

### **Scenario 1: Safe Cleanup After Video Processing**
```python
# Scan first to see what's running
scan_result = await scan_zombie_processes()

# Auto-kill all safe zombies (recommended)
cleanup_result = await kill_all_safe_zombies()
```

### **Scenario 2: Targeted Process Elimination**
```python
# Scan and identify specific problematic PIDs
scan_result = await scan_zombie_processes() 

# Kill specific PIDs that are consuming resources
kill_result = await kill_zombie_processes([81886, 82024])
```

### **Scenario 3: Force Kill Hung Processes**
```python
# When normal termination fails, force kill
kill_result = await kill_all_safe_zombies(force=True)
```

### **Scenario 4: Integrated System Cleanup**
```python
# Full system cleanup (includes process scanning)
cleanup_result = await cleanup_partial_operations()
# Now includes process scan results and kill recommendations
```

## Safety Guarantees

### **🛡️ MCP Server Protection**
- Automatically detects MCP servers by command patterns
- Never suggests killing processes with 'uvicorn' + 'mcp' or port patterns like ':8091'
- Blocks kill attempts on classified MCP servers

### **🔒 Service Classification**
- Firebase emulators marked as 'caution' - require explicit confirmation
- Java services (Komposteur) marked as 'caution' - may be processing
- Unknown services default to 'caution' - safe by default

### **⚙️ Kill Method Control**
- **SIGTERM (-15)** by default - allows graceful shutdown
- **SIGKILL (-9)** with `force=True` - immediate termination
- Process existence verification before kill attempts

## Integration with Existing Systems

### **Timeout Management Integration**
- Process scanning integrated with timeout manager
- Cleanup callbacks can now include zombie process elimination
- System health monitoring includes process health assessment

### **File Cleanup Integration**
- `cleanup_partial_operations()` now includes process scanning
- Provides comprehensive system cleanup in single call
- Coordinates temp file cleanup with process cleanup

## Current System Status (Example Output)

```
🔍 CLASSIFIED PROCESS SCAN RESULTS
==================================================

🚨 SAFE TO KILL (Zombie/Hung Processes):
  PID 81886: Python spawn zombie - CPU: 0.1%, Started: 26Jun25
  PID 82024: Python spawn zombie - CPU: 0.1%, Started: 26Jun25

⚠️  CAUTION - ASK BEFORE KILLING:
  PID 6352: Firebase Service - CPU: 0.0%, Started: 26Jun25
  PID 6410: Firebase Service - CPU: 0.0%, Started: 26Jun25

❌ DO NOT KILL (Critical Services):
  PID 82020: MCP Server - CPU: 0.0%, Started: 26Jun25
  PID 81883: MCP Server - CPU: 0.0%, Started: 26Jun25

🛠️  SAFE KILL COMMAND:
  kill 81886 82024
```

## Benefits

### **For Users:**
- **Safe zombie cleanup** without risk to critical services
- **Automated detection** of problematic processes
- **Clear classification** of what's safe to kill vs protect

### **For LLMs/Agents:**
- **Intelligent process management** with built-in safety
- **Automated zombie elimination** for system health
- **Integration with existing video processing workflows**

### **For System Health:**
- **Prevents resource leaks** from accumulating zombie processes
- **Maintains service stability** by protecting critical processes
- **Provides system health visibility** through classification

## Operational Recommendations

### **Regular Maintenance:**
```python
# Run after video processing sessions
cleanup_result = await kill_all_safe_zombies()
```

### **System Health Monitoring:**
```python
# Check system health periodically  
scan_result = await scan_zombie_processes()
health = scan_result['summary']['system_health']  # healthy/warning/critical
```

### **Emergency Cleanup:**
```python
# When system is unresponsive
cleanup_result = await kill_all_safe_zombies(force=True)
```

The system now provides comprehensive zombie process management while maintaining safety and service protection, all embedded within the existing FFMPEG MCP server architecture.