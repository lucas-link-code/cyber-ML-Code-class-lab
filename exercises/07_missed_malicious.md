# EXERCISE NAME: 07 | The malicious code it misses

**OBJECTIVE:** Read the false negatives, see why stealthy samples slip through, and lower the threshold to recover recall.

**SCENARIO:** Some malicious snippets avoid the obvious markers. You need to catch more of them and understand the cost.

**DATASET:** `datasets/code_samples.csv`, validation split.

**ALGORITHM:** Logistic regression, lexical features; only the threshold changes.

**COMMAND:**

```bash
python scripts/run_classification.py --features lexical --algorithm logistic --name fn_base
python scripts/inspect_errors.py --experiment fn_base --type fn --rows 15
python scripts/run_classification.py --features lexical --algorithm logistic --threshold 0.30 --name fn_loose
```

**WHAT THE COMMAND DOES:** The baseline run at 0.5, then a list of the malicious snippets it missed, then the same model alerting from probability 0.30 upward.

**EXPECTED OUTPUT (ILLUSTRATIVE, NOT VERIFIED OUTPUT):** format only. Expect the misses to be dominated by the `M_stealth_dualonly` family, malicious samples built from only dual-use or ordinary fragments. Lowering the threshold recovers some, at the cost of more false positives.

**WHAT TO OBSERVE:** The missed samples look benign by construction: they carry little or no obfuscation and no strong sink. A lower cutoff catches more of them but also turns borderline benign code into alerts. ROC-AUC does not change; you are moving the operating point, not improving the ranking.

**INVESTIGATION:** 1. Which family accounts for most misses? 2. At threshold 0.30, how many more malicious samples do you catch, and how many extra false positives did it cost?

**IMPROVEMENT:** Change only the threshold. For a real improvement on these misses you would need better features or more labelled stealth examples, not just a lower cutoff.

**COMPARISON:** `python scripts/compare_models.py fn_base fn_loose --name compare_fn`

**LESSON:** Recall is the share of malicious code caught. A lower threshold trades false negatives for false positives on the same scores. When a whole family hides in ordinary-looking code, the fix is usually more signal, not a different cutoff.
