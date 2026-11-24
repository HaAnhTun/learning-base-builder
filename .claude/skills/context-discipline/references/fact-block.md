# Fact block

The in-session working copy; STATE.md and DECISIONS.md (cross-session) belong to `project-state`, which also owns the secret rule: secrets never go in a block, record where they live. Placement and use: SKILL.md step 4.

## What to capture [CCAR 16]

Capture in explicit categories, since "extract the important facts" leaves the choice to the model:

- identifiers: ids, ticket numbers, versions, paths
- numeric limits: budgets, thresholds, caps, retries
- named entities: people, tools, datasets, services
- decisions, including rules the user stated

Symptoms that a fact was lost to summarising: a stated rule silently ignored (constraint amnesia), a plausible wrong name or number substituted (entity confusion), a settled choice reopened (decision drift).

## Format

Typed `key: value` lines under one heading. Write `none` for a category where nothing was stated, which shows the extraction ran.

```
## Facts
goal: <one line>
ids: <name>=<value>
limits: <name>=<value> (stated 2026-11-24, or at milestone X)
entities: <name>: <role>
decisions: <decision> because <reason>
```

## Update strategy

- Mutable facts: the newer value replaces the old.
- Facts whose history matters: append, keep both.
- Re-check high-stakes values against the source message to catch a fact captured wrongly.

## Size

- At most 30 lines and 5 entries per category; prioritise inside the cap.
- Age out entries nothing has referenced since the last milestone.
- Merge entries about one entity under one key.
- Tier it: permanent (session goal) versus ephemeral (prunable freely).
