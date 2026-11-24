---
name: prompt-craft
description: Manual reference for writing prompts, system prompts and subagent briefs, structured output and retry.
disable-model-invocation: true
---

This skill owns the prompt text, the subagent brief template, retry after a failed output, and the test of a prompt. Session memory lives in skill `project-state`.

Rule provenance: tags [CCAR NN] name the course lesson file number that supports the rule; [practice] marks a sound Claude Code practice the lessons do not cover.

## Route

- Any prompt: run **Write a prompt**.
- Brief for a subagent: fill the **Subagent brief** template, then run Write a prompt on its task.
- System prompt or CLAUDE.md-style standing instruction: also open `references/system-prompts.md`.
- Output failed or varies between runs, or needs a retry loop or reviewer pass: run **Fix a failing prompt**.
- A rule that must never break: run **Code enforces, prompts guide**.
- A multi-turn refinement: open `references/multi-turn.md`.

## Write a prompt

1. **One goal.** State the goal as a verb-led instruction (write, extract, classify, compare, list). Split into ordered prompts when the task has phases that yield different outputs, when one phase must be checked before the next, when precision needs more than two or three constraints, or when a single prompt keeps missing part of the task. [CCAR 13]
   Done when each prompt has one goal and one output you can check on its own. [CCAR 13]
2. **Close the gaps.** Specify format, length, audience and perspective or tone. Name what to include, what to exclude, what to treat as already established, and where the task ends. Phrase each instruction as the behaviour wanted ("write three sentences for a non-technical reader"); keep prohibitions for a Constraints section. [CCAR 13]
   Done when two tests pass. Interpretation: no reasonable reader can take the prompt two ways. Gap: every assumption the model would make is written down or harmless. [CCAR 13]
3. **Order and tag.** For long documents, put them above the instructions and the query, with the query last. Wrap parts in descriptive XML tags used consistently across prompts (`<task>`, `<context>`, `<examples>`, `<output_format>`), close every tag, nest one or two levels. Give each document its own `<document>` with `<source>` and `<document_content>`, indexed. When only some documents should inform a part of the answer, refer to them by name or index. [CCAR 13]
   Done when instructions and data never share an untagged block. [CCAR 13]
4. **Examples when they earn it.** Start without. Add them when variance survives instruction fixes or the format is novel or structured; design and test them with `references/examples-and-reasoning.md`. [CCAR 14]
   Done when a run with the examples beats a run without them on varied inputs. [CCAR 14]
5. **Reasoning on demand.** Ask for visible step-by-step reasoning where a wrong intermediate step would change the answer; which tasks qualify and how to ask: `references/examples-and-reasoning.md`. [CCAR 14]
   Done when the prompt asks for reasoning only where an intermediate step matters. [CCAR 14]
6. **Output format.** State the shape: structure, field names with value types, order, length. When code consumes the output, take the schema-backed route in `references/structured-output.md`. [CCAR 13, 14]
   Done when a parser could be written from the prompt alone. [practice]
7. **Test.** Run varied phrasings and inputs, including an empty or very long input and one at the edge of the task. After every edit, re-run the earlier cases. Open `references/testing-prompts.md` when comparing versions across a saved suite or checking attribution in a multi-document prompt. [CCAR 13]
   Done when outputs on the varied set are ones you would accept and no earlier case regressed. [CCAR 13]

## Subagent brief

Single template for every delegated task. Fill all four blocks; when `<context>` holds long documents, it sits first, above `<task>`. [CCAR 04, 13]

```
<context>Only what this task needs: paths, settled decisions, prior output passed in or referenced explicitly.</context>
<task>One verb-led goal and where it ends.</task>
<output_format>Exact reply shape: fields, order, length bound. Answer first.</output_format>
<constraints>Scope: include, exclude, treat as given. Limits to respect. Stop condition: when to return what it has.</constraints>
```

- A subagent runs in its own context and does not inherit the parent conversation: put everything it needs into the brief and pass prior output explicitly. Relevant context only; surplus context competes with the instructions. [CCAR 04]
- Ask for the source beside each claim (file and line, URL, quoted passage) and for "not found" when evidence is missing, so unsupported claims show. [CCAR 15]
- Give parallel subagents the same tag names and reply shape so results merge. [CCAR 04, 13]

Done when someone reading only the brief could do the task and knows what to hand back. [CCAR 04] To validate a reply, open `.claude/skills/agent-orchestration/SKILL.md` section 4 (checking a handback against the brief); when the subagent errored or returned nothing usable, open its section 5 (Handle failure).

## Fix a failing prompt

1. **Classify the failure.**
   - Results differ between runs, or look plausible but unwanted: the prompt left a gap and the model filled it. Ask "what did I leave unspecified?" and close it with step 2 above. [CCAR 13]
   - Wrong shape or tone: show the shape with an example or a schema; open `references/examples-and-reasoning.md` for examples, `references/structured-output.md` when code parses the output. [CCAR 14, 15]
   - Valid shape, wrong content: add a semantic check (`references/validation-retry.md`, Validation layers) and sharpen the field descriptions (`references/structured-output.md`, Schema design). [CCAR 15]
   - A rule broken now and then: if one miss is costly or irreversible, move it into code (section Code enforces, prompts guide, below); if a miss is cheap, tighten the wording and re-test. [CCAR 05]
   - Quality decays across a long conversation: open `references/multi-turn.md`; when the cause is drift or noise in the window, open `.claude/skills/context-discipline/SKILL.md` section 6 (Fight drift). [CCAR 14]
   Done when the failure is assigned one class and the gap behind it is named. [practice]
2. **Repair at the source.** Fix the prompt before adding a reviewer pass; a repeated semantic failure inside a retry loop is also a signal to change the prompt. Remove or replace a bad example instead of adding instructions around it. [CCAR 14, 15]
   Done when the change is made to the prompt text and the failing input is re-run. [practice]
3. **Retry with evidence.** Re-prompt with the error, the source and the previous output; the cap, the escalation and the reviewer pass are in `references/validation-retry.md`. [CCAR 15]
   Done when a retry path exists that sends the error, the source and the previous output, and ends in a defined escalation. [CCAR 15]

Done for the whole fix when the failing input passes, earlier cases still pass, and the fix is a change to the prompt or to code. [CCAR 05, 15]

## Code enforces, prompts guide

Wording sets how often Claude complies; code decides what can happen. [CCAR 05]

- Put the constraint in code (hook, permission rule, schema, validator, output filter) when a violation is costly or irreversible: money, personal data, destructive actions, safety. Keep the prompt line as the statement of intent. [CCAR 05]
- Leave tone, formatting preferences and ordinary defaults to the prompt; a miss there is cheap to fix. [CCAR 05]
- Use a before-the-action hook as the gate: it blocks by exiting 2 (the message goes back to Claude as the reason); exit-code and event details are in the layer-choice reference below. A PermissionRequest hook denies through a decision object instead. [CCAR 05]
- Match the response to the risk: block non-negotiable limits, warn on advisory ones, escalate the ambiguous cases to a human; calibrate a block that fires on legitimate work. [CCAR 05]

Done when each hard constraint has a code check that holds even if the model ignores the prompt. [CCAR 05]

Open `.claude/skills/agent-orchestration/references/layer-choice.md` when choosing between hook, permission rule and schema, or when wiring hook exit codes. Hook wiring in settings.json: skill `update-config`.
