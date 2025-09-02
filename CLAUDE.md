# FFMPEG MCP Server - AI-Assisted Music Video Creation

This project is an intelligent MCP server for creating professional music videos through AI-guided FFmpeg processing. It combines FastTrack analysis, Build Detective CI validation, and hierarchical subagent orchestration to deliver cost-effective, high-quality video processing.

## What This Project Does

**Primary Mission**: Transform video processing from manual, error-prone workflows into intelligent, automated systems that understand content, predict optimal strategies, and deliver professional results at scale.

**Core Value Proposition**: 
- **99.7% Cost Reduction**: $0.02 AI analysis vs $125+ manual decisions
- **95% Success Rate**: AI-guided processing vs 70% manual reliability  
- **Professional Quality**: Automated crossfades, beat-sync, format optimization
- **Intelligent Orchestration**: Multi-agent coordination for complex workflows

## How We Approach Video Processing

### Music Video Creation Strategy

**Philosophy**: Separate video and audio processing streams for maximum flexibility and performance.

- **Video Processing**: Focus on visual effects, timing, and transitions (drop audio with `-an`)
- **Audio Integration**: External high-quality audio sources (MP3, WAV) replace video audio
- **Smart Assembly**: AI-guided combination of processed video + prepared audio
- **Performance Optimization**: Simpler processing without unnecessary audio stream overhead

## ⚠️ MANDATORY CONSULTATION RULES ⚠️

**CRITICAL**: Always consult before architectural changes to prevent over-engineering cycles.

**NEVER** change base images, package managers, or core dependencies without explicit permission:
- **Tech Stack Changes**: Alpine→Debian, pip→UV, Python versions require approval
- **Always Present Options**: "Fix Alpine deps vs switch to Debian - which?" 
- **Wait for Permission**: No implementation until explicit user approval
- **VIOLATION = IMMEDIATE STOP**

**Root Cause Analysis Protocol**:
1. Compare CI environment vs local environment EXACTLY
2. Check if main branch has this issue  
3. Look for SIMPLEST explanation first (often 3-line fixes)
4. If fix requires >10 lines, PAUSE and reconsider approach

## Project Organization Standards

### File Organization Strategy

**Zero Root Directory Pollution**: AI-generated files NEVER appear in project root.

**Directory Structure**:
```
/tmp/kompo/haiku-ffmpeg/     # All generated content
├── generated-videos/        # Final outputs
├── youtube-downloads/       # Source material
├── test-files/             # Experiments
└── temp/                   # Processing cache
```

**File Value Classification**:
- **Keep**: Source code (`src/`), configurations, documentation, small tests (<10MB)
- **Archive**: Historical analysis, old experiments, legacy configs  
- **Temp**: AI reports with timestamps, runtime artifacts, large files (>10MB)

**Git Rules**: Never stage timestamped reports, logs, build artifacts, or large binaries

## AI Intelligence Framework

**The system combines two specialized AI agents for cost-effective, high-quality video processing:**

### FastTrack Subagent (Video Analysis)
- **Ultra-Low Cost**: $0.02-0.05 per analysis (99.7% cost savings vs manual)
- **Frame Alignment Detection**: Automatically identifies and fixes timing issues
- **Smart Strategy Selection**: AI chooses optimal FFmpeg approach based on content
- **Quality Assurance**: PyMediaInfo verification with confidence scoring  
- **Creative Transitions**: 44 FFmpeg xfade effects with intelligent selection
- **Fallback Mode**: Works offline without API keys for development

### Build Detective Subagent (CI Analysis)  
- **Pre-Commit Validation**: Local CI testing prevents GitHub Actions failures
- **Maven Multi-Module Expertise**: Comprehensive build log parsing
- **Token-Saving Protocol**: BD analysis before expensive LLM operations
- **Confidence Framework**: High confidence (>8/10) = direct implementation

**Delegation Strategy**: Automatically route tasks to specialized subagents based on content analysis.

## Multi-Agent Orchestration

**YOLO operates as master orchestrator** coordinating specialized subagents:

- **FastTrack**: Video analysis and strategy selection
- **Komposteur**: Beat-synchronization and S3 infrastructure  
- **VideoRenderer**: FFmpeg optimization and crossfade processing
- **VDVIL**: DJ-mixing and audio composition
- **Build Detective**: CI/build failure analysis

**Coordination Benefits**:
- **Parallel Processing**: Multiple agents work simultaneously
- **Seamless Handoffs**: FastTrack analysis → Audio (VDVIL) → Beat-sync (Komposteur) → Crossfades (VideoRenderer) → Final assembly (YOLO)
- **Quality Assurance**: Master oversight with consistent standards
- **Cost Optimization**: Intelligent resource sharing with budget awareness

## Lessons Learned

**Architectural Anti-Pattern**: Git submodules for source dependencies create tight coupling, repository bloat, and maintenance nightmares. Use API-first integration with Maven dependencies instead.

**LLM Over-Engineering Prevention**: 
- **"3-Line Rule"**: If root cause likely <10 lines, analyze more than implement
- **Environment Comparison**: Compare CI vs local before architectural changes  
- **Symptom vs Root Cause**: Avoid "whack-a-mole" fixing cycles
- **Progressive Error Resolution**: Each fix should produce NEW, more specific errors

## Technical Implementation Details

### Development vs Production Strategy
**Local Development**: Use latest JARs from `~/.m2/repository/` for fast iteration without network delays
**Production CI**: GitHub Packages with authentication for reproducible, secure builds
**Auto-Detection**: System automatically prefers local development JARs when available

### Video Format Strategy  
**Final User Output**: Always use YUV420P format for maximum compatibility (VLC, QuickTime)
**Intermediate Processing**: YUV444P acceptable for internal workflows (higher quality)
**Verification**: Test final videos in standard players before delivery

### Local CI Validation
**Command**: `uv run python test_basic_ci.py && echo "✅ CI PASSED"`
**Components**: Basic validation, Build Detective analysis, video format strategy testing
**Git Hook Integration**: Available but not enabled - user observes performance first

## Project Navigation

**Clean Repository Structure** (Root contains only essential files):
- **Core**: `src/`, `tests/`, `docs/`, `tools/`, `examples/`
- **Configuration**: `pyproject.toml`, `CLAUDE.md`, `Dockerfile`, `Makefile`
- **Generated Content**: `/tmp/kompo/haiku-ffmpeg/` (never in project root)
- **Archives**: `archive/` for historical analysis, configs, media files

**Quick Navigation by Domain**:
```bash
# Video Processing Intelligence
src/haiku_subagent.py              # FastTrack core system
tools/ft                           # FastTrack CLI
docs/FASTTRACK_*.md               # Documentation

# CI/Build Analysis  
tools/scripts/bd_*.py              # Build Detective scripts
docs/ai-agents/BUILD_DETECTIVE_*.md # BD documentation

# Music Video Creation
integration/komposteur/            # Komposteur bridge
examples/komposition-examples/     # Templates
```

## ⚠️ **LOCAL CI BUILD SYSTEM** ⚠️

### **CI Build Strategy** ✅ **IMPLEMENTATION REQUIRED**

**Local CI Command:**
```bash
# Run complete CI validation before push
uv run python test_basic_ci.py && echo "✅ CI PASSED - Ready to push"
```

**CI Components:**
1. **Basic Validation**: `test_basic_ci.py` - Code structure and documentation
2. **Build Detective Analysis**: Automated quality assessment post-commit
3. **Integration Testing**: Video format strategy validation

**Pre-Push Workflow:**
```bash
# 1. Run local CI tests
uv run python test_basic_ci.py

# 2. If tests pass, commit and push
git add . && git commit -m "Feature implementation"
git push origin feature-branch

# 3. BD automatically analyzes pushed changes
# (BD report available within minutes of push)
```

**Future Git Hook Integration:**
- **NOT ENABLED YET** - User must observe CI build performance first
- **When ready**: Add `test_basic_ci.py` to pre-push hook
- **Estimated time**: ~5-10 seconds for basic validation

**BD Integration:**
- BD automatically analyzes all pushed branches
- BD reports available via Build Detective subagent
- Use BD confidence scores to validate positive changes

## ⚠️ **CRITICAL: LLM OVER-ENGINEERING ANTI-PATTERNS** ⚠️

### **PR 22 Case Study: The Danger of Symptom-Fixing** 🚨

**LESSON LEARNED**: LLMs can create "whack-a-mole" patterns that make simple problems exponentially more complex.

#### **The Symptom-Fixing Cycle**
```
Real Issue: Missing try/except around `import docker` (3 lines)
↓
LLM Fix 1: "Missing temp/ files" → Dockerfile.ci changes
↓  
LLM Fix 2: "Module import errors" → src/ directory restructuring
↓
LLM Fix 3: "Complex workflow issues" → 301-line workflow replacement
↓
LLM Fix 4: "Merge conflicts" → Complex resolution strategy
↓
LLM Fix 5: "Dependency issues" → pyproject.toml restructuring
↓
Real Fix: try/except ImportError (3 lines) ✅
```

#### **WARNING SIGNS of LLM Over-Engineering** 
- ❌ **Multiple successive "fixes"** for the same core issue
- ❌ **Each fix touches 5+ files** or adds complex configuration
- ❌ **Local tests pass but CI fails repeatedly** 
- ❌ **"Simple" fixes require architectural changes**
- ❌ **Solution complexity >> problem complexity**

#### **MANDATORY PROTOCOL: Root Cause Analysis First**
```bash
# BEFORE implementing any "fix":
1. Ask: "Is this treating a symptom or the root cause?"
2. Compare CI environment vs local environment EXACTLY
3. Check: Does main branch have this issue?
4. Look for the SIMPLEST explanation first
5. If fix requires >10 lines, PAUSE and reconsider approach
```

#### **Success Pattern: CI Environment Comparison**
- **What worked**: Compare CI scripts between branches
- **What worked**: Check exact import failures in CI logs  
- **What worked**: Make the failing import optional (try/except)
- **What failed**: Complex dependency management, workflow rewriting, Docker restructuring

#### **Key Learning**: 
**"90% of the time CI failures are due to LLM code changes"** - The user was absolutely correct. LLMs tend to add complexity instead of finding the simple root cause.

#### **Validation Protocol**:
```python
# Always make optional imports when dealing with CI issues:
try:
    import optional_heavy_dependency
except ImportError:
    optional_heavy_dependency = None  # Graceful degradation
```

#### **Documentation Requirement**:
For any multi-fix PR, document:
- What was the original simple problem?
- How many "fixes" were attempted?  
- What was the actual root cause?
- Could this have been solved in 1-3 lines initially?

### **Build Detective Evolution**: From Problem to Solution
- **Problem**: CI failures recurring despite multiple fixes
- **Root Cause Discovery**: Compare main branch vs feature branch CI
- **Simple Solution**: Optional import pattern
- **Learning**: Always check environment differences first, not configuration complexity

This case study demonstrates that **simpler is usually correct** when dealing with import/dependency issues in CI environments.

### **CRITICAL DISTINCTION: Good vs Bad Multi-Fix Patterns** 🎯

#### **✅ GOOD Pattern: Sequential Problem Discovery (Gemini Example)**
*From gemini-ffmpeg changes_summary_20250824.md - demonstrates proper systematic debugging*

```
Problem 1: Method call mismatch → Fix: Load file + use correct async method → New error
Problem 2: JSON structure mismatch → Fix: Add sources list + sourceRef pattern → New error  
Problem 3: File path restrictions → Fix: Update FileManager config + hardcoded paths → Success
```

**Why This Was CORRECT Multi-Fix Approach**:
- ✅ **Each fix revealed NEW, SPECIFIC error message** (progress indicators)
- ✅ **Targeted changes** addressing actual underlying issues  
- ✅ **No architectural rewrites** - just corrected specific mismatches
- ✅ **Sequential problem discovery** - fix A reveals problem B

#### **❌ BAD Pattern: Same Problem Escalating Complexity (PR 22)**
```
Same CI Failure → Complex Dockerfile fix → Still failing → Workflow rewrite → Still failing → etc.
```

**Why This Was WRONG Multi-Fix Approach**:
- ❌ **Same error recurring** despite multiple "fixes"
- ❌ **Each fix more complex/architectural** than the last
- ❌ **Solution >> Problem Complexity** (50+ line fixes for import issue)
- ❌ **Symptom-fixing cycle** without root cause identification

### **Refined Over-Engineering Detection** 🔍

#### **REAL Warning Signs** (Replace crude metrics)
- ❌ **Same Error Persisting** after 2+ attempts with different approaches
- ❌ **Architectural Drift** - "simple" fix requiring tech stack changes  
- ❌ **Solution >> Problem Complexity** - 50-line fix for 3-line problem
- ❌ **Recursive Complexity** - each fix creates more problems than it solves

#### **NOT Warning Signs** (False positives to avoid)
- ✅ **Multiple files changed** when each change addresses specific, different issues
- ✅ **Sequential debugging** that progresses through distinct problems
- ✅ **Multiple fix attempts** when each attempt targets a newly discovered issue

#### **Key Insight: Error Message Patterns**
```bash
# GOOD Sequential Pattern:
Error 1: "Method 'process_komposition_file' not found" → Fix method call
Error 2: "No source found for segment: None" → Fix JSON structure  
Error 3: "File path not allowed: /tmp/music/source/..." → Fix path handling

# BAD Recurring Pattern:  
Error: "ModuleNotFoundError: No module named 'docker'" → Fix 1
Error: "ModuleNotFoundError: No module named 'docker'" → Fix 2
Error: "ModuleNotFoundError: No module named 'docker'" → Fix 3
```

**CRITICAL LEARNING**: **Quality of analysis** matters more than **quantity of changes**. Systematic debugging applied to multiple sequential issues is exactly what we want - not over-engineering.

## ⚠️ **COMPREHENSIVE AI RESTRAINT PROTOCOLS** ⚠️

### **Research-Based Constraint Framework** 📚
*Based on analysis of Anthropic Engineering, The Ground Truth, Spec-Driven Development, and Claude Code documentation*

#### **The "3-Line Rule"** 🎯
**Principle**: If root cause is likely <10 lines of code, spend MORE time analyzing than implementing.

**Protocol**:
1. **Analysis Phase**: Use Build Detective, compare branches, identify patterns  
2. **Minimal Fix Hypothesis**: Propose simplest possible solution FIRST
3. **Escalation Threshold**: Only expand scope with explicit user approval

#### **The "Stable Point Protocol"** 🔗  
**Principle**: Always work from known-good state → known-good state.

**Steps**:
1. **Verify Starting Point**: Ensure current state compiles/tests pass
2. **Single Change**: Make one logical change only
3. **Verification**: Confirm new state is stable (BD local CI)
4. **Commit**: Version the change before next modification

#### **Pre-Implementation Constraint Gates** 🚪

**MANDATORY CHECKPOINTS**:
- [ ] **Planning Phase**: Force AI to plan before ANY code changes
- [ ] **Root Cause Analysis**: Compare branches, identify simplest solution
- [ ] **Scope Definition**: Define maximum files/lines to change
- [ ] **YOLO Mode Approval**: Require explicit permission for >3 file changes

**AUTOMATIC TRIGGERS** (Refined based on Gemini vs PR 22 analysis):
- **Same Error Persisting** → After 2+ attempts, switch to BD/environment comparison
- **Architectural Drift** → "Simple" fix requiring tech stack changes → STOP and ask  
- **Recursive Complexity** → Each fix creates more problems → STOP and reassess
- **Solution >> Problem** → 50+ line fix for single error message → Justify or simplify

#### **The Domain Expert Consultation Protocol** 🤝
**Principle**: Senior developers know the codebase; ask instead of assuming.

**Implementation**:
```bash
# Before ANY architectural change:
1. "What's the typical pattern for X in this codebase?" 
2. "Has this issue occurred before?"
3. "Do you prefer approach A or B for this type of change?"
4. "Will this change affect any other systems?"
```

#### **Course Correction Protocols** 🛑

**Interrupt Capabilities**:
- **ESC Key Protocol**: Stop mid-process when complexity escalates
- **Token Budget Awareness**: Reassess after significant token usage  
- **Build Detective First**: Use BD tools before LLM analysis for build issues
- **Branch Comparison**: When debugging, compare working vs broken branches FIRST

#### **Mature Codebase Sensitivity Rules** 🏛️

**GOLDEN RULES**:
1. **Incremental Over Comprehensive**: Small testable changes vs rewrites
2. **Backward Compatibility**: Maintain existing behavior patterns
3. **Domain Language**: Use project-specific terminology consistently  
4. **Change Impact Assessment**: Estimate affected systems before starting

**VIOLATION CONSEQUENCES**:
- **First Violation**: Warning and course correction
- **Second Violation**: Session reset with planning restart
- **Pattern Violation**: Immediate escalation to user oversight

### **Success Metrics & Monitoring** 📊

**Target Metrics**:
- **Progressive Error Resolution**: Each fix produces new, more specific error (not same recurring error)
- **First-Fix Success**: >80% problems solved without architectural changes
- **BD Usage Rate**: >90% build issues use BD before LLM analysis  
- **User Satisfaction**: Reduced overwhelming change review burden

**Warning Indicators** (Refined):
- **Error Message Stagnation**: Same error after multiple different approaches
- **Complexity Escalation**: Each successive fix more architectural than previous
- **Recursive Problem Creation**: Fixes generate more issues than they solve
- **Token Burn Without Progress**: High usage without advancing through distinct problems

### **Implementation Roadmap** 🗺️

**Phase 1 (Immediate)**:
- [ ] Add explicit approval gates for >3 file changes
- [ ] Implement "pause and ask" checkpoints during complex tasks
- [ ] Create change impact estimator before modifications

**Phase 2 (Short-term)**:  
- [ ] Build Detective first protocol for all CI failures
- [ ] Subagent specialization with domain-specific constraints
- [ ] Automated scope detection based on task analysis

**Phase 3 (Long-term)**:
- [ ] Change complexity scoring with escalation thresholds
- [ ] Historical pattern learning from over-engineering incidents
- [ ] Continuous improvement feedback loops

**CRITICAL SUCCESS FACTOR**: Balancing AI capability with mature codebase sensitivity through explicit approval gates and domain expert consultation protocols.

## LLM Issue Reporting and Improvement Tracking

### Komposteur and Video Renderer Improvement Guidelines
- If LLM identifies needed changes/fixes in sub-process/library Komposteur, video-renderer etc, write a comprehensive report for Claude agents responsible for these, detailing:
  - Specific issues discovered
  - Current state of the component
  - Desired future state and recommended improvements
  - Potential impact on overall system performance
- this project is a learning process. Each run is to validate our assumptions, find flaws and improvements. MCP server is for exploratory, Komposteur is for make it production ready with lessons learned