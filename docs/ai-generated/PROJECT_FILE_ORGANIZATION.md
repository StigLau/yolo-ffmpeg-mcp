# Project File Organization

## Root Directory Policy

**Goal**: Minimal root files that clearly show new developers where to start.

### Essential Root Files (Keep)
- **README.md** - Primary entry point for all users
- **CLAUDE.md** - Development guide for LLMs
- **test-all.sh** - Single test command for developers
- **Dockerfile** - Production Docker image
- **pyproject.toml** - Python project configuration
- **uv.lock** - Dependency lock file

### Core Directories
- **src/** - All source code
- **tests/** - All test suites
- **examples/** - Usage examples and workflows  
- **documents/** - All documentation
- **docker/** - Additional Docker configurations
- **deployment/** - Production deployment scripts
- **tools/** - Development and analysis tools
- **presets/** - Configuration presets
- **scripts/** - Utility scripts
- **archive/** - Legacy/deprecated files

## File Lifecycle Management

### Active Files
Files in active development and use.

### Deprecated Files 
Files moved to `archive/` when:
- Replaced by newer implementation
- No longer used in workflows
- Kept for historical reference

### Removal Criteria
Files deleted when:
- Completely obsolete
- Security risk
- Significant maintenance burden

## Developer Navigation

### New Developer Path
1. Read `README.md` - Overview and quick start
2. Run `./test-all.sh` - Verify system works
3. Read `CLAUDE.md` - Complete development guide
4. Explore `examples/` - Learn usage patterns
5. Check `documents/` - Detailed specifications

### LLM Navigation
1. Start with `CLAUDE.md` - Comprehensive context
2. Reference `PROJECT_STRUCTURE.md` - Code organization
3. Use `DEVELOPMENT_NOTES.md` - Architecture decisions
4. Check `documents/` for feature specifications

## Cleanup History

### 2025-06-16: Major Organization
- Moved 6 Dockerfiles → `docker/`
- Moved deployment scripts → `deployment/`
- Moved test utilities → `tools/testing/`
- Moved project docs → `documents/`
- Moved loose files → `archive/`
- Created single `test-all.sh` entry point
- Reduced root files from 30+ to 12 essential files

### Benefits Achieved
- Clear entry points for new developers
- Logical grouping of related files
- Minimal cognitive load in root directory
- Easy navigation for both humans and LLMs
- Historical preservation via archive

## File Status Tracking

### Active Development
All files in main directories are actively maintained.

### Maintenance Status
- **High**: Core system (`src/`, `tests/`, `README.md`, `CLAUDE.md`)
- **Medium**: Examples and documentation
- **Low**: Archive and legacy files

### Review Schedule
- Monthly review of root directory files
- Quarterly review of archive for deletion candidates
- Annual review of entire project structure