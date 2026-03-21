# AI Over-Engineering Restraint Research - Key Findings

## Problem Statement
**Critical Issue**: AI assistants (Claude) tend to over-engineer solutions, making excessive file changes and going down rabbit holes when mature codebases require only small, targeted fixes.

**Root Cause Pattern**: PR 22 demonstrated the classic symptom → 5 complex fixes → 3-line root cause solution cycle.

## Research Sources Analysis

### 1. The Ground Truth Workflow (Substack)
**Key Insight**: Structure prevents chaos through granular task management.

**Restraint Techniques**:
- **Structured Planning**: Create ROADMAP.md with high-level overviews
- **Granular Task Files**: Individual task files with prerequisites, current/desired states
- **Step-by-Step Execution**: "Stop after completing each step and wait for further instructions"
- **Context Grounding**: Explicit planning documents in AI context
- **Session Management**: One task per session, clear context between tasks

### 2. Anthropic Engineering Best Practices
**Key Insight**: Planning before coding prevents over-engineering.

**Constraint Methods**:
- **Plan Before Code**: "Ask Claude to make a plan first" with "think" triggers
- **Test-Driven Development**: Write failing tests → minimal implementation → verification
- **Iterative Visual Validation**: 2-3 increments with reference points
- **Scope Constraints**: Extremely specific instructions + explicit "what NOT to do"
- **Course Correction**: Escape key, /clear, checklists, multiple instances for verification

### 3. Spec-Driven Development Framework (GitHub)
**Key Insight**: Atomic tasks prevent scope creep.

**Workflow Patterns**:
- **Requirements → Design → Tasks → Implementation** structure
- **Atomic, Agent-Friendly** task breakdowns
- **Steering Documents** for persistent project context
- **60-80% Token Reduction** through efficient document processing
- **Slash Commands** for controlled interactions (/spec-create, /spec-execute)

### 4. Anthropic Claude Code Documentation
**Key Insight**: Incremental improvement over comprehensive rewrites.

**Mature Codebase Principles**:
- **Minimal Change Approach**: Start broad → narrow to specific areas
- **Backward Compatibility**: Maintain existing behavior
- **Small Testable Increments**: Refactoring in digestible pieces
- **Domain Language**: Use project-specific terminology
- **Plan Mode**: Safe, read-only analysis before changes

## Core Anti-Over-Engineering Strategies

### A. Pre-Implementation Constraints
1. **Mandatory Planning Phase**: Force AI to plan before any code changes
2. **Root Cause Analysis First**: Compare branches, identify simplest solution
3. **Explicit Scope Definition**: Define maximum number of files/lines to change
4. **YOLO Mode Approval**: Require explicit permission for extensive changes

### B. Implementation Restraints
1. **One Change Per Commit**: Force atomic, reviewable changes
2. **Stable Point Jumping**: Work from compilation → tests → next stable state
3. **Test-First Validation**: Write tests before implementation
4. **Change Impact Assessment**: Estimate affected files before starting

### C. Course Correction Protocols
1. **Interrupt Capability**: ESC key, /clear for mid-process stops
2. **Build Detective First**: Use BD tools before LLM analysis for build issues
3. **Branch Comparison**: When debugging, compare working vs broken branches first
4. **Token Budget Awareness**: Stop and reassess after significant token usage

## Specific Protocols for Mature Codebases

### The "3-Line Rule"
**Principle**: If root cause is likely <10 lines of code, spend more time analyzing than implementing.

**Implementation**:
1. **Analysis Phase**: Use Build Detective, compare branches, identify patterns
2. **Minimal Fix Hypothesis**: Propose simplest possible solution first
3. **Escalation Threshold**: Only expand scope with explicit user approval

### The "Stable Point Protocol"
**Principle**: Always work from known-good state to known-good state.

**Steps**:
1. **Verify Starting Point**: Ensure current state compiles/tests pass
2. **Single Change**: Make one logical change
3. **Verification**: Confirm new state is stable (BD local CI)
4. **Commit**: Version the change before next modification

### The "Domain Expert Consultation"
**Principle**: Senior developers know the codebase; ask instead of assuming.

**Implementation**:
1. **Context Questions**: "What's the typical pattern for X in this codebase?"
2. **Historical Context**: "Has this issue occurred before?"
3. **Preference Queries**: "Do you prefer approach A or B for this type of change?"
4. **Impact Assessment**: "Will this change affect any other systems?"

## Implementation Recommendations

### Immediate Actions
1. **Add explicit approval gates** for changes affecting >3 files
2. **Implement Build Detective first** protocol for CI failures
3. **Create change impact estimator** before any modifications
4. **Establish "pause and ask" checkpoints** during complex tasks

### Long-term Process Changes
1. **Subagent specialization** for domain-specific constraints
2. **Automated scope detection** based on task analysis
3. **Change complexity scoring** with escalation thresholds
4. **Historical pattern learning** from previous over-engineering incidents

## Success Metrics
- **Reduced PR Size**: Average files changed per PR
- **First-Fix Success Rate**: Problems solved in first attempt vs iteration cycles  
- **Build Detective Usage**: BD analysis before LLM token consumption
- **User Satisfaction**: Less overwhelming change review burden

## Conclusion
The research consistently points to **structured constraint systems** that force deliberate, incremental changes over comprehensive rewrites. The key is creating **friction for expansion** and **smooth paths for minimal fixes**.

**Critical Success Factor**: Balancing AI capability with mature codebase sensitivity through explicit approval gates and domain expert consultation protocols.