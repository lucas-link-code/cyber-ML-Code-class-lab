# EXERCISE NAME: 03 | Same features, different algorithms

**OBJECTIVE:** Compare algorithm families on identical features and splits, and notice the training/validation gap.

**SCENARIO:** A team asks whether a simple linear model is enough, or whether trees do better here.

**DATASET:** `datasets/code_samples.csv`, lexical features in every run.

**ALGORITHM:** Logistic regression, decision tree, random forest, gradient boosting, naive Bayes.

**COMMAND:**

```bash
python scripts/run_classification.py --algorithm logistic --features lexical --name alg_logistic
python scripts/run_classification.py --algorithm tree --features lexical --name alg_tree
python scripts/run_classification.py --algorithm random_forest --features lexical --name alg_forest
python scripts/run_classification.py --algorithm gradient_boosting --features lexical --name alg_boost
python scripts/run_classification.py --algorithm naive_bayes --features lexical --name alg_nb
python scripts/compare_models.py alg_logistic alg_tree alg_forest alg_boost alg_nb --name compare_algorithms
```

**WHAT THE COMMAND DOES:** Fits five algorithms on the same feature matrix and split. The difference is what function each one learns, not the data.

**EXPECTED OUTPUT (ILLUSTRATIVE, NOT VERIFIED OUTPUT):** format only. Expect close validation F1 across several models, but very different `train_f1`: a single tree and an unrestricted forest can sit near 1.0 on training while validation is far lower.

**WHAT TO OBSERVE:** Look at the gap between `train_f1` and validation `f1` for each model. A large gap is an overfitting warning, explored in Exercise 09. Naive Bayes may trade precision for recall because of its independence assumption.

**INVESTIGATION:** 1. Which model had the best validation F1? 2. Which had the widest train-to-validation gap, and does the best training score mean the best validation score?

**IMPROVEMENT:** Change only the algorithm. Keep features and threshold fixed so the comparison is fair.

**COMPARISON:** `python scripts/compare_models.py alg_logistic alg_tree alg_forest alg_boost alg_nb --name compare_algorithms`

**LESSON:** Different model families draw different boundaries from the same inputs. Choose on held-out performance and the error profile you can live with, not on training score or on which algorithm sounds strongest.
