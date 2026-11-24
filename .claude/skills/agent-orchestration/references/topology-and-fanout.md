# Topology and fan-out

Open from SKILL.md section 2 when choosing how agents are wired, merging branch results, or running unattended.

## Pick the shape from the data flow

Read the task's data flow; the structure usually chooses itself. [CCAR 04]
1. Natural hierarchy (one agent decomposes, specialists execute): hub-and-spoke. [CCAR 04]
2. Order forced by data (each step needs the previous output): pipeline. [CCAR 04]
3. Loosely coupled agents, no shared state, no required order: peer-to-peer. [CCAR 04]
4. Need a complete decision log: use hub-and-spoke or pipeline. [CCAR 04]

Done when: the choice names the question that decided it. [practice]

## The three shapes

| Shape | Gains | Costs |
|---|---|---|
| Hub-and-spoke | One place for policy, state, audit, recovery | Hub is a single point of failure and a bottleneck; its context grows with every spoke [CCAR 04] |
| Pipeline | Modular stages, each swappable and testable | Latency is the sum of stages; a failed middle stage blocks the rest [CCAR 04] |
| Peer-to-peer | No single point of failure, lower latency | Hard to audit, emergent behaviour, no central state [CCAR 04] |

- The hub mediates all spoke communication. A Claude Code subagent returns its result to its parent, which fits hub-and-spoke. [CCAR 04, 11]
- Handle errors at every pipeline boundary, not only at the end. [CCAR 04]

## Hybrids and anti-patterns

- Hybrids are legitimate (hub delegating into an internal pipeline). Name which subsystem each pattern serves, then define the handoff at every seam: output shape, failure behaviour, how state crosses. [CCAR 04]
- A hub needs a hierarchy to coordinate; with none, let the agents work directly. [CCAR 04]
- Do not choose peer-to-peer when a complete decision log is required: the log cannot be rebuilt afterwards, and instrumentation only partly compensates. [CCAR 04]

## Decomposition shapes

- Hierarchical: each level holds only its tier. Every added level lengthens the path an error travels back up. Add depth for real specialization. [CCAR 03]
- Sequential: order enforced by data dependency; easiest to debug; total time is the sum of steps. [CCAR 03]
- Parallel: independent branches, a fan-in at the end. [CCAR 03]
- Choose per segment from the dependencies. [CCAR 03]
- Over-decomposition: coordination costs more than the work. Under-decomposition: one failure restarts everything. False parallelism (dependent steps run together) fails quietly with wrong answers; run dependent steps in sequence. [CCAR 03]

## Fan-in

Fan-in collects successes, handles failures, restores order when order matters, and merges. Design each explicitly. [CCAR 03]

- Voting: branches answer the same question, majority wins. [CCAR 03]
- Concatenation: branches cover distinct segments, outputs are joined. [CCAR 03]
- Structured aggregation: each branch fills a named field of one object. [CCAR 03]
- Merge strategy shapes what each branch returns, so choose it first. [CCAR 03]
- Rate limits cap real concurrency; size batches to the limit. [CCAR 03]

Failed-branch policy (decided before dispatch): fail the whole run when every branch is required; proceed with partial results and flag what failed when partial is useful; retry only the failed branches. Return every failed branch in the merge with its error. [CCAR 03]

## Cost and fit

- Fan-out multiplies spend with the branch count; add orchestrator planning and result merging on top. [CCAR 03, 05]
- Breadth-first work (many independent sources) fits fan-out. Tightly coupled work is sequential, one agent. [CCAR 05]

## Handoffs

- Use structured schemas with required fields, types and nullability at every boundary, so a mismatch fails loudly instead of defaulting to null. [CCAR 03]
- Design against an interface, so receivers are interchangeable. [CCAR 04]
- Confirm the receiver has what it needs before letting go of control. [CCAR 04]
- Every structured handoff payload carries a schema version field the receiver can inspect. [CCAR 04]
- A handoff is a stage boundary: log it per Validation gates in [error-handling.md](error-handling.md). [CCAR 04]

## Headless runs

A workflow that runs without a human (CI, scheduled job) takes one atomic task per invocation, a fully self-contained prompt, structured output, idempotent effects, scoped permissions and a timeout. [CCAR 12]
- Run every unattended invocation with `claude -p` (print mode), which runs the prompt non-interactively and exits. [CCAR 12]
- Pair it with `--output-format json`, capture stdout, fail the step on a non-zero exit, and set a step timeout. [CCAR 12]
- `--allowedTools` pre-approves the listed tools; it does not block others. To deny calls that would prompt, add `--permission-mode dontAsk` (read-only actions still run) and `permissions.deny` rules for anything that must never run. [practice]
