# Project Restructure Report: yolo-ffmpeg-mcp

**Date**: 2026-03-21
**Branch**: cleanup/project-restructure
**Base**: main

## Executive Summary

The project has accumulated significant cruft: 40+ root-level files, 7 sub-project directories that don't belong, ~210MB of duplicated test media, 43 remote branches (18 already merged), and a 428-line CLAUDE.md filled with anti-pattern essays. This report details what to move, delete, and restructure.

---

## 1. Root Directory Audit

### Current State: 59 files, 23 directories at root level

**Files that belong at root** (keep as-is):
- `CLAUDE.md`, `README.md`, `pyproject.toml`, `Makefile`, `Dockerfile`, `.gitignore`
- `.mcp.json`, `.python-version`, `.dockerignore`, `containerfile`
- `uv.lock` (dependency lock)

**Files to MOVE to `docs/`**:
| File | Destination |
|------|-------------|
| `AGENT_WORKFLOW_USAGE.md` | `docs/ai-generated/` |
| `AI_OVER_ENGINEERING_RESTRAINT_RESEARCH.md` | `docs/ai-generated/` |
| `CLAUDE_CODE_WORKFLOW.md` | `docs/ai-generated/` |
| `DEVELOPMENT_NOTES.md` | `docs/` |
| `DOCKER_IMAGES_USED.md` | `docs/ai-generated/` |
| `FASTTRACK_SUBAGENT_COMPLETE.md` | `docs/ai-generated/` |
| `FASTTRACK_VS_BUILD_DETECTIVE_COMPARISON.md` | `docs/ai-generated/` |
| `java_management_guide.md` | `docs/ai-generated/` |
| `KOMPOSTEUR_INTEGRATION_REQUEST.md` | `docs/ai-generated/` |
| `KOMPOSTEUR_ISSUES_FOR_CLAUDE.md` | `docs/ai-generated/` |
| `LANDSCAPE_VIDEO_SOLUTION.md` | `docs/ai-generated/` |
| `MCP_REGISTRY_AND_CACHING_SYSTEM.md` | `docs/ai-generated/` |
| `MCP_SERVER_HAIKU_IMPROVEMENTS.md` | `docs/ai-generated/` |
| `NATURAL_LANGUAGE_MUSIC_VIDEO_DEMO.md` | `docs/ai-generated/` |
| `PRIORITY_IMPLEMENTATION_COMPLETE.md` | `docs/ai-generated/` |
| `PROJECT_STRUCTURE.md` | `docs/` |
| `RUSTY_MUSIC_VIDEO_PROJECT.md` | `docs/ai-generated/` |
| `SECURITY_ALERT.md` | `docs/` |
| `TESTING_README.md` | `docs/` |
| `TODO_RESTORE_FILTER_ANALYSIS_CI.md` | `docs/ai-generated/` |
| `VIDEO_FORMAT_STRATEGY.md` | `docs/ai-generated/` |
| `VIDEORENDERER_CICD_KNOWLEDGE_TRANSFER.md` | `docs/ai-generated/` |
| `YOLO_CONTEXT.md` | `docs/ai-generated/` |
| `YOUTUBE_API_CREDENTIALS_SETUP.md` | `docs/` |
| `YOUTUBE_DOWNLOAD_COMPILATION_ISSUES.md` | `docs/ai-generated/` |
| `ZOMBIE_PROCESS_MANAGEMENT.md` | `docs/ai-generated/` |

**Files to MOVE to `tests/`**:
| File | Destination |
|------|-------------|
| `test_ai_integration_comparison.py` | `tests/dev/` |
| `test_ci_working.py` | `tests/ci/` |
| `test_gemini_fixed.py` | `tests/dev/` |
| `test_haiku_ts_performance.py` | `tests/dev/` |
| `test_registry_guided_llm_collaboration.py` | `tests/dev/` |
| `test_registry_guided_llm_collaboration_fixed.py` | `tests/dev/` |
| `test_true_registry_guided_collaboration.py` | `tests/dev/` |

**Files to MOVE to `scripts/`**:
| File | Destination |
|------|-------------|
| `test_ci_config.sh` | `scripts/` |
| `test_mcp_natural_environment.sh` | `scripts/` |
| `test_music_video_creation.sh` | `scripts/` |
| `test-local-ci.sh` | `scripts/` |
| `run_full_test.sh` | `scripts/` |

**Files to DELETE** (junk/generated):
| File | Reason |
|------|--------|
| `.modified` | Empty file, no purpose |
| `knowledge_graph.db` | SQLite database, generated artifact |
| `firestore.rules.test` | Orphaned config fragment |
| `.env.local` | Should be gitignored (already in .gitignore but committed) |
| `.env.example` | Move to `config/` |
| `.eslintrc.json` | Orphaned, no JS at root |
| `haiku_generated_music_video_description.txt` | Generated artifact |
| `Dockerfile.ci` | Duplicate (already in `docker/`) |
| `.aider.chat.history.md` | Should be gitignored |
| `.aider.input.history` | Should be gitignored |

---

## 2. Sub-Project Directories Audit

### Directories that DON'T belong in this repo:

| Directory | Size | Content | Recommendation |
|-----------|------|---------|----------------|
| `bd-project/` | 0B | Empty | **DELETE** |
| `komposteur-repo/` | 0B | Empty | **DELETE** |
| `vdvil/` | 0B | Empty | **DELETE** |
| `VideoRenderer/` | 0B | Empty | **DELETE** |
| `haiku-mcp-ts/` | 320K | Separate TypeScript MCP server | **Separate repo or delete** |
| `typescript-mcp/` | 116K | Another TypeScript MCP | **Separate repo or delete** |
| `haiku-integration/` | 228K | Haiku LLM integration | **Move to `integration/haiku/`** |
| `integration/` | 152K | Java/Komposteur integration | **Keep, consolidate** |
| `komposteur-github-workflows/` | 48K | CI configs for another repo | **DELETE** (belongs in komposteur) |
| `mcp-scripts/` | 96K | MCP utility scripts | **Merge into `scripts/`** |

### Directories to KEEP (core project):

| Directory | Purpose |
|-----------|---------|
| `src/` | Python source code |
| `tests/` | Test suite |
| `docs/` | Documentation (consolidate `documents/` into this) |
| `scripts/` | Utility scripts |
| `tools/` | Analysis tools |
| `examples/` | Example configs and workflows |
| `docker/` | Dockerfile variants |
| `deployment/` | Deploy configs |
| `config/` | Configuration files |
| `presets/` | Effect presets |
| `archive/` | Legacy/historical |
| `.github/` | CI/CD workflows |
| `.claude/` | Claude Code config |

### `documents/` vs `docs/` - CONSOLIDATE

Both exist. Merge `documents/` into `docs/` and delete `documents/`.

---

## 3. Test Media - Duplicate Elimination (~70MB savings)

### Duplicated files between `.testdata/` and `tests/files/`:
- `_wZ5Hof5tXY_136.mp4` (10MB) - in both
- `JJVtt947FfI_136.mp4` (16MB) - in both
- `Subnautic Measures.flac` (27MB) - in both

### Recommendation:
1. Keep `tests/files/` as the single test media location
2. Delete `.testdata/` entirely (140MB)
3. Add `tests/files/` large media to `.gitignore` and use Git LFS or download script
4. Currently `.gitignore` blocks `*.mp4` and `*.mov` but these are committed via `.testdata/`

---

## 4. Branch Cleanup

### 18 Remote Branches - MERGED (safe to delete):
```
origin/docs/architecture-consolidation-strategy
origin/feature/build-detective-system
origin/feature/ci-analyzer-shared-setup
origin/feature/docker-build-optimization
origin/feature/end-to-end-music-video-test
origin/feature/mcp-server-priority-implementations
origin/feature/mcp-testing-ci-integration
origin/feature/mcp-testing-suite
origin/feature/transition-effects
origin/feature/typescript-mcp-investigation
origin/feature/video-filter-testing
origin/feature/video-format-strategy
origin/feature/youtube-direct-upload
origin/feature/youtube-quality-intelligence
origin/fix/ci-script-permissions
origin/fix/ci-test-failures
origin/haiku-llm-integration
```

### 24 Remote Branches - UNMERGED (evaluate individually):

**Dependabot (auto-close or merge)**:
- `dependabot/npm_and_yarn/haiku-mcp-ts/*` (4 branches) - for haiku-mcp-ts sub-project
- `dependabot/npm_and_yarn/typescript-mcp/*` (4 branches) - for typescript-mcp sub-project

**Stale feature branches (likely abandon)**:
- `origin/ai-docs-organization` - superseded by current cleanup
- `origin/organize-project-structure` - superseded by current cleanup
- `origin/cleanup/preserve-uncommitted-docs` - evaluate content first
- `origin/feature/golden-mcp-server-restored` - evaluate
- `origin/feature/elm-editor-integration` - evaluate
- `origin/feature/docker-optimizations` - evaluate

**Active/valuable feature branches (merge or rebase)**:
- `origin/feature/container-alternatives` - 3 commits ahead of main
- `origin/feature/video-effects-system` - large feature, evaluate
- `origin/feature/advanced-mcp-server-complete` - evaluate
- `origin/feature/haiku-mcp-server` - if keeping haiku-mcp-ts
- `origin/feature/standalone-haiku-mcp-server` - if keeping haiku-mcp-ts
- `origin/feature/sonnet-outer-llm` - evaluate
- `origin/feature/registry-and-audio-integration` - evaluate
- `origin/feature/cloud-music-video-app` - evaluate
- `origin/mcp-media-discovery-fixes` - evaluate
- `origin/feature/youtube-integration` - evaluate

### 2 Local Branches (not on main):
- `feature/container-alternatives` - 3 commits ahead, merge to main
- `feature/video-effects-system` - subset of container-alternatives

---

## 5. CLAUDE.md Overhaul

### Problem
Current CLAUDE.md is 428 lines, ~60% of which are anti-pattern essays and case studies that belong in documentation, not agent instructions. Inspired by kompo.ai's approach:

### New Structure
1. **CLAUDE.md** (~80 lines): Project identity, quick start, core rules, navigation
2. **`.claude/skills/`**: Reusable patterns extracted from CLAUDE.md
   - `core-philosophy/skill.md` - Over-engineering prevention, consultation rules
   - `video-processing/skill.md` - FFmpeg patterns, format strategy
   - `ci-debugging/skill.md` - Build Detective, CI comparison protocol
   - `multi-agent/skill.md` - Subagent orchestration patterns

---

## 6. .gitignore Improvements

### Add to .gitignore:
```
# Test media (use download script instead)
.testdata/

# Generated databases
*.db

# Environment files (already partially covered)
.env.local
.env.example

# Empty marker files
.modified

# Aider files (strengthen pattern)
.aider*
```

---

## 7. Proposed Target Structure

```
yolo-ffmpeg-mcp/
├── .claude/
│   ├── settings.local.json
│   └── skills/
│       ├── core-philosophy/
│       ├── video-processing/
│       ├── ci-debugging/
│       └── multi-agent/
├── .github/workflows/
├── src/                          # Python source (unchanged)
├── tests/
│   ├── ci/
│   ├── dev/
│   ├── docker/
│   ├── data/
│   └── files/                    # Single test media location
├── docs/
│   ├── ai-generated/             # All AI-written docs
│   ├── architecture/
│   ├── guides/
│   └── archive/
├── scripts/                      # All shell/utility scripts
├── tools/                        # Analysis tools
├── examples/
│   ├── komposition-examples/
│   ├── effect-templates/
│   └── video-workflows/
├── docker/                       # Dockerfile variants
├── deployment/                   # Deploy configs
├── config/                       # Configuration files
├── presets/                      # Effect presets
├── integration/                  # External integrations (if keeping)
├── archive/                      # Legacy code
├── CLAUDE.md                     # Lean agent instructions
├── README.md
├── pyproject.toml
├── Makefile
├── Dockerfile
├── .gitignore
├── .mcp.json
└── uv.lock
```

**Root: 10 files + 14 directories** (down from 59 files + 23 directories)
