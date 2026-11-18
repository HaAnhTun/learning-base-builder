# Practice Exam 2 - Moderate Difficulty

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · Practice Exams · 60 questions · pass mark 72% · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies

## Question 1 [D1]

A Customer Support Agent runs an action loop that reads a ticket, queries account tools, and replies. During a billing-system outage it began retrying the same failing balance lookup hundreds of times, never terminating, until it exhausted the rate limit. The architect must add the control that most directly prevents this class of failure while preserving autonomy. Which design BEST addresses the root cause?

A. Lower the model temperature to zero so the loop behaves deterministically and stops generating varied retry attempts each cycle
B. Replace the agent with a fixed workflow so the retry behavior is hard-coded and the model can no longer choose to repeat the lookup, because removing runtime autonomy is the only sure way to guarantee a loop can never run away
C. Add explicit termination conditions plus exponential backoff that classifies the outage as a transient environment error and escalates after bounded retries
D. Switch the balance lookup to a parallel fan-out of three concurrent calls so a healthy replica answers before the loop repeats

**Answer:** C
**Explanation:** Every agentic loop requires explicit termination conditions, the absence of which caused the runaway. Pairing a max-retry bound with exponential backoff (appropriate for transient environment errors) and an escalation trigger after the bound combines the action loop with error propagation and escalation design. This stops the storm while keeping the agent autonomous for normal cases.
**Why not A:** Temperature controls token sampling, not loop termination. A deterministic loop with no stop condition still runs forever; this misdiagnoses a control-flow defect as a sampling problem.
**Why not B:** Abandoning agentic architecture to fix a missing termination condition is overcorrection. A workflow could repeat the same bug; the real fix is bounding the loop, not removing autonomy.
**Why not D:** Fan-out multiplies load against an already-failing system and still lacks a termination bound. Parallelizing a call that fails because the backend is down accelerates the rate-limit exhaustion.

## Question 2 [D1]

Which of the following BEST captures the difference between tool use and an agentic loop in a Data Extraction context?

A. Tool use is strictly read-only, whereas an agentic loop is what introduces the ability to write changes back to external systems and persist them
B. Tool use refers to a single tool invocation; an agentic loop is many tool invocations chained by the model based on observations
C. Tool use requires JSON schemas; an agentic loop accepts free-form output
D. Tool use is synchronous; an agentic loop is asynchronous

**Answer:** B
**Explanation:** Tool use is the capability; the agentic loop is the architectural pattern where the model chains tool calls based on observations. A single tool call wired into a workflow is tool use without the loop; an agent chains tools at runtime.
**Why not A:** Read/write semantics do not distinguish tool use from agentic loops. Both can include read and write tools. The distinction is whether the model chooses sequence at runtime.
**Why not C:** Both tool use and agentic loops use structured tool schemas. Agentic loops are not less structured; they just iterate, which is orthogonal to schema requirements.
**Why not D:** Synchrony is an implementation detail unrelated to the distinction. Both tool use and agentic loops can be implemented synchronously or asynchronously; the architectural property is iteration with runtime decisions.

## Question 3 [D4]

A Customer Support Agent handles long sessions where users iteratively refine their issue description over 15-20 turns. Engineers observe that by turn 12, Claude begins dropping references to details established in turns 2-4, causing repetitive questions to the user. The context window is not full. Which multi-turn design pattern MOST directly addresses this mid-conversation forgetting?

A. Increase max_tokens to allow longer responses so Claude has more room to reference earlier turns.
B. Inject a structured summary of confirmed facts into the conversation before context degrades.
C. Reduce the number of turns by prompting users to submit a complete issue description upfront rather than iterating.
D. Enable extended thinking so Claude reasons more carefully about the full conversation before generating each response.

**Answer:** B
**Explanation:** Proactive fact injection counters the lost-in-the-middle effect by surfacing key established facts near the current turn where attention is highest. This is a standard multi-turn design pattern for long sessions where early context risks being underweighted.
**Why not A:** max_tokens controls response output length, not how much of the conversation history is attended to; increasing it does not improve attention to early turns.
**Why not C:** Changing the interaction model avoids the multi-turn design challenge rather than solving it; many support workflows require iterative clarification and cannot be collapsed to a single turn.
**Why not D:** Extended thinking improves multi-step reasoning depth but does not specifically address the lost-in-the-middle effect, which is an attention-weighting phenomenon, not a reasoning depth issue.

## Question 4 [D1]

A Multi-Agent Research platform team is choosing whether to define a feature as a workflow or as an agentic system with workflow-like guardrails. The CTO asks for criteria that drive the choice. Which criteria MOST cleanly capture CCA-F guidance?

A. Workflow when sequence is predetermined and enforcement is paramount; agentic with workflow-like guardrails when adaptation within bounds is needed
B. Use a workflow if the team likes structure and an agentic design if the team likes flexibility, since the choice ultimately comes down to which style the team is more comfortable with
C. Use a workflow for new features and an agentic design for the legacy ones
D. Always use a workflow, on the grounds that workflows are simpler

**Answer:** A
**Explanation:** Workflow class fits predetermined sequence with strong enforcement; agentic-with-guardrails fits adaptation within defined bounds. CCA-F guidance favors this stake-vs-flexibility criterion. Workflows trade adaptability for enforceability; agents-with-guardrails trade some enforceability for adaptability.
**Why not B:** Preference is not the criterion. CCA-F guidance is property-driven: predetermined sequence favors workflow, adaptive favors agent.
**Why not C:** Feature age is not the criterion. New features can be either class; legacy features can be either. The choice is property-driven.
**Why not D:** Always-workflow forces inappropriate structure on adaptive tasks. CCA-F guidance favors stake-driven choice.

## Question 5 [D2]

A Code Generation client connects to three MCP servers. After the initial handshake, all three servers' tools are exposed to the model. A new server is added to the configuration mid-session. Which behavior is correct?

A. The client refuses the addition because federation is fixed at session start, so any server not present during the initial handshake cannot contribute tools until the whole session is restarted fresh
B. The client establishes a connection to the new server, runs the initialization handshake, and adds its capabilities to the federated surface presented to the host — the model's tool catalog grows mid-session
C. The client terminates the current session and requires a full restart to bring the new server online, treating any mid-session federation change as something that only a completely clean reinitialization can handle safely
D. The new server's tools are queued internally and become available only on the next user turn, since the client defers exposing any freshly federated capabilities until a turn boundary is reached

**Answer:** B
**Explanation:** MCP clients support adding servers mid-session: connect to the new server, run the initialization handshake, federate its capabilities into the unified surface. The model's tool catalog grows accordingly. This is the symmetric operation to mid-session disconnect — federation is dynamic, not locked at session start.
**Why not A:** Federation is dynamic, not fixed at session start. Servers can be added or removed during a session.
**Why not C:** Session restart is too aggressive for mid-session server addition. Clients support dynamic federation.
**Why not D:** There is no protocol-mandated queuing for mid-session additions. Once the handshake completes, capabilities are exposed.

## Question 6 [D2]

A Multi-Agent Research orchestrator's tools each accept a `confidence_threshold` parameter (float 0 to 1). Tools were authored by different teams and the parameter's semantics drift: some treat 0.7 as 'high confidence,' others as 'medium.' The team wants consistent semantics across tools. What is the BEST architectural fix?

A. Add a description note to each tool documenting how that tool interprets the float
B. Replace the float with a shared enum (low/medium/high) defined in a common schema module, and have every tool import the enum so semantics are unified at the type level
C. Standardize on float and publish a guideline that 0.5 means medium across all tools
D. Have the orchestrator post-process tool calls to normalize the threshold before invoking, so a single centralized normalization step rewrites every tool's float into one canonical scale regardless of how each tool author defined it

**Answer:** B
**Explanation:** Cross-tool semantic consistency is enforced by sharing a canonical type, not by per-tool documentation. A shared enum defined once and imported by every tool gives all tools the same meaning of low/medium/high, makes drift impossible at the type layer, and centralizes any future change. This is the production pattern for cross-tool semantic alignment.
**Why not A:** Per-tool documentation does not enforce consistency. Teams drift again on the next change. The fix needs to be at the type/schema layer where it cannot be skipped.
**Why not C:** Guidelines without enforcement drift over time. Without a shared type, each tool's authors will reinterpret the float as their use case requires.
**Why not D:** Orchestrator-side normalization papers over an upstream inconsistency and adds maintenance burden when new tools join. Fixing the parameter's type once at the source is durably cleaner.

## Question 7 [D5]

A Multi-Agent Research firm designs a workflow where 12 subagents each produce 5KB findings, an aggregator concatenates them into 60KB and asks Claude to synthesize a final report. Mid-list findings consistently underrepresent in the synthesis. Which architectural change BEST addresses this while preserving the multi-agent pattern?

A. Reduce the subagent count to three and let each cover four topics
B. Use a tree-structured aggregator that synthesizes groups of three findings first, then synthesizes those summaries
C. Concatenate findings as JSON with explicit numerical indexes to force ordering attention, since indexing each finding makes the model weight all positions equally and cancels the mid-list dip
D. Sort findings by relevance score and only include the top three in the synthesis

**Answer:** B
**Explanation:** A hierarchical aggregator bounds each synthesis context to roughly 15KB at a time, keeping every finding in the high-attention zone. The final synthesis sees four summaries instead of twelve, and the lost-in-the-middle exposure is eliminated at each level. The multi-agent pattern is preserved and even strengthened.
**Why not A:** Collapsing 12 into 3 reintroduces the per-agent dilution that motivated decomposition in the first place. The bottleneck is the synthesis step, not the subagent count.
**Why not C:** JSON indexing aids parsing but does not change attention weighting. Items 4 through 9 in a JSON list of 12 still sit in the lost-in-the-middle zone of the model's context.
**Why not D:** Discarding nine of twelve findings throws away information the team explicitly chose to gather. The problem is synthesis attention, not finding quality; the fix should preserve the data.

## Question 8 [D2]

A Multi-Agent Research orchestrator dispatches four sub-queries in parallel. One returns valid results, two return validation errors, and one times out. The orchestrator currently aggregates only the successful one and ignores the rest. Engineers complain about silent quality degradation. What is the BEST architectural fix?

A. Aggregate ALL outcomes (success, validation errors, timeout) into a single structured response, annotate the partial-failure cases, and have the orchestrator surface both the data and the degradation signal to its caller
B. Wait for all four branches to fully succeed before returning any results at all, so the orchestrator only ever aggregates a complete, fully-validated set of sub-query outputs
C. Take the single successful branch and discard the other three branches silently, since the one valid result is enough to proceed and surfacing the failed branches would only clutter the orchestrator's downstream reasoning
D. Retry the three failed branches repeatedly until they all succeed, then aggregate the now-complete set so the consumer always receives every branch's contribution

**Answer:** A
**Explanation:** Silent quality degradation is a fallback-without-signal antipattern: the system continues producing output but the consumer can't tell it was partial. The fix is propagating the degradation signal alongside the partial data — aggregate every branch's outcome, annotate failures, and surface the structured response to the caller. Then the consumer (agent or user) can decide whether the partial result is acceptable.
**Why not B:** All-or-nothing waiting sacrifices the partial successes that arrived correctly and may block indefinitely on transient failures. Aggregate-with-signal is the durable pattern.
**Why not C:** This is the current behavior driving the complaint — silent degradation. The fix is making the degradation visible to the consumer.
**Why not D:** Retrying timeouts and validation errors blindly can spin indefinitely and doesn't address the design problem that the system silently degrades. The fix is signaling partial outcomes, not hiding them under retries.

## Question 9 [D1]

A Multi-Agent Research platform team is designing a general-purpose orchestration layer. The team must decide how to handle both sequential and parallel execution uniformly. Which design strategy is MOST consistent with CCA-F principles for a flexible orchestration layer?

A. Force absolutely everything to run strictly sequentially one after the other in order to keep the orchestrator itself as simple as possible
B. Express subtasks with explicit dependencies in a DAG; the orchestrator runs independent nodes in parallel and dependent nodes sequentially
C. Force everything to be parallel to maximize speed
D. Let each subagent decide its own execution pattern

**Answer:** B
**Explanation:** A directed acyclic graph (DAG) of subtasks with explicit dependencies lets the orchestrator decide parallel-vs-sequential per pair of nodes automatically. CCA-F guidance treats DAG-based orchestration as the canonical flexible model: dependencies drive scheduling, independence enables parallelism, and the orchestrator handles fan-in/fan-out implicitly.
**Why not A:** Forcing sequential gives up parallel benefits and is not a flexible layer — it cannot run independent subtasks concurrently. The DAG-based approach is more general and more efficient.
**Why not C:** Forcing parallel violates dependencies and produces incorrect results on dependent subtasks. A flexible layer must respect dependencies, not ignore them.
**Why not D:** Subagents do not have global dependency view — the orchestrator does. CCA-F guidance places scheduling at the orchestrator, not in individual subagents, because only the orchestrator can see the full DAG.

## Question 10 [D2]

A Customer Support Agent calls a `refund_payment` tool. The first call appears to fail with a network timeout, so Claude retries. The user is later double-refunded. Which tool design change PREVENTS this failure mode?

A. Add server-side rate limiting so duplicate calls within five seconds are rejected
B. Increase the tool's timeout from 30 seconds to 5 minutes to reduce retries, since a longer window lets slow refunds finish before Claude ever concludes the call failed
C. Make the tool synchronous so Claude waits for the response and cannot retry prematurely, because a blocking call holds the model until the refund definitively succeeds or fails, removing the window in which a duplicate retry could fire
D. Require an `idempotency_key` parameter on the tool, with the server deduplicating retries by that key

**Answer:** D
**Explanation:** An idempotency key lets the server recognize a retry as a retry rather than as a fresh request. The server stores the result of the first successful execution against the key and returns the cached result on any subsequent call with the same key. This is the canonical pattern for retry-safe write tools.
**Why not A:** Rate limiting blocks rapid duplicates but does not establish a stable identity for the original request. A retry after the rate-limit window still double-refunds. The right primitive is idempotency.
**Why not B:** Increasing timeouts reduces retry frequency but does not make retries safe when they do happen. The goal is making retries non-destructive, which requires idempotency keys.
**Why not C:** Synchronous tools still time out at the network layer, and Claude still retries when timeouts occur. Synchrony does not address retry safety; idempotency does.

## Question 11 [D4]

A Data Extraction team wants to test a new system prompt against the production prompt without affecting customers. Both prompts target the same Claude model. Which approach BEST supports the A/B comparison?

A. Deploy the new prompt to production and roll back if anyone complains
B. Route 50% of live traffic to each prompt and compare customer complaints, since real production traffic is the most representative test and complaints are ground truth
C. Run each prompt on 10 ad-hoc examples and read the outputs manually
D. Run both prompts against a shared held-out test dataset of labeled examples and compare structured metrics — exact match, field-level F1, parse failures

**Answer:** D
**Explanation:** A/B prompt evaluation requires a frozen labeled dataset and structured metrics. Shared inputs and code-based grading produce apples-to-apples comparison without affecting customers. Live traffic comparisons risk customer exposure to the worse prompt and confound the metric with traffic mix changes.
**Why not A:** Deploy-and-pray bypasses evaluation. Customer impact is uncontrolled.
**Why not B:** Live traffic A/B exposes customers to the worse prompt and uses complaint as a noisy lagging metric. Held-out evaluation is faster and cleaner.
**Why not C:** Ten ad-hoc examples give coverage far too narrow to represent real inputs, and reading outputs manually makes grading subjective and unrepeatable. Prompt selection needs a frozen labeled dataset with structured metrics.

## Question 12 [D1]

A Code Generation platform team is reviewing decomposition designs across multiple agents. The CTO asks for a set of properties that distinguish well-decomposed designs from poorly decomposed ones. Which set MOST cleanly captures CCA-F guidance?

A. Minimum subtask count, flattest hierarchy, sequential execution everywhere, and smallest models
B. Maximum possible subtask count, the deepest achievable hierarchy, parallel execution applied everywhere, and the largest available models
C. Right-sized subtasks, disjoint scopes, explicit dependencies, checkpointable boundaries, and clean orchestrator contracts
D. Whatever the team finds most readable in code review

**Answer:** C
**Explanation:** CCA-F decomposition quality reduces to five properties: right-sized subtasks (controllability), disjoint scopes (no duplication), explicit dependencies (correct sequencing), checkpointable boundaries (validation), and clean orchestrator contracts (extensibility). Each property addresses a distinct failure mode of poor decomposition.
**Why not A:** Minimizing every axis under-decomposes the work and forfeits parallel opportunity. Blanket minimization is just as wrong as blanket maximization; the CCA-F properties describe a balance across these axes, not a push to either extreme.
**Why not B:** Maximizing each axis ignores trade-offs — more subtasks pay orchestration cost, deep hierarchies inflate coordination, parallel-everywhere assumes independence that may not hold, large models do not address structure. The CCA-F properties are about balance, not maxima.
**Why not D:** Readability is one operational concern but not the design framework. CCA-F decomposition quality has objective properties — right-sized, disjoint, explicit, checkpointable, clean contracts — that go beyond code-review aesthetics.

## Question 13 [D1]

A Customer Support Agent orchestrator dispatches three parallel subagents and the fan-in pattern is voting (majority wins). Which CCA-F insight MOST directly applies?

A. Voting fan-in increases reliability through redundancy but pays 3× the cost of single execution
B. Voting across the branches is essentially always going to be cheaper overall than just a single execution
C. Voting is inappropriate for any agentic task
D. Voting requires sequential execution

**Answer:** A
**Explanation:** Voting fan-in is a quality/reliability pattern that pays cost proportional to branch count. CCA-F guidance acknowledges the trade-off: more branches improve majority robustness but increase cost. Choose voting when reliability matters more than cost on a specific task.
**Why not B:** Voting executes the same task on multiple branches and is more expensive than single execution. The benefit is reliability, not cost reduction.
**Why not C:** Voting is a valid pattern for high-reliability scenarios. CCA-F guidance treats it as one tool in the design toolkit, not as a categorically wrong pattern.
**Why not D:** Voting typically uses parallel execution of identical tasks. Sequential voting wastes the wall-time benefit of parallelism without changing the voting semantics.

## Question 14 [D2]

A customer support platform needs to deploy an MCP server that will be accessed by multiple agent instances running on different hosts. The server must support concurrent connections and will be accessed over the network. Which MCP transport should the team use?

A. STDIO, because standard input/output can be redirected over SSH tunnels to support network access.
B. StreamableHTTP, because it is designed for remote, multi-user, and production deployments accessed over the network.
C. Either transport, since MCP servers support hot-switching between STDIO and StreamableHTTP without configuration changes.
D. STDIO on the server host combined with a reverse proxy to convert HTTP client requests to STDIO format for each agent instance.

**Answer:** B
**Explanation:** StreamableHTTP is the correct transport for remote, multi-user production deployments. It runs the server as an HTTP service, supports concurrent connections from multiple clients, and can stream responses via Server-Sent Events.
**Why not A:** Using SSH tunnels to redirect STDIO over a network is an anti-pattern for production multi-user deployments. StreamableHTTP is the specified transport for network-accessible, multi-user MCP servers.
**Why not C:** STDIO and StreamableHTTP are fundamentally different deployment models -- one runs as a child process, the other as an HTTP service. They are not interchangeable without architectural changes.
**Why not D:** Adding a reverse proxy to adapt HTTP to STDIO creates unnecessary complexity. StreamableHTTP is the purpose-built transport for exactly this scenario.

## Question 15 [D2]

A Code Generation MCP server emits a progress notification 'progress: 40%, stage: parsing' during a long tool call. The client wants to surface this to the model so the agent can decide whether the operation is on track. Should the client forward progress notifications to the model?

A. Yes, the model should see every single progress notification as it arrives so it stays continuously informed about how far along the operation is and can react the moment anything looks like it is going wrong during the long-running tool call it is currently waiting on
B. Generally no — progress notifications are operational signals for the host UX and observability, not model context; forwarding every progress update would clutter the model's working memory with telemetry it can't usefully act on
C. Yes, but the client should forward the progress notification to the model only when it reaches one hundred percent, so the model learns the operation finished without being flooded by the intermediate updates
D. The protocol forces the client to forward all progress notifications to the model and gives the client no choice in the matter, so whether the model sees them is dictated by MCP rather than by host policy

**Answer:** B
**Explanation:** Progress notifications are for the host (UI progress bar, observability) and the human user, not for the model. Forwarding them to the model adds telemetry the model can't usefully act on (the model can't speed up a parsing job) and clutters its working memory. The model sees the final tool result; intermediate progress is for the human-facing path.
**Why not A:** Per-notification model context clutters the working memory with telemetry. Progress is for the human-facing path.
**Why not C:** 100% completion is signaled by the tool's actual return, not a notification. The notification at 100% is redundant.
**Why not D:** Clients have control over what reaches the model. Progress is for host UX by convention, not model context.

## Question 16 [D5]

A Developer Productivity agent running in Claude Code approaches its context limit after 80 turns of codebase exploration. The developer wants to continue the session with minimal disruption. Which action MOST directly addresses context pressure while preserving session coherence?

A. Increase the context window via API parameter to continue without modification.
B. Start a new Claude Code session and re-explain the task from scratch.
C. Run /compact to summarize conversation history, preserving key context in a compressed form.
D. Delete recent tool call results to free context space, preserving only the conversational turns.

**Answer:** C
**Explanation:** Correct. /compact is Claude Code's built-in context management command that summarizes conversation history to free context space while preserving session coherence through a structured summary. It is the canonical tool for managing context pressure in long Claude Code sessions.
**Why not A:** Context window size is determined by the model and cannot be increased via API parameter. Claude Code operates within the model's fixed context limits.
**Why not B:** Starting fresh loses all accumulated reasoning, discoveries, and decisions from the 80-turn session. This sacrifices coherence entirely and forces redundant work.
**Why not D:** Manually deleting tool results would require the developer to manually manage context content. This is error-prone and does not preserve the structured summary that /compact produces.

## Question 17 [D5]

A Customer Support Agent platform serves Tier 1, Tier 2, and Enterprise customers. The team wants escalation triggers, handoff schemas, and review-queue routing tuned per tier. They consider three approaches: separate agents per tier, one agent with tier-conditional logic, or one agent with externalized policy. Which architecture BEST scales as the tier list grows?

A. One agent with externalized policy keyed by tier — triggers, schemas, queues all driven by policy lookup
B. Separate agents per tier, since full isolation makes per-tier debugging and policy changes far easier to reason about as tiers grow
C. One agent with hardcoded tier-conditional branches in the prompt
D. Identical policy across all tiers; let humans decide manually

**Answer:** A
**Explanation:** Externalized policy keyed by tier scales to N tiers without code change. Adding a new tier means adding a row in the policy store; triggers, schemas, and queue routes all read from it. Separate agents would multiply maintenance; tier-conditional code in one agent quickly becomes unmaintainable. Policy-driven systems are the standard architectural pattern when business segmentation grows.
**Why not B:** Separate agents create N codebases to maintain, version, deploy, and test. Tier-specific debugging is easier per agent but the operational surface area grows linearly with tiers — the wrong scaling property.
**Why not C:** Hardcoded conditional prompts become unmaintainable as tiers grow. Every change requires re-testing all branches, and the prompt itself bloats.
**Why not D:** Uniform policy across distinct tiers either over-gates the low tier or under-gates the high tier. Per-tier customization is the explicit requirement of the scenario.

## Question 18 [D4]

A Developer Productivity assistant exposes a Bash tool through an MCP server. Security wants Claude to refuse destructive shell commands. An engineer adds a system-prompt instruction: 'You are a careful DevOps expert; never run destructive commands.' During a red-team test, a crafted user request still elicits a destructive command. Which assessment of this control is MOST accurate from an architectural standpoint?

A. The role assignment grants the careful persona the authority to block destructive commands, so the failure must stem from a malformed system prompt section that, once corrected, will let the persona reliably enforce the refusal as a hard control
B. Setting temperature to 0 will make refusals deterministic, so the same destructive request will then be consistently blocked across runs
C. Adding more forceful language and capitalized warnings to the system prompt will make the behavioral constraint reliable enough to serve as the control
D. Prompt-based guardrails are probabilistic and can fail under adversarial input; the destructive-command block belongs in the MCP tool's deterministic permission layer

**Answer:** D
**Explanation:** A system-prompt behavioral constraint is a soft guardrail that adversarial inputs can defeat. Enforcing the block in the MCP server's tool permissions makes it deterministic and outside the model's discretion. Defense in depth keeps the prompt instruction but does not rely on it as the control.
**Why not A:** Role assignment shapes style and does not grant or revoke capabilities; a persona cannot enforce a security boundary. The premise that the persona has blocking authority is the misconception.
**Why not B:** Temperature 0 reduces sampling variance but does not make a soft instruction adversarially robust; the model can deterministically comply with a crafted bypass.
**Why not C:** Stronger wording does not convert a probabilistic prompt guardrail into a deterministic boundary; adversarial prompts can still override emphasis.

## Question 19 [D2]

A Code Generation team's MCP server lists 12 tools via tools/list. Each tool definition includes a comprehensive `inputSchema` and `description`. Clients still report that some tools are confusing to choose between. Which addition to each tool's definition MOST directly helps the host application surface clearer choices to its users?

A. Add an `annotations` block (e.g., `readOnlyHint`, `destructiveHint`, `idempotentHint`) so the host can render visual cues to users about each tool's nature
B. Add a `priority` integer so the host can sort tools in display order
C. Include the full source code of the tool implementation in the description so the host can show users exactly what each tool does, removing any ambiguity about behavior when two tools sound similar
D. Provide a screenshot of the tool's output in each tool's metadata so users can preview what the tool returns before choosing it

**Answer:** A
**Explanation:** MCP tool annotations like readOnlyHint and destructiveHint give the host application metadata to render visual cues (e.g., a warning icon for destructive tools, a check for read-only ones). These hints help users — not the model — distinguish between similar-sounding tools at the UI layer. The model still relies on descriptions for routing.
**Why not B:** There is no standard priority field in MCP tool definitions. The protocol provides annotations for tool semantics, not display ordering.
**Why not C:** Including source code in the description does not help user choice and inflates the per-turn token cost. The user needs semantic hints, not implementation detail.
**Why not D:** Screenshots are not part of the MCP tool definition shape. Tool annotations are the structured way to communicate semantic properties to the host.

## Question 20 [D1]

A Customer Support Agent team built an agent because they expected the task to require runtime adaptation. After six months, telemetry shows that the agent makes the same five tool-call sequences 92% of the time. Which interpretation is MOST consistent with CCA-F guidance?

A. Add more tools to the agent so it has even more flexibility
B. The agent is clearly performing perfectly well on all the data, so absolutely no architectural change of any kind is needed here
C. The original choice was wrong for the common path; a workflow with the five sequences would better fit the 92%
D. Replace the agent with a conversational system

**Answer:** C
**Explanation:** 92% predictable sequences indicate the agentic class is over-engineered for the dominant case. CCA-F principles favor matching architecture to actual usage; the right refactor is to encode the five sequences as a workflow and keep the agent for the 8% residual where adaptation is real.
**Why not A:** Adding tools to an agent that mostly does five sequences extends the scope problem rather than addressing the mismatch. The fix is to match architecture to usage, not to expand capability the usage does not need.
**Why not B:** 'Performing' on 92% predictable cases is what a workflow would also do — at lower cost and lower variance. The evidence shows the agentic class is unnecessary on the dominant case, which is a cost-and-variance issue even if functional output is acceptable.
**Why not D:** Conversational cannot take the actions the support agent currently performs. The downgrade target is workflow for the predictable case, not all the way to conversational.

## Question 21 [D5]

A Developer Productivity team adds an escalation trigger for any action that would commit code. After deployment they find the agent escalates even on local test runs that never commit. Which adjustment is MOST appropriate?

A. Narrow the trigger to actual commit invocations, not actions that could potentially lead to commits
B. Disable the trigger entirely, since commit actions are routine enough that they do not actually need any human oversight
C. Widen the trigger to include any file modification
D. Manually approve every action including local test runs

**Answer:** A
**Explanation:** Triggers should fire on the specific action they aim to gate, not on a broader class that includes it. Local test runs are not commits and should not be gated by a commit trigger. Narrowing the trigger to actual commit invocations restores intended behavior without losing oversight on real commits.
**Why not B:** Disabling removes the oversight the team explicitly wanted. The miscalibration is in the trigger condition, not in whether to have one.
**Why not C:** Widening the trigger increases false positives further — even more legitimate work would be gated. The direction is wrong.
**Why not D:** Requiring approval for everything defeats the purpose of automation. The trigger should match the specific risk it gates.

## Question 22 [D1]

A Multi-Agent Research orchestrator has three subtasks: fetch from feed A, fetch from feed B, fetch from feed C. Which execution pattern is MOST appropriate?

A. Run only feed A and skip the others
B. Sequential execution of the three fetches in order to maintain strict consistency across all of them
C. Parallel execution because the three fetches are independent and can proceed concurrently
D. Execute the fetches in a hub-and-spoke topology

**Answer:** C
**Explanation:** Three independent fetches with no inter-dependencies are the canonical parallel case. Wall time becomes max(A, B, C) instead of A + B + C. CCA-F guidance assigns parallel execution to truly independent subtasks; the fan-out pattern fits cleanly here.
**Why not A:** Skipping feeds loses data the team explicitly wants. The requirement is three feeds; parallel execution is the right pattern, not partial skipping.
**Why not B:** Independent fetches do not need sequencing for consistency — they retrieve from different sources. Sequential execution wastes wall time without providing any consistency benefit.
**Why not D:** Hub-and-spoke is a coordination topology, not an execution pattern. Parallel fetches can use a hub-and-spoke pattern, but the execution choice — parallel — is the answer to the execution-pattern question.

## Question 23 [D5]

A Multi-Agent Research firm wants to use compaction in subagents as well as the parent. Which design consideration BEST applies?

A. Subagents cannot be compacted at all, since the compaction mechanism only ever applies to the parent session
B. Subagents should compact more aggressively than parents, since their tighter and more focused scope means heavier summarization does less damage and frees the most working room for the delegated task
C. Subagents typically have shorter lifespans and tighter scope, so compaction is often unnecessary — design for context-clean delegation instead
D. Require compaction for every subagent as a universal context-hygiene rule

**Answer:** C
**Explanation:** Subagents that complete a single task usually do not need compaction — their context is built fresh for the task and discarded after. The right design is to size subagent contexts to fit their task without compaction. Compaction is more relevant for long-running parent agents or sessions that span many tasks.
**Why not A:** Subagents can be compacted if they run long enough, but typically the task is short and compaction is unnecessary. Capability is not the limit; design appropriateness is.
**Why not B:** Short-lived subagents typically do not benefit from compaction — they finish before compaction would matter. The pattern fits long-running contexts.
**Why not D:** Requiring compaction in short-lived subagents adds drift risk without benefit. Apply compaction where context pressure exists, not as a universal rule.

## Question 24 [D2]

A CI/CD Integration team's MCP server has a tool that takes 5-20 seconds to complete. The team wants to ensure the tool does not hold the protocol connection blocked while it executes, so other server activity (notifications, list calls) can interleave. Which implementation pattern is correct?

A. Move slow tools to a separate dedicated server so the main server stays fast and is never held up waiting on any long-running operation
B. Make every tool synchronous and run the server single-threaded — concurrency is the client's problem, since the client can simply space out its requests so the slow tool never blocks anything important
C. Spawn one process per tool call to maximize isolation, so each slow operation runs in its own process and never blocks the others
D. Implement the tool handler asynchronously so it yields control to the server's event loop while it waits on its slow operation, allowing notifications and other calls to flow concurrently

**Answer:** D
**Explanation:** MCP servers handle multiple concurrent requests over their transport, and tool handlers should be async-aware so they yield while awaiting slow operations. This keeps the protocol connection responsive to notifications, list calls, and other tool invocations while the slow tool runs. Blocking handlers serialize all server activity behind the slowest call.
**Why not A:** Splitting servers is one valid pattern but is far heavier than making handlers async, and it does not solve the general problem for any future slow tool. Async handlers are the right primary lever.
**Why not B:** Single-threaded blocking handlers cause head-of-line blocking on the protocol connection, freezing notifications and list calls behind any slow tool. The server is responsible for keeping its connection responsive.
**Why not C:** Per-call processes are overkill for the concurrency requirement and add significant startup cost. Async handlers achieve concurrency without process overhead.

## Question 25 [D4]

A Code Generation team uses tool-use schema. The schema has 8 fields. The model occasionally populates fewer than 8. Which interpretation is MOST consistent with required-field semantics?

A. Mark all eight fields as required to fix the omissions, since forcing every field to be present is the simplest way to guarantee none of them are ever left out
B. Tool-use ignores the required array, so marking fields as required has no effect and the omissions must be addressed by some other mechanism entirely
C. Lower temperature to fill the missing fields, since a more deterministic setting makes the model populate all eight fields rather than leaving some empty
D. If the model omits fields, those fields aren't in the required array; review the schema's required list and add the fields that must always be populated

**Answer:** D
**Explanation:** Tool use respects the required array, so omitted fields are almost certainly missing from it. Adding them to the required list makes the model populate them reliably, and enabling strict mode (strict: true) guarantees required-field conformance on every call. This is the canonical control for field completeness in tool-use schemas.
**Why not A:** Over-marking forces null/placeholder for fields that may legitimately be optional. Mark only what must be populated.
**Why not B:** Tool use does not ignore the required array; the model honors it, and with strict mode (strict: true) required-field conformance is guaranteed. The required list is exactly the mechanism for addressing these omissions.
**Why not C:** Temperature controls sampling randomness, not schema enforcement; a more deterministic setting does not compel the model to populate fields the schema treats as optional. Field completeness is controlled by the required array.

## Question 26 [D3]

A Customer Support Agent maintainer wants to compare Claude Code's tool use to MCP tool use conceptually for an internal doc. Which characterization is MOST accurate under CCA-F's architecture model?

A. Claude Code does not support MCP — only the Claude API integrates with MCP servers
B. Claude Code tools are model-controlled but MCP tools are application-controlled, so Claude cannot invoke MCP tools directly and must wait for the host application to call them on its behalf
C. Both are model-controlled tool calls — Claude Code uses built-in tools plus any configured MCP servers as additional tool sources
D. MCP tools replace Claude Code's built-in tools when configured — only one source is active at a time

**Answer:** C
**Explanation:** Claude Code's built-in tools and MCP-server-exposed tools are both invoked by the model under the same model-controlled tool-call pattern. MCP simply adds a standardized protocol for exposing extra tools; the loop treats them as additional callable surfaces.
**Why not A:** Claude Code supports MCP server configuration directly. Pretending it does not removes a core piece of the D3/D2 integration story.
**Why not B:** MCP tools are model-controlled; that is the defining property of the MCP tool primitive. Resources are application-controlled and prompts are user-controlled, so this option assigns the tool primitive the control model that actually belongs to resources.
**Why not D:** MCP-exposed tools augment, not replace, the built-in tool set. Claude Code can mix built-in and MCP tools in the same session.

## Question 27 [D4]

A Code Generation assistant must emit commit messages in a strict team format. The team is deciding between zero-shot with a precise format spec and a few-shot prompt with several examples. Commit messages are a common, well-defined task, and the assistant runs on every commit in a CI/CD pipeline where prompt tokens are billed at high volume. Which choice is BEST and why?

A. Use few-shot with several examples, because few-shot prompting always outperforms zero-shot for any structured output formatting requirement and concrete examples are strictly more reliable than a spec for enforcing a fixed format
B. Use zero-shot with a precise format specification, since well-defined common tasks can match few-shot performance while avoiding per-commit token bloat
C. Use one-shot as a middle ground, since one example is the standard fallback whenever few-shot would add too many tokens to the request
D. Use few-shot but cache the example block so the per-commit token cost of the examples is amortized across the pipeline's many runs

**Answer:** B
**Explanation:** Commit messages are a common, well-defined task where zero-shot with a clear spec can match few-shot. In a high-volume CI/CD path, dropping example tokens from every invocation is a meaningful cost win with no accuracy loss. Few-shot earns its tokens only for novel formats or edge-case-heavy tasks.
**Why not A:** Few-shot does not always win; for well-defined common tasks zero-shot with clear instructions matches it, and the examples add recurring token cost on every CI run for no benefit.
**Why not C:** One-shot is not a generic fallback; the zero/one/few choice is deliberate by task complexity, and a single example is unnecessary for a common, well-specified format.
**Why not D:** Caching can reduce repeated input cost but still adds unnecessary examples for a task zero-shot handles; it optimizes a choice that was avoidable, and the spec alone suffices.

## Question 28 [D1]

A Data Extraction team's workflow occasionally runs steps out of order when the agent decides to optimize. Which CCA-F principle MOST directly applies?

A. Just remove the step ordering from the workflow definition altogether
B. Agents should always optimize execution regardless of the declared ordering, since a capable agent reordering steps for efficiency will still reach the same correct outcome
C. Workflow step ordering should be treated as merely advisory guidance
D. Workflow step ordering must be enforced programmatically — agent optimization should not bypass declared ordering

**Answer:** D
**Explanation:** Workflow ordering is a structural property, not a model decision. CCA-F guidance favors programmatic ordering enforcement — the workflow engine enforces sequence; the agent operates within steps, not over them. Optimization within a step is fine; reordering steps is not.
**Why not A:** Removing ordering loses the workflow's structure. The fix is enforcement, not removal.
**Why not B:** Out-of-order execution violates the workflow contract. CCA-F guidance favors workflow ordering as enforced structure, not advisory.
**Why not C:** Advisory ordering produces the inconsistency the team is observing. CCA-F guidance favors enforced ordering.

## Question 29 [D4]

A Code Generation prompt says 'Generate idiomatic SQL queries.' Reviewers report inconsistent style — sometimes uppercased keywords, sometimes lowercased, sometimes inconsistent column quoting. Which change MOST directly stabilizes style?

A. Name the style guide explicitly — 'Follow SQL Style Guide by Simon Holywell: uppercase keywords, lowercase identifiers, double-quote case-sensitive names'
B. Raise temperature so style varies less from query to query, since a hotter sampler tends to smooth idiosyncratic keyword-casing choices into one consistent house style
C. Provide one example query and instruct the model to match its keyword casing and quoting
D. Use prefilling to start each response with 'SELECT ' so the style is anchored early

**Answer:** A
**Explanation:** Idiomatic SQL has many regional dialects. Naming a published style guide imports a full rule set in one phrase, plus the three specific rules anchor the most variable dimensions. The model can no longer interpret 'idiomatic' variably because the criterion has been named.
**Why not B:** Raising temperature increases variance, not decreases it; and even with lower temperature, an unstated style guide produces deterministic idiomatic-by-the-model's-choice queries.
**Why not C:** One example covers a narrow region of the style space. Novel query shapes can pattern-match to it in unexpected ways.
**Why not D:** Prefilling anchors the opening token but does not specify keyword case or quoting style across the rest of the query.

## Question 30 [D1]

Which of the following BEST describes the trade-off between sequential and parallel execution per CCA-F guidance?

A. Parallel execution is always strictly far better than sequential execution here, simply because it is faster across the board in every single case
B. Sequential is always better because it is simpler
C. Sequential is simpler and avoids partial failure; parallel is faster on independent subtasks but adds coordination and partial-failure handling
D. Sequential and parallel are interchangeable and the choice does not matter

**Answer:** C
**Explanation:** This is the canonical CCA-F trade-off. Sequential trades wall time for simplicity and the absence of partial failure; parallel trades simplicity for wall-time gains but requires explicit fan-in handling. The choice depends on dependency structure and operational priorities.
**Why not A:** Parallel is not faster on dependent subtasks and is no faster than sequential on a single-branch task. The trade-off is genuine; both classes have appropriate use cases.
**Why not B:** Sequential is not always better — on independent subtasks, it wastes wall time. The trade-off is real; CCA-F guidance favors matching execution pattern to dependency structure.
**Why not D:** The choice matters because wall time, partial-failure scenarios, and coordination overhead all differ. CCA-F guidance is explicit about the trade-off, not indifferent to it.

## Question 31 [D3]

A Customer Support Agent team's parent issues an Agent tool call but the subagent task description was vague. The subagent produces irrelevant output. Which BEST diagnoses the cause?

A. Vague handoff — the parent did not specify task, expected output, and constraints clearly enough for the subagent to focus
B. Subagents always produce irrelevant output because they are unreliable by design, so the team should expect wandering results and treat any useful output as a pleasant surprise
C. The subagent's own CLAUDE.md was malformed, corrupting its behavior, since each child loads a separate configuration file that can drift from the parent's project settings
D. The parent should have used a slash command instead of the Agent tool, since slash commands give far more reliable scoped output than delegating to a subagent ever does

**Answer:** A
**Explanation:** Subagent quality depends heavily on handoff specificity. A vague task description leaves the subagent to interpret broadly, producing wandering output. The fix is at the parent's handoff layer: precise task, expected output schema, and constraints.
**Why not B:** Subagents are not inherently unreliable. The cause is usually handoff quality.
**Why not C:** Subagents load the same CLAUDE.md as the parent's project. The likely root cause is handoff vagueness.
**Why not D:** Slash commands and subagents differ. The fix here is handoff specificity, not feature swap.

## Question 32 [D1]

A Code Generation orchestrator passes the entire codebase to every subagent. The team observes high cost and slow execution. Which CCA-F principle MOST directly applies?

A. Context isolation means passing no context whatsoever to the subagent
B. Subagents always need the entire codebase passed in to function correctly, since a subagent given only its scoped slice will lack the context to do its task well
C. Passing more context to a subagent is always the cheaper option
D. Context isolation should pass only the context each subagent needs — passing everything wastes tokens and slows execution

**Answer:** D
**Explanation:** Over-passing context is the inverse failure of under-passing. CCA-F guidance favors passing only what each subagent needs — minimal context for the scoped task. Passing the full codebase to every subagent treats handoff as a bulk dump rather than a tailored hand-off.
**Why not A:** No context is under-passing, which causes the subagent to fail. The right amount is what the scoped task needs — neither zero nor everything.
**Why not B:** Most subagent tasks need only a small subset of the codebase. CCA-F guidance favors tailored handoffs; the assumption that everything is needed is the over-passing failure mode.
**Why not C:** More context costs more tokens and slows inference. Cost grows with context size; over-passing is expensive precisely because of this.

## Question 33 [D1]

A Multi-Agent Research orchestrator dispatches a subagent that loops over web search, scrape, and synthesize tools. The team observes that the subagent occasionally returns results with no actual sources cited. What property of agentic systems does this MOST directly highlight?

A. Agentic systems require structured tool output schemas to function correctly
B. Agentic loops cannot reliably use web search tools because of latency
C. Agentic autonomy can satisfy a stop condition without satisfying the actual goal
D. Agentic systems require Claude's largest model to reliably follow every complex instruction given

**Answer:** C
**Explanation:** Autonomous agents can declare task completion when they have produced any answer, not necessarily a correct or complete one. Termination conditions that check only 'output produced' miss this failure mode; the fix is goal-constraint validation at loop exit.
**Why not A:** Structured schemas are a quality lever but do not address this specific failure. The subagent is returning results — the problem is that the loop terminated without enforcing the source-citation property.
**Why not B:** Tool latency is unrelated to citation completeness. Web search works in agents; the failure is in how the loop validates output, not in the tool itself.
**Why not D:** Model size is not the root cause. A larger model in the same loop will still terminate when it believes the task is done; the architectural fix is a validation gate that checks goal satisfaction, not a model swap.

## Question 34 [D1]

A Multi-Agent Research subagent receives a handoff with required fields, optional fields, and field types specified. Which CCA-F principle does this design MOST directly satisfy?

A. Structured handoff schema — explicit fields, types, and required-vs-optional designation make the inter-agent contract machine-enforceable
B. Maximum information density, on the theory that the more fields a handoff carries the better
C. A free-form prose handoff, chosen for its flexibility across tasks
D. An identical handoff format applied to all subagents regardless of their task, since one universal schema is easier to maintain than per-task contracts and avoids drift between them

**Answer:** A
**Explanation:** Required, optional, and typed fields make the handoff a structured schema. CCA-F guidance favors machine-enforceable contracts because prose handoffs produce inter-agent errors. Schema enforcement catches missing fields, type mismatches, and contract violations at the boundary.
**Why not B:** Density is not the principle — appropriate scope is. CCA-F guidance favors structured schemas with task-relevant fields, not maximum field count.
**Why not C:** Free-form prose is the opposite of structured schema. CCA-F guidance favors structured schemas; prose is the anti-pattern.
**Why not D:** Different subagents have different scopes and need different handoff schemas. CCA-F guidance favors task-specific schemas, not one-size-fits-all.

## Question 35 [D3]

A Code Generation team wants their SDK app to fall back to a different model if Claude is unavailable. Which characterization is MOST accurate?

A. Fallback is the application's job — the SDK targets Claude Code; the application implements model fallback logic around SDK calls
B. The SDK automatically falls back to other vendors on failure, so the application gets cross-provider resilience for free without writing any fallback logic
C. The SDK natively supports OpenAI as a fallback target, so the team can configure a secondary provider directly in the SDK and let it switch on failure
D. Cross-model fallback is not supported in any SDK at all, so if Claude is unavailable the application has no path to continue and must simply fail the request

**Answer:** A
**Explanation:** The SDK is the Claude Code surface; cross-model fallback is application-level logic. The application can call the SDK, catch failure, and fall back to another model or service. The SDK itself does not orchestrate cross-provider fallback.
**Why not B:** No cross-vendor auto-fallback. Application must implement.
**Why not C:** SDK targets Claude Code; cross-provider fallback is application logic.
**Why not D:** Application-implemented fallback is fully supported; the SDK is just one of multiple model surfaces an application can use.

## Question 36 [D3]

A CI/CD team wants a slash command that spawns a subagent to run tests in parallel while the main session continues. What does the command template need to include to enable this?

A. A Bash command in the template to launch a background process.
B. The command template should not include Agent tool calls — subagents can only be configured in CLAUDE.md.
C. Add a `parallel: true` flag to the command's frontmatter so Claude Code automatically forks the session and runs the command body in a background subagent
D. Instruct Claude to use the Agent tool to spawn a subagent for test execution with the needed context — enabling parallel operation while the main session continues

**Answer:** D
**Explanation:** Slash command templates guide Claude's reasoning and tool use. A template that instructs Claude to 'Use the Agent tool to spawn a subagent with the following task: run the test suite in [directory] and report results' will cause Claude to issue an Agent tool call, creating a parallel subagent for test execution. The main session can continue while the subagent handles testing independently.
**Why not A:** Launching background processes via Bash does not create a Claude subagent — it runs shell commands in the background without Claude's reasoning capabilities. Spawning a Claude subagent requires the Agent tool call, not a Bash background process.
**Why not B:** Subagent delegation via the Agent tool can be initiated from any context where Claude is reasoning — including during execution of a slash command template. CLAUDE.md configures Claude Code's behavior but does not restrict where subagent calls can originate.
**Why not C:** Wrong: there is no `parallel: true` frontmatter flag that forks the session. Parallel subagent execution is driven by the prompt — the command body instructs Claude to use the Agent tool to delegate the task — not by a configuration flag.

## Question 37 [D4]

A Multi-Agent Research subagent prompt says 'Fetch the most relevant 5 sources.' Sources sometimes overlap heavily, sometimes diverge wildly. Which change BEST improves source diversity?

A. Increase the source count to 10 so diversity emerges naturally, since a larger candidate set spans more distinct viewpoints and the broader sweep crowds out the heavy overlap
B. Require sources to cover distinct viewpoints — name the diversity dimensions (date range, authorship, methodology) and forbid duplicates within each dimension
C. Raise temperature so the source selection from the candidate pool is more varied
D. Sort the sources alphabetically and take the first five for reproducibility

**Answer:** B
**Explanation:** 'Most relevant' optimizes for similarity, which naturally produces overlap. Specifying diversity dimensions and forbidding duplicates within each turns the selection criterion from a single-axis ranking into a multi-axis cover, eliminating both the overlap and the wild-divergence failure modes.
**Why not A:** More sources without a diversity rule produce more overlap, not better cover. The selection criterion is the lever.
**Why not C:** Temperature affects token sampling, not source selection from a candidate pool. The variance is in the rule, not the sampling.
**Why not D:** Alphabetic order is unrelated to diversity. The same overlap pattern emerges.

## Question 38 [D1]

A Multi-Agent Research orchestrator stores session state in a single shared database that all subagents read and write. The team observes inconsistencies. Which CCA-F-consistent design MOST directly addresses this?

A. Have the subagents lock the database during every single write
B. Concentrate state ownership at the orchestrator — subagents read filtered state and return updates, the orchestrator commits
C. Accept the inconsistencies as inherent to multi-agent systems, since concurrent subagents writing to shared state will always race and the conflicts cannot be prevented
D. Replicate the entire database separately for every subagent

**Answer:** B
**Explanation:** Distributed writes to a single database produce inconsistencies. CCA-F guidance places state ownership at the orchestrator — subagents read filtered state and return updates as part of their handoff response, and the orchestrator commits with concurrency control.
**Why not A:** Database-level locks across subagents add latency and may produce deadlocks. CCA-F guidance favors structural change — orchestrator-owned commits — over fine-grained locking.
**Why not C:** Inconsistencies are a design issue, not inherent. CCA-F guidance favors centralized ownership to prevent them.
**Why not D:** Replication produces divergent state across subagents — exactly the opposite of consistency. CCA-F guidance favors single source of truth at the orchestrator.

## Question 39 [D4]

A Customer Support Agent prompt asks Claude to translate to Spanish when the user writes in Spanish. The model sometimes responds in English to Spanish messages with English code-switching. Which change MOST directly enforces language matching?

A. Add 'always be linguistically appropriate' so the model self-corrects its language
B. Run a language-detection step in a separate API call first
C. Lower temperature to 0 so the language choice becomes deterministic, since a stable sampler reliably matches the user's language without code-switching
D. Rule: detect the dominant language of the user's most recent message and respond entirely in that language unless the user explicitly requests another

**Answer:** D
**Explanation:** Code-switching messages confuse simple 'match the user's language' rules. Specifying dominant-language detection plus the entirely-in-that-language constraint with an explicit override mechanism gives the model an unambiguous decision rule for mixed-language inputs.
**Why not A:** Adverb without an actionable rule.
**Why not B:** An external detection step adds latency and is not necessary — the model can detect dominant language inline given the explicit rule.
**Why not C:** Determinism on an unstated rule still produces unstated rule variance. The fix is the rule.

## Question 40 [D3]

A CI/CD Integration team adds Claude Code to a GitHub Actions workflow to scan diffs for security issues. The job must run unattended, fail the build when high-severity findings exist, emit machine-readable results, and never hang on confirmation prompts. Their first attempt invoked claude-code without the -p flag and the job stalled. The architect must specify the correct invocation and result contract. Which design is MOST correct?

A. Use -p but always exit zero and post findings as a comment, letting reviewers decide whether to merge
B. Run claude-code interactively inside the GitHub Actions runner and have a background watcher process detect and answer each confirmation prompt automatically as it appears
C. Use -p but parse free-form prose output with regular expressions to decide whether to fail the build
D. Invoke with the -p flag for non-interactive execution, request structured JSON findings, and exit non-zero from the step when high-severity issues are present

**Answer:** D
**Explanation:** The -p flag runs Claude Code non-interactively so the job never waits on confirmation prompts (D3), the required fix for the stall. Requesting structured JSON gives the downstream step a machine-readable contract (D4 structured output), and exiting the step non-zero on high-severity findings fails the build deterministically. Each requirement maps cleanly to the print-mode automation pattern.
**Why not A:** Always exiting zero means high-severity findings never fail the build, violating the requirement. Human-gated merge is not the deterministic build failure the team specified.
**Why not B:** Interactive mode in CI is exactly what caused the hang; scripting prompt answers is fragile and unsupported. The -p flag is the designed mechanism for non-interactive automation.
**Why not C:** Free-form prose is brittle to parse and unreliable for a build-gating decision. Requesting structured JSON output gives a stable contract the downstream step can consume deterministically.

## Question 41 [D5]

A code generation agent's prompt caching metrics show 95% cache hit rate but overall API costs are only 15% lower than before caching was enabled. What could explain this gap?

A. 95% cache hit rate with only 15% cost savings indicates the cached prefix is a small fraction of total input tokens — most input tokens are dynamic and not cached
B. 95% cache hit rate means 5% are cache misses, each incurring overhead roughly 10 times the normal uncached cost — the miss-penalty offsets all per-token savings from successful cache reads
C. The caching TTL has been set too short — cache entries expire before the second hit, making every request effectively a cache write
D. Output tokens have increased since caching was enabled — the model generates longer responses when the system prompt is cached

**Answer:** A
**Explanation:** Cost savings from prompt caching = (cached_token_count / total_token_count) × cache_savings_rate. If the cached prefix is 500 tokens but the dynamic user code context is 4,500 tokens per request, only 10% of input tokens benefit from caching. At 90% savings on cached tokens: 10% × 90% = 9% total input cost reduction. If input tokens are 60% of total cost (40% output), overall savings = 9% × 60% = 5.4% — far less than the hit rate suggests. High hit rate on a small prefix produces modest savings.
**Why not B:** Cache misses incur a cache write premium (~25% above base price for the cached tokens), not a 10x penalty. At 5% cache misses, the write premium is: 5% × 1.25x × cached_token_cost — a minor overhead, not a cost cancellation. A 95% hit rate with a 25% write premium nets enormous savings; no realistic cache miss penalty could cancel 95% hit savings.
**Why not C:** If every request were a cache write (0% hit rate), the metric would show 0% hit rate, not 95%. The 95% hit rate is measured data — the cache is working. The gap between high hit rate and modest savings is a proportion problem (small cacheable prefix vs. large dynamic content), not a TTL problem.
**Why not D:** Prompt caching has no effect on output token generation behavior — the model generates responses based on the input content, not based on whether the input was cached or processed fresh. Output token counts are determined by the task and model parameters (max_tokens, stop sequences), not by cache status.

## Question 42 [D2]

A Multi-Agent Research team's MCP server is deployed in a Kubernetes cluster behind an Ingress. Engineers find that connections drop after exactly 60 seconds of idle time. Which is the MOST likely cause?

A. The server's tool execution time happens to be exactly 60 seconds, so the connection drops precisely when each long-running tool call finishes rather than as a result of any idle period on the connection
B. The MCP protocol itself enforces a strict 60-second connection limit, so any connection is closed automatically once it reaches one minute regardless of what the surrounding infrastructure is configured to do, which is why the drops land on such a precise and consistent boundary every single time the connection sits idle
C. The Ingress (or upstream load balancer) has an idle-connection timeout that closes connections after 60 seconds of inactivity — configure the timeout to be longer than expected idle periods, or have the client emit keepalive traffic to keep the connection active
D. The Kubernetes pods backing the server are being restarted every 60 seconds on a fixed schedule, so each connection is severed when the pod it is bound to cycles out and a fresh replacement pod takes over

**Answer:** C
**Explanation:** Kubernetes Ingresses (and load balancers in general) have idle-connection timeouts that close connections after a configurable period of inactivity. For long-lived MCP connections (especially StreamableHTTP with notifications), the Ingress timeout must be configured longer than expected idle gaps, or the client must emit keepalive traffic. This is a common operational issue with hosted MCP deployments.
**Why not A:** Tool execution time doesn't cause idle-connection drops. Idle-timeouts are about inactivity, not active call duration.
**Why not B:** MCP doesn't enforce a 60-second limit. The cause is infrastructure-layer timeout, not protocol-level.
**Why not D:** Pods don't restart on a 60-second schedule by default. The Ingress idle timeout is the standard cause for this symptom.

## Question 43 [D5]

A Developer Productivity agent helps a team refactor a large codebase across many sessions. Each new session starts without memory of prior decisions — which modules were already refactored, which patterns were rejected, and which open questions remain. The team wants continuity without re-explaining context every time. What is the recommended approach?

A. Embed all prior decisions in the system prompt so the model sees them at every session start.
B. Rely on the model's in-weights training to recall prior session decisions — Claude retains project context between sessions through parametric memory, with no external file
C. Maintain a NOTES.md or CONTEXT.md scratchpad that is loaded at session start and updated at session end with new decisions and open questions.
D. Store decisions in CLAUDE.md so Claude automatically inherits them as project rules.

**Answer:** C
**Explanation:** The scratchpad pattern solves cross-session statefulness. Loading at start injects prior context; writing at end captures new decisions. The file evolves with the project, not with model weights.
**Why not A:** System prompts carry static rules. Evolving state like refactoring decisions and open questions belongs in a mutable scratchpad file, not baked into the prompt, which is harder to update incrementally.
**Why not B:** Claude has no persistent memory across sessions from training. Each new session is stateless. External files are required for cross-session knowledge persistence.
**Why not D:** CLAUDE.md is for stable rules and instructions, not evolving state. Mixing frequently updated decisions into CLAUDE.md blurs the distinction between rules and mutable context, making both harder to maintain.

## Question 44 [D4]

A Data Extraction prompt instructs Claude to 'extract dates in ISO format.' Some outputs use 2026-06-15, some 2026/06/15, some June 15 2026. Which change BEST stabilizes the format?

A. Use JSON mode so the date is emitted as a clean string value
B. Provide three examples of ISO dates and trust the model to generalize, since worked instances implicitly teach the exact pattern for every novel date
C. Lower temperature so the date-format choice stabilizes across extractions
D. Specify 'YYYY-MM-DD with hyphens, zero-padded; reject any other format' and provide one canonical example

**Answer:** D
**Explanation:** 'ISO format' is ambiguous because ISO 8601 admits several variants. Specifying the exact pattern (YYYY-MM-DD, hyphens, zero-padding) plus a canonical example removes interpretation latitude and gives the model an unambiguous target.
**Why not A:** JSON mode constrains structure, not date format within the string field.
**Why not B:** Examples without a stated rule produce pattern-match, not constraint. The model can still pick a variant if a novel date shape arrives.
**Why not C:** Format choice is a rule decision, not a sampling decision. Determinism on a vague rule produces deterministic ambiguity.

## Question 45 [D3]

A Developer Productivity user asks Claude Code to summarize the test suite without modifying anything. Which tool sequence MOST closely matches the read-only intent?

A. Run a Bash find command to delete cached test artifacts before summarizing
B. Edit each file with an empty replacement to confirm presence then summarize
C. Write a temporary inventory file and read it back to produce the summary
D. Read each test file individually and then return the summary to the user

**Answer:** D
**Explanation:** Read is the explicit read-only tool. Using only Read keeps the action observably non-mutating, gives Claude precise content access, and matches the user's stated read-only intent.
**Why not A:** Deleting artifacts is destructive and unrelated to the summarization task. The user requested no modifications, so any deletion violates the constraint regardless of test-suite hygiene benefits.
**Why not B:** Edit is a mutation tool even with a no-op replacement and triggers write semantics. Misusing Edit to probe files violates the read-only intent and may trip PreToolUse hooks.
**Why not C:** Write mutates the working directory by creating a new file. The user explicitly requested no modifications; introducing a scratch file violates that constraint when Read alone is sufficient.

## Question 46 [D3]

A Developer Productivity team wants CLAUDE.md to encourage Claude to ask clarifying questions before destructive operations. Which phrasing is MOST effective?

A. Aspirational phrasing such as always be cautious with sensitive operations, trusting the model to infer when an operation is risky enough to warrant pausing
B. Explicit trigger plus action — 'Before deleting files or dropping tables, ask the user to confirm the scope.'
C. Generic phrasing such as when in doubt, ask the user, leaving it to the model to judge which situations actually warrant a confirmation
D. Inverted — 'Never ask the user anything during a session.'

**Answer:** B
**Explanation:** Explicit triggers (deleting files, dropping tables) paired with the desired action (ask for confirmation) give Claude a clear if-then. Vague encouragements like 'be careful' are weaker.
**Why not A:** 'Cautious' is subjective. Without explicit triggers and actions, the rule fails to shape behavior reliably.
**Why not C:** Doubt is subjective. Explicit triggers anchor the rule to observable events.
**Why not D:** This is the opposite of the requirement. Explicit if-then phrasing is the right tool.

## Question 47 [D5]

A Data Extraction agent queries a database for records matching a filter. The query succeeds but returns 0 rows. The agent reports 'no records found.' Which is the MOST important reliability check before accepting that conclusion?

A. Verify the agent had access to the table and the filter executed correctly
B. Re-run the query at a different time of day
C. Trust the database driver to report any access issue, since a silent driver implies the table was genuinely empty
D. Cache the empty result so the next query is faster

**Answer:** A
**Explanation:** An empty result and an access failure can look identical — both produce 'no records.' The reliability discipline is to confirm the query actually ran against the intended scope with permission, distinguishing a true empty result from a permission-denied query that silently returned empty. CCA-F treats this distinction as a primary reliability gate.
**Why not B:** Time-of-day variation does not address the empty-vs-access-failure distinction. The agent might run the query 24 hours later with the same access issue and same empty result.
**Why not C:** Many access patterns silently return empty rather than erroring — RBAC may scope the visible rows to none, views may filter, or the connection may target a wrong schema. The driver is not always reliable for this distinction.
**Why not D:** Caching an empty result that may actually be an access failure compounds the problem — future queries return the wrong empty conclusion from cache.

## Question 48 [D4]

A Code Generation team's system prompt has 8 instructions all phrased imperatively: 'Use type hints. Avoid global state. Test all functions.' New rules are appended at the bottom over time. Which change BEST improves long-term maintainability?

A. Convert the imperatives to declaratives so the rules read more naturally to editors
B. Number the rules so each can be referenced by a stable index when editing
C. Group related rules under XML-tagged sections — <type_safety>, <state_management>, <testing> — and assign each new rule to a section
D. Lower temperature so the rules are applied more consistently, since a deterministic sampler enforces all eight imperatives uniformly enough to feel maintained

**Answer:** C
**Explanation:** Flat imperative lists scale poorly because related rules drift apart over edit cycles. XML sectioning by concern gives each new rule a natural home, makes related rules discoverable together, and surfaces duplications when they appear. Maintenance becomes proportional to section count, not rule count.
**Why not A:** Phrasing change does not address organization. Maintenance pain comes from structure, not voice.
**Why not B:** Numbering creates fragile cross-references — adding a rule shifts all subsequent numbers. Tagging by concern is order-independent.
**Why not D:** Parameters do not affect prompt organization.

## Question 49 [D2]

A Multi-Agent Research team uses Claude's built-in web_search and a custom MCP-exposed academic-database search. Both descriptions are well-written and disambiguating. The team adds prompt-injection-resistant phrasing to the system prompt asking the model to prefer the academic-database for scholarly queries. Why might this still fail to enforce the routing?

A. System-prompt rules are always ignored by Claude, so encoding the routing preference there can never have any effect on which search tool the model actually selects at decision time
B. System-prompt routing rules are instructions the model usually follows but can be overridden by adversarial inputs or context drift — for high-impact routing decisions, the tool descriptions themselves are more durable because the comparison happens at every routing decision
C. System-prompt rules only work for tools and not for distinguishing built-in tools from MCP-exposed ones, because the model routes the two sources through different paths a single instruction cannot span
D. System-prompt routing rules are forbidden by Anthropic's terms of service when they steer the model away from a built-in tool toward a third-party one, so the rule would have to be removed for compliance anyway, and any preference expressed in the system prompt that demotes a first-party tool in favor of a custom MCP tool is treated as an unsupported configuration

**Answer:** B
**Explanation:** System prompts are instructions, not enforcement. They guide the model under normal conditions but can be overridden by prompt injection, context drift, or contradictory user requests. The routing decision happens at description comparison; system-prompt rules are a softer layer above it. Description-level routing is more durable because it lives in the comparison the model actually performs.
**Why not A:** Claude does follow system-prompt rules under normal conditions. The concern is durability under adversarial or drifted contexts, not total ignorance.
**Why not C:** System-prompt rules apply uniformly across tool sources. The durability concern is general, not specific to built-in vs. MCP.
**Why not D:** No such prohibition exists. The concern is durability and effectiveness, not a TOS violation.

## Question 50 [D1]

A Customer Support Agent receives a vague request: 'fix my account.' The agent must decide whether to ask clarifying questions or to interpret and proceed. Which factor MOST strongly favors asking?

A. The agent is configured with a polite persona
B. The user has simply not gone to the trouble of specifying what exactly the word 'fix' is supposed to mean here
C. The agent has access to multiple tools
D. The agent's actions are irreversible or high-impact, making misinterpretation costly

**Answer:** D
**Explanation:** Irreversibility and high impact tip the balance toward clarification. CCA-F guidance favors asking when misinterpretation is costly; for reversible low-impact actions, interpreting-and-proceeding may be fine. Impact drives the design choice.
**Why not A:** Persona affects tone, not the decision to ask. A polite agent still must judge when clarification is warranted versus interpretation; that judgment is impact-driven.
**Why not B:** Vagueness alone is not sufficient — many vague requests have a reasonable default interpretation. The discriminator is whether misinterpretation is costly enough to justify the clarification friction.
**Why not C:** Tool count is unrelated to ambiguity handling. Whether to ask depends on impact of misinterpretation, not on toolset breadth.

## Question 51 [D1]

A Customer Support Agent uses a workflow that classifies the user's intent, retrieves docs, and generates a reply. The team wants to upgrade to handle multi-turn back-and-forth where Claude can ask clarifying questions and call account tools as needed. Which class change BEST describes the upgrade?

A. Workflow to agentic, because the new behavior requires runtime decisions about tool calls and clarifications
B. Workflow to conversational, because the clarifying questions are themselves nothing more than user-turn interactions
C. Workflow to multi-agent, because clarification is a separate concern from tool use
D. No change, because the existing workflow can handle the new behavior with more branches

**Answer:** A
**Explanation:** Adding runtime decisions about when to ask clarifying questions and when to call account tools moves the system out of the workflow class. The model now decides the next action at each turn — the defining property of an agentic loop.
**Why not B:** Conversational systems do not call account tools or take action — they only respond. Adding tools and runtime decisions takes the system into the agentic class, not back into conversational.
**Why not C:** Clarification and tool use can both run in a single agent. Splitting them across agents adds coordination overhead without unlocking new capability — the upgrade is to agentic, not to multi-agent.
**Why not D:** Multi-turn back-and-forth with runtime decisions about tool calls cannot be expressed as fixed branches without combinatorial explosion. The new requirements need runtime decision-making, which workflows cannot provide by definition.

## Question 52 [D3]

A Data Extraction team uses Claude Code to read large vendor invoices and write normalized records. Sessions degrade after an hour: Claude forgets earlier extraction rules and re-reads processed files. The lead suspects repeated Read results are crowding out the standing rules. Given how the Claude Code execution model accumulates tool output in the session context window, which redesign MOST directly addresses the root cause?

A. Lower the temperature on the underlying model calls so extraction becomes more deterministic and Claude stops re-reading files, since lower sampling randomness makes the model recall earlier rules more reliably and avoid redundant tool calls as the session grows
B. Move the extraction rules into the user-level CLAUDE.md so they are reloaded automatically and cannot be forgotten mid-session
C. Delegate the verbose per-file reading to subagents that return only the extracted fields, keeping bulky Read output out of the parent session context
D. Increase the size of each Read call so fewer total calls are needed, reducing the number of tool results stored in context

**Answer:** C
**Explanation:** In Claude Code's execution model, every Read result accumulates in the session context window and can push out standing rules. Subagent delegation isolates verbose discovery (D5) so the parent receives only compact results, preserving the rules and session continuity. This pairs the tool execution model (D3) with context-efficiency design (D5).
**Why not A:** Temperature controls sampling randomness, not context window occupancy. The forgetting is caused by accumulated tool output displacing earlier content, which sampling parameters do not affect.
**Why not B:** CLAUDE.md is loaded once at session start and itself counts against the context window. It is not re-injected as the window fills, so it does not prevent rules from being compacted out by tool output.
**Why not D:** Larger reads put MORE bytes of tool output into the context window per call, accelerating the displacement of earlier rules rather than relieving it.

## Question 53 [D5]

A CI/CD Integration job uses Claude to summarize nightly build logs. The 500MB log is chunked into 250 chunks and processed serially, with each call's output passed forward as context. By chunk 50, summaries become generic. Which factor BEST explains it?

A. Build logs at chunk 50 contain no useful information
B. The model's training data does not include build logs, so by chunk 50 it is generating from priors rather than the specific log content in context
C. Accumulated prior summaries dominate context and dilute the new chunk's signal
D. JSON mode is rate-limiting the output, so the structured-format overhead throttles each call and the summaries thin out as the throttle tightens

**Answer:** C
**Explanation:** Carrying every prior summary forward grows the running context with each chunk, eventually overwhelming the current chunk's signal. The model attends increasingly to prior summaries rather than the new log content, producing generic, recap-style output rather than fresh, log-specific findings.
**Why not A:** The stem describes a systematic decay pattern starting at chunk 50, not a content gap. Real logs of that size contain useful information throughout.
**Why not B:** Training-data coverage does not explain a quality decay that appears specifically after chunk 50. If the model could summarize early chunks well, the architecture, not the training corpus, is the cause of the degradation.
**Why not D:** JSON mode constrains output shape, not summary specificity. The stem does not mention JSON mode and rate limits would produce errors, not generic content.

## Question 54 [D5]

A Code Generation team's agent emits confidence scores from 0-1. The team finds confidence 0.9 and 0.5 both produce wrong code at similar rates. Which is the MOST important step before relying on these scores?

A. Calibrate the confidence scores against a labeled validation set so 0.9 maps to actual 90% accuracy
B. Trust the raw confidence scores as-is, since a model's self-reported certainty is the best available accuracy signal
C. Drop confidence scoring and instead gate auto-merge purely on whether the generated code compiles cleanly
D. Train the model further on edge cases until its confidence becomes reliable

**Answer:** A
**Explanation:** Raw model confidence is uncalibrated — the model's self-rated certainty may not match true outcome probability. Calibration against a labeled validation set establishes the mapping (e.g., model-reported 0.9 maps to actual 70% accuracy). Without calibration, the score is a noisy signal; with calibration, it becomes operationally useful.
**Why not B:** Trusting uncalibrated confidence is exactly the failure mode the team observed. Trust requires calibration first.
**Why not C:** Calibration is the fix; dropping the signal removes a useful routing dimension.
**Why not D:** Further training is heavy and does not directly address calibration. A calibration step uses the existing model with a measured mapping.

## Question 55 [D3]

A CI/CD Integration job runs Claude Code with -p in non-interactive mode. Which session-continuity property BEST describes that run?

A. -p runs share session state with any active interactive Claude Code session on the same machine
B. -p maintains a rolling session across invocations as long as the same working directory is reused, so successive pipeline runs implicitly inherit the prior run's accumulated context
C. -p disables CLAUDE.md loading entirely to keep CI runs lean, so non-interactive pipeline runs deliberately start without any project configuration
D. Each -p invocation is a fresh session — no state from prior -p runs carries over unless reloaded from files

**Answer:** D
**Explanation:** Non-interactive -p runs are bounded by the single invocation. They start fresh, do their work, and exit. Anything that needs to persist between runs has to ride in CLAUDE.md or files the next run loads explicitly.
**Why not A:** Sessions are not shared across processes or modalities. An interactive session and a -p run are independent contexts.
**Why not B:** There is no implicit cross-invocation session for -p. Each call is its own context. Working directory affects file resolution, not session continuity.
**Why not C:** -p does not disable CLAUDE.md. The configuration hierarchy still applies; -p only controls interactivity.

## Question 56 [D3]

A Developer Productivity user asks Claude Code to 'just answer the question, don't touch any files.' Claude still issues a single Read. Which BEST characterizes the situation?

A. Read is forbidden under a do-not-touch constraint and Claude should have answered from memory without it, because honoring the user's instruction means avoiding every tool call rather than only the mutating ones
B. Claude violated the constraint — any tool call counts as touching files
C. Read is non-mutating and does not violate the do-not-touch constraint — file content is unchanged
D. Read mutates the file's access time metadata so it counts as a modification

**Answer:** C
**Explanation:** Read does not modify files; it loads content into context. 'Don't touch any files' typically refers to mutation, which Read does not cause. The constraint is upheld even when Claude grounds the answer by reading.
**Why not A:** Read is not forbidden by a do-not-touch constraint focused on mutation. Forbidding all tools is a different, stricter request the user did not make.
**Why not B:** Read is read-only by definition. Treating any tool call as a violation conflates 'tool use' with 'mutation' and misrepresents Claude Code's tool model.
**Why not D:** atime updates are filesystem metadata that users almost never mean when they say 'touch any files.' Treating that as a violation of the user's intent is hyper-literal and misreads the constraint.

## Question 57 [D3]

A Code Generation team has a 12,000-word CLAUDE.md that documents every coding standard. They notice Claude Code sometimes ignores newer rules late in long sessions. Which BEST diagnoses the cause?

A. Rules are applied strictly in order of appearance, and later rules require Claude to re-read the entire CLAUDE.md on each turn, so newer rules at the bottom get skipped under time pressure
B. Verbose CLAUDE.md consumes session context — long sessions plus a heavy CLAUDE.md crowd out working memory
C. CLAUDE.md content is parsed only when /init is run; standing rules expire after the first hour
D. CLAUDE.md files over 10,000 words are silently truncated and most rules are dropped

**Answer:** B
**Explanation:** CLAUDE.md content counts against the context window. A 12,000-word file leaves less room for code, tool results, and reasoning, and as sessions extend the combined pressure causes earlier or middle content (including rules) to be deprioritized.
**Why not A:** Claude does not re-read CLAUDE.md every turn — it is loaded once at session start. The problem is total context budget, not a per-turn re-read step.
**Why not C:** CLAUDE.md is reloaded at session start, not only at /init time, and there is no built-in expiration. The cause is context window economics.
**Why not D:** There is no documented hard truncation at 10,000 words. The issue is pressure on a finite context window, not a fixed truncation threshold.

## Question 58 [D4]

A Code Generation team wants Claude to refactor a function while preserving public behavior. The prompt says 'Refactor for readability while keeping behavior the same.' Some refactors silently change function signatures. Which change MOST directly prevents signature changes?

A. Lower temperature to 0 so refactors become more conservative
B. Explicitly forbid signature changes — 'Function name, parameter names, parameter order, and return type must remain identical'
C. Run the refactor through a linter after Claude finishes
D. Use prefilling to start with 'def ' and the original function name, since anchoring the opening tokens locks the signature to match the original

**Answer:** B
**Explanation:** 'Keeping behavior the same' is interpretable; the model can treat signature changes as behavior-preserving if semantics are unchanged. Enumerating the four immutable signature attributes turns the rule into an explicit checklist the model can verify before responding.
**Why not A:** Conservativeness is not the same as signature preservation. The model can deterministically change signatures with low temperature.
**Why not C:** A linter does not check signature equivalence with the original; only the prompt rule does. Linting is downstream of the issue.
**Why not D:** Prefilling anchors the function name but not parameter order, names, or return type. Partial constraint, partial fix.

## Question 59 [D4]

A Developer Productivity assistant generates README files. The prompt says 'Write a good README.' Some READMEs include installation but skip usage; others include badges but no quickstart. Which change MOST efficiently fixes the gaps?

A. Require a fixed section order — Overview, Quickstart, Installation, Usage, Configuration, Contributing, License — each labeled and present
B. Show Claude five high-quality READMEs from popular projects, since strong exemplars implicitly teach the full required section set to reproduce
C. Lower temperature so the README structure stabilizes between runs
D. Add 'be thorough and complete' to the prompt so no section is skipped

**Answer:** A
**Explanation:** 'Good README' is a label without a structure. Specifying the required section list plus the order forces every output to include every section, eliminating the omission gaps and producing readmes that match team expectations regardless of which the model would have prioritized.
**Why not B:** Five examples may vary in their own structures. Without a stated section list, the model still picks the variant it favors.
**Why not C:** Temperature does not introduce a section list. Determinism produces deterministically omitted sections.
**Why not D:** Thoroughness adjective produces no required section set.

## Question 60 [D3]

A Developer Productivity team's hook is supposed to validate test files after Edits but mistakenly validates non-test files too. Which fix is MOST appropriate?

A. Disable the hook for non-test work through a CLAUDE.md instruction, since a standing rule can tell Claude Code to skip the validation on non-test files
B. Register the hook only for the specific tool calls that touch test files, since hook registration lets you scope by file path so non-test files are never seen
C. Inspect the file path inside the hook and skip non-test files — narrow the hook's effective scope by pattern matching
D. Add a SKILL.md that disables the hook in certain scopes, since skills can be configured to suppress a hook whenever the work falls outside the test directory

**Answer:** C
**Explanation:** Hooks see tool-call details. Filtering by file path inside the hook scopes its effect to the intended files. This is the documented way to narrow per-call hook applicability without registering separate hooks per pattern.
**Why not A:** CLAUDE.md does not toggle hooks. In-hook filtering is the right mechanism.
**Why not B:** Hook registration is per lifecycle event, not per file path. Filtering happens inside the hook script.
**Why not D:** Skills do not control hook activation. Filtering inside the hook script is the mechanism.
