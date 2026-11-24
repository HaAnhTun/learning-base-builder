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

## 2026-11-24 Quiz-driven upgrade plan (confirmed after grilling Q1-Q16)
Quiz = benchmark with answer key; learn from baseline failures. Split: tests 1-3 learn, 4 validate (max 2 iteration rounds), 5-6 sealed, run exactly once. Scope: daily Claude Code rules only; SDK/API patterns are recorded in docs/quiz-patterns.md but not put in skills. Write a rule only where no-skill Claude fails >=30% of a pattern's training questions (a question fails when wrong in >=2 of 3 runs); skip patterns >=90% correct. New skill claude-code-playbook; cards (situation -> choose -> instead of -> why, tagged [Q-Pnn]); old prose moves to references/. project-state: compare only, fix real gaps. Gates on sealed 5-6 (3 runs per arm: none / current skills at 97dedec / upgraded): no regression on 120 and per domain (noise 2 questions); auto-invocation of the whole knowledge set only if +4 questions on the 47 daily questions; otherwise stay manual and report honestly. Budget approved: staged, report after each phase. Multi-select scored exact-match, answering model without tools.

## 2026-11-24 Quiz baseline result: no knowledge gap for Sonnet 5.5, so no rules to write
Blind baseline (no skills, no tools, 3 runs) on tests 1-4 scored 100% on tests 1-3 and 98.3% on test 4; one stable failure in 240. By the Q8 rule (write only where no-skill Claude fails >=30%, skip >=90%) no pattern qualifies, so phases 3-7 are moot and the sealed tests 5-6 stay unused. The Q15 gain gate (+4 on 47 daily questions) is unreachable when the baseline is near the ceiling. Caveats: recognising the right option is not the same as acting on it in a real task; the questions may be in the model's training data; a weaker model was not tested.

## 2026-11-24 Quiz upgrade closed: Haiku also at the ceiling
Haiku 5.5 baseline (24 agents, blind, no tools, audited): 539/540 on tests 1-3, 59/60 on test 4 in every run, same single stable miss as Sonnet. The only audience that could have benefited from knowledge skills shows no gap either. Decision: write no rules, keep the knowledge skills manual, keep tests 5-6 sealed for any future attempt. Result recorded in docs/quiz-benchmark.md.

## 2026-11-24 Adopt four mattpocock mechanisms into existing skills, net-zero
Adopted (MIT, rewritten not copied, attributed): ask-matt phase-boundary tree -> context-discipline [D5]; code-review two-axis independent review -> agent-orchestration [D1]; git-guardrails fail-closed hook example -> layer-choice [D3]; domain-modeling ADR gate + handoff reference-not-copy -> project-state [D5]. No new skills, activation unchanged, SKILL.md not longer. Verified by three independent reviewers per skill. Lesson: the docs fact-checker was wrong once (hook trust dialog); resolve conflicting doc reports with the page's verbatim text.
