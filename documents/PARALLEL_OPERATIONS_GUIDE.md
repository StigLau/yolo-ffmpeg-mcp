# Claude Code Parallel Operations Guide

## Strategic Tool Batching for Maximum Efficiency

### Core Principle: Single Message, Multiple Tool Calls
Claude Code allows multiple tool invocations within a single message. This dramatically reduces latency and improves workflow efficiency.

## High-Impact Batching Patterns

### 1. Information Gathering (Research Phase)
```
# Instead of sequential calls:
Read file A → Read file B → Grep pattern → LS directory

# Use parallel batch:
Read(fileA) + Read(fileB) + Grep(pattern) + LS(dir)
```

**Example Use Case**: Understanding codebase structure
- Read multiple config files simultaneously 
- Search for patterns across different file types
- List directories while reading key files

### 2. Multi-File Analysis
```python
# Parallel file inspection
Read(src/server.py) + Read(src/config.py) + Read(pyproject.toml) + Grep("import.*server", include="*.py")
```

### 3. Cross-Platform Testing
```bash
# Parallel CI validation
Bash(pytest tests/unit/) + Bash(pytest tests/integration/) + Bash(docker build .) + Bash(podman build .)
```

### 4. Git Operations
```bash
# Atomic git status inspection
Bash(git status) + Bash(git diff) + Bash(git log --oneline -10)
```

## MCP Video Processing Optimization

### Parallel File Analysis
```python
# Instead of: list_files() → get_file_info(id1) → get_file_info(id2) → get_file_info(id3)
# Use: list_files() + analyze_video_content(id1) + analyze_video_content(id2) + analyze_video_content(id3)
```

### Batch Video Operations
```python
# Leverage batch_process() for chained operations
operations = [
    {"input_file_id": "file_123", "operation": "trim", "params": "start=0 duration=10"},
    {"input_file_id": "OUTPUT_PREVIOUS", "operation": "resize", "params": "width=1080 height=1920"},
    {"input_file_id": "OUTPUT_PREVIOUS", "operation": "replace_audio", "params": "audio_file_id=file_456"}
]
# Single call processes entire pipeline atomically
```

## Advanced Batching Strategies

### 1. Conditional Execution Patterns
```bash
# Test multiple environments in parallel
Bash(command -v podman && echo "podman available") + 
Bash(command -v docker && echo "docker available") + 
Bash(command -v uv && echo "uv available")
```

### 2. Error Recovery Batching
```python
# Parallel validation + fallback preparation
Read(config.json) + Read(config.yaml) + LS(/etc/configs/) + Glob("**/*.conf")
```

### 3. Performance Comparison
```bash
# Benchmark multiple approaches simultaneously
Bash(time podman build .) + Bash(time docker build .) + Bash(time uv sync)
```

## Anti-Patterns (Avoid These)

### ❌ Sequential File Reading
```
Read file1 → Wait → Read file2 → Wait → Read file3
```

### ❌ Single-Purpose Bash Calls
```
Bash(ls) → Bash(pwd) → Bash(git status)
```

### ❌ Iterative MCP Calls
```
get_file_info(id1) → get_file_info(id2) → get_file_info(id3)
```

## Optimal Patterns for Different Scenarios

### Project Analysis (Codebase Understanding)
```python
# Single message with comprehensive analysis
Read(README.md) + Read(pyproject.toml) + Read(CLAUDE.md) + 
Grep("class.*Server", include="*.py") + LS(src/) + LS(tests/)
```

### CI/CD Troubleshooting
```bash
# Parallel CI state inspection
Bash(git status) + Bash(docker ps -a) + Bash(pytest --collect-only) + 
Bash(uv pip list) + Read(.github/workflows/ci.yml)
```

### Video Processing Workflow
```python
# Parallel content analysis for multiple sources
list_files() + analyze_video_content(video1) + analyze_video_content(video2) + 
detect_speech_segments(audio1) + get_format_presets()
```

### Development Environment Setup
```bash
# Parallel environment validation
Bash(python --version) + Bash(uv --version) + Bash(ffmpeg -version) + 
Bash(podman --version) + LS(/tmp/music/source/)
```

## Performance Impact

### Latency Reduction
- **Sequential**: 5 tools × 200ms = 1000ms total
- **Parallel**: 5 tools × 200ms = 200ms total (5x improvement)

### Context Efficiency  
- Single message preserves context across all operations
- Reduces token overhead from multiple message exchanges
- Enables atomic decision-making based on combined results

## Best Practices

1. **Group Related Operations**: Batch tools that inform the same decision
2. **Prepare for Failures**: Include fallback options in the same batch
3. **Combine Read + Analysis**: Read files while running related searches
4. **Leverage MCP Atomics**: Use batch_process(), apply_video_effect_chain()
5. **Think in Workflows**: Design tool combinations around complete user goals

## Implementation Example

Instead of this conversation:
```
User: "Check if the CI is working"
Assistant: [calls Bash(git status)]
User: "What about the tests?"  
Assistant: [calls Bash(pytest --collect-only)]
User: "And Docker?"
Assistant: [calls Bash(docker ps)]
```

Use this approach:
```
User: "Check if the CI is working"
Assistant: [calls Bash(git status) + Bash(pytest --collect-only) + Bash(docker ps) + Read(.github/workflows/ci.yml)]
# Single response with complete CI health assessment
```

## Race Conditions and Conflict Avoidance

### Understanding Claude Code's Parallel Execution Model

Claude Code executes multiple tool calls **concurrently within a single message**, but this creates potential conflicts that must be carefully managed.

### 1. File System Race Conditions

#### ❌ Dangerous: Concurrent File Modifications
```python
# This can cause corruption or unpredictable results
Edit(file.py, old="config = {}", new="config = {a: 1}") + 
Edit(file.py, old="config = {}", new="config = {b: 2}")
# Both edits target the same string - undefined behavior
```

#### ✅ Safe: Read-Then-Sequential-Edit Pattern
```python
# Gather information in parallel, then edit sequentially
Read(file.py) + Read(config.json) + Grep("config", include="*.py")
# Analyze results, then make single targeted edit
```

#### ✅ Safe: Multi-File Modifications
```python
# Different files can be modified safely in parallel
Edit(server.py, old="PORT = 8000", new="PORT = 8080") + 
Edit(config.json, old='"env": "dev"', new='"env": "prod"') + 
Edit(README.md, old="# Old Title", new="# New Title")
```

### 2. MCP Server Resource Conflicts

#### ❌ Dangerous: Concurrent Video Processing
```python
# Multiple operations on same video file can cause corruption
process_file(file_123, "trim", "mp4", "start=0 duration=10") + 
process_file(file_123, "resize", "mp4", "width=1920 height=1080")
# Both operations try to write to temp directory simultaneously
```

#### ✅ Safe: Use Atomic batch_process()
```python
# Single atomic operation prevents conflicts
batch_process([
    {"input_file_id": "file_123", "operation": "trim", "params": "start=0 duration=10"},
    {"input_file_id": "OUTPUT_PREVIOUS", "operation": "resize", "params": "width=1920 height=1080"}
])
```

#### ✅ Safe: Parallel Analysis (Read-Only)
```python
# Multiple read-only operations are safe
analyze_video_content(file_123) + 
get_video_insights(file_456) + 
detect_speech_segments(file_789)
```

### 3. Directory and Temp File Conflicts

#### ❌ Dangerous: Concurrent Temp Directory Usage
```python
# Multiple operations creating temp files with same names
process_file(video1, "extract_audio", "wav") + 
process_file(video2, "extract_audio", "wav")
# Both may try to create "audio_extract.wav" simultaneously
```

#### ✅ Safe: Separate Contexts
```python
# Different file types or explicit naming
process_file(video1, "extract_audio", "wav", "output_name=audio1") + 
process_file(video2, "to_mp3", "mp3", "output_name=audio2")
```

### 4. State-Dependent Operations

#### ❌ Dangerous: Dependent Git Operations
```python
# Second command depends on first command's state change
Bash(git add .) + Bash(git commit -m "changes")
# If git add fails, commit will fail or commit wrong state
```

#### ✅ Safe: Atomic Git Operations
```python
# Combine into single atomic operation
Bash(git add . && git commit -m "changes")
```

#### ✅ Safe: Independent Status Checks
```python
# All are read-only operations
Bash(git status) + Bash(git diff --cached) + Bash(git log --oneline -5)
```

### 5. Resource Allocation Conflicts

#### ❌ Dangerous: Concurrent Container Operations
```python
# Multiple containers fighting for same resources
Bash(docker run --name test1 -p 8000:8000 image) + 
Bash(docker run --name test2 -p 8000:8000 image)
# Port conflict - both try to bind to 8000
```

#### ✅ Safe: Different Ports/Names
```python
# Separate resource allocation
Bash(docker run --name test1 -p 8001:8000 image) + 
Bash(podman run --name test2 -p 8002:8000 image)
```

## Conflict Resolution Strategies

### 1. Read-Heavy Parallel Patterns
```python
# Safe: Multiple reads, single decision point
Read(file1) + Read(file2) + Read(file3) + Grep(pattern) + LS(dir)
# Process all results, then make single modification
```

### 2. Resource Partitioning
```python
# Safe: Different resources per operation
Bash(pytest tests/unit/) + Bash(pytest tests/integration/) + Bash(pylint src/)
# Each test suite works on different files
```

### 3. Atomic Operations
```python
# Safe: Use tools designed for concurrent operations
MultiEdit(file, [
    {"old_string": "config1", "new_string": "new_config1"},
    {"old_string": "config2", "new_string": "new_config2"}
])
```

### 4. Temporal Separation
```python
# Safe: Read in parallel, then act sequentially
parallel_reads = Read(a) + Read(b) + Read(c)
# Process results...
sequential_action = Edit(target_file, old, new)
```

## Parallel-Safe Operation Categories

### ✅ Always Safe (Read-Only)
- `Read()` - File reading
- `LS()` - Directory listing  
- `Grep()` - Content search
- `Glob()` - Pattern matching
- `analyze_video_content()` - Content analysis
- `get_video_insights()` - Cached insights
- `git status`, `git diff`, `git log` - Git queries

### ⚠️ Conditionally Safe (Resource-Dependent)
- `Bash()` - Depends on commands
- `process_file()` - Safe if different files
- `detect_speech_segments()` - Safe if different files
- Container operations - Safe with different ports/names

### ❌ Never Safe in Parallel (Write Operations)
- `Edit()` - Same file modifications
- `Write()` - Same file writes
- `MultiEdit()` - Same file (but atomic within single call)
- Dependent operations (second depends on first's output)

## Best Practices for Conflict-Free Parallelization

1. **Batch Reads, Sequential Writes**: Gather all information in parallel, then make modifications sequentially
2. **Resource Isolation**: Ensure each parallel operation uses different resources (files, ports, directories)
3. **Atomic Operations**: Use tools designed for concurrent operations (batch_process, MultiEdit)
4. **Dependency Analysis**: Map operation dependencies before parallelizing
5. **Fail-Safe Patterns**: Design operations to be idempotent where possible

## Decision Tree: Can I Parallelize This?

```
Are all operations read-only? → YES → ✅ Parallel Safe
↓ NO
Do operations modify different resources? → YES → ✅ Parallel Safe  
↓ NO
Does operation B depend on operation A's output? → YES → ❌ Keep Sequential
↓ NO
Are there atomic alternatives available? → YES → ✅ Use Atomic Operation
↓ NO
❌ Keep Sequential
```

This conflict-awareness transforms Claude Code from a fast-but-dangerous parallel executor into a sophisticated concurrent processing system that maximizes speed while maintaining data integrity.