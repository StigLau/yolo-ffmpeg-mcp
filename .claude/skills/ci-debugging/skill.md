---
name: ci-debugging
description: CI/CD debugging and Build Detective analysis patterns. Activated when investigating CI failures, Docker build issues, or test pipeline problems.
---

# CI Debugging Patterns

## First Response Protocol

1. **Compare environments**: CI vs local EXACTLY
2. **Check main branch**: Does it have this issue?
3. **Read the actual error**: Not the symptom, the root cause
4. **Simplest fix first**: Usually 1-3 lines

## Build Detective Integration

- Run BD analysis BEFORE expensive LLM operations
- BD reports available via Build Detective subagent
- High confidence (>8/10) = direct implementation
- Use BD confidence scores to validate changes

## Common CI Pitfalls

### Import Errors
```python
# Always make heavy deps optional in CI:
try:
    import docker
except ImportError:
    docker = None
```

### Path Issues
- CI uses different paths than local
- Check for hardcoded paths in test files
- Use relative paths or environment variables

### Docker Build Issues
- Check if base image has required system packages
- Verify COPY paths match actual file locations
- Layer caching: order Dockerfile commands by change frequency

## Anti-Pattern: The Whack-a-Mole Cycle

```
Real Issue: Missing try/except (3 lines)
  → LLM Fix 1: Dockerfile changes
  → LLM Fix 2: src/ restructuring
  → LLM Fix 3: 301-line workflow replacement
  → Real Fix: try/except ImportError (3 lines) ✅
```

**90% of CI failures from LLM code changes are simple fixes.**
