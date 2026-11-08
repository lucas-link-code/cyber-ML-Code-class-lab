# EXERCISE NAME: 08 | How a leaky split flatters the score

**OBJECTIVE:** Show that splitting by row instead of by near-duplicate cluster inflates the validation score.

**SCENARIO:** Your corpus contains near-duplicate snippets, the same code with tiny edits. If a copy is in training and its twin is in validation, the model looks better than it is.

**DATASET:** `datasets/code_samples.csv`. About 18% of samples belong to a near-duplicate cluster sharing a `group_id`.

**ALGORITHM:** Random forest, lexical features; only `--split` changes.

**COMMAND:**

```bash
python scripts/run_classification.py --algorithm random_forest --features lexical --split group --name split_group
python scripts/run_classification.py --algorithm random_forest --features lexical --split random --name split_random
python scripts/compare_models.py split_group split_random --name compare_split
```

**WHAT THE COMMAND DOES:** `group` keeps a whole duplicate cluster on one side of the split, which is honest. `random` splits by row, so a snippet and its near-twin can land on opposite sides, which leaks.

**EXPECTED OUTPUT (ILLUSTRATIVE, NOT VERIFIED OUTPUT):** format only. Expect the random split to report higher F1 and higher ROC-AUC than the grouped split, even though it is the same model and the same data.

**WHAT TO OBSERVE:** The random split is not measuring generalisation to new code. It is partly measuring the model's ability to recognise a twin it already saw. The grouped number is the honest one.

**INVESTIGATION:** 1. How much higher is the random-split F1 and ROC-AUC? 2. Why does the gap exist even though both runs use the same forest and the same rows overall?

**IMPROVEMENT:** Change only the split. The grouped split is the default everywhere else in the lab for this reason.

**COMPARISON:** `python scripts/compare_models.py split_group split_random --name compare_split`

**LESSON:** Duplicates and near-duplicates across a split leak information and inflate the score. Group by whatever makes samples near-identical, a cluster, a campaign, a host, so the evaluation measures new code, not memory.
