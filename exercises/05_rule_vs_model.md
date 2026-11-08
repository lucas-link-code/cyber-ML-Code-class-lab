# EXERCISE NAME: 05 | The raw rule versus the trained model

**OBJECTIVE:** Score the regex rules and a trained classifier on the same held-out rows, and see where the model earns its keep.

**SCENARIO:** The rules alert too often on ordinary developer code. You want to know whether a model trained on the same labels raises fewer false alarms while still catching the malicious samples.

**DATASET:** `datasets/code_samples.csv`, validation split.

**ALGORITHM:** Logistic regression on the `all` feature set, compared with the shipped rules.

**COMMAND:**

```bash
python scripts/rule_vs_model.py --features all --algorithm logistic --name rule_vs_model
```

**WHAT THE COMMAND DOES:** Trains the model on the training split, then on the same validation rows it scores both the model and the raw rules. It prints a two-row comparison, counts the malicious rows the rule missed but the model caught, and the benign rows the model false-alarmed on. It writes `outputs/rule_vs_model.csv` and `charts/rule_vs_model.png`.

**EXPECTED OUTPUT (ILLUSTRATIVE, NOT VERIFIED OUTPUT):** format only. Expect the rules to show high recall and low precision with many false positives, and the model to show much higher precision with far fewer false positives at similar recall.

**WHAT TO OBSERVE:** The headline is the false-positive count. The rule fires on every snippet containing a suspicious token; the model has learned that the same token in ordinary context is usually fine. Look at the "regex miss, model catch" examples: these are variants no rule covered.

**INVESTIGATION:** 1. By how much did the model cut the false positives versus the rules? 2. Did it give up any recall to do so, and would that trade be acceptable in your queue?

**IMPROVEMENT:** Try `--algorithm random_forest` or `--features lexical`. Keep the same rules so the baseline is fixed.

**COMPARISON:** Open `charts/rule_vs_model.png` for the precision, recall and F1 bars side by side.

**LESSON:** Rules give high precision on the exact patterns you wrote and tend to over-alert when written broadly. A model trained on the same labels learns context and cuts false alarms. The strongest setup uses both: rules to label and to catch the known, a model to generalise and to filter.
