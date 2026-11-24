# Validation and retry after a failed output

For a tool, API or environment failure (classification, backoff, retry-after, silent failures, fallbacks, human pause), open `.claude/skills/agent-orchestration/references/error-handling.md`. To choose between hook, schema and permission rule, open `.claude/skills/agent-orchestration/references/layer-choice.md`; the rule in this skill is SKILL.md section "Code enforces, prompts guide".

## Contents

- Validation layers
- The loop
- Reviewer pass

## Validation layers

Use all three; a valid shape can still hold a wrong value. [CCAR 15]

1. Schema: fields present, types right, enums in set. Deterministic and cheap. [CCAR 15]
2. Format and business rules: dates in range, identifiers that exist, numbers plausible. Needs codified domain logic. [CCAR 15]
3. Semantic: values agree with the source, related fields do not contradict, the content means what it should. [CCAR 15]

Add at least one semantic check; a simple rule (mentions a required topic, score in a plausible range) is enough to start. [CCAR 15]

## The loop

Extract, validate, re-prompt on failure, validate again; validation at the end needs a re-prompt path. [CCAR 15]

Re-prompt contents:
- the specific validation error and the expected value; [CCAR 15]
- the original source text, so the model re-extracts from evidence and does not repair from memory; [CCAR 15]
- the previous output; [CCAR 15]
- an instruction to correct only the failing fields (full regeneration can break fields that were right). [CCAR 15]

Budget and exit:
- Cap at 2 to 3 attempts; a case that fails three times is a prompt design problem. Log what failed and why on each attempt. [CCAR 15]
- When the cap runs out, escalate explicitly (structured error, human review queue, safe default) so the failure is visible. [CCAR 15]
- Structurally valid but semantically wrong output on repeated attempts is design feedback: change the prompt. A reasoning error repeats on identical input, so change the context, scope or instruction before re-sending. [CCAR 05, 15]
- If attempts keep failing the same check, vary the framing slightly; in long chains anchor each retry to the source and the original goal to avoid semantic drift. [CCAR 15]
- Use a loop when errors have downstream consequences or run unattended at scale; light validation plus human review fits interactive use. [CCAR 15]

Done when failure leads to a specific re-prompt, a capped number of attempts, and a defined escalation. [CCAR 15]

## Reviewer pass

A second call that only evaluates the first output against a checklist. [CCAR 15]

1. Checklist items have clear pass/fail conditions across three categories: completeness, accuracy against the source, tone and format. [CCAR 15]
2. The reviewer returns, per failed check: which one, why, and a suggested correction. [CCAR 15]
3. A revision call takes the original output plus the critique and addresses each point; run the same checklist again. [CCAR 15]

- Use an independent reviewer (often a stronger model) when stakes are high or the domain is regulated; a self-review is cheap and generous to its own output. [CCAR 15]
- Worth it for high-stakes or long-form output; skip it for drafts, brainstorming, high-volume low-cost output, or where a human already reviews. [CCAR 15]
- Fix the primary prompt first; a reviewer controls the variance that remains. [CCAR 15]

Done when the checklist items each have a pass/fail condition and the revision call re-runs them. [CCAR 15]
