# EXERCISE NAME: 02 | Which features: lexical, n-grams, or both

**OBJECTIVE:** See how the choice of features changes detection, with the algorithm held fixed.

**SCENARIO:** You want to know whether hand-chosen numeric signals, raw character patterns, or both work best on this code.

**DATASET:** `datasets/code_samples.csv`, same split in every run.

**ALGORITHM:** Logistic regression throughout; only `--features` changes.

**COMMAND:**

```bash
python scripts/run_classification.py --features lexical --algorithm logistic --name feat_lexical
python scripts/run_classification.py --features ngram --algorithm logistic --name feat_ngram
python scripts/run_classification.py --features all --algorithm logistic --name feat_all
python scripts/compare_models.py feat_lexical feat_ngram feat_all --name compare_features
```

**WHAT THE COMMAND DOES:** Each run turns the same code into a different feature matrix. `lexical` is the numeric indicators. `ngram` is character n-grams via TF-IDF, with the vocabulary learned on the training rows only. `all` concatenates both. The comparison reads the saved metrics, not live models.

**EXPECTED OUTPUT (ILLUSTRATIVE, NOT VERIFIED OUTPUT):** format only. Expect the three rows to differ: n-grams often raise precision, lexical often raises recall, and the ranking metrics (ROC-AUC, PR-AUC) move less than the threshold-dependent ones.

**WHAT TO OBSERVE:** Compare validation F1 and the precision/recall split. Character n-grams latch onto obfuscation substrings; the lexical features summarise structure. Neither is automatically better.

**INVESTIGATION:** 1. Which feature set gave the best PR-AUC? 2. Did adding n-grams to lexical (`all`) actually beat lexical alone, or just match it?

**IMPROVEMENT:** Change only the feature set, keep logistic regression and threshold 0.5. Inspect where `feat_ngram` and `feat_lexical` disagree by comparing their prediction CSVs on `sample_id`.

**COMPARISON:** `python scripts/compare_models.py feat_lexical feat_ngram feat_all --name compare_features`

**LESSON:** Feature engineering decides what the model can separate. More features are not automatically better; measure on held-out rows and check whether the extra features earned their place.
