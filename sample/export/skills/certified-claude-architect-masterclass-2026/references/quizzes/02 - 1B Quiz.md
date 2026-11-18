# 1B Quiz

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · D1: Agentic Architecture - Task Decomposition & Planning · 12 questions · pass mark 70% · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies

## Question 1

An orchestrator coordinates three subagents: one retrieves company financial data, one retrieves market benchmark data, and one synthesizes a report from both. The first two run simultaneously; the third waits for both. At each handoff, the full internal context window of each retrieval subagent is passed to the synthesis agent. What design principle is being violated?

A. The synthesis subagent should be replaced by the orchestrator directly, as synthesizing results is an orchestrator responsibility.
B. The orchestrator cannot coordinate more than two subagents without incurring coordination overhead beyond the task budget.
C. The parallel execution structure is invalid; retrieval subagents must always run sequentially to avoid race conditions.
D. The handoff passes full context windows instead of only the structured outputs the synthesis agent requires.

**Answer:** D
**Explanation:** The deck's guidance on handoff points is explicit: pass only what the next step actually needs. Dumping entire context windows into the handoff payload creates noise and can cause the receiving agent to focus on irrelevant information. The correct approach is to extract and pass only the structured outputs the synthesis agent requires, using an explicit schema. Passing everything is a handoff design failure that can cause silent errors.

## Question 2

A team has decomposed a research task into twelve individual subtasks, each handling one sentence of context enrichment. The orchestration layer now requires more logic to coordinate handoffs than the enrichment work itself takes. A colleague claims this is fine because more subtasks always means better fault isolation. What decomposition principle does this scenario violate?

A. The decomposability spectrum principle: over-decomposition creates coordination overhead that can exceed the work itself.
B. Single responsibility: each subtask should perform exactly one function with no additional scope.
C. Handoff schema design: each handoff must use a structured schema rather than passing free-form text.
D. Dynamic planning: the number of subtasks must be determined at inference time by the agent, not preset by the developer at design.

**Answer:** A
**Explanation:** The deck explicitly covers the decomposability spectrum and warns that over-decomposition creates coordination overhead that can exceed the cost of the actual work. The goal is subtasks that are meaningful, executable units — not micro-steps that should have been combined. Fault isolation is a real benefit of decomposition, but it stops paying off when the coordination logic becomes the dominant cost. The colleague's claim that more subtasks always equals better isolation is the specific misconception the deck addresses.

## Question 3

A team is designing a multi-agent research system where a top-level orchestrator delegates market analysis to a subagent, which in turn delegates data retrieval to another subagent. The architect is debating how many levels to add. According to the principles taught in this lesson, what is the primary risk of adding each additional hierarchy level?

A. Each added level reduces specialization, because agents at lower tiers must handle broader context from the levels above them.
B. Each added level reduces auditability because the top-level orchestrator loses direct visibility into how lower-tier agents complete their work.
C. Each added level increases the error propagation surface, giving failures more layers to travel through before being caught.
D. Each added level forces sequential execution, eliminating any possibility of running parallel branches within the hierarchy.

**Answer:** C
**Explanation:** Each added level increases the error propagation surface. An error at the bottom of a deep hierarchy travels back up through every intermediate orchestration layer before it is caught, and each layer is a chance for the error to be misinterpreted or swallowed. The lesson explicitly states that depth should earn its cost through genuine specialization gains, not just because the structure looks clean.

## Question 4

An architect is reviewing a parallel agentic pipeline where five independent research tasks run concurrently. After all branches complete, their results are passed to the next stage. The design looks correct, but the architect notices the branches write status flags to a shared object during execution. What design requirement does this violate, and what failure mode does it introduce?

A. It violates the fan-in requirement, because the synchronization step cannot collect results when branches write to the same output object during execution.
B. It violates the branch independence requirement, allowing shared writes to produce non-deterministic results depending on which branch finishes last.
C. It violates the over-decomposition principle, because shared status flags should be managed by the orchestrator rather than by individual parallel agents.
D. It violates the sequential fallback rule, which requires any branches sharing state to be converted to a sequential chain before running.

**Answer:** B
**Explanation:** Parallel decomposition requires that each branch is truly independent with no shared mutable state. When two branches write to the same shared resource without coordination, the result depends on which branch finishes last, making output non-deterministic. The lesson calls this a race condition and identifies it as the core risk when the independence requirement is violated.

## Question 5

A developer has built a five-step content-processing pipeline where step 3 enriches records and step 4 formats the output. During a review, the architect discovers that step 4 does not actually use any field produced by step 3 — it only needs the original input from step 2. What does the deck call this situation, and what should the team do about it?

A. An artificial dependency: steps 3 and 4 are sequential only by convention, so they could run concurrently after step 2 to cut latency.
B. A cascade risk: step 3 failing would propagate to step 4, so the steps must stay sequential with explicit error handling added at each boundary.
C. A handoff schema mismatch: step 3's output schema is incompatible with step 4's input contract, requiring schema alignment before proceeding.
D. An under-decomposition failure: the pipeline needs an intermediate aggregation step between steps 3 and 4 to prevent silent data loss.

**Answer:** A
**Explanation:** The deck distinguishes true dependencies (step B reads a field produced by step A) from artificial dependencies (steps are sequential only by convention, not by data need). When a dependency is artificial, removing it unlocks parallel execution, cutting latency without changing correctness. The deck recommends auditing every step boundary before committing to sequential ordering.

## Question 6

A team builds a document-processing pipeline where step 2 passes its output to step 3 as a JSON object. In production, step 3 occasionally receives responses missing a required field, silently defaults to null, and continues — producing wrong output several steps later that is hard to trace. What design practice would have prevented this, according to the lesson?

A. Defining an explicit handoff schema at each step boundary, with required fields, types, and nullability, so mismatches fail loudly at the boundary.
B. Converting steps 2 and 3 to parallel execution so field availability can be validated before either step's output is finalized and passed forward.
C. Splitting step 2 into two narrower sub-steps, so each sub-step is responsible for only one output field and reduces the chance of a missing-field failure.
D. Adding a retry loop at step 3 that re-requests step 2's output whenever a required field is missing from the incoming response.

**Answer:** A
**Explanation:** The deck teaches that every step boundary needs a defined schema specifying required fields, types, and nullability. Defining the output schema of step N as the formal input contract for step N+1 catches mismatches at the boundary as an explicit failure, rather than letting malformed data travel downstream and surface as a mysterious wrong result at the pipeline's end.

## Question 7

An engineering team fans out five research tasks to run in parallel. Three branches return results successfully, but two branches time out. The fan-in step collects the three successes and continues the pipeline without any record of the failures. A reviewer flags this as a serious design flaw. Why, according to the lesson?

A. The fan-in step must use voting aggregation whenever branches fail, so the majority result from the three successful branches determines the final output.
B. Continuing with three results violates the independence test, since fan-in aggregation requires all branches to produce output before the merge step can run.
C. The fan-in step should always retry every failed branch before continuing, so the pipeline must stop and re-dispatch all five tasks from the beginning.
D. Silently dropping failed branches produces incorrect results that are extremely hard to diagnose, because the pipeline treated incomplete data as if it were complete.

**Answer:** D
**Explanation:** The deck states unambiguously that silently dropping failed branches and continuing as if they succeeded is always the wrong answer. It introduces incorrect results that are extremely hard to diagnose after the fact. Fan-in must handle partial failures explicitly — either by failing the whole pipeline, proceeding with partial results while flagging failures, or retrying individual failed branches.

## Question 8

A product team is considering switching a sequential five-step pipeline to a parallel fan-out design because it would cut wall-clock time from 50 seconds to 10 seconds. Before approving the change, the architect asks the team to model the cost impact. What does the lesson teach about token spend in parallel execution relative to sequential?

A. Token cost and latency both decrease in parallel execution, making it strictly superior to sequential for any workflow where steps are independent.
B. Parallel execution multiplies token consumption per second by the branch count, so total cost equals the sum across all branches, not just the longest.
C. Token cost in parallel execution equals the cost of the longest branch only, since shorter branches complete before the billing window for additional tokens opens.
D. Parallel execution reduces total token cost because branches share context, so each branch processes a smaller input than a single sequential step would.

**Answer:** B
**Explanation:** The deck teaches that parallel execution cuts latency but increases token spend. When branches run simultaneously, token consumption per second multiplies by the number of branches. Total token cost equals the sum across all branches, not just the longest one. Rate limits may also constrain achievable concurrency. The lesson prescribes modeling both dimensions explicitly before choosing parallel over sequential.

## Question 9

A customer-support agent is mid-execution when a tool call returns an empty result the plan did not anticipate. The agent must decide whether to replan or continue. The architect reviewing the system asks: according to the framework taught in this lesson, what is the correct question to ask before triggering a replanning cycle?

A. Whether the original goal is still achievable via the current plan with adjustments, or whether a core assumption has been invalidated.
B. Whether the failed tool call was a transient network error or a permanent data unavailability, since only permanent failures justify triggering a replanning cycle.
C. Whether the agent has already exhausted its maximum iteration limit, since replanning is only permitted when iteration cycles remain in the agent's budget.
D. Whether a human operator is available to approve the revised plan before execution resumes, since dynamic plans require pre-authorization at each replan step.

**Answer:** A
**Explanation:** The deck teaches that not every surprise warrants a full replanning cycle. The correct decision criterion is whether the original goal is still achievable via the current plan with adjustments. Replanning is warranted only when a core assumption has been invalidated. Unnecessary replanning wastes tokens, adds latency, and increases the risk of goal drift.

## Question 10

After several replanning cycles, an agent's revised plan successfully resolves each immediate obstacle but no longer addresses the original user request. It has pivoted to an adjacent goal that was never specified. What failure mode does the lesson name for this, and what mechanism does it prescribe to prevent it?

A. Over-decomposition: the agent creates too many sub-plans, and coordination cost between them causes the original goal to become obscured across cycles.
B. False parallelism: the agent treats dependent sub-goals as independent, causing plans to diverge. Prevention requires enforcing sequential replanning cycles throughout.
C. Goal drift: the agent solves obstacles but loses alignment with original requirements. Prevention requires validating every revised plan against the preserved original goal before resuming.
D. Constraint violation: the agent crosses a safety boundary by taking actions outside the original plan. Prevention requires adding boundary checks at each individual replanning step.

**Answer:** C
**Explanation:** The deck calls this goal drift — one of the most dangerous failure modes in replanning systems. It occurs when successive plan revisions solve immediate obstacles but lose alignment with the original requirements. The prevention mechanism is to preserve the original goal specification as a persistent artifact and explicitly validate every revised plan against it before proceeding. Logging original intent alongside each revision also creates an audit trail.

## Question 11

A workflow automation agent receives an instruction to clean up old project folders. The instruction does not specify which folders are in scope. The agent is about to begin deleting files. According to the decision criteria taught in this lesson, should the agent clarify upfront or proceed on assumptions — and why?

A. Clarify upfront only if the operation will exceed the agent's token budget, since high cost is the primary factor the lesson uses to justify clarification delays.
B. Clarify upfront, because the action is irreversible and the task boundaries are unclear — two of the three criteria the lesson cites as requiring clarification.
C. Proceed on assumptions, because the instruction was user-provided and any reasonable interpretation of 'old project folders' is a valid target.
D. Proceed and document the interpretation used in the output log, since documented assumptions are sufficient to make an irreversible action safe without prior clarification.

**Answer:** B
**Explanation:** The deck identifies three situations that warrant upfront clarification: irreversible actions, high-cost operations, and scope uncertainty. File deletion is both irreversible and scope-uncertain — the agent does not know what is in or out of bounds. Both criteria individually justify clarification, and together they make assuming-and-proceeding clearly inappropriate.

## Question 12

A content-generation agent uses an evaluator-optimizer loop to improve draft quality. After nine iterations, the evaluator still has not confirmed the quality bar is met, and the system keeps looping. What mechanism does the lesson say is non-optional for preventing this, and why?

A. A fallback to a static plan after three failed iterations, since dynamic loops must defer to pre-authored plans when convergence is not achieved quickly.
B. A structured critique format for the evaluator, since richer feedback causes faster convergence and effectively eliminates the need for a hard loop limit.
C. A maximum iteration cap, which the lesson calls non-optional because without it the loop runs indefinitely when the evaluator remains unsatisfied.
D. Human approval at each iteration boundary, since the lesson requires a reviewer to confirm quality before the generator produces the next revised version.

**Answer:** C
**Explanation:** The deck states explicitly that an iteration cap — a maximum iteration count — is non-optional for the evaluator-optimizer pattern. Without it, the loop can run indefinitely on tasks where the evaluator is hard to satisfy. The cap is what makes the pattern safe to deploy in production without human supervision of every single run.
