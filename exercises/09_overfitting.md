# EXERCISE NAME: 09 | Training score is not generalisation

**OBJECTIVE:** See an overfitting gap and close it with one capacity parameter.

**SCENARIO:** A forest scores almost perfectly on code it has seen and much worse on new code. You need to tell memorisation from learning.

**DATASET:** `datasets/code_samples.csv`, `all` features.

**ALGORITHM:** Random forest; only `--max-depth` changes.

**COMMAND:**

```bash
python scripts/run_classification.py --algorithm random_forest --features all --name rf_unrestricted
python scripts/run_classification.py --algorithm random_forest --features all --max-depth 6 --name rf_depth6
python scripts/compare_models.py rf_unrestricted rf_depth6 --name compare_overfitting
```

**WHAT THE COMMAND DOES:** The first grows unrestricted trees. The second limits how deep each tree can go, which reduces capacity during fitting. Both report `train_f1` next to validation `f1`.

**EXPECTED OUTPUT (ILLUSTRATIVE, NOT VERIFIED OUTPUT):** format only. Expect the unrestricted forest to sit near 1.0 on training with a much lower validation F1. Limiting depth lowers the training score and closes most of the gap, with validation roughly steady or slightly better.

**WHAT TO OBSERVE:** Compare `train_f1` to validation `f1` for each run. A near-perfect training score with a large gap is the warning sign. Depth limiting changes the model's capacity, not the threshold.

**INVESTIGATION:** 1. How large is the train-to-validation gap for the unrestricted forest? 2. Does limiting depth help validation, or only shrink the gap?

**IMPROVEMENT:** Change only `--max-depth`. Try 4 and 10 as well. Keep the number of trees fixed so you are testing one thing.

**COMPARISON:** `python scripts/compare_models.py rf_unrestricted rf_depth6 --name compare_overfitting`

**LESSON:** A high training score alone proves nothing. Judge a model on held-out code and watch the gap. Reducing capacity can help generalisation, but the goal is the level of held-out performance, not the smallest gap.
