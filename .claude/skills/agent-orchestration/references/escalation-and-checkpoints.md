# Escalation and checkpoints

Open from SKILL.md section 6 or 7 when writing an approval request, choosing a review mode, or saving or resuming state for interrupted work.

## Triggers

The policy is in SKILL.md section 6. Each trigger is a condition the agent can check. [CCAR 17]
- Policy trigger: an action on the deny list escalates; an action off the allow list escalates. Hold irreversible or financial paths with code as well. [CCAR 05, 17]
- Failure trigger: count tool errors and validation rejections; at the failure ceiling, escalate with a log of attempts. [CCAR 17]
- Explicit tool: give the agent an `escalate` or `request_review` tool that logs decision, context and reason in one structured call. [CCAR 17]
- Tune thresholds from observed escalation rates: constant escalation makes reviewers stop reading; no escalation ships unreviewed output. [CCAR 17]

## Escalation payload

Build it for the receiver, as defined fields. [CCAR 17]
- Conversation summary: compressed account up to the trigger. [CCAR 17]
- Triggering question, verbatim. [CCAR 17]
- What was tried: a log of tool calls, validations and retries with results. [CCAR 17]
- Suggested next step, even an uncertain one. [CCAR 17]
- For approvals add: the decision required as one answerable question; what follows from approve and from reject; the deadline and what happens at timeout. [CCAR 05]

## Sync or async review

- Synchronous: halt until approved. Use when nothing else can proceed without the decision. [CCAR 05]
- Asynchronous: queue the request, continue independent branches, and track what is pending. [CCAR 05]
- Define the timeout threshold and timeout action (escalate further, abort, or apply a safe default) before deploying. [CCAR 05]

## Routing and loop closure

- The orchestrator routes the payload: human reviewer for judgment or authority a model should not exercise; specialist agent for another domain; a more capable model when the limit was capability. [CCAR 17]
- Close the loop: append the reviewer's answer and notes to the context the agent escalated from, then resume from the saved state. [CCAR 05, 17]
- Log trigger type, payload, destination and resolution; one trigger causing most escalations points at a threshold or allow-list gap. [CCAR 17]
- On resume, start at the first incomplete phase; the persisted state is the source of truth. [CCAR 04, 05]

## Checkpoint design

- Save at the end of each phase. Save after every step when steps are expensive to rerun, have external side effects, or cannot be retried idempotently. [CCAR 04]
- Write the checkpoint before an irreversible action in the next phase, so a restart cannot replay it. [CCAR 04]
- Contents: phase marker, outputs later phases depend on, original task inputs, timestamp, and an environment fingerprint for version checks (here: the repo head). [CCAR 04]
- Resume: look for a checkpoint first; verify it (phase marker present, repo head equals `git rev-parse HEAD`); skip completed phases; continue at the first incomplete one. Partial coverage: resume from what it covers and flag the gap. [CCAR 04]
- When the document, resource or config changed since the save, flag the conflict and wait for a decision. [CCAR 04]
- State that must survive truncation or session end goes to an external store (here: `.claude/state/`). [CCAR 04] Pruning and hot-versus-cold state: `.claude/skills/project-state/SKILL.md` and `.claude/skills/context-discipline/SKILL.md` (open them when pruning state or splitting it hot from cold).
