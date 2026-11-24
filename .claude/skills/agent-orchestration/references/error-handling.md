# Error handling

Open from SKILL.md section 5 when designing recovery, writing a subagent's error path, or when a tool returned nothing.

## Classify first

Ask where the failure originated. [CCAR 05]

| Class | Meaning | Recovery |
|---|---|---|
| Tool | The tool or API reported it (timeout, rate limit, bad input, denied) | Transient: retry with backoff. Permanent: fallback or escalate [CCAR 05] |
| Reasoning | The tool ran; the plan or reading was wrong | Change the prompt or context, or escalate; an identical retry repeats the result [CCAR 05] |
| Environment | The tool could not reach its own dependency (network, database, filesystem) | Wait, retry after a delay, monitor [CCAR 05] |

## Caps

State each cap once, here. Defaults apply unless the task states another number and a reason. [practice]
- Retry budget: 3 attempts with exponential backoff and jitter; honour a retry-after hint. [CCAR 05]
- Failure ceiling: 3 consecutive failures on the same step, then escalate with a log of attempts. [CCAR 17]
- Replan cap: 2 replanning cycles per goal. [practice]
- Evaluator loop cap: 3 iterations, then report the last score. [practice]
- At any cap, stop and escalate (the evaluator loop instead reports its last score); each cap exists so loops end in a decision. [CCAR 03]

## Retry and abort

- Abort permanent errors at once (invalid input, permission denied, auth failure, wrong plan) and surface them visibly. [CCAR 05]
- Ambiguous error (a 500 could be either): one retry after a delay, then treat as permanent. [CCAR 05]
- Exhausted retry budget: abort and escalate upstream. [CCAR 05]

## Where to catch it

The propagation boundary is a design choice; write it down. [CCAR 17]
- Recover locally and log it: retryable transients, recoverable validation failures, idempotent refetches. Test: the orchestrator's plan would not change. [CCAR 17]
- Propagate: scope violations, policy denials, exhausted retry budgets, anything that changes sequencing or allocation. [CCAR 17]
- Unsure: propagate with low severity, since a warning can be dismissed and an unreported failure cannot be acted on. [CCAR 17]
- Log every local recovery (type, time, retries needed). A subagent retrying on nearly every call signals a degraded dependency. [CCAR 17]
- Aim between the extremes: report what changes the plan, absorb the rest. [CCAR 17]

## Error envelope

Failures cross the boundary as a typed object: [CCAR 17]
- `error_type`: machine-readable category to branch on. [CCAR 17]
- `severity`: warning (log, continue), recoverable (retry with backoff or fallback), fatal (halt the dependent chain, escalate). Decide the policy per severity in advance. [CCAR 17]
- `context`: subagent id, task reference, enough input state to reconstruct. [CCAR 17]
- `completed_steps`: how far it got, so a retry resumes there and side effects happen once. [CCAR 17]
- `recovery_hint`: optional suggestion; the orchestrator may ignore it. [CCAR 17]

Retried writes carry an idempotency key, so a repeat returns the earlier result. Add a span id per hop when nesting is deep. [CCAR 17]

## Empty result vs access failure

An empty tool result is ambiguous: either the source was checked and nothing matched, or the tool never reached it. The model reads both as "nothing exists". [CCAR 17]
- Put a mandatory status enum on every tool response: success, empty, partial, access_failure. Name each branch in the prompt, since an unnamed branch gets the model's own assumption. [CCAR 17]
- Map in the wrapper: HTTP success with empty body is `empty`; 4xx, 5xx or a timeout is `access_failure`; a truncated body is `partial`. [CCAR 17]
- Retry only `access_failure`. [CCAR 17]
- Words follow status: "found nothing" for confirmed empty; "couldn't check" for access failure; "may be incomplete" for partial. [CCAR 17]
- Log each access failure when it happens: time, tool and endpoint, error class, retry applied and outcome. [CCAR 17]

## Fallback chains

- Order alternatives in advance (primary, alternate tool, cached result, escalate). Each step fires when the previous one failed, and the chain ends in an explicit result or escalation. [CCAR 05]
- Test each fallback under the conditions that break the primary. [CCAR 05]
- Degraded output carries a flag or confidence field that propagates to every downstream consumer. [CCAR 05]
- Partial result or full failure: if partial output is low-risk and reversible, pass it on, flagged; if high-risk and irreversible, escalate first. [CCAR 05]

## Validation gates

Put a gate at each stage boundary, before the output feeds the next step. [CCAR 05]
- Plausibility means these checks: schema matches, values in range, result non-empty, key entities present, no contradiction with the input. [CCAR 05]
- Run a check before acting (inputs, permissions) and after (outputs, business rules, anomalies). Runtime limits (cost, iteration cap, scope) catch slow drift. [CCAR 05]
- Match the response to the risk: hard block for non-negotiable limits, soft warning for advisory concerns, escalation for ambiguous cases. [CCAR 05]
- Gate failure order: retry with corrected input, then fallback, then human or alert. [CCAR 05]
- Log inputs and outputs at every boundary, so a silent failure leaves a trace. [CCAR 05]
