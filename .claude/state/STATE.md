# Project state
updated: 2026-11-24
head: bec29ea

## Goal & scope
Personal Learning Base Builder: Udemy course transcripts, quizzes and attachments become clean Markdown for NotebookLM/LLMs (Python engine, `python -m engine <cmd>`, SQLite). AI extraction (vocab/knowledge) and the Claude-skill exporter were removed on purpose; do not rebuild them unprompted.
Second track (this session): an agent-productivity skill set under `.claude/skills/` that carries project state across sessions and encodes context, prompt and orchestration practice from the CCAR course. Out of scope: other projects for now (workspace-local on purpose, for audit).

## Current state
Ingestion pipeline is complete and unchanged this session: login, fetch, import, clean, export notebooklm, stats. CCAR (`certified-claude-architect-masterclass-2026`) is the only dev/test course.
project-state (hooks + installer + structure lint) is the active skill; the three knowledge skills (context-discipline, prompt-craft, agent-orchestration) are manual references. Much of the session's work is uncommitted (see git status). Hooks are wired in `.claude/settings.json`.

## In progress
- (none)

## Next
1. User reviews and commits the pending skill edits, tests, docs and state files (git status).
2. Watch whether `project-state` earns its keep over a few weeks (stale state? Stop nudges useful?).
3. Later: move the skills to user level or a plugin once audited (user's choice).

## Done
- 2026-11-24: Contract spec A/B (wf_da046088-f4e, 80 agents): valid rate 100% in both arms (prose vs JSON Schema + example) on 4 contracts and 2 models, so the locked rule ships no schema files; value correctness was higher with the example (C1 1.0 vs 0.7, C2 0.9 vs 0.6), from the example not the schema (docs: DECISIONS.md).
- 2026-11-24: Five extensions (wf_ffcf7da6-43f): STATE.md structure lint in the once-per-session Stop nudge + `state_hook.py check`, testing-prompts expansion, subtask criteria, handoff audit log, replan triggers; SKILL.md net-zero; 172 tests pass. Verifiers caught a secret leak in `check` (head: line) and non-UTF-8 crashes; both fixed and reproduced.
- 2026-11-24: mattpocock mechanisms adopted net-zero (phase-boundary tree, two-axis review, ADR gate, reference-not-copy, fail-closed hook example) + CCA-F domain map in docs/agent-skills.md; docs verifier was wrong once on the hook trust dialog, corrected from the hooks page verbatim.
- 2026-11-24: Quiz benchmark closed (docs/quiz-benchmark.md): Sonnet and Haiku, no skills, blind, ~100% on tests 1-3 and 59/60 on test 4; no rule passes the 30% rule; tests 5-6 stay sealed.
- 2026-11-24: Two A/B rounds (100 agents) found no reliable gain from the knowledge skills; context-discipline, prompt-craft, agent-orchestration are now manual (`disable-model-invocation: true`); `tests/test_skills_frontmatter.py` guards YAML (an unquoted `: ` silently drops frontmatter).
- 2026-11-24: Stop nudge seen live: false positive on `.claude/worktrees/`, fixed with IGNORED_PREFIXES + test.
- 2026-11-24: `docs/agent-skills.md` (Vietnamese guide, CCA-F domain map) written.

## Open questions
- Where the skills should finally live (user-level vs plugin) and when to leave workspace-local.
- Whether to keep the 14-day / 30-commit staleness limits (my defaults, not user-specified).

## Constraints & gotchas
- Code comments English; CLI messages and project docs Vietnamese. Skills are English; replies to the user Vietnamese.
- `config.local.yaml` holds the Udemy token: never grep or print it.
- Interactive sessions hold project hooks back until the workspace trust dialog is accepted; `claude -p` and the SDK run them without it. additionalContext is capped at 10,000 chars.
- Ask decisions with AskUserQuestion, not chat lists.

## Last session
Audited the user's review (34/39 techniques already covered), ran the contract A/B (no schemas), added five small extensions with a hook-side STATE.md lint. Left: user review and commit.
First thing next: ask the user whether to commit.
