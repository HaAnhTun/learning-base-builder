# 1C Quiz

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · D1: Agentic Architecture - Multi-Agent Orchestration · 15 questions · pass mark 70% · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies

## Question 1

A multi-agent system has an orchestrator that delegates summarization tasks to three subagents. One subagent fails to return a result. According to the lesson, where should the logic that decides what to do next — retry, substitute, or escalate — live, and why?

A. In the orchestrator — subagents report failures and the orchestrator decides how to respond, keeping behavior predictable and auditable.
B. In each subagent, so the failing agent can self-correct and retry its own task without consuming orchestrator resources on transient errors.
C. In a dedicated error-handling subagent the orchestrator spawns on failure, keeping error logic modular and reusable across different task types.
D. Distributed across all agents using a shared error registry, so any agent can read current failure state and adjust its own behavior without waiting for the orchestrator.

**Answer:** A
**Explanation:** The deck explicitly states that error handling logic belongs in the orchestrator, not in the subagents. Subagents report failures; the orchestrator decides how to respond. This separation keeps system behavior predictable and auditable. The three response options are retry (reissue with same or adjusted instructions), substitute (route to an alternate agent), or escalate (surface to a human).

## Question 2

A team is evaluating the hub-and-spoke topology for their orchestrator-subagent architecture. One engineer raises a concern about what happens if the orchestrator becomes overloaded during a peak traffic period. According to the lesson, what architectural tradeoff does this concern reflect?

A. Hub-and-spoke eliminates partial failure risk by routing all subagent results to one collection point, removing the bottleneck concern the engineer raised.
B. Hub-and-spoke requires subagents to coordinate directly with each other during peak load to reduce orchestrator traffic, which is why the topology introduces peer-to-peer communication overhead.
C. Hub-and-spoke distributes load evenly across subagents, so orchestrator overload indicates a subagent routing misconfiguration rather than a structural limitation.
D. Hub-and-spoke centralizes coordination for auditability but creates a single point of failure and bottleneck if the orchestrator is overloaded.

**Answer:** D
**Explanation:** The deck teaches that hub-and-spoke architecture centralizes all task assignments, result collection, and routing decisions at the orchestrator (hub), with subagents (spokes) that do not communicate directly. This centralization makes the system easy to reason about and audit, but the explicit exam-tested tradeoff is that it creates a single point of failure and a potential bottleneck. If the orchestrator fails or becomes overloaded, the entire system stalls.

## Question 3

An orchestrator spawns a subagent to validate a document. The subagent performs well in isolation, but in production it occasionally produces errors that are hard to trace. Upon investigation, the team discovers the subagent is silently using values from the orchestrator's system prompt that were never explicitly passed to it. According to the lesson, what principle does this violate, and what should the correct design look like?

A. Least-privilege isolation: the subagent should only access specific data fields it needs, and system prompt access must be removed from its permission configuration.
B. Result aggregation isolation: the subagent is writing outputs to the orchestrator's shared state before validation, bypassing the collect-validate-synthesize sequence.
C. Context isolation: subagents start with a blank context window and must receive everything they need via explicit passing from the orchestrator at task assignment time.
D. Authority boundary isolation: the subagent is accessing tool permissions it was not explicitly granted, which requires removing excess tool access from its configuration.

**Answer:** C
**Explanation:** The deck defines context isolation as the principle that a subagent starts with a blank context window when spawned. It does not inherit the orchestrator's conversation history, system prompt, or any other context unless the orchestrator explicitly copies that information into the subagent's instructions. If a subagent silently relies on inherited state, it cannot be reliably tested in isolation and its behavior becomes unpredictable when that state changes.

## Question 4

An orchestrator spawns a summarization subagent with instructions that read: 'Summarize the attached document thoroughly.' During aggregation the orchestrator finds that some runs return bullet lists, others return flowing prose, and some return a single sentence. All are technically valid summaries but incompatible with the downstream synthesis step that expects a structured JSON object. What subagent design principle does this violate?

A. The orchestrator is violating context isolation by passing the same document to multiple subagent instances, causing them to return non-deterministic formats when competing for the shared resource.
B. The orchestrator's aggregation step lacks a schema validator, and adding one at the fan-in point would normalize inconsistent formats before synthesis without changing subagent instructions.
C. The subagent has overly broad authority because 'summarize' permits multiple output modes, and the orchestrator should restrict the permitted action to one specific output type.
D. The instructions are missing a precise output format specification — one of three required elements — causing inconsistent outputs that break the orchestrator's aggregation step.

**Answer:** D
**Explanation:** The deck teaches that effective subagent instructions must specify the output format precisely so that aggregation is reliable. Vague instructions produce inconsistent outputs that break aggregation. The instruction lacks a precise output format specification, which is one of three required elements the deck names for every subagent instruction set alongside narrow scope and explicit success criteria.

## Question 5

A team building a multi-agent research system notices that as they add more specialist agents, overall throughput drops and the coordinator becomes overwhelmed with state tracking. Which topology are they using, and what design property is causing this?

A. Pipeline; sequential stage latency accumulates until downstream agents stop receiving inputs in time.
B. Hub-and-spoke; routing all messages through the hub creates a throughput bottleneck and state bloat.
C. Pipeline; the central stage cannot process simultaneous outputs from multiple upstream agents.
D. Peer-to-peer; distributing state across agents creates coordination overhead that degrades overall speed.

**Answer:** B
**Explanation:** Hub-and-spoke centralizes all coordination through one orchestrator. As spokes are added, the hub becomes a throughput bottleneck because every message routes through it, and it accumulates context for every active spoke. These are the two defining failure modes of the hub-and-spoke topology at scale.

## Question 6

An architect is evaluating a five-stage document processing system built with pipeline topology. A code review flags that a failure in stage three will silently stall the final output. What pipeline property makes this concern valid?

A. A failed mid-stage agent blocks every downstream stage because those stages have no input to process.
B. A failed mid-stage agent increases total latency because the system must retry the stage from the pipeline entry point.
C. A failed mid-stage agent forces the hub to reroute the task to a parallel specialist instead.
D. A failed mid-stage agent triggers a peer-to-peer fallback so other agents can complete the remaining steps.

**Answer:** A
**Explanation:** In a pipeline, each stage depends on the previous stage's output. A failed mid-stage agent has no output to pass forward, so every downstream stage is blocked. This cascade failure surface grows with pipeline depth, making error handling at every stage boundary a design requirement.

## Question 7

A team implements an evaluator-optimizer loop where a generator agent drafts a plan and an evaluator scores it against a rubric, feeding feedback back for revision. After deployment, the loop runs continuously without stopping. What required design element was omitted?

A. A maximum iteration count or quality threshold to guarantee the loop terminates.
B. A peer-to-peer channel so the generator and evaluator can exchange feedback without routing overhead.
C. A versioned message schema so the evaluator parses the generator's output correctly across iterations.
D. A hub orchestrator to track iteration count and coordinate handoffs between the two agents.

**Answer:** A
**Explanation:** The evaluator-optimizer pattern requires both a quality threshold and a maximum iteration count. Without a termination condition the loop has no guaranteed stopping point and will run indefinitely. The deck explicitly calls this a hard requirement, not an optional enhancement.

## Question 8

A compliance team is designing a multi-agent audit workflow and proposes peer-to-peer topology so agents can collaborate without routing delays. A senior architect flags the proposal as a topology anti-pattern. What makes P2P wrong for this use case?

A. P2P requires all agents to share a central state store, which creates a bottleneck that slows audit processing.
B. P2P introduces a single point of failure at the most connected agent, which compliance systems cannot tolerate.
C. P2P accumulates message-routing latency across hops, which audit workflows cannot accommodate under time constraints.
D. P2P distributes state across agents, making it impossible to reconstruct a full decision log for compliance.

**Answer:** D
**Explanation:** The deck explicitly identifies this as the P2P anti-pattern: using P2P when a complete audit trail is required. Distributed state makes it impossible to reconstruct a full decision log after the fact. Compliance and audit requirements demand centralized state, which P2P cannot provide by design.

## Question 9

A subagent in a document classification pipeline receives its handoff message but returns incorrect outputs on one in five tasks. Investigation shows the subagent cannot access the sender's conversation history and is missing key classification rules on affected tasks. What design principle was violated?

A. Agent substitutability: the handoff was designed for a specific implementation that is no longer deployed.
B. Schema versioning: the handoff lacked a version field, so the receiver parsed the message incorrectly.
C. Output format specification: without a defined output structure, the receiver produced inconsistent results.
D. Context isolation: subagents have separate context windows, so needed information must be explicitly sent.

**Answer:** D
**Explanation:** Context isolation means subagents operate in their own context window and nothing passes automatically. Every piece of information the receiver needs must be explicitly included in the handoff message. Relying on the receiver to access the sender's history violates this principle and causes the described failures.

## Question 10

An engineering team updates a handoff message schema by adding a new required field for task priority. Agents running older sender code start producing messages without this field, and receivers crash on arrival. Which schema design practice would have prevented this outcome?

A. Writing contract tests that confirm all required fields are present before the receiver processes the message.
B. Reducing handoff payload size by excluding all optional fields so older and newer senders produce identical messages.
C. Designing handoffs against an interface so any compliant receiver can process messages from any sender.
D. Providing a migration path for older senders and having receivers handle missing fields gracefully.

**Answer:** D
**Explanation:** Schema versioning requires a migration path when adding new required fields. The deck specifies that receivers should handle missing optional fields gracefully and that new required fields need sender-side migration before the schema change ships. Forward compatibility keeps systems stable during incremental updates.

## Question 11

After a multi-agent order-processing workflow completes, a customer reports receiving a duplicate shipment. The orchestrator's logs show all handoffs as successful. An engineer suspects one handoff dropped the 'skip-duplicate-check' flag without raising an error. What failure pattern does this describe?

A. Under-specified handoff: the sender omitted required context and the receiver filled the gap with a wrong guess.
B. Undifferentiated error: the subagent returned a generic error code the orchestrator could not interpret.
C. Error swallowing: the subagent caught an internal exception and returned empty output instead of an error payload.
D. Silent failure: the handoff appeared to succeed but dropped a critical field, so the system acted on bad state.

**Answer:** D
**Explanation:** Silent failure is a handoff that appears to succeed but drops or corrupts critical information without raising an error signal. The orchestrator proceeds on incorrect state and the failure surfaces downstream. The deck identifies this as the most dangerous pattern because it masquerades as success.

## Question 12

A customer-support agent manages open tickets across multiple sessions. The current ticket details and recent tool outputs are referenced frequently during each turn, while closed ticket history is rarely accessed but must survive for later review. Where should each type of state live?

A. All ticket data in context so the agent can access both current and historical records without a retrieval step.
B. All ticket data in external storage so it persists across every session without loss.
C. Current ticket details in a vector index for similarity retrieval; closed history in context for direct reference.
D. Current ticket details in context for fast access; closed ticket history in external storage for durability.

**Answer:** D
**Explanation:** The deck's framework puts hot state—actively changing and frequently referenced this turn—in context for zero-latency access. Cold state—rarely accessed but needing to survive sessions—belongs in external storage. Mixing these up adds unnecessary latency to hot access paths or loses durable data on session end.

## Question 13

An agent needs to recall the most relevant prior customer interaction from a database of thousands of past conversations. The agent does not know which session ID to look up—retrieval must be based on the meaning of the current query. Which external store type is the correct fit?

A. A vector index, because it retrieves stored content by embedding similarity rather than requiring an exact key.
B. A key-value store, because conversations are identified by session IDs that enable fast exact lookup.
C. In-context state, because loading recent interactions directly avoids the tool-call latency of any external retrieval.
D. A relational database, because structured queries and filtering by customer and date fields scale to thousands of records.

**Answer:** A
**Explanation:** The deck teaches three external store types and their access patterns. Vector indexes support semantic similarity search—returning the most relevant stored content by meaning rather than exact key. When the agent cannot supply an exact identifier, a vector index is the correct match for the retrieval need.

## Question 14

A data pipeline agent runs a 12-phase workflow. The team is deciding whether to checkpoint after every tool call or at phase boundaries only. Individual tool calls are fast and idempotent, and the team wants the simplest design. What does the deck's framework recommend?

A. Fine-grained per-tool-call checkpoints, since a 12-phase workflow has too much failure surface for phase-only saves.
B. Coarse phase-boundary checkpoints, since steps are idempotent and per-call saves add complexity without benefit.
C. No checkpointing at all, since idempotent steps can be safely rerun from scratch after any failure.
D. Hybrid granularity: fine-grained in early phases where rework is expensive, coarse in later ones.

**Answer:** B
**Explanation:** The deck recommends coarse phase-boundary checkpoints as the better default. Fewer writes, simpler state management, and easier recovery reasoning make them preferable when individual steps are fast and idempotent. Fine-grained checkpoints are justified only when steps are expensive to rerun or have external side effects.

## Question 15

An agent resumes from a checkpoint after an overnight interruption and begins executing the next phase. Unknown to the agent, a source document it relies on was updated during the interruption. The agent completes the phase confidently using stale data. Which design mechanism was missing?

A. Fine-grained checkpointing: saving after every tool call keeps the agent's view of external sources more up to date.
B. Memory hygiene: pruning the stale checkpoint forces the agent to rebuild state from current source documents.
C. State versioning: an environment hash saved at write time lets the agent detect changes before resuming.
D. Graceful degradation: the agent continues with partial state and notes the gap rather than relying on version checks.

**Answer:** C
**Explanation:** State versioning records a timestamp and environment hash at checkpoint write time. On resume, the agent compares the current environment against the saved version and flags the conflict rather than silently proceeding. Without this, the agent acts on stale state with high confidence, producing incorrect decisions that are hard to trace.
