# EXERCISE NAME: 10 | Your own rules, distribution drift, and a candidate rule

**OBJECTIVE:** Point the labeller at your own rules, test a frozen model on a shifted cohort, and export a candidate YARA rule from what the model learned.

**SCENARIO:** You want to apply this to your own captured code, and you want to know how a model holds up when the traffic changes.

**DATASET:** `datasets/code_samples.csv` and `datasets/code_samples_challenge.csv` (a shifted cohort). Optionally your own rules in `rules/local/`.

**ALGORITHM:** Random forest for the drift test; a character n-gram logistic model for the candidate rule.

**COMMAND:**

```bash
# A) use your own EKFiddle rules as the labeller (optional)
# cp /path/to/CustomRegexes.txt rules/local/
python scripts/ekfiddle_label.py --name my_weak_labels

# B) train on the main cohort, score the shifted cohort without retraining
python scripts/evaluate_shift.py --features all --algorithm random_forest --name shift

# C) turn the strongest learned signals into a candidate YARA rule
python scripts/export_candidate_yara.py --name candidate_js
```

**WHAT THE COMMAND DOES:** A applies your rules (if present in `rules/local/`, which is git-ignored) and scores them as a labeller. B fits on the main training rows and applies the frozen model to the whole challenge cohort, comparing old-cohort validation with the new cohort. C fits a character n-gram model and writes the top malicious-leaning n-grams as a candidate YARA rule to `outputs/candidate_js.yar`.

**EXPECTED OUTPUT (ILLUSTRATIVE, NOT VERIFIED OUTPUT):** format only. Expect the frozen model's false-positive count and precision to move on the challenge cohort, because its benign mix is different. Expect the candidate YARA rule to over-trigger on real code; it is a starting point for a human, not a finished rule.

**WHAT TO OBSERVE:** In B, note that a changed input distribution moves the metrics even though the model is unchanged, and that precision depends on the malicious prevalence in each cohort. In C, read the generated `$sN` strings and judge which are meaningful and which are noise.

**INVESTIGATION:** 1. How did the frozen model's false positives change from the main cohort to the challenge cohort? 2. Which of the candidate YARA strings would you keep, and which would cause false positives on ordinary code?

**IMPROVEMENT:** If you brought your own rules, compare their labeller precision and recall with the shipped `sample_rules.txt`. Keep your rules and any model trained on them local; see `rules/README.md`.

**LESSON:** Models drift when the world does, so freeze-and-test on a new cohort before trusting a deployed model, and read precision against the real base rate. A model can propose detection content, but a human reviews and tightens it before it ever runs.
