# 5B Quiz

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · D5: Context Management - Multi-Agent Failure Modes · 12 questions · pass mark 70% · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies

## Question 1

An agent is deployed to process expense reimbursements. Its system prompt lists permitted action types but does not enumerate prohibited ones. During a review, an auditor flags that the agent approved a reimbursement category that is explicitly banned by company policy. The trigger intended to catch this case never fired. What design gap most directly caused the failure?

A. The agent lacked a denylist check; without one, no hard trigger fires for prohibited categories even when they are known policy violations.
B. The repeated-failure trigger was not configured, so the agent reprocessed the same category multiple times before the policy violation was noticed.
C. The confidence gate threshold was set too high, causing the agent to report high confidence and skip the escalation check for the banned category.
D. The system prompt used ambiguous natural language rather than a structured allowlist, so the model misinterpreted the permitted categories.

**Answer:** A
**Explanation:** Denylist triggers are hard triggers that fire immediately when a planned action matches a prohibited entry — no model judgment involved. An allowlist-only system permits everything not explicitly listed as allowed, but does not create a hard stop for known prohibited actions. Both allowlists and denylists are needed to cover the full policy surface; relying only on an allowlist leaves the gap the auditor found.

## Question 2

A developer is designing escalation logic for a document review agent. The agent handles sensitive contracts and must reliably hand off to a human reviewer whenever it encounters a situation outside its authority. The developer considers using free-text output like 'I cannot handle this' versus a dedicated escalation tool. What advantage does the ask-for-help tool pattern provide?

A. The tool pattern eliminates the need for a denylist because the model will call the tool whenever it detects a policy violation.
B. Free-text escalation messages are processed faster by downstream routing systems than structured tool call outputs.
C. A dedicated escalation tool produces a structured, logged, routable handoff record that free-text output cannot reliably provide.
D. The ask-for-help tool allows the agent to escalate without interrupting the current workflow, completing the task before handing off.

**Answer:** C
**Explanation:** Defining a dedicated escalation tool (e.g., 'escalate' or 'request_review') gives the model a function it can call deliberately. When invoked, it produces a structured record containing the decision, context, and reason in one step — making it routable, parseable, and auditable. Free-text escalation messages are harder to detect, route, and parse, and are easier to miss in production monitoring.

## Question 3

An agent escalates a billing dispute to a human reviewer. The reviewer resolves it, but the original agent resumes from its pre-escalation state and escalates again on the same issue. Which design step was omitted?

A. The escalation was routed to a specialist agent instead of a human reviewer.
B. The handoff payload did not include a suggested next step for the reviewer.
C. The reviewer's resolution was never re-injected into the original agent's context window.
D. The payload used a narrative dump rather than a structured schema.

**Answer:** C
**Explanation:** Closing the loop means re-injecting the reviewer's response back into the original agent's context window after the escalation resolves. Without that step, the agent restarts from its pre-escalation state and cannot use the resolution — causing repeated escalations. The other options describe real payload elements but none of them is the step that delivers the resolution back to the agent.

## Question 4

A team reviews escalation logs and finds that identical trigger categories account for 60% of all handoffs. Which action does this pattern most directly support?

A. Switch from structured payloads to narrative dumps to capture more nuance.
B. Add a second suggested-next-step field to the payload for that trigger type.
C. Review the threshold or allowlist configuration for that trigger category.
D. Replace the human reviewer queue with a supervisor model for that trigger.

**Answer:** C
**Explanation:** The deck teaches that structured escalation logging reveals patterns — such as a single trigger category dominating volume — which then drive threshold refinement, allowlist additions, or prompt fixes. The pattern is a diagnostic signal, not merely a reporting artifact. The other options describe reasonable operational steps but do not match what the deck says a concentrated trigger pattern most directly calls for.

## Question 5

A subagent handling document retrieval catches every exception internally and always returns a success signal to the coordinator. Three sessions later, analysts notice the coordinator has been planning on malformed output for days. Which failure mode is this?

A. Silent corruption — the coordinator proceeded on output that was partially wrong and had no error signal to act on.
B. Retry budget exhaustion — the subagent ran out of local retries before the coordinator could intervene.
C. Coordinator thrash — every blip surfaces as a failure event, overwhelming the coordinator with noise.
D. Propagation boundary misconfiguration — the boundary was set too high, blocking legitimate failure signals.

**Answer:** A
**Explanation:** The deck defines 'never propagate' as the failure mode where the coordinator receives a success signal regardless of what happened internally, leading to silent data corruption. The harm accumulates invisibly because no error event is raised. The other options describe the opposite extreme (coordinator thrash) or unrelated concepts from the deck.

## Question 6

A subagent hits a rate-limit pause that resolves in 200 milliseconds on its own. According to the coordinator-needs-to-know test, how should this be handled?

A. Handle it locally — the pause resolved itself and the coordinator's plan is unaffected.
B. Propagate it as a warning-level event so the coordinator can log the rate-limit pattern.
C. Halt the task and surface it as fatal because rate limits indicate a resource constraint.
D. Propagate it as a recoverable error so the coordinator can apply exponential backoff.

**Answer:** A
**Explanation:** The deck's coordinator-needs-to-know test asks whether the coordinator's higher-level plan would change if it knew about the failure. A transient rate-limit pause that resolves itself does not affect scope, sequencing, or resource allocation, so local recovery is the right call. The coordinator gets accurate results and needs no adjustment. The other options misapply the test or escalate unnecessarily.

## Question 7

A subagent completes the first three steps of a five-step data-migration task, then fails on step four and propagates an error envelope to the coordinator. The coordinator retries by re-invoking the full task from the beginning. Steps one through three execute again, doubling writes to the external database. Which missing element caused this?

A. The severity level was set to warning instead of recoverable, preventing retry logic from activating.
B. The subagent failed to include idempotency keys for the external database writes.
C. The error envelope used an unstructured free-text description instead of typed fields.
D. The error envelope lacked a completed_steps field, so the coordinator had no way to resume from step four.

**Answer:** D
**Explanation:** The deck teaches that the error envelope must include a completed_steps field so the coordinator knows how far the subagent got before failing. Without it the coordinator cannot distinguish 'failed at start' from 'failed partway through' and may re-execute successful steps, causing duplicate side effects. Idempotency keys are a related safeguard but do not tell the coordinator which steps were already done.

## Question 8

A coordinator receives a propagated error and reads the severity field as 'fatal.' Based on the propagation contract taught in this deck, what should the coordinator do next?

A. Route the task to a fallback agent with a different model implementation.
B. Log the event and continue executing the remaining task chain without interruption.
C. Retry the subagent with exponential backoff until the retry budget is exhausted.
D. Halt the dependent task chain and escalate the failure to a human operator.

**Answer:** D
**Explanation:** The deck defines three severity levels with explicit coordinator policies. Fatal means halt the dependent task chain and escalate to a human operator who can exercise judgment that automated policy cannot. Warning maps to log-and-continue; recoverable maps to retry or fallback. These policies must be pre-defined, not improvised at runtime.

## Question 9

An agent queries a vector-index search tool. The index service is offline, but the tool returns an empty list with no error flag. The agent responds to the user: 'I could not find anything on that topic.' Why is this response problematic?

A. It is too hedged — the agent should answer confidently even when tool results are uncertain.
B. The response is missing a disclaimer noting that the vector index was unavailable at query time.
C. It implies a successful search when the tool never reached the data source, misleading the user into acting on unconfirmed absence.
D. The agent should have retried the query before responding, which would have returned real results.

**Answer:** C
**Explanation:** The deck explains that 'I could not find anything' implies the search succeeded with no matches, which is only appropriate for a confirmed empty result. When the tool failed to reach the data source at all, the correct statement is 'I was unable to check.' Using the wrong phrase causes users to make decisions on a false premise — believing data does not exist when it was never actually searched.

## Question 10

During a code review, an engineer notices that a search tool returns a raw empty list whenever a query times out. The deck teaches this is a 'silent false negative.' What architectural layer does the deck say must fix this?

A. The orchestrator's error-handling policy, which should intercept empty results before they reach the agent.
B. The tool-wrapper layer, which must catch the timeout and attach an access-failure status before passing the response to the agent.
C. The vector-index service itself, which should return a non-200 status on every timeout.
D. The agent's system prompt, which should instruct the model to treat empty lists as uncertain until verified.

**Answer:** B
**Explanation:** The deck places the responsibility for disambiguation squarely at the tool-wrapper layer — not the model prompt, not the agent logic. The wrapper intercepts every raw tool response, detects access failures (including timeouts), and attaches an explicit status field before the agent ever sees the result. Fixing the prompt or the model's instructions cannot compensate for a tool that never signals the failure.

## Question 11

A tool wrapper receives a 200 HTTP response with an empty list from a search endpoint. It also intercepts a 503 response from the same endpoint on a second call. How should the wrapper classify each outcome according to the status enum taught in this deck?

A. Both should be classified as access_failure because neither call returned usable data.
B. The 200/empty is success because the call completed; the 503 should be retried silently without updating the status field.
C. The 200/empty is partial_result because the index may have been truncated; the 503 is access_failure.
D. The 200/empty is empty_result (confirmed absence, no retry); the 503 is access_failure (do not conclude, retry per policy).

**Answer:** D
**Explanation:** The deck's first wrapper rule is that HTTP success with an empty body and HTTP failure are fundamentally different outcomes. A 200 with an empty list is a valid empty_result — the server processed the query and found nothing. A 5xx is an access_failure regardless of body content. These map to different status enum values and different agent behaviors: empty_result is a confirmed answer (no retry), access_failure triggers retry with backoff.

## Question 12

A team wants to prevent an agent from ever seeing ambiguous empty results. They make the status field in the tool response schema optional to preserve backward compatibility. The deck argues this approach will fail. Why?

A. Backward compatibility requires keeping the old schema, so a new status field cannot be added at all.
B. Optional fields get omitted by developers under pressure, reverting those calls to the ambiguous silent-failure state.
C. Optional fields increase response payload size, slowing the agent's inference over the result.
D. Optional status fields prevent the wrapper from executing retry logic for access failures.

**Answer:** B
**Explanation:** The deck specifies that the status field must be mandatory, not optional. Optional fields get omitted under time pressure, and any call that omits the field reverts to the ambiguous-nothing problem. The wrapper cannot enforce disambiguation if the schema allows the status to be absent. The field must also be a typed enum, not a free-text string, to support deterministic branching.
