# Multi-turn work

Cross-session carry-forward (decisions, constraints, task state) lives in skill `project-state`. Drift, noise and reset: skill `context-discipline`, section 6. This file covers the prompt side of dialogue inside one session.

## When dialogue beats one prompt

Use turns when the task is ambiguous, when the final output depends on intermediate results, when a human approves one step before the next, or when length creates context pressure. [CCAR 14]

## Clarifying turn

1. Acknowledge what was understood. [CCAR 14]
2. Ask one question about the ambiguity most likely to produce wrong output. [CCAR 14]
3. Say what happens once it is answered. [CCAR 14]

Take the answers the context already gives, and ask only what it cannot answer. [CCAR 14]
Done when one specific question was asked and nothing inferable was asked. [CCAR 14]

## Turn sequences and refinement

- Map what each step needs from the previous one; that map is the turn structure. One goal per turn, short instructions limited to the current step. [CCAR 14]
- Pass the prior output forward explicitly (quote it or refer to it); the model does not carry why it wrote it. [CCAR 14]
- Refinement: draft from the specification; targeted feedback on a named aspect ("the opening paragraph is too abstract, lead with the main finding", not "make it better"); apply and confirm; then one category of issue per turn. Small changes are easy to verify. [CCAR 14]
- Open a turn with the current step and progress so far ("we are now revising the introduction"). [CCAR 14]
- Correct a wrong turn by naming what was wrong, one issue at a time, reaffirming the correct context first when an earlier framing may have misled the model, and verifying the repair before the next step. [CCAR 14]

Done when the next turn carries the goal, the active constraints and the prior output it needs. [CCAR 14]
