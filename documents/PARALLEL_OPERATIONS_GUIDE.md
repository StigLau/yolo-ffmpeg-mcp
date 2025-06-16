# Claude Code Parallel Operations Guide

## Strategic Tool Batching for Maximum Efficiency

### Core Principle: Single Message, Multiple Tool Calls
Claude Code allows multiple tool invocations within a single message. This dramatically reduces latency and improves workflow efficiency.

## User Prompting Strategies for Maximum Parallelization

### 🎯 Optimal: Single Instance, Compound Commands

#### ✅ Best Practice: Batch Multiple Requests in One Message
```
"Analyze the codebase: check git status, read the main config files, 
search for TODO comments, and list recent commits"
```

This triggers Claude to execute in parallel:
- `Bash(git status)`
- `Read(config.json) + Read(pyproject.toml) + Read(CLAUDE.md)`  
- `Grep("TODO", include="*.py")`
- `Bash(git log --oneline -10)`

#### ✅ Advanced: Multi-Domain Compound Requests
```
"Fix the CI failures: check test results, analyze failing files, 
and also optimize the video processing workflow by listing available 
operations and analyzing the test videos"
```

Claude will automatically parallelize across both domains:
- CI Analysis: `Read(.github/workflows/ci.yml) + Bash(pytest --collect-only)`
- Video Processing: `mcp__list_files() + mcp__analyze_video_content()`

### 🚫 Suboptimal: Multiple CLI Windows

#### ❌ Avoid: Separate Claude Instances for Related Tasks
```
Window 1: "Check git status"
Window 2: "Read the config file"  
Window 3: "Run tests"
```

**Problems:**
- No shared context between instances
- 3x slower due to sequential processing
- Duplicate analysis and redundant operations
- Context switching overhead

#### ❌ Avoid: Fragmented Sequential Commands
```
User: "Check git status"
Claude: [shows git status]
User: "Now read package.json"  
Claude: [reads package.json]
User: "Run the tests"
Claude: [runs tests]
```

### 💡 Prompting Techniques for Maximum Efficiency

#### 1. **Scope Bundling**: Group Related Operations
```
❌ "Fix the tests" → "Update docs" → "Check CI"
✅ "Fix tests, update related docs, and verify CI passes"
```

#### 2. **Context Anticipation**: Include Supporting Info Requests
```
❌ "Fix this error: [error message]"
✅ "Fix this error by reading the relevant files, checking recent changes, 
    and examining similar code patterns: [error message]"
```

#### 3. **Dependency Specification**: Clarify Sequential vs Parallel Parts
```
✅ "Analyze these videos in parallel, then create a single composition 
    using the best scenes from each"
```

#### 4. **Multi-Modal Requests**: Combine Different Tool Types
```
✅ "Check the video processing system: verify MCP server status, 
    list available files, analyze video content, and validate the 
    Docker containers are working"
```

### 🔧 Advanced Prompting Patterns

#### Pattern 1: Investigation + Action
```
"Investigate the failing CI tests by reading logs and config files, 
then fix the identified issues"
```

Triggers:
1. Parallel investigation: `Read(logs) + Read(configs) + Bash(test status)`
2. Sequential fix based on findings

#### Pattern 2: Analysis + Comparison
```
"Compare our video processing performance with the benchmark: 
analyze our current metrics, check the benchmark data, and run 
a quick performance test"
```

#### Pattern 3: Multi-Environment Validation
```
"Verify the deployment works across environments: test locally with UV, 
check Docker containers, and validate Podman compatibility"
```

### 🎨 Prompt Engineering for Parallelization

#### Effective Prompt Structure:
```
[Action Verb] [Multiple Targets]: [Specific Operations] [, and] [Related Tasks]

Examples:
- "Analyze the codebase: read configs, check git status, and run tests"
- "Debug the video system: list files, analyze content, and check operations"  
- "Optimize the CI: review workflows, test locally, and validate containers"
```

#### Keywords That Trigger Parallel Execution:
- **"and"** - signals multiple parallel operations
- **"check both"** - parallel validation
- **"analyze all"** - parallel analysis
- **"compare"** - parallel information gathering
- **"investigate"** - comprehensive parallel research

### 🔤 Natural Language Notation for Parallel Operations

#### ❌ Don't Use Technical Notation
```
# Avoid programmer syntax - Claude interprets this literally
"Read(server.py) + Read(config.json) + Bash(git status)"
"Execute: list_files() && analyze_video_content() && get_operations()"
```

#### ✅ Use Natural Language Connectors

##### Best: Conjunction Words
```
"Read server.py AND config.json AND check git status"
"List files, analyze video content, AND check available operations"
"Investigate the CI: read workflow files AND run tests AND check Docker status"
```

##### Alternative: List Structure  
```
"Do these in parallel:
- Read the main server file
- Check git status  
- Run the test suite
- Analyze video files"
```

##### Comma Separation with Context
```
"Analyze the system: read configs, check git status, run tests, validate Docker"
"Debug video processing: list files, analyze content, check operations, test MCP server"
```

#### 🎯 Parallel Signal Phrases

##### Explicit Parallel Instructions:
```
✅ "Simultaneously check..."
✅ "In parallel, analyze..."  
✅ "At the same time, verify..."
✅ "Concurrently examine..."
```

##### Batch Operation Phrases:
```
✅ "Gather information about: [list items]"
✅ "Get a complete picture by: [list actions]"
✅ "Investigate all aspects: [list areas]"
✅ "Comprehensive analysis of: [list targets]"
```

#### 📝 Parallel Prompting Templates

##### Template 1: Investigation Pattern
```
"Investigate [PROBLEM]: 
read [FILE1] and [FILE2], 
check [SYSTEM_STATE], 
and analyze [DATA_SOURCE]"

Example:
"Investigate CI failures: 
read workflow configs and test results, 
check git status, 
and analyze error logs"
```

##### Template 2: Multi-Domain Pattern  
```
"[ACTION] the [SYSTEM1] and [SYSTEM2]: 
[OPERATION1] and [OPERATION2] and [OPERATION3]"

Example:
"Optimize the video system and CI pipeline: 
analyze video files and check test status and review Docker containers"
```

##### Template 3: Context + Action Pattern
```
"[GATHER_CONTEXT], then [ACTION]"

Example:
"Read all config files and check system status, then fix the deployment issues"
```

#### ⚡ Power User Shortcuts

##### Compressed Parallel Syntax:
```
✅ "Status check: git + configs + tests + Docker"
✅ "Video analysis: files + content + operations + MCP"  
✅ "Debug CI: logs + configs + tests + containers"
```

##### Ampersand for Technical Users:
```
✅ "Analyze: server.py & config.json & git status & test results"
✅ "Check: video files & MCP operations & Docker status & test suite"
```

#### 🚫 Anti-Patterns to Avoid

##### Sequential Language (Forces Series):
```
❌ "First read server.py, then check git status, then run tests"
❌ "After reading configs, check Docker, then analyze videos"
❌ "Step 1: X, Step 2: Y, Step 3: Z"
```

##### Ambiguous Scope:
```
❌ "Check everything" (too vague)
❌ "Fix the issues" (no specific targets)
❌ "Look at the code" (no parallel operations implied)
```

### 🎨 Style Guide for Parallel Prompts

#### Recommended Structure:
```
[INTENT]: [PARALLEL_OPERATION_1] and [PARALLEL_OPERATION_2] and [PARALLEL_OPERATION_3]

Examples:
• "Debug the system: read error logs and check configurations and test the API"
• "Prepare for deployment: validate tests and build containers and check dependencies"
• "Analyze performance: profile the code and check resource usage and review metrics"
```

#### Natural Flow Examples:
```
✅ "I need to understand the video system - can you read the main files, 
    check what operations are available, and analyze the test videos?"

✅ "Help me debug the CI: look at the workflow configs, check test results, 
    and see if Docker containers are working properly"

✅ "Let's optimize this: analyze the current performance, check for bottlenecks, 
    and review the system configurations"
```

**Key Insight**: Claude naturally recognizes parallel intent from context and conjunctions. No special notation needed - just clear, natural language with "and" or comma-separated operations!

### 🚀 Performance Comparison

#### Single Instance, Parallel Prompting:
```
Time to completion: ~200ms (5 tools in parallel)
Context preservation: 100%
Analysis quality: Comprehensive
Decision accuracy: High (full context)
```

#### Multiple Windows, Sequential:
```
Time to completion: ~1000ms (5 tools sequential)
Context preservation: 0% (isolated instances)
Analysis quality: Fragmented  
Decision accuracy: Low (missing context)
```

### 📋 CLI User Checklist

Before sending a message, ask yourself:
- [ ] Can I combine multiple requests into one message?
- [ ] Are there related files/operations I need context from?
- [ ] Should I include both analysis and action in one request?
- [ ] Am I providing enough context for intelligent parallelization?

#### Example Transformation:
```
❌ Inefficient (3 separate messages):
"What files are in src/?"
"Read the server.py file"  
"Check if tests are passing"

✅ Efficient (1 compound message):
"Understand the server architecture: list files in src/, read server.py, 
and check if tests are passing"
```

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