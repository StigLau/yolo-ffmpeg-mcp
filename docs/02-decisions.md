# Architecture Decisions Log (ADR)

*Keep this under 10 bullets - only significant decisions that affect future work*

## Active Decisions

### 2025-01-XX: Agent-Based Workflow Experiment
- **Context**: Testing specialized agents (modular-architect, reviewer-readonly) for focused task execution
- **Decision**: Create agents with tight domain focus to reduce general LLM context overhead
- **Impact**: May improve task quality by keeping agents within their expertise
- **Reversibility**: Experimental branch - can revert if approach proves toxic

### 2025-01-XX: Build Detective First Protocol
- **Context**: CI failures often escalate into over-engineering cycles
- **Decision**: Always use BD analysis before LLM token consumption for build issues
- **Impact**: Prevents symptom-fixing cycles, faster root cause identification
- **Status**: Implemented in CLAUDE.md protocols

### 2025-01-XX: Optional Docker Import Pattern
- **Context**: CI failures due to missing docker package in containerized environments
- **Decision**: Make docker import optional with graceful degradation
- **Implementation**: `try: import docker except ImportError: docker = None`
- **Impact**: CI compatibility without breaking production containerized features

### 2025-01-XX: MCP Server as Master Orchestrator
- **Context**: Multiple video processing subsystems (Komposteur, VideoRenderer, VDVIL)
- **Decision**: YOLO-FFMPEG-MCP coordinates but doesn't duplicate functionality
- **Impact**: Clear boundaries, leverage external JAR expertise
- **Integration**: Via Maven dependencies and GitHub Packages

## Historical Decisions
*Move completed/superseded decisions here*

---

*Add one line per significant decision. Keep recent decisions at top, archive old ones.*