# Testing prompts

Open when comparing prompt versions across a saved suite. The loop is dataset, run, grade, compare against the previous version's baseline. [CCAR 15]

Done when the comparison is written down and the change is promoted or reverted on that evidence. [CCAR 15] A small saved file of inputs, each with the property its output must have, is enough to start. [practice]

- Cover typical, edge (unusual, ambiguous, at the limit of scope) and adversarial inputs, with enough cases that one failure does not swing the pass rate. [CCAR 15]
- Prefer code-based grading when correctness is a rule (exact match, regex, schema validation, assertions). Use model-based grading for subjective output, giving the grader the input, the output and a specific rubric. [CCAR 15]
- Calibrate a model grader: have humans label a sample, run the grader on it, track the agreement rate, and adjust the rubric where they disagree. Version the grading prompt and test it like any prompt. [CCAR 15]
- Track regression rate (previously passing, now failing; zero or falling). [CCAR 15]
- Run the full suite on every prompt change, however small, and also on a regular schedule, since model behaviour can shift under an unchanged prompt. [CCAR 15]
