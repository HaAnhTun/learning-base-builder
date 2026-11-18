# 1A Quiz

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · D1: Agentic Architecture - Foundations · 11 questions · pass mark 70% · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies

## Question 1

A developer is designing a system where Claude receives a customer request, decides which of three internal APIs to call based on the request, executes the call, reads the result, and then decides whether a follow-up call is needed. Which term best describes this system?

A. A deterministic workflow, because the developer defines which APIs are available before the system runs.
B. An agentic system, because the model controls flow by selecting tools and iterating at inference time.
C. A conversational chatbot, because the user sends a request and the system generates a reply.
D. A prompt chain, because multiple model calls execute in sequence to complete the task.

**Answer:** B
**Explanation:** The defining characteristic of an agentic system is that the model selects actions and controls the flow at inference time. Because Claude decides which API to call and whether a follow-up is needed based on runtime context, the system meets that definition. A deterministic workflow has fixed control flow authored at design time; a chatbot cannot invoke APIs or take external actions; prompt chaining is a fixed sequential pipeline where the developer sets the sequence.

## Question 2

A team is building a document summarization system. The input format is always a PDF, the desired output is always a structured JSON summary, and every processing step can be specified before the system runs. A junior engineer proposes wrapping the whole thing in an agentic architecture for future flexibility. What is the strongest argument against this?

A. Agentic complexity adds a broader failure surface with no capability gain for a fully pre-scriptable task.
B. Claude cannot produce structured JSON output, so the predefined output format requirement rules out using it here.
C. Adding a human-in-the-loop checkpoint to the agentic design would eliminate all the risks that architecture introduces.
D. Agentic systems cannot process PDF inputs, making the architecture incompatible with this use case.

**Answer:** A
**Explanation:** When all steps can be authored at design time, the output format is fixed, and inputs are predictable, a deterministic workflow is the correct choice. Agents add token cost, a broader failure surface, and harder-to-audit execution traces without delivering any capability gain for a task that requires no runtime judgment. The concern is not that agents are unusable, but that they introduce unnecessary overhead for tasks that workflows handle cleanly.

## Question 3

An engineer reviews a tool schema and finds the description reads: 'Handles order data.' After deploying the agent, they notice it frequently skips this tool even when order lookups are clearly needed. What is the most likely root cause based on how Claude selects tools?

A. The runtime layer intercepts the tool call and redirects it to a different tool with a similar name.
B. The tool's parameter specification is missing required fields, so Claude cannot construct a valid tool call.
C. The observation returned by the tool is being injected into the wrong position in the model's context window.
D. The vague description leaves Claude no reliable basis for deciding when this tool applies to the task.

**Answer:** D
**Explanation:** Claude selects tools by reading their natural-language descriptions, not by inspecting implementation code. A vague description like 'handles order data' gives Claude no reliable basis for deciding when the tool applies, which leads to it being skipped. The fix is a precise description that states what the tool does, what inputs it expects, and what it returns — something a non-engineer could act on.

## Question 4

A customer-support agent is mid-task when a tool call returns a 404 error on what should be a stable internal API. According to the agentic loop, what should happen next?

A. The perception phase discards the error and re-reads only the last successful observation to resume the plan.
B. The loop terminates immediately, because any tool error always triggers a hard stop condition by default in agent design.
C. The error is injected as an observation, and the reasoning phase replans — retrying, switching tools, or escalating.
D. The action phase retries the identical tool call automatically without involving the reasoning phase.

**Answer:** C
**Explanation:** In the agentic loop, an error result is an observation like any other — it is injected into context and the model reads it in the next perception phase. The reasoning phase then replans: retry with different parameters, try an alternative tool, or escalate. This adaptive response to unexpected observations is what distinguishes an agent from a fixed pipeline, which would simply propagate the failure.

## Question 5

A long-running research agent is five minutes into its task. An engineer checks the context window and sees the original instructions, three sets of search results, two full article texts, and several lines of intermediate planning reasoning. Which concept from the agentic loop does this pattern illustrate?

A. The observation phase is malfunctioning because tool results belong in a persistent external database, not in context.
B. Dynamic planning has failed because a well-functioning agent clears prior observations each iteration to stay under capacity.
C. The reasoning phase is writing redundant planning notes, signaling the agent is spinning without making real progress.
D. The context window is the agent's ephemeral working memory, filling with inputs, tool results, and reasoning each loop.

**Answer:** D
**Explanation:** The deck describes the context window as the agent's working memory. As the agentic loop runs, inputs, accumulated tool calls, observations (results), and intermediate reasoning all pile up in context. This accumulation is a key design constraint: a long-running agent can fill its context window, losing the ability to process new information. The engineer is observing the normal fill pattern described in the lesson.

## Question 6

An agentic pipeline has been running for 45 minutes on a data-enrichment task. Each iteration, the agent issues the same database query with identical parameters and gets back the same empty result set. The loop has not stopped. What is this failure mode called, and what design element should have prevented it?

A. This is circular reasoning, prevented by requiring the model to explicitly self-report when it considers the task complete.
B. This is spinning, prevented by a turn budget in the orchestration layer that caps iterations before the agent starts.
C. This is an escalation failure, prevented by the agent issuing a stop signal after the first empty result set.
D. This is task failure, prevented by configuring the database to return a non-empty result for every query type.

**Answer:** B
**Explanation:** The deck defines spinning as repeated actions without new results — the goal state does not get closer even as context grows. The primary prevention mechanism is a turn budget (max_iterations limit) set in the orchestration layer before the agent starts. Tracking repeated tool calls with identical parameters is one of the recommended detection methods. Without a hard cap, the loop can run indefinitely.

## Question 7

An agent processing insurance claims reaches a step where it would need to approve a payment above a threshold that exceeds its authorization. It has no new data to work with and no alternative tool path available. According to loop-control best practices, what should the agent do?

A. Continue iterating until the turn budget is exhausted, then surface whatever partial result has been achieved so far.
B. Iterate with a reduced payment amount to stay within the approval threshold, adjusting the claim value autonomously.
C. Emit a stop signal to terminate the loop cleanly without passing any context to a human or fallback system.
D. Escalate to a human operator, because the agent has reached its authorization boundary with no viable alternative.

**Answer:** D
**Explanation:** The deck defines escalation as the correct response when an agent reaches its authorization boundary or lacks the information needed to proceed. It distinguishes this from iteration, which requires new data or a different approach to try. When neither condition for iteration is met and the agent cannot proceed autonomously, escalation to a human or fallback system is the designed safety valve — not a failure.

## Question 8

A product team is building a system that must extract key fields from structured insurance forms. Input format is a fixed PDF schema, output format is a predefined JSON object, and every processing step can be written before deployment. A colleague insists they need an agentic system. Based on the decision signals covered in this lesson, what is the correct response?

A. A prompt chain is insufficient here because sequential calls cannot handle structured extraction from multi-page forms.
B. An agentic system is correct because PDF parsing often encounters unexpected formatting variations that require runtime judgment.
C. A deterministic workflow is correct because input, output, and steps are all fully defined before runtime.
D. Both architectures perform equivalently here; the choice is a matter of team preference and existing tooling.

**Answer:** C
**Explanation:** The deck gives three explicit tests: predictable input, known output format, and every step specifiable at design time. When all three hold, a deterministic workflow is the correct choice. Adding agentic complexity in this scenario increases token cost, creates a harder-to-audit execution trace, and introduces failure surface — all without delivering any capability the workflow cannot provide.

## Question 9

A content platform uses a system that routes user-submitted articles to one of three specialized review prompts based on topic, then runs each routed article through a quality-scoring call. The developer asks whether this qualifies as an agentic system since it involves multiple LLM calls. What is the correct answer?

A. It is agentic because the classifier LLM is autonomously choosing which review path to invoke at inference time.
B. It is a workflow using the routing pattern, because the topology is fixed at design time even when LLMs are involved.
C. It is a hybrid system because it combines LLM calls with deterministic steps, and hybrids always qualify as agentic.
D. It is agentic because multiple LLM calls with distinct, specialized roles always constitute an orchestrator-subagent pattern.

**Answer:** B
**Explanation:** The deck covers routing as one of the five core workflow patterns. Even when a routing step calls an LLM, the topology — which specialized paths exist and when they activate — is fixed at design time by the developer. Multiple LLM calls alone do not make a system agentic. Agency requires the model to select tools at inference time based on context, which is not happening here.

## Question 10

An engineering team has a working prompt-chain workflow that handles 95% of customer queries correctly. It fails on 5% of cases that require fetching real-time pricing data unavailable at design time. A senior engineer recommends rebuilding the entire system as a fully agentic pipeline. What does the incremental complexity principle suggest instead?

A. Accept the 5% failure rate as a reasonable tradeoff to preserve the workflow's auditability across all cases.
B. Add a human-in-the-loop checkpoint to the existing workflow for the 5% of failing cases without any architectural change.
C. Replace only the pricing-fetch step with agent behavior while leaving the rest of the workflow intact.
D. Rebuild the entire pipeline as a fully agentic system to future-proof against additional edge cases that may arise.

**Answer:** C
**Explanation:** The deck describes incremental complexity as building the workflow first, identifying the specific step that breaks, and replacing only that step with agent behavior. Rebuilding the entire system as agentic would introduce unnecessary token cost, broader failure surface, and harder-to-audit traces across the 95% of cases that the workflow already handles correctly. The right approach is surgical: add agentic behavior only at the pricing-fetch step.

## Question 11

A team is comparing two designs for a content-moderation pipeline. Design A uses a deterministic workflow with a fixed rule-based router and three specialized prompts. Design B uses a fully autonomous agent that selects moderation strategies at inference time. The task involves well-defined categories and a fixed decision schema. Which of the three tradeoff axes from this lesson most directly favors Design A?

A. The cost axis, because agentic systems always consume fewer tokens per run than equivalent multi-step workflow systems.
B. The capability axis, because the fixed routing schema limits the full range of moderation decisions the workflow can make.
C. The adaptability axis, because agents handle a wider range of variable inputs than fixed routing rules allow.
D. The auditability axis, because workflow steps are individually testable and failures localize cleanly to a specific step.

**Answer:** D
**Explanation:** The deck presents three explicit tradeoff axes: cost vs. capability, auditability vs. flexibility, and reliability vs. adaptability. For a well-defined task with a fixed decision schema, the auditability axis most directly favors the workflow. Every step is individually testable and failures localize to a specific point. Design B would trade that auditability for flexibility the task does not require.
