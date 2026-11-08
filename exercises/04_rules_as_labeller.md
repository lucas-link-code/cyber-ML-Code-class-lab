# EXERCISE NAME: 04 | Your rules as a labelling function

**OBJECTIVE:** Apply detection rules to unlabelled code to produce training labels, and measure how good the rules are at that job.

**SCENARIO:** You have EKFiddle regexes that flag suspicious browser code. Before training anything, you want to know how well they separate malicious from benign on their own.

**DATASET:** `datasets/code_samples.csv`. The shipped rules are `rules/sample_rules.txt` (generic, public patterns).

**ALGORITHM:** None. This is pattern matching, the step that creates labels.

**COMMAND:**

```bash
python scripts/ekfiddle_label.py --name weak_labels
```

**WHAT THE COMMAND DOES:** Parses the `SourceCode` rules, applies each to every snippet, and writes `outputs/weak_labels.csv` with a `weak_label` (1 if any rule fired), the `matched_rules`, and a per-sample hit count. It prints per-rule coverage. Because this synthetic set also carries a true `label`, it scores the rules as a labeller: precision and recall against the truth.

**EXPECTED OUTPUT (ILLUSTRATIVE, NOT VERIFIED OUTPUT):** format only. Expect high recall and lower precision: broad single-token rules catch most malicious code but also fire on benign code that uses the same tokens for a good reason.

**WHAT TO OBSERVE:** The per-rule coverage shows which rules do the work. The precision figure is the false-alarm problem in numbers: of everything the rules flag, how much is really malicious. The false positives here are ordinary code using `eval`, `atob` or `new Function` legitimately.

**INVESTIGATION:** 1. Which single rule flagged the most samples? 2. Are the rules missing malicious samples (false negatives), over-flagging benign ones (false positives), or both?

**IMPROVEMENT:** Open `outputs/weak_labels.csv` and look at rows where `weak_label` is 1 but `label` is 0. These are the benign snippets the rules over-trigger on. Note the families (`B_dual`, `B_suspicious`).

**COMPARISON:** Keep this file. Exercise 05 trains a model and compares it against exactly these rules.

**LESSON:** A regex is a cheap labelling function, not a finished detector. Measuring its precision and recall as a labeller tells you how noisy your training labels are and how much room a model has to improve on them.
