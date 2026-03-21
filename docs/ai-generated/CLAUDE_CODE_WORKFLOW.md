# The Claude Code Workflow You Can Copy

*This is the workflow I use when I want useful code fast without creating a mess I'll regret later. It's opinionated, repeatable, and built around Claude Code's strengths (agents, short feedback loops, clean diffs).*

## 0. One-Time Setup

Create this project structure:

```
/docs/01-scope.md         # single source of truth for goals & constraints
/docs/02-decisions.md     # architecture decisions log (ADR-style, <10 bullets)
/docs/03-tasks.md         # running task list with checkboxes
/PLAYBOOK.md              # "how this project works" for future-me / team
/CONTEXT.md               # compressed summary Claude reads first
/src/                     # code
/tests/                   # tests (even if thin)
/scripts/                 # one-off utilities (seed, migrate, import)
```

**Keep CONTEXT.md tiny (≤ 200 lines).** Describe modules, data shapes, APIs, and non-negotiables. Update it after every milestone.

## 1. Create Five Focused Agents

In Claude Code: `claude update → /agents`.

Make these once; reuse everywhere:

### `mvp-planner`
- **Role**: Turn a vague goal into a MVP with a crisp scope.
- **Always output**: 
  - "We will NOT build" list
  - Risks with mitigation

### `ui-stylist`
- **Role**: Restyle components to a design token set (typography, spacing, colour).
- **Constraints**: no library swaps without approval; return a patch diff only.

### `bug-fixer`
- **Role**: Reproduce, write a failing test, fix, and return a minimal patch.
- **Always include**: root cause in 1–2 sentences.

### `modular-architect`
- **Role**: Propose directory structure, boundaries, and interfaces.
- **Output**: ASCII module map + reasons for each boundary.

### `reviewer-readonly`
- **Role**: Code review with NO edits.
- **Return**: inline comments, risk ranking (High/Med/Low), and a "merge/no-merge" call.

> Claude will auto-route to these when your prompt matches. If it doesn't, call the agent explicitly.

## 2. The 35-Minute Build Loop

**Run this loop until you ship. Don't stretch it. The constraint keeps quality high.**

### Minute 0–5 — Frame
- Edit `/docs/01-scope.md` (what we're doing next, acceptance)
- Update `/CONTEXT.md` if structure changed

### Minute 5–20 — Build
- Prompt Claude with one atomic task (see templates below)
- Ask for patch diff, not prose
- If you get noise, ask for the same patch but smaller ("touch max 3 files")

### Minute 20–30 — Test
- Request a failing test first, then a fix
- Run locally, keep logs, trim scope if needed

### Minute 30–35 — Commit & Compress
- **Commit**: `feat: add invoice export (csv)`
- Append one line to `/docs/02-decisions.md` if a decision happened
- Rewrite `/CONTEXT.md` deltas (keep it under 200 lines)
- **Repeat**

## 3. Prompt Templates That Actually Work

### A. New Feature (Atomic)
```
Goal: [one sentence]
Constraints: [stack, libraries, patterns that must remain]
Touch budget: max 3 files
Return: unified PATCH DIFF only + brief rationale (≤3 bullets)
Use CONTEXT.md to preserve architecture.
```

### B. Styling Pass (No Logic Changes)
```
Apply design tokens (font scale, spacing, radius).
No JS behaviour edits.
Return patch diff for *.tsx/*.css only.
If tokens missing, create tokens.ts and refactor to use it.
```

### C. Bug Fix with Safety Rails
```
Reproduce bug: [steps]
Write failing test first in /tests/[name].spec.ts.
Then propose smallest fix.
Return: test diff + code diff.
Explain root cause in 2 sentences.
```

### D. "Too Big" Response Recovery
```
Your patch is too large. Split into sequential patches of ≤50 lines each.
Return only PATCH 1 now. I will apply and ask for PATCH 2.
```

## 4. When You Get Stuck, Use the Stuck Ladder (In Order)

1. **Narrow the ask** (one file, one function)
2. **Add a concrete example** (input/output JSON)
3. **Duplicate the page** and reframe the prompt (fresh context often routes the right agent)
4. **Switch the persona** (call `modular-architect` to reshape before coding)
5. **Cut the surface area** (feature flag, ship a smaller slice)

**If you're still stuck after 20 minutes, you're solving the wrong problem. Go back to `/docs/01-scope.md`.**

## 5. Scaling to Large Codebases

### Compress First
Keep `/CONTEXT.md` up to date; ask Claude to regenerate it when modules shift:
```
Summarise repo by modules, public interfaces, data contracts. ≤ 180 lines. 
Highlight coupling hotspots. Output to CONTEXT.md (overwrite).
```

### Work in Slices
"Only touch `/src/billing/*`." Claude respects fences when you declare them.

### Batch Refactors
Lock logic, run the `ui-stylist` or linting changes as separate patches to avoid noisy diffs.

### Index Hotspots
Maintain a short list at the top of `/CONTEXT.md`: "Here be dragons" with file paths.

## 6. Ship Ritual

- [ ] `reviewer-readonly` agent must say "merge" (no edits)
- [ ] Tests run locally (even if minimal)
- [ ] Docs bumped (one line in decisions + any API shape changes)
- [ ] Release note (3 bullets: what changed, risk, rollback)

## 7. Example: Feature from Nothing

**Brief**: "Export invoices to CSV with filters."

### Start
1. **Scope**: add "Export CSV" button, filter by date/status, job finishes
2. `modular-architect`: adds `/src/export` module with interface
3. **Feature prompt (atomic)**: returns patch for service + controller + button stub
4. `bug-fixer`: writes failing test for timezone edge case, then patch
5. **Commit**, decisions line: "CSV uses UTC; display converts to local."

## 8. FAQ in One-Liners

**Why patch diffs?** They anchor Claude to change less, so you get safer edits. This is also why a tool like v0 or ChatGPT is slower for coding with AI as they always regenerate the entire file.

**Why CONTEXT.md?** It's the guardrail. Claude reads it; you maintain it.

**Why 35 minutes?** Long enough to finish a slice, short enough to avoid scope creep. If you can't ship features at a regular cadence your scope is too big.

**Why five agents?** More agents does not equal more speed. These five cover 95% of work. I found that if you have too many it wasn't routing to the correct one.

## 9. Copy-Paste Starter Pack

Add these to the top of every Claude session:

### House Rules:
- Return patch diffs, not prose.
- Respect `/CONTEXT.md` constraints.
- If unsure, propose 2 options with trade-offs (≤80 words).
- Keep changes surgical: max 3 files unless I expand scope.
- If more than 3 files tell me why and what

### First Message in a New Project:
```
Read CONTEXT.md and 01-scope.md.
Propose a clear MVP plan with a JSON backlog.
List what we will NOT build.
Then wait.
```

> I like saying "list what we will not build."

---

**This is the whole thing.** Keep the docs small, keep the tasks atomic, demand patch diffs, and let the agents do the jobs you hired them for.