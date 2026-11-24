# Decisions
Append-only. One entry per decision: date, decision, why, alternatives rejected.

## 2026-11-24 State lives in the repo, not in Claude memory
Why: CCAR 18 (scratchpad with decision log, current state, open questions), diffable, travels with the repo. Rejected: Claude Code memory dir (machine-bound), tickets per task (too heavy for solo work).

## 2026-11-24 Hot/cold split: STATE.md (<=80 lines, auto-injected) + DECISIONS.md (read on demand) + archive/
Why: CCAR 04/18 hot vs cold state; only STATE.md costs context each session. Rejected: one file (decision log would grow and lose reasons).

## 2026-11-24 SessionStart hook injects STATE.md verbatim on startup|resume|clear|compact; CLAUDE.md block holds pointers only
Why: @import loads in full every launch and does not reduce context cost; summaries lose identifiers and decisions (CCAR 16). additionalContext capped at 10,000 chars, so STATE.md is cut at 8,000. Rejected: digest-only injection, no injection after compact.

## 2026-11-24 Stop hook blocks once per session on stale state, over-cap state, or a secret
Why: SessionEnd cannot block, so the end-of-session write is instruction-driven and the hook is the safety net; stop_hook_active prevents loops. Secrets block every time (without echoing the value). Rejected: soft nudge only, no hook.

## 2026-11-24 Hooks as exec-form `python` + args in .claude/settings.json; scripts live inside the skill folder
Why: one source, no copy to keep in sync; `python` verified on this machine. Rejected: settings.local.json (not shared), copying scripts to .claude/hooks/.

## 2026-11-24 Four skills, workspace-local; agent never commits state
Why: user wants easy audit now. Skills: project-state, context-discipline, prompt-craft, agent-orchestration. Rejected: 3 skills (merging prompt-craft), 5 skills (separate resume).

## 2026-11-24 Source tags: every rule carries [CCAR NN] or [practice]
Why: user audits rules against the course. A reviewer-fix pass once deleted all tags to dodge findings; restored and verified against the lessons. Exam trivia and version-specific numbers are left out.

## 2026-11-24 Measure the knowledge skills with a blind A/B before trusting them
Why: reviews only checked fidelity and style, not whether behaviour improves; Claude already has auto-memory, compaction and good defaults. Design: control runs in a clean worktree (no skills, no CLAUDE.md block), treatment is forced to read the matching skill, outputs sanitized of skill names/tags, subjective tasks judged pairwise by two lenses, objective tasks scored on a hidden checklist. Limits: n=2 per cell, forced triggering is a best case, judges are the same model family. Rejected: shipping on opinion.

## 2026-11-24 Stop hook ignores .claude/worktrees/
Why: first live Stop block was a false positive caused by agent worktrees (untracked, newer than STATE.md). State files and worktrees are not project work.

## 2026-11-24 A/B verdict on the knowledge skills (n=2 per cell, forced triggering)
Result: prompt-craft helped on prompt-writing tasks per blind judges; agent-orchestration and context-discipline showed no measurable effect (both arms already single-agent and lossless on compaction). Caveats: control ran in a worktree without gitignored data/ and one brief cited the worktree path, which tilted T1 r1 and T3 r2 toward treatment; judges are the same model family and may favour the skill's brief template; no functional test (running the briefs) yet. Not decided yet: keep, demote to user-invoked, or re-test with harder tasks.

## 2026-11-24 Round-2 A/B verdict: the three knowledge skills show no reliable benefit
Evidence: objective checklists, functional runs (system prompt on 20 labelled paragraphs with Haiku; brief executed as an audit), conflicting-source and trap-laden compaction tasks, orchestration plans. Baseline Claude is at ceiling on most (P1, C2, O1). Small gain only on C1 (fewer false statements). Losses: P2 (brief template with length bound gave fewer findings), O2 (skill pushes single-agent; checklist assumed fan-out). Artifacts: control worktree vs treatment in a dirty main tree; sanitizer renamed the project-state path to `guidance`, which graders counted as wrong in O1, so `wrong` counts for O tasks are unreliable while checklist scores are valid. Only project-state (deterministic hooks) fills a gap Claude does not cover natively.

## 2026-11-24 Demote the three knowledge skills to user-invoked
Why: two A/B rounds found no reliable gain; they cost context in every session if auto-listed. Done: disable-model-invocation: true, one-line human-facing descriptions, CLAUDE.md block trimmed to the state bullets. Rejected: deleting (untracked files cannot be recovered), keeping them auto-invoked, a third test round.
Gotcha: an unquoted `: ` inside a YAML description makes Claude Code ignore the whole frontmatter (it fell back to the first body line and ignored the flag); guarded by tests/test_skills_frontmatter.py.
