# 4B Quiz

> Course: Claude Certified Architect (CCAR-F) - 2026 Exam Prep · D4: Prompt Engineering - Advanced Prompting Techniques · 18 questions · pass mark 70% · ANSWER KEY INCLUDED: show a question and its choices first, reveal the answer only after the learner replies

## Question 1

A team switches a structured report-generation prompt from zero-shot with detailed prose instructions to a three-shot prompt with concrete examples. Output consistency improves noticeably. According to this deck, what mechanism explains the improvement?

A. Examples increase total prompt token count, which causes the model to allocate proportionally more processing attention to the task and consistently produce more careful, thorough outputs.
B. Three examples reduce prompt ambiguity by providing broad coverage of edge cases, which means the model encounters far fewer out-of-scope input patterns during actual generation.
C. Few-shot prompting switches the model into a retrieval mode that surfaces more relevant training knowledge, improving output quality by giving the model better access to domain-specific patterns.
D. Examples remove the interpretation step: the model matches the demonstrated pattern directly instead of translating a prose description into output behavior.

**Answer:** D
**Explanation:** The deck explains that prose instructions require the model to interpret a description and translate it to output, introducing variance. Examples eliminate the interpretation step: the model matches the demonstrated pattern directly, extracting implicit rules for format, tone, scope, and reasoning. This is the pattern-matching mechanism that explains improved consistency.

## Question 2

A developer has a structured output prompt that uses five examples. Output quality is still inconsistent. Before adding a sixth example, what does this deck say the developer should do first, and why?

A. Drop to zero-shot first to establish a clean baseline output, then systematically add examples back one at a time until the desired level of output consistency is achieved.
B. Add a weighting instruction after the examples that explicitly tells the model which single example it should treat as the primary reference when new inputs most closely resemble that case.
C. Audit the existing examples for inconsistent formatting or tone before adding more, since conflicting signals cause the model to average across them and produce muddled output.
D. Increase to seven examples and include at least one covering each major edge case so the model's averaged pattern naturally converges on the intended output structure.

**Answer:** C
**Explanation:** The deck teaches that adding more examples to a failing prompt is the wrong instinct. When examples have inconsistent formatting or off-tone phrasing, the model averages across conflicting signals and produces muddled output. The prescribed action is to audit existing examples for consistency and quality before adding more.

## Question 3

A developer has built a few-shot prompt for a support ticket classifier. All five examples come from billing disputes — the most common ticket type. In testing, the model handles billing tickets well but misclassifies technical and account-access tickets. Which design flaw best explains this behavior?

A. The example outputs contain stylistic artifacts from the billing context that contaminate responses written for unrelated ticket types.
B. The ordering of examples is wrong — the most representative billing example should be placed last in the prompt to reduce its anchoring effect.
C. A static few-shot set is being used instead of dynamic selection, so examples are never matched to the specific current input at runtime.
D. The examples all come from one input type, so the model overfits to billing tickets and generalizes poorly to other categories.

**Answer:** D
**Explanation:** When all examples come from one narrow input type, the model learns to handle that specific pattern and generalizes poorly to other categories. The fix is a diverse example set that covers different input types, not more examples from the same slice.

## Question 4

A prompt engineer notices that every response in her few-shot-prompted workflow ends with the phrase 'Please let me know if you need clarification.' — a phrase that appeared in only one of her five examples. She doesn't want that phrase in production. What phenomenon does this illustrate, and what is the correct fix?

A. This is example contamination; review each example output as a production response and remove the artifact from the offending example.
B. This is a dynamic selection failure; switching to runtime example retrieval will prevent the biased example from being surfaced for unrelated inputs.
C. This is an ordering effect; placing the contaminated example earlier in the prompt will reduce its influence on subsequent outputs.
D. This is an input diversity problem; adding examples from more input categories will dilute the artifact phrase across the wider example pool.

**Answer:** A
**Explanation:** A phrase from one example's output propagates into all responses because examples are narrow or stylistically biased. The correct fix is to review each example output as if it were a production response and remove any element you would not want reproduced.

## Question 5

A developer is building a multi-step expense reimbursement validator. The model must check the amount, verify the category, confirm the date format, and flag policy violations — all in a single response. Output accuracy is inconsistent and errors compound across steps. Which technique, as taught in this deck, is most likely to improve accuracy?

A. Add a chain-of-thought elicitation phrase so the model reasons through each validation step visibly before giving the final result.
B. Provide structured few-shot examples showing completed reimbursement validations so the model can pattern its output on those cases.
C. Lower the temperature to near zero so the model consistently picks the highest-probability validation outcome at each individual step.
D. Switch to extended thinking by setting a token budget API parameter so the model reasons internally before generating any response.

**Answer:** A
**Explanation:** Tasks requiring several sequential steps benefit most from chain-of-thought prompting because visible intermediate reasoning lets each step be checked before it feeds the next, reducing error accumulation.

## Question 6

An architect asks whether chain-of-thought prompting is a suitable replacement for extended thinking in a production API integration. A colleague argues they are equivalent because both make the model reason before answering. What is the most accurate response according to this deck?

A. They are not equivalent: CoT lives in prompt text with no API configuration, while extended thinking is an API parameter that streams reasoning blocks separately.
B. Chain-of-thought is activated via an API flag, while extended thinking requires writing explicit reasoning instructions directly into the prompt text.
C. Extended thinking is a more reliable version of CoT and should always be preferred in any production system that requires intermediate reasoning steps.
D. They are effectively equivalent for production use because both produce visible step-by-step reasoning that developers can inspect before reading the final answer.

**Answer:** A
**Explanation:** Chain-of-thought lives entirely in the prompt text and produces reasoning inline in the response. Extended thinking is an API parameter that allocates a token budget and streams reasoning as separate blocks. Conflating them leads to incorrect API design decisions.

## Question 7

A team is choosing between chain-of-thought prompting and extended thinking for a task that requires the model to weigh competing engineering tradeoffs across several technical constraints before recommending an architecture. Which consideration from this deck most directly guides that choice?

A. Use extended thinking immediately because architecture tradeoffs always require the deeper token budget that only an API parameter can provide.
B. Choose extended thinking because it gives the developer control over reasoning length via a token budget, which CoT cannot match.
C. Use chain-of-thought with a structured scaffold since the labeled reasoning template will enforce consistent tradeoff analysis across all similar prompts.
D. Try chain-of-thought prompting first; switch to extended thinking only if CoT does not produce sufficient quality for this level of complexity.

**Answer:** D
**Explanation:** Extended thinking is most appropriate for tasks requiring exploration of multiple solution paths under genuine complexity. The deck teaches trying CoT first; extended thinking is warranted only when CoT falls short and the complexity justifies the added cost and implementation overhead.

## Question 8

An engineer integrating extended thinking into a pipeline notes that the thinking blocks arrive before the final answer and are billed even though they don't appear in the response text. She also notices that allocating a very large thinking budget reduced the space available for her long system prompt. Which two properties of thinking blocks from this deck explain both observations?

A. Thinking blocks are billed as tokens and count against the context window, so a large budget shrinks the space available for the prompt and final response.
B. Thinking blocks are generated by the developer as prompt text and streamed inline, so they consume both prompt tokens and response tokens simultaneously.
C. Thinking blocks are streamed as separate events and are not part of the output text, so they are billed at a discounted token rate separate from the main response.
D. Thinking blocks are separate from the output text and bypass the context window, which is why a larger budget does not reduce space available for the prompt.

**Answer:** A
**Explanation:** Thinking blocks count against the model's context budget and are billed even though they don't appear in the final response. A large thinking budget reduces the tokens available for the prompt and final answer, explaining both observations.

## Question 9

A developer needs Claude to return a JSON object with a specific schema for every API call in a production pipeline. She is considering prefilling the assistant turn with a left curly brace. What does this deck teach about this approach, and what should she combine it with for maximum reliability?

A. A JSON opener prefill alone fully guarantees valid JSON structure throughout a long multi-field response without any additional schema instructions.
B. Prefilling the assistant turn with a curly brace fully bypasses the need for JSON mode and is always preferred over any API-level format enforcement.
C. The developer should rely only on explicit format instructions in the system prompt, since prefilling adds ambiguity about where the model's continuation begins.
D. The curly brace anchors JSON format from the first token; pair it with explicit schema instructions in the user turn for the most reliable output.

**Answer:** D
**Explanation:** Anchoring with a left curly brace commits the model to JSON object format from the first token. The deck teaches that combining this prefill with explicit schema instructions in the user turn is the most reliable approach — neither technique alone is as strong as both together.

## Question 10

A CCA-F candidate encounters a question describing a scenario where a developer uses prefilling to complete the opening of a response the model would otherwise decline to give. The question asks what category of prefilling use this represents. What is the correct answer according to this deck?

A. This is an advanced form of format anchoring that uses the output structure to guide the model's content generation.
B. This is a dynamic output steering technique that adjusts the response path based on downstream processing requirements.
C. This is acceptable if the developer has system-prompt authority, because prefilling in that context is a legitimate configuration tool.
D. This is inappropriate use of prefilling; appropriate prefilling is limited to format anchoring and does not suppress safety behavior.

**Answer:** D
**Explanation:** The deck identifies refusal bypass as the most common inappropriate use of prefilling and flags it as a high-frequency exam trap. Appropriate prefilling is restricted to format anchoring — JSON openers, structural markers, language starters — and does not touch safety or reasoning behavior.

## Question 11

A team wants their content generation pipeline to produce outputs with consistent tone and scope across all turns without relying on per-turn instructions. Which steering technique from this deck is most directly suited to establishing persistent tone and scope?

A. Explicit length anchoring in the user turn with an exact word count will regulate scope and prevent off-topic elaboration across outputs.
B. System prompt framing sets persistent tone and scope that applies across all turns without needing per-turn repetition.
C. A format lock combining a few-shot example with a prefill opener will enforce both structure and tone consistently across all outputs.
D. Prefilling the assistant turn with an opening phrase that reflects the desired tone will anchor that tone for each individual response.

**Answer:** B
**Explanation:** The deck teaches that system prompt framing sets persistent tone and scope that applies across all turns in a session — unlike per-turn instructions, it operates at a level that shapes every response without needing to be repeated.

## Question 12

A developer has a prompt that instructs the model to produce a 'brief overview' but also requires ten specific sections, each with a heading and at least two bullet points. Testing shows that outputs are either too short to cover all sections or so long that they don't feel like brief overviews. Which anti-pattern from this deck explains this failure?

A. This is a length anchoring failure; switching from implicit scope cues to an explicit word count target will fully resolve the contradictory output behavior.
B. This is a framing effect problem; rewriting the system prompt framing to specify the correct audience will naturally bring length and section coverage into alignment.
C. This is conflicting constraint over-steering; 'brief overview' and ten required sections are incompatible signals that force the model to fail on one requirement.
D. This is a missing format lock; pairing a few-shot example with a prefill opener would demonstrate how to balance brevity and ten-section completeness at once.

**Answer:** C
**Explanation:** The deck explicitly uses the 'brief overview with ten required sections' as an example of contradictory constraints. Over-steering with incompatible signals forces the model to satisfy requirements that cannot both be met, degrading quality on both dimensions.

## Question 13

An ML engineer sets temperature to 0 on all prompts in their production pipeline, reasoning that the lowest setting always yields the safest and most accurate outputs. For which task type does this deck specifically identify temperature 0 as the wrong choice?

A. Creative writing — temperature 0 forces the model onto the same highest-probability path every time, producing flat, repetitive output.
B. Entity extraction — temperature 0 makes the model overconfident and causes it to hallucinate field values it cannot find in the source text.
C. Classification tasks — temperature 0 causes the model to assign every input to the same dominant class regardless of the actual distribution.
D. Factual question answering — temperature 0 makes the model ignore low-probability but correct answers when the training data is ambiguous.

**Answer:** A
**Explanation:** The deck directly refutes the assumption that temperature 0 is universally safe. For creative writing and similar tasks requiring output diversity, temperature 0 causes the model to always pick the same highest-probability path, producing repetitive, flat output.

## Question 14

A developer observes that after combining temperature 0.7 with top_p 0.85, output quality on her creative task is inconsistent in ways that neither parameter alone produced. She wants to diagnose which parameter is responsible. What does this deck advise?

A. Increase top_k to 50 alongside the current settings to widen the candidate pool and directly offset the negative interaction between temperature and top_p.
B. Use a structured few-shot example set to override the sampling behavior and make output quality fully independent of temperature and top_p settings.
C. Reset one parameter to its default and test with only the other changed; running both simultaneously makes it impossible to isolate which is responsible.
D. Set temperature to 2.0 to widen the candidate distribution so the interaction with top_p becomes easier to observe directly.

**Answer:** C
**Explanation:** The deck teaches that temperature reshapes the distribution before top_p restricts the pool, creating compound interaction effects that are not additive. The guidance is to adjust one parameter at a time so output quality changes can be attributed to a specific parameter.

## Question 15

A product manager submits a vague ticket asking Claude to 'improve the onboarding flow.' A multi-turn agent responds with a clarification turn that asks three separate questions about the user base, technical constraints, and timeline. Testing shows users disengage after this turn. What specific design flaw does this deck identify?

A. The agent should have launched a turn sequence instead; breaking the improvement task into focused steps eliminates the need for an upfront clarification turn.
B. The questions were too open-ended; converting all three to targeted yes/no questions would keep the clarification turn efficient without reducing the number asked.
C. Asking three questions at once turns a clarification into a form; the agent should pick the one ambiguity most likely to cause wrong output and ask only that.
D. The agent failed to acknowledge what it understood before asking its questions, which made users feel their input was being ignored entirely.

**Answer:** C
**Explanation:** The deck teaches that a clarification turn with multiple questions creates a form-filling experience rather than a conversation. The correct design is to identify the single ambiguity most likely to produce wrong output and ask exactly one targeted question about it.

## Question 16

A developer is building a multi-turn document drafting workflow. After the first turn produces a draft, subsequent turns are losing track of what was completed and the model treats each message as if it were a fresh start. Which technique from this deck directly addresses this problem?

A. Add an iterative refinement loop where each turn delivers targeted feedback on one category of change until all outstanding issues are resolved.
B. Use a clarification turn at the very start of the workflow to gather all requirements upfront so the model never loses context mid-workflow.
C. Switch to a single long prompt that includes all prior instructions and the full draft so the model always has complete context in one call.
D. Open each turn with a brief recap of what was completed and name the current workflow phase before giving the next instruction.

**Answer:** D
**Explanation:** The deck prescribes state signaling as the solution to workflow drift: open each turn with a brief recap of prior completion, reference the relevant prior output before the next instruction, and name the current phase explicitly. These signals prevent the model from treating each turn as a fresh conversation.

## Question 17

A developer notices that after twenty turns of a support-ticket workflow, Claude starts addressing the user by the wrong department name and gradually shifts from resolving tickets to summarizing them. No single turn looks obviously wrong. Which term best describes the root cause of this degradation?

A. Context drift, where the model's behavior gradually diverges from original intent across many turns.
B. Noise buildup, caused by repeated contradictory instructions accumulating in the conversation history.
C. Context window truncation, where older turns are silently dropped as the conversation exceeds the token limit.
D. Turn misalignment, where the assistant response is appended out of sequence in the conversation history.

**Answer:** A
**Explanation:** Context drift is the gradual shift in topic, tone, or task framing that accumulates across many turns without any single turn being obviously wrong. Periodic re-anchoring with explicit framing reminders is the primary tool for preventing it.

## Question 18

An automated multi-turn workflow has been running for thirty turns and output quality is degrading. The conversation history contains several overridden instructions, abandoned subtask exchanges, and verbose confirmation back-and-forth. The engineer wants to salvage the useful decisions already reached without restarting from scratch. What approach does the deck recommend?

A. Delete the last ten turns to trim the most recent noise while keeping the earlier conversation intact.
B. Summarize the full history into a single message and append it to the same conversation thread to compress the noise.
C. Start a new thread, carrying forward only key decisions, confirmed constraints, and relevant outputs.
D. Continue the existing thread and inject a reminder of the original system prompt at the next turn to re-anchor the model.

**Answer:** C
**Explanation:** When noise has built up or drift has occurred, a partial reset starts a new thread but carries forward only essential prior context — key decisions, confirmed constraints, and relevant outputs — leaving noise and abandoned branches behind.
