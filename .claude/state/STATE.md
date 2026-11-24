# Project state
updated: 2026-11-24
head: b3d1495

## Goal & scope
Personal Learning Base Builder: Udemy course transcripts, quizzes and attachments become clean Markdown for NotebookLM/LLMs (Python engine, `python -m engine <cmd>`, SQLite). AI extraction (vocab/knowledge) and the Claude-skill exporter were removed on purpose; do not rebuild them unprompted.
Second track (this session): an agent-productivity skill set under `.claude/skills/` that carries project state across sessions and encodes context, prompt and orchestration practice from the CCAR course. Out of scope: other projects for now (workspace-local on purpose, for audit).

## Current state
Ingestion pipeline is complete and unchanged this session: login, fetch, import, clean, export notebooklm, stats. CCAR (`certified-claude-architect-masterclass-2026`) is the only dev/test course.
project-state (hooks + installer) is the active skill; the three knowledge skills (context-discipline, prompt-craft, agent-orchestration) are manual references. All uncommitted. Hooks are wired in `.claude/settings.json`.

## In progress
- (none)

## Next
1. User reviews and commits `.claude/`, `tests/test_state_*.py`, `docs/agent-skills.md`, the CLAUDE.md block.
2. Watch whether `project-state` earns its keep over a few weeks (stale state? Stop nudges useful?).
3. Later: move the skills to user level or a plugin once audited (user's choice).

## Done
- Hook script `state_hook.py` (SessionStart inject, Stop nudge + secret scan, PreCompact) and `install.py`: `python -m pytest tests/test_state_hook.py tests/test_state_install.py` -> 35 passed.
- Skills context-discipline, prompt-craft, agent-orchestration written from CCAR lessons, then reviewed against the lessons, Anthropic skill best practices and Claude Code docs; source tags `[CCAR NN]` restored after a fixer pass had stripped them.
- `init` run on this repo: settings.json hooks + CLAUDE.md block installed.
- Acceptance (b): `claude -p "Hello"` in a fresh session replied in Vietnamese with the in-progress item and next step, from the injected state alone.
- A/B test done (40 agents, wf_dc010c64-2df): prompt-craft T1 3W/0L/1T, T2 4W/0L; agent-orchestration T3 2W/2L; context-discipline T4 6,6 vs 5,6 of 7, T5 13/13 both. Only prompt-craft showed benefit; T3 and part of T1 were contaminated by the control worktree (no data/, worktree path in the brief). Tasks T4/T5 were at the ceiling.
- A/B round 2 (60 agents, objective grading, functional runs, wf_a04a7cb1-977): prompt-craft no gain (P1 20/20 vs 20/20,19/20; P2 control found more real issues: 10,15 vs 7,13); context-discipline C1 10,10 vs 9,10 (wrong 0 vs 1), C2 14/14 both; agent-orchestration O1 6,7 vs 7,6, O3 7,6 vs 6,6, O2 control 4,5 vs treat 2,2 (skill rejects fan-out; arguable ground truth). Round-1 judge preference for prompt-craft did not replicate functionally.
- User chose to demote: context-discipline, prompt-craft, agent-orchestration now `disable-model-invocation: true` (manual /name only); CLAUDE.md block trimmed to 3 bullets; `tests/test_skills_frontmatter.py` added after an unquoted `: ` in a description broke YAML silently. 126 tests pass.
- `docs/agent-skills.md` (Vietnamese guide) written.
- Stop nudge seen live: it fired on agent worktrees under `.claude/worktrees/` (false positive). Fixed with IGNORED_PREFIXES + test; 36 hook/installer tests pass.

## Open questions
- Where the skills should finally live (user-level vs plugin) and when to leave workspace-local.
- Whether to keep the 14-day / 30-commit staleness limits (my defaults, not user-specified).

## Constraints & gotchas
- Code comments English; CLI messages and project docs Vietnamese. Skills are English; replies to the user Vietnamese.
- `config.local.yaml` holds the Udemy token: never grep or print it.
- Project hooks run only after the workspace trust dialog is accepted; additionalContext is capped at 10,000 chars.
- Ask decisions with AskUserQuestion, not chat lists.

## Last session
Built the four-skill set and hooks via grilling (Q1-Q20) plus two review workflows. Left: user review and commit.
First thing next: ask the user to commit `.claude/`, `tests/`, `docs/agent-skills.md`, CLAUDE.md.
