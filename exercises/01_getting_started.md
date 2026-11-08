# EXERCISE NAME: 01 | First look and first classifier

**OBJECTIVE:** Build the data, see what the model sees, train one classifier and read its confusion matrix.

**SCENARIO:** You have a pile of browser JavaScript and HTML and you want a model that flags the malicious ones.

**DATASET:** `datasets/code_samples.csv` (3,000 synthetic snippets, about 34% malicious).

**ALGORITHM:** Logistic regression on the lexical feature set.

**COMMAND:** From the lab folder with the environment active.

```bash
python scripts/generate_dataset.py
python scripts/inspect_data.py --rows 6
python scripts/run_classification.py --features lexical --algorithm logistic --name exercise01
```

**WHAT THE COMMAND DOES:** The first command writes the datasets. The second prints label balance, families and the numeric features for a few rows. The third extracts ~48 numeric features from each snippet, fits logistic regression on the training split, scores the validation split at threshold 0.5, and writes metrics, predictions and charts.

**EXPECTED OUTPUT (ILLUSTRATIVE, NOT VERIFIED OUTPUT):** format only, your run prints the real numbers. A confusion matrix with non-zero FP and FN, precision around the high 0.8s, recall lower than precision.

**WHAT TO OBSERVE:** `label` is the answer and is never a feature. `family` and `group_id` are never features either. The malicious snippets are not all obvious: some use only ordinary-looking functions. Read the printed confusion matrix and match TP, FP, FN, TN to the printed precision and recall.

**INVESTIGATION:** 1. Which column holds the ground-truth answer? 2. How many benign snippets were flagged, and how many malicious were missed?

```bash
python scripts/inspect_errors.py --experiment exercise01 --type fp
python scripts/inspect_errors.py --experiment exercise01 --type fn
```

**IMPROVEMENT:** Do not change the model yet. Open `outputs/exercise01_predictions.csv` and sort by `positive_probability`. This changes what you look at, not the model.

**COMPARISON:** Open `outputs/exercise01_metrics.json` and `charts/exercise01_confusion.png`. Confirm the counts agree with the metrics.

**LESSON:** Code becomes numeric features, the model learns from the training split only, a threshold turns a probability into an alert, and the confusion matrix is how you read the result. A single accuracy number would hide the misses.
