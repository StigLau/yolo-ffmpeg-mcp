---
name: multi-agent
description: Multi-agent orchestration patterns for video processing. Activated when coordinating FastTrack, Komposteur, VideoRenderer, or VDVIL subagents.
---

# Multi-Agent Orchestration

## YOLO operates as master orchestrator coordinating specialized subagents:

| Agent | Role |
|-------|------|
| **FastTrack** | Video analysis, strategy selection ($0.02-0.05/analysis) |
| **Komposteur** | Beat-synchronization, S3 infrastructure |
| **VideoRenderer** | FFmpeg optimization, crossfade processing |
| **VDVIL** | DJ-mixing, audio composition |
| **Build Detective** | CI/build failure analysis |

## Coordination Flow

FastTrack analysis → Audio (VDVIL) → Beat-sync (Komposteur) → Crossfades (VideoRenderer) → Final assembly (YOLO)

## Delegation Strategy

- Route tasks to specialized subagents based on content analysis
- Parallel processing: multiple agents work simultaneously
- Quality assurance: master oversight with consistent standards
- Cost optimization: intelligent resource sharing with budget awareness

## LLM Issue Reporting

When identifying needed changes in sub-projects (Komposteur, VideoRenderer, etc.):
1. Write a comprehensive report for Claude agents responsible
2. Detail: specific issues, current state, desired state, impact
3. This project is exploratory; Komposteur is production-ready
