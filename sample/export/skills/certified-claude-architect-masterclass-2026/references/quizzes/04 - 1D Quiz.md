# 1D Quiz

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · D1: Agentic Architecture - Reliability & Human Oversight · 16 questions · pass mark 70% · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies

## Question 1

An orchestrator calls a document search API and receives a 404 response indicating the requested resource was not found. A team member suggests retrying with exponential backoff. According to this deck's classification framework, why is that the wrong recovery strategy?

A. A 404 is a transient error from a temporarily missing resource; exponential backoff with a max retry count is correct.
B. A 404 is an environment error from a network partition that prevented the routing layer from resolving the identifier.
C. A 404 could be either type depending on the service; retry once to determine the category before choosing a fallback.
D. A 404 is a permanent error: the resource does not exist, so the same call always fails; recovery needs a fallback.

**Answer:** D
**Explanation:** The deck teaches that permanent tool errors—invalid input, permission denied, resource not found—will produce the same failure on every retry because the call is structurally incorrect. Retrying wastes resources and delays reaching a fallback or escalation path. HTTP 4xx codes signal permanent errors; exponential backoff is for transient errors (5xx, timeouts, rate limits).

## Question 2

An agent asked to summarize product descriptions confidently misattributes a feature from product A to product B, even though all correct descriptions were in its context. Rerunning the identical prompt produces the same error. How does the deck's classification framework categorize this, and what recovery is appropriate?

A. A transient tool error: the retrieval service returned wrong descriptions this run; retrying will likely return the correct data and the model will produce a right summary.
B. A reasoning error: the model misinterpreted correct data, and since nothing in its context changed, retrying with the same prompt will produce the same mistake.
C. A permanent tool error: the product database returned incorrect records; recovery requires a fallback data source with accurate feature mappings.
D. An environment error: a database inconsistency returned stale records; waiting and retrying after a delay will resolve the mapping mismatch.

**Answer:** B
**Explanation:** The deck teaches that reasoning errors originate inside the model. The tool ran correctly and infrastructure was available, but the model produced an incorrect interpretation. The defining characteristic is that retrying with identical input produces the same error because the model's context has not changed. Recovery requires prompt modification, context correction, or escalation—never a blind retry.

## Question 3

A customer-support agent processes orders and occasionally returns a response with HTTP 200 and no exception raised, but the order record is never actually updated. A QA engineer notices wrong order states appearing several steps later. Which detection mechanism is specifically designed to catch this class of failure?

A. Output schema validation — checking that the response fields and types match the required structure
B. State verification — reading back the record after the write to confirm it was actually persisted
C. Sanity checks — verifying the response length and key entities are plausible given the input
D. Retry logic — re-attempting the write step when the error code indicates a transient failure occurred

**Answer:** B
**Explanation:** State verification checks whether the world matches what the agent expected after a step — for example, reading a record back after a write to confirm it persisted. This is the only mechanism that catches cases where a call returned without error but the underlying system was never actually changed. Output validation and sanity checks evaluate the structure or plausibility of the returned value, not whether the side effect occurred. Retry logic does not help because no error code was raised.

## Question 4

A developer argues that adding only schema validation at each pipeline stage boundary is enough to catch silent failures, since it checks structure, types, and null values automatically. A senior engineer disagrees. Which gap does schema validation leave open that requires an additional layer?

A. Schema validation cannot detect whether an API returned an HTTP error code during the last call
B. Schema validation cannot run at stage boundaries and requires the full pipeline output before executing
C. Schema validation cannot check whether required fields are present or whether types are correct
D. Schema validation cannot verify whether the content is correct or meaningful given the input context

**Answer:** D
**Explanation:** Schema validation verifies structure — required fields, correct types, no unexpected nulls. It does not verify whether the content is actually correct or meaningful given the input. Semantic validation covers that gap by asking whether the output is plausible in context. A response can be perfectly schema-valid and still be logically wrong. Both layers are needed together for complete detection coverage.

## Question 5

An agentic pipeline hits a rate-limit response from an external API. A developer applies a fixed-delay retry policy, waiting three seconds between each of five attempts. A colleague recommends exponential backoff with jitter instead. What does exponential backoff with jitter provide that a fixed-delay policy does not?

A. A fixed wait interval on each attempt so the downstream service receives predictable, evenly spaced requests
B. Classification of the error as persistent so the pipeline can abort and escalate without further retrying
C. Increasing wait intervals plus randomized timing that prevents clients from all retrying at the same moment
D. An immediate first retry before any delay is applied, then longer delays for each subsequent attempt

**Answer:** C
**Explanation:** Exponential backoff doubles the wait time after each failure, giving the downstream system progressively more recovery time. Jitter adds randomness so multiple clients hitting the same rate limit do not all retry simultaneously, which would immediately re-trigger the limit. Fixed-delay retry applies a constant wait that does not adapt to burst failure conditions and can create synchronized retries when multiple clients share the same interval.

## Question 6

An agent produces a plan that misidentifies the target resource and issues a destructive command. The operation fails. The agent retries the same prompt three more times, each time generating the same incorrect plan. Which retry design principle does this scenario violate?

A. Exponential backoff should not exceed a configured cap to prevent runaway spend on rate-limit errors
B. Retry budgets must cap all transient errors at one to three attempts to keep pipeline latency bounded
C. Ambiguous errors should use one conservative retry with a delay before being treated as persistent
D. Persistent errors should abort immediately — retrying the same prompt cannot correct a reasoning error

**Answer:** D
**Explanation:** A reasoning error in the model's plan is a persistent error by definition. The deck teaches that retrying a persistent error wastes resources and delays the escalation that is actually needed. Retrying the same prompt cannot change the plan; the agent should abort immediately and escalate so the plan can be corrected at the source. Applying any retry policy to a persistent error just delays failure recognition without improving the outcome.

## Question 7

A fallback chain for a document-retrieval agent is: try Tool A, then Tool B, then return a cached result. During an outage, Tool A fails. Tool B also fails under conditions that were never tested. The cached result is returned to downstream components with no signal attached. Which two design failures does this scenario illustrate?

A. Using a cached result as the final fallback and failing to escalate after the second step also failed
B. Applying a fixed-delay retry to Tool B instead of exponential backoff before moving to the cached result
C. Exceeding the retry budget on Tool A and failing to define an explicit terminal step in the fallback chain
D. Deploying an unvalidated fallback that introduced a new failure mode, and masking degradation from downstream components

**Answer:** D
**Explanation:** The scenario shows both major fallback anti-patterns from the deck. Tool B failed under conditions it was never validated against — the untested-fallback anti-pattern, where a fallback introduces new failure modes exactly when reliability matters most. The cached result was returned without a degradation signal — the silent-masking anti-pattern, where downstream components treat a partial result as full-quality output and errors compound invisibly.

## Question 8

After a fallback fires and returns a partial result, the agent attaches a degradation flag to the output object. A downstream component reads the flag, lowers its confidence threshold, and routes the result to a human reviewer instead of committing it. Which concept does this design correctly implement?

A. State verification — reading back the stored result to confirm the fallback write actually succeeded
B. Silent degradation — returning a partial result without informing downstream of any quality reduction
C. Graceful degradation — signaling the quality reduction explicitly so downstream components can respond
D. Pre-validation — confirming that the fallback step will work before the primary tool is ever invoked

**Answer:** C
**Explanation:** The deck teaches that degradation signals must travel with the result — a flag or metadata field in the output object — so every downstream component can check it and adjust. A component that sees the flag can lower confidence, reroute, or refuse to commit an irreversible action. This is graceful degradation: the quality reduction is explicit and visible. Without propagation, downstream components operate on a false assumption that the output is full quality, turning a contained fallback event into a pipeline-wide silent failure.

## Question 9

A team builds a payment-processing agent and uses a detailed system prompt instructing the model to never authorize amounts above a configured limit. During a stress test, a crafted user message causes the model to authorize an out-of-range transaction that the prompt would normally block. Which limitation of prompt-based guardrails does this expose?

A. Prompt guardrails add excessive latency on high-stakes paths because they require additional inference passes
B. Prompt guardrails are only suitable for tone guidance and cannot constrain any meaningful agent behavior
C. Prompt guardrails work only in the user turn and cannot be placed in the system prompt effectively
D. Prompt guardrails rely on the model choosing compliance at inference time and can be bypassed by crafted inputs

**Answer:** D
**Explanation:** Adversarial inputs are one of the three failure modes the deck teaches for prompt-only enforcement. No prompt wording fully resists a determined attacker who crafts inputs designed to navigate around the instructions. For a high-stakes path like financial authorization, probabilistic compliance is not acceptable. The deck teaches that code must enforce what the prompt can only guide, using hard-coded amount limits and authorization checks that run before execution.

## Question 10

An architect reviewing a new agent design notes that the system relies entirely on a system prompt to govern P.I.I. handling, with no additional enforcement layer. The architect flags this as insufficient. What architectural role should code play that the prompt cannot fulfill, according to the design principle taught in this deck?

A. Code prevents non-compliant outputs from reaching the execution layer — it enforces, not guides
B. Code monitors output logs after deployment and alerts operators when a non-compliant response is detected
C. Code adds a second prompt in a separate inference call that is harder to bypass than the first prompt
D. Code reduces how often the model produces non-compliant outputs by shaping the behavioral distribution

**Answer:** A
**Explanation:** The deck's core design principle is that prompts reduce the frequency of non-compliant outputs while code prevents non-compliant outputs from reaching the execution layer at all. For PII handling, the deck names output filters as the code-layer mechanism. Treating a prompt as a substitute for code enforcement is described as an architectural mistake, not a tradeoff. The two layers are complementary — each serves a different function and neither substitutes for the other.

## Question 11

A validation gate on a financial-approval pipeline is configured to emit a soft warning and allow execution to continue when an output fails an authorization limit check. A compliance reviewer flags this as a misconfiguration. Why is a soft warning the wrong response mode for this constraint?

A. Authorization limits are non-negotiable — a gate that allows execution to continue is not actually enforcing them
B. Soft warnings should only be used at post-execution gates and never at pre-execution validation steps
C. Hard blocks must be applied to every output validation gate regardless of the risk level of the constraint
D. Soft warnings are a deprecated response mode replaced by escalation triggers for financial pipelines

**Answer:** A
**Explanation:** The deck teaches that hard blocks should be used for non-negotiable constraints — financial authorization limits, permission violations, and safety boundaries — where there is no valid execution path that includes the invalid output. Soft warnings are appropriate only for advisory constraints where human judgment can add value. Using a soft warning for an authorization limit means the gate logs the issue and moves on, which provides no actual enforcement of the constraint.

## Question 12

A pipeline has schema checks before model invocation and output validation after generation, but during a load test an agent enters a runaway loop, consuming tokens far beyond budget without any gate firing. Which enforcement layer is absent from this design?

A. Runtime checks — iteration caps and cost limits that enforce constraints during execution, not just at boundaries
B. Semantic validation — checking whether the output is plausible and consistent with the input context
C. Pre-execution validation — schema and permission checks that run before the agent invokes any tool
D. Post-execution validation — output schema compliance and business rule checks applied after generation

**Answer:** A
**Explanation:** The deck describes runtime checks as the enforcement layer that monitors the agent continuously while it is running, rather than at defined input or output boundaries. Iteration caps prevent runaway loop cycles; cost limits enforce token budgets mid-run. Pre-execution gates catch invalid inputs and post-execution gates catch invalid outputs, but neither fires during the middle of an in-progress agent loop. Runtime checks fill that gap and are the safety net for failure modes without clean stage boundaries.

## Question 13

A customer-service agent handling routine chat interactions escalates to a human reviewer every time its confidence score drops below 0.95, even for simple formatting decisions. Reviewers report approving requests without reading them because the volume is overwhelming. Which escalation design failure does this illustrate?

A. Replacing programmatic validation with HITL gates for constraints that code should be enforcing
B. Using undefined gut-feel triggers instead of explicit conditions to decide when to escalate
C. Over-escalation on low-stakes reversible actions that floods reviewers until approvals become reflexive
D. Under-escalation on high-stakes irreversible actions that allows consequential errors without human review

**Answer:** C
**Explanation:** The deck identifies over-escalation as a failure mode that defeats the purpose of automation. Escalating on every uncertain step — especially for low-stakes reversible actions — floods reviewers with unnecessary interruptions, causing them to approve without reading. At that point, human oversight becomes theater with no real safety benefit. Valid escalation triggers should be targeted at irreversible high-stakes actions or explicit authority limits, not at general uncertainty on reversible tasks.

## Question 14

A team designing an agent escalation system writes the trigger condition as: 'escalate when the agent seems to be struggling.' A senior engineer pushes back and asks them to rewrite it. What property must the revised condition have that the current version lacks?

A. A fallback chain that fires automatically whenever the escalation trigger condition is not matched
B. A natural-language instruction the model interprets at inference time to judge when a pause is warranted
C. A soft warning response mode so the agent can continue while the reviewer evaluates the situation
D. An explicit, testable threshold such as a numeric score or failure count that is consistent across every run

**Answer:** D
**Explanation:** The deck teaches that triggers defined as explicit conditions are the only reliable design. A condition like 'seems to be struggling' is not testable, not auditable, and not consistently reproducible across runs. The correct form specifies a concrete threshold — such as 'confidence score below 0.7' or 'third consecutive failure' — that can be checked in code, consistently applied, and adjusted based on observed escalation rates. Condition-based triggers are also tunable as the system evolves.

## Question 15

An agent pauses before a data-deletion step and sends a review request to a human. The reviewer approves, but by the time approval arrives, the agent's context has been cleared by a session timeout. The agent cannot determine what it was doing and restarts the entire task from scratch. Which design gap caused this failure?

A. The handoff message lacked a deadline field, so the reviewer did not know the session had a timeout
B. The agent relied on in-context state rather than persisting task progress and decisions to external storage
C. The team chose synchronous escalation when async escalation would have preserved context automatically
D. The escalation trigger was invalid — data deletion is a reversible action that does not require human review

**Answer:** B
**Explanation:** The deck teaches that in-context state is lost when the context window is truncated or a session ends, and that state preservation requires external persistence — a database or structured store. Task progress and agent decisions must be stored externally so the agent can resume from the interruption point after approval arrives, without restarting. The failure here is the absence of external state storage, not a problem with the handoff message or the escalation trigger.

## Question 16

An agent queues an approval request asynchronously and continues processing other branches. After two hours with no reviewer response, the workflow proceeds as if approval was granted. A compliance audit later flags this as a design flaw. What does the deck teach is the correct design for this situation?

A. Reduce the volume of escalation requests so reviewers can always respond within the expected window
B. Define an explicit timeout threshold and a timeout action — escalate further, abort, or apply a safe default
C. Store the pending approval in external state and automatically retry the review request on the next agent run
D. Switch to synchronous escalation so the workflow blocks completely until a human responds

**Answer:** B
**Explanation:** The deck teaches that async escalation requires explicit design for the timeout case. An unhandled timeout — where the workflow silently continues as if approval was granted — is a silent failure: the workflow appears to be running but is making unauthorized progress. Three components are required: a timeout threshold, a timeout action (escalate further, abort, or apply a safe default), and the queue-and-continue pattern for independent branches. Silently proceeding without a decision is the specific behavior the deck identifies as wrong.
