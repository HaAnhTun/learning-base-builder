# Examples and reasoning

## Contents

- Examples: when, how to design, how to test
- Reasoning: step-by-step prompting versus extended thinking
- Consistency versus variety

## Examples: when

- Zero-shot first. A common task with flexible format needs no examples. Add examples when variance survives instruction improvements, or when the format is novel, domain-specific or structured. [CCAR 14]
- A demonstration beats a description for format: the model mirrors it instead of interpreting words. For a format the model rarely sees, the example becomes the convention. [CCAR 14]
- Use the minimum that reliably anchors the pattern. One example suffices when a single canonical case defines it; add more only when inputs span genuinely different types or edge cases. One strong example beats several weak ones. [CCAR 14]
- Before adding examples to a failing prompt, audit the ones present: inconsistent format or tone across examples produces muddled output. [CCAR 14]

## Examples: design

- Inputs are realistic and representative of production, not simplified stand-ins. [CCAR 14]
- Each output is exactly what you would accept as correct, with no artifact, odd phrasing or extra formatting you would not want reproduced. Review each output as if shipping it. [CCAR 14]
- Make the set diverse: different lengths, topics and phrasing, including one example at the edge of the pattern. Similar examples teach one narrow pattern. [CCAR 14]
- Contamination: unusual phrasing, a single topic area or over-long outputs get reproduced in unrelated outputs. Remove them. [CCAR 14]
- Put the most representative, highest-quality example last, next to the task; later examples carry more weight. When variance is unexplained, reorder before rewriting. [CCAR 14]
- Wrap them in `<examples>` tags. [CCAR 13]
- When inputs vary widely, select examples at run time by similarity to the current input from a maintained pool. [CCAR 14]

## Examples: test

1. Run with examples and without. If zero-shot matches, the examples only add length: drop them. [CCAR 14]
2. Look for one example's artifacts in the outputs: that is contamination. [CCAR 14]
3. Run inputs unlike the examples. Quality dropping there means the set lacks diversity. [CCAR 14]
4. A bad example is removed or replaced; more instructions around it do not fix it. [CCAR 14]

Done when the example set beats zero-shot on varied inputs and reproduces no example's quirks. [CCAR 14]

## Reasoning

- Chain of thought is text in the prompt, not an API setting. Elicit it explicitly ("think step by step", "explain before answering", or reasoning shown in examples) when intermediate steps matter; without the phrase the model gives a direct answer, not visible reasoning. [CCAR 14]
- Freeform when task types vary too much for a template. Labeled scaffold ("identify the constraints, analyse the options, conclude") when tasks share a shape and outputs must be comparable or feed downstream steps. [CCAR 14]
- Use it for multi-step arithmetic, logic and deduction, planning and sequencing, and instructions with several constraints. Skip it for factual lookups, clear-signal classification, short direct answers and creative work; it adds latency and tokens, and rigid steps can stiffen creative output. [CCAR 14]
- Test with and without the phrase on representative inputs. Check that the reasoning supports the conclusion; plausible steps that reach wrong answers mean the technique does not fit the task. [CCAR 14]
- Keep prompt-level reasoning and extended thinking as separate choices. Extended thinking is an API feature in which the model reasons internally; its tokens cost money and context, and client code must handle its separate blocks. Try prompt-level reasoning first; move to extended thinking for genuinely complex, exploratory or high-stakes problems where that falls short. Check the current API docs for the model in use: reasoning setting and sampling parameters. [CCAR 14]

## Consistency versus variety

Express the wanted behaviour in the prompt rather than through sampling parameters: ask plainly for consistent output and constrain the format for extraction and classification; ask for variety in the instructions for brainstorming and creative work. Validate the behaviour against real outputs. [CCAR 14]
