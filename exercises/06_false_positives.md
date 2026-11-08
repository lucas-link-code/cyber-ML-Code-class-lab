# EXERCISE NAME: 06 | Why benign code gets flagged

**OBJECTIVE:** Read the model's false positives, understand why they happen, and raise the threshold to cut them.

**SCENARIO:** Developers complain that ordinary scripts are being flagged. You need fewer false alarms without blinding the detector.

**DATASET:** `datasets/code_samples.csv`, validation split.

**ALGORITHM:** Logistic regression, lexical features; only the threshold changes.

**COMMAND:**

```bash
python scripts/run_classification.py --features lexical --algorithm logistic --name fp_base
python scripts/inspect_errors.py --experiment fp_base --type fp --rows 15
python scripts/run_classification.py --features lexical --algorithm logistic --threshold 0.70 --name fp_tight
```

**WHAT THE COMMAND DOES:** The first run is the baseline at threshold 0.5. The inspector prints the benign snippets it flagged. The third run keeps the same model but only alerts when the probability is at least 0.70.

**EXPECTED OUTPUT (ILLUSTRATIVE, NOT VERIFIED OUTPUT):** format only. Expect most false positives to be the `B_suspicious` family, benign code that used a suspicious-looking fragment. Raising the threshold cuts false positives and also removes some true positives, so recall drops.

**WHAT TO OBSERVE:** Read the actual flagged snippets. They legitimately use tokens like `createElement`, `eval` on a config, or a submit handler. The model is not wrong to be suspicious; the cost is context it cannot see. Note that ROC-AUC and PR-AUC do not move when only the threshold changes.

**INVESTIGATION:** 1. Which family dominates the false positives? 2. When you raise the threshold to 0.70, how many false positives disappear, and how many malicious samples do you now miss?

**IMPROVEMENT:** Change only the threshold. Then compare the two runs.

**COMPARISON:** `python scripts/compare_models.py fp_base fp_tight --name compare_fp`

**LESSON:** Precision is about both true and false positives. A higher threshold usually raises precision and lowers recall on the same scores. It does not improve the model's ranking; it only moves the line between alert and no-alert.
