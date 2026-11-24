# Project state
updated: 2026-11-24
head: b3d1495

## Goal & scope
Personal Learning Base Builder: Udemy course transcripts, quizzes and attachments become clean Markdown for NotebookLM/LLMs (Python engine, `python -m engine <cmd>`, SQLite). AI extraction (vocab/knowledge) and the Claude-skill exporter were removed on purpose; do not rebuild them unprompted.
Second track (this session): an agent-productivity skill set under `.claude/skills/` that carries project state across sessions and encodes context, prompt and orchestration practice from the CCAR course. Out of scope: other projects for now (workspace-local on purpose, for audit).

## Current state
Ingestion pipeline is complete and unchanged this session: login, fetch, import, clean, export notebooklm, stats. CCAR (`certified-claude-architect-masterclass-2026`) is the only dev/test course.
The four-skill set is written and tested but uncommitted: project-state (hooks + installer), context-discipline, prompt-craft, agent-orchestration. Hooks are wired in `.claude/settings.json`.

## In progress
- (none)

## Next
1. User reviews and commits `.claude/`, `tests/test_state_*.py`, `docs/agent-skills.md`, the CLAUDE.md block.
2. Live-test the Stop nudge in a real session (unit-tested only so far).
3. Later: move the skills to user level or a plugin once audited (user's choice).

## Done
- Hook script `state_hook.py` (SessionStart inject, Stop nudge + secret scan, PreCompact) and `install.py`: `python -m pytest tests/test_state_hook.py tests/test_state_install.py` -> 35 passed.
- Skills context-discipline, prompt-craft, agent-orchestration written from CCAR lessons, then reviewed against the lessons, Anthropic skill best practices and Claude Code docs; source tags `[CCAR NN]` restored after a fixer pass had stripped them.
- `init` run on this repo: settings.json hooks + CLAUDE.md block installed.
- Acceptance (b): `claude -p "Hello"` in a fresh session replied in Vietnamese with the in-progress item and next step, from the injected state alone.
- `docs/agent-skills.md` (Vietnamese guide) written.

## Open questions
- Where the skills should finally live (user-level vs plugin) and when to leave workspace-local.
- Whether to keep the 14-day / 30-commit staleness limits (my defaults, not user-specified).

## Constraints & gotchas
- Code comments English; CLI messages and project docs Vietnamese. Skills are English; replies to the user Vietnamese.
- `config.local.yaml` holds the Udemy token: never grep or print it.
- Project hooks run only after the workspace trust dialog is accepted; additionalContext is capped at 10,000 chars.
- Ask decisions with AskUserQuestion, not chat lists.

## Last session
Built the four-skill set and hooks via grilling (Q1-Q20) plus two review workflows. Left: user review and commit; Stop nudge not yet seen live.
First thing next: ask the user to review and commit, then watch a real Stop nudge.
