# Agent Workflow Usage Guide

*How to work with specialized agents in YOLO-FFMPEG-MCP development*

## Core Principle
**Specialized agents handle domain-specific tasks while general Claude handles coordination and complex reasoning.** This reduces context overhead and keeps agents focused on their expertise.

## Available Agents

### `modular-architect`
**When to Use**: Structural decisions, code organization, module boundaries
```
User: "We need to add speech detection to video processing. How should this be structured?"
→ Claude routes to modular-architect
→ Agent provides ASCII module map + boundary justification
→ User gets focused architectural recommendation
```

### `reviewer-readonly`  
**When to Use**: Code review before merge, risk assessment
```
User: "Review this MCP tool implementation for merge readiness"
→ Claude routes to reviewer-readonly  
→ Agent provides risk ranking + inline comments + merge/no-merge decision
→ User gets focused code quality assessment
```

## Workflow Integration

### 35-Minute Build Loop
```
Minute 0-5: Frame
- Update docs/01-scope.md with current objective
- Check YOLO_CONTEXT.md alignment

Minute 5-20: Build  
- Use agents for specialized tasks:
  * modular-architect: "How should I structure this new feature?"
  * reviewer-readonly: "Is this code ready for merge?"
- Request patch diffs, not full rewrites
- Keep changes surgical (max 3 files unless sequential debugging)

Minute 20-30: Test
- Verify BD local CI passes
- Test MCP integration manually
- Run relevant unit tests

Minute 30-35: Commit & Compress
- Commit with clear message
- Update docs/02-decisions.md if architectural decision made
- Update YOLO_CONTEXT.md if boundaries changed
```

### Agent Routing

#### Automatic Routing
Claude should automatically route these patterns:
- **"How should I structure..."** → `modular-architect`
- **"Review this code..."** → `reviewer-readonly`
- **"Is this ready to merge..."** → `reviewer-readonly`

#### Explicit Routing
Force specific agent when auto-routing fails:
```
@modular-architect: Propose directory structure for new speech detection module
@reviewer-readonly: Review the attached MCP tool implementation for integration safety
```

## Agent Expectations

### What Agents Should Deliver
- **Domain-Focused Output**: Stay within their expertise area
- **Actionable Recommendations**: Specific, implementable suggestions  
- **Context Awareness**: Read YOLO_CONTEXT.md and understand project boundaries
- **Consistent Patterns**: Follow established project conventions

### What Agents Should NOT Do
- **Code Implementation**: Provide structure/review, not code
- **Business Logic**: Focus on technical implementation quality
- **Cross-Domain Tasks**: Stay within their specialized role
- **Over-Analysis**: Provide focused, actionable feedback

### Agent Learning Pattern
Agents should accumulate project knowledge through:
- **YOLO_CONTEXT.md**: Current state and patterns
- **docs/02-decisions.md**: Historical architectural decisions
- **Previous Interactions**: Learn from past reviews/recommendations

## Error Patterns & Recovery

### When Agents Go Off-Track
**Symptoms**:
- Agent provides generic advice instead of project-specific recommendations  
- Agent tries to implement code instead of providing structural guidance
- Agent ignores established project boundaries/patterns

**Recovery**:
1. **Redirect**: "Focus only on [specific domain area] for this project"
2. **Context Refresh**: "Read YOLO_CONTEXT.md and provide recommendation based on current architecture"
3. **Scope Limit**: "Provide only structural recommendations, no implementation"

### When to Use General Claude
- **Complex Coordination**: Multi-domain tasks requiring broad reasoning
- **Integration Debugging**: Issues spanning multiple systems
- **Strategic Planning**: High-level project direction and prioritization
- **Context Synthesis**: Understanding complex interactions between systems

## Success Metrics

### Agent Effectiveness
- **Focused Output**: Agents stay within domain expertise  
- **Project Awareness**: Recommendations align with current architecture
- **Actionable Results**: Suggestions can be implemented without additional research
- **Context Retention**: Agents remember project patterns across sessions

### Workflow Efficiency  
- **Reduced Token Usage**: Agents handle specialized tasks without general context
- **Faster Decisions**: Domain expertise accelerates task completion
- **Consistent Quality**: Specialized focus improves output reliability
- **Lower Cognitive Load**: User doesn't need to provide full context for specialized tasks

## Testing & Validation

### Agent Testing Protocol
1. **Give Real Task**: Provide actual project challenge in agent's domain
2. **Evaluate Focus**: Did agent stay within expertise boundaries?
3. **Assess Quality**: Are recommendations actionable and project-appropriate?
4. **Check Learning**: Does agent retain context for follow-up questions?

### Toxicity Detection
**Warning Signs**:
- Agent becomes too generic (loses specialization value)
- Agent creates more complexity than it solves
- Agent recommendations conflict with project constraints
- Agent requires excessive context re-explanation

**Mitigation**:
- **Branch Reversion**: This is all on experimental branch for easy rollback
- **Agent Refinement**: Update agent configuration based on real usage
- **Selective Usage**: Use agents only for tasks where they add clear value

## Implementation Notes

### Current Status
- **Experimental Branch**: `feature/agent-workflow-experiment`
- **Agent Configs**: `.claude/agents/modular-architect.md`, `.claude/agents/reviewer-readonly.md`
- **Documentation Structure**: `docs/01-scope.md`, `docs/02-decisions.md`, `docs/03-tasks.md`, `YOLO_CONTEXT.md`

### Next Steps
1. **Test modular-architect** with real structural decision
2. **Test reviewer-readonly** with actual code review
3. **Evaluate effectiveness** vs general Claude approach
4. **Refine or revert** based on practical results

---
*This guide evolves based on real usage experience. Update based on what works in practice.*