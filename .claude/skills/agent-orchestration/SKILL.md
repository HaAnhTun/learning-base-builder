---
name: agent-orchestration
description: Manual reference for single versus multi-agent work, fan-out, errors, human approval, checkpoints and where an instruction lives.
disable-model-invocation: true
---

Read sibling skills by file path; a skill name cannot fire a user-invoked skill. Open `.claude/skills/prompt-craft/SKILL.md` when writing a subagent brief, `.claude/skills/project-state/SKILL.md` when saving or resuming state, `.claude/skills/context-discipline/SKILL.md` when a long run needs trimming or a handoff fact block. Rule provenance: tags [CCAR NN] name the course lesson file number; [practice] marks sound Claude Code practice the course does not state; [D1]-[D5] label the CCA-F exam domain of an adopted card.

## 1. Choose the mode

Fan-out or any multi-agent topology needs a yes to all three; one no means a single agent is almost always the better call. [CCAR 05]
1. Does the work split into parallel directions that barely touch each other? Size is not parallelism: most coding tasks have fewer independent pieces than breadth-first research, because files depend on each other and changes must stay consistent. [CCAR 03, 05]
2. Does each piece fit its own context, with no shared state passed back and forth? [CCAR 05]
3. Does the expected gain (breadth, wall-clock time) justify multiplying token spend by the branch count? [CCAR 05]

A single subagent needs one of these reasons:
- Isolation: an investigation that reports back, or a work stream with its own context. [CCAR 11]
- A different tool or permission set than the parent. [CCAR 11]

Precondition for any subagent: the handback can be defined without the parent's in-flight state; if it cannot, keep the work inline. [CCAR 11]

Everything else stays inline: work that needs the full parent context, depends on prior steps, or costs less to do than to delegate. [CCAR 11]

Done when: one line names the mode and the question that decided it. [practice]

## 2. Plan before fan-out

1. Ask three questions of the goal: which parts run independently, which output feeds the next input, which parts need different capabilities. [CCAR 03]
2. Draw the dependency graph: edge A to B when B needs A's output. No incoming edge means it can start first or in parallel. [CCAR 03]
3. Audit every edge: a true dependency stays sequential; an artificial one (sequential by habit) gets removed. [CCAR 03]
4. Run the independence test on each branch pair: B starts without A's output; no shared writes; any order gives the same result. One failure means sequence them or fix the dependency. [CCAR 03]
5. Give each parallel branch that writes files its own copy of the workspace (a worktree). [CCAR 03, 11]
6. Pick the merge strategy before designing branches, and write the failed-branch policy before dispatch (options in the reference). [CCAR 03]
7. Stop splitting where coordination costs more than the retry point buys; merge two adjacent levels that would run the same prompt. [CCAR 03]

Done when: the graph is drawn, merge strategy and failed-branch policy are written down. [CCAR 03]

Topology (hub-and-spoke, pipeline, peer-to-peer), merge options, headless runs: [references/topology-and-fanout.md](references/topology-and-fanout.md). Open it when choosing wiring, merging branch results, or running unattended.

## 3. Dispatch

1. Fill each brief with the Subagent brief template in `.claude/skills/prompt-craft/SKILL.md` (open its Subagent brief section before the first dispatch). Add two orchestration items:
   - the list of what the subagent does not receive. [CCAR 03]
   - an output schema with a status field and an error shape. [CCAR 11]

   Withhold by default: parent conversation history, other subagents' outputs, irrelevant system prompts, credentials the task does not need. [CCAR 04]
2. Context is not inherited: pass what the subagent needs. Tools and permissions do come down from the parent, so narrow them: read-only for investigators, one directory for service-scoped work. [CCAR 11]
3. Test each subagent on its own. A subagent that cannot run alone has too broad a scope or a hidden dependency on orchestrator state. [CCAR 04]
4. Fan out independent branches at once, or in batches sized to the rate limit; run dependent steps in sequence. [CCAR 03]

Done when: every handback has a status and a typed error path, and every subagent runs standalone. [CCAR 04, 11]

## 4. What the orchestrator owns

- The orchestrator owns the master plan, execution state, error handling and aggregation rules. Subagents report; the orchestrator decides retry, substitute or escalate. Update state per `.claude/skills/project-state/SKILL.md` (open it when STATE.md must change). [CCAR 04]
- Validate every handback before using it: schema, range and non-empty checks from the Validation gates in [references/error-handling.md](references/error-handling.md). An empty or confident-looking result is checked, not trusted. [CCAR 04, 05]
- After a side effect, read the state back; a return value alone does not prove the change. [CCAR 05]

Done when: every returned result has a recorded validation verdict and STATE.md names the next owner. [practice]

## 5. Handle failure

1. Classify where it originated (tool, reasoning, environment), then recover by class from the table in the reference, retrying only inside the retry budget. [CCAR 05]
2. Propagate by the test in the reference; return typed errors, and make retried writes idempotent. [CCAR 17]

Done when: no failure path ends in a silent drop, and every retry has a budget. [CCAR 05]

Error classes, caps, propagation test, error envelope, empty-vs-failure, fallback chains, validation gates: [references/error-handling.md](references/error-handling.md). Open it when designing recovery, validating a handback, or when a tool returned nothing.

## 6. Human in the loop

Escalate when a hard trigger fires: a deny-list or out-of-policy action, or the failure ceiling (Caps in the error-handling reference). [CCAR 17]

Place an approval gate before an irreversible action, a high-cost action, at phase boundaries and on anomalies, or when the scope is unclear: a review after the action prevents nothing. For low-stakes reversible work, proceed on an assumption and write it down. Weak or partial results: Fallback chains in [references/error-handling.md](references/error-handling.md). [CCAR 03, 05]

- Reserve escalation for consequences that are high and hard to reverse; reviewers who see only those keep reading each request. [CCAR 17]
- Back a prompt-level deny or allow list with code (PreToolUse hook, permission check) for irreversible or financial actions; the prompt list suffices for low-stakes paths. Prompt wording is probabilistic. [CCAR 05, 12]
- Where a model-reported confidence score is used, calibrate it against outcomes and log the reasoning behind a low score. [CCAR 17]

Done when: each escalation names its trigger, and the request carries the payload fields. [CCAR 17]

Payload fields, sync vs async review, timeouts, loop closure, checkpoint design: [references/escalation-and-checkpoints.md](references/escalation-and-checkpoints.md). Open it when writing an approval request or choosing a review mode and timeout.

## 7. Checkpoint interrupted work

Save a checkpoint at each phase end and before any irreversible action. [CCAR 04] Open the Checkpoint design section of [references/escalation-and-checkpoints.md](references/escalation-and-checkpoints.md) before saving or resuming: it holds the resume check and the mismatch rule.

Done when: a fresh session could continue from the checkpoint without repeating a completed step. Here the checkpoint is STATE.md (written per `.claude/skills/project-state/SKILL.md`). [CCAR 04]

## 8. Plan mode and replanning

- Plan first when work is hard to reverse, spans modules, or is ambiguous; a one-file mechanical fix goes straight to editing. [CCAR 11]
- Enter plan mode with Shift+Tab, `/plan <request>` or `--permission-mode plan`; no file is written until the plan is approved. Ask for 5-8 numbered steps, each naming real files, with assumptions and risks listed. For complex work, have a read-only investigator subagent explore first and a hook validate steps. [CCAR 11]
- Before executing, tell the agent to stop and surface any divergence from the plan. This reduces silent improvisation without guaranteeing it: read the diff against the approved plan, and use a hook for a hard stop. [CCAR 11]
- Replan when a core assumption broke; patch and continue when one step is affected. Check each revised plan against the original goal, kept as a fixed artifact, within the replan cap (Caps in the error-handling reference). [CCAR 03, 11]

Done when: an approved plan names files, assumptions and the divergence rule. [CCAR 11]

## 9. Evaluator loop

Use a generator and an evaluator for writing or analysis, where quality is hard to specify and easy to recognize. Write the rubric first; the evaluator scores against it and returns specific feedback. Stop at the quality bar or at the loop cap (Caps in the error-handling reference). [CCAR 03, 04]

Done when: the rubric exists before the first loop, and the run ends at the bar or the cap with the last score reported. [CCAR 03]

**Two-axis review** [D1] (adapted from mattpocock/skills, MIT: code-review). Situation: a diff needs checking against the repo's documented standards and against the spec or ticket it came from. Choice: two reviewer subagents in parallel, one per axis, each in a fresh context. [CCAR 11] Replaces one combined pass, where a clean result on one axis can hide a failure on the other. [practice]
1. Validate once, before spawning: the ref resolves and the diff is non-empty, so a bad input fails once in the orchestrator, not twice inside the reviewers. [practice]
2. Each brief states its inputs (diff command; standards files or spec text) and the exact report shape, and asks for the source line (rule or spec line) quoted per finding. [practice]
3. Show the two reports side by side under one heading each; every axis keeps its own findings and its own ranking. [practice]

Done when: both reports are shown separately, each with its own findings, ranking and count. [practice]

## 10. Place an instruction

Open [references/layer-choice.md](references/layer-choice.md) before placing any instruction in CLAUDE.md, a rule, a hook or a slash command, and apply its decision list.

Done when: no layer copies another layer's text (a command extends CLAUDE.md instead of duplicating it); a hard constraint may appear twice, as guidance in the prompt and as enforcement in a hook or code. [CCAR 05, 11]
