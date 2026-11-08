# Cyber ML Code Classifier Lab

**Train a model classifier to identify malicious functions, tell malicious HTML/JavaScript code from benign scripts.**

Python 3.11+ | offline after install | no credentials, no network, no live malware included in this repository | deterministic synthetic data only

This is a runnable, command line lab for a security analyst who wants to learn
machine learning on a real detection problem: labelling JavaScript and HTML as
malicious or benign. It is a training course and a working proof of concept at
the same time. You do not need Jupyter, an IDE, or any experience writing Python
models. You run commands, read the output, change one thing, and run again.

It is the code classification sibling of the Cyber ML Lab. If you have used that
one, this is the same idea but for code classification: inspect the datasets, train a model, read the confusion matrix,
investigate the errors, change one variable, compare.

## The idea behind this lab

A detection rule, such as an EKFiddle regex, either matches or it does not. It is
exact. It catches the patterns you wrote down and nothing else, and it has no
sense of context, so a broad rule tends to over-alert on ordinary code that
happens to use a suspicious-looking function.

A classifier works differently. You show it many examples labelled malicious or
benign, it measures dozens of properties of each one, entropy, encoding markers,
how often decode and execution functions appear, and it learns the *shape* of
suspicious code. It can then flag variants nobody wrote a rule for, and it can
learn that `eval` inside an ordinary config parse is not the same as `eval` of a
decoded blob.

This lab shows the whole path. You use rules as a cheap way to label data, you
train classifiers on that data, and you measure where the model beats the raw
rules and where it does not. The rules become training signal, not the final
detector.

## 1. Install on macOS or Linux

Run these from a terminal, from wherever you unpacked or cloned the lab, then
`cd` into the folder.

```bash
cd cyber_ml_code_class_lab
python3 --version          # expect 3.11 or newer
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 1b. Install on Windows PowerShell

```powershell
Set-Location cyber_ml_code_class_lab
py -3 --version
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, skip it and call the environment's Python
directly, for example `.\.venv\Scripts\python.exe scripts\inspect_data.py`.

Internet is needed only for that one `pip install`. Everything after it runs
offline.

## 2. First three commands

With the environment active, run these in order. They are the whole of Exercise
01.

```bash
python scripts/generate_dataset.py
python scripts/inspect_data.py --rows 6
python scripts/run_classification.py --features lexical --algorithm logistic --name first_run
```

- The first command writes the two synthetic datasets into `datasets/`.
- The second prints the label balance, the template families and the numeric
  features for a few rows, so you can see what the model will see.
- The third turns the code into features, fits logistic regression on the
  training split, scores the validation split, and prints a confusion matrix and
  the metrics. It writes `outputs/first_run_metrics.json`,
  `outputs/first_run_predictions.csv` and three charts under `charts/`.

Then look at the mistakes it made:

```bash
python scripts/inspect_errors.py --experiment first_run --type fp
python scripts/inspect_errors.py --experiment first_run --type fn
```

**Stop here** until you can answer: how many benign snippets were flagged
(false positives), and how many malicious ones were missed (false negatives)?
Which is worse in your setting?

## 3. The workflow you repeat

```
Code (synthetic corpus, or your own captured JS/HTML)
   |  rules as a labelling function  (ekfiddle_label.py)   [optional]
Labelled code: malicious (1) or benign (0)
   |  feature extraction  (lexical numeric features, or char n-grams)
Feature matrix
   |  split by near-duplicate cluster: training / validation / final test
Fit the classifier on training only
   |  predict probabilities on validation -> threshold -> confusion matrix
Investigate the false positives and false negatives
   |  change ONE thing: features, algorithm, threshold, split, depth
Compare on the same validation rows, then confirm once on the final test
```

Two things make this honest, and both have an exercise of their own:

- **Grouped split.** Some snippets come in near-duplicate clusters sharing a
  `group_id`. The default split keeps a whole cluster on one side, so the model
  cannot pass by memorising a twin it already saw. Exercise 08 shows how much the
  score inflates if you split by row instead.
- **Rules are a labeller, not the model.** Exercise 04 measures how good the
  regex is *as a way to label data*, and Exercise 05 trains a model on those
  labels and shows where it improves on the rule.

## 4. The datasets

Two files, both written by `generate_dataset.py`, both fully synthetic and
inert (reserved `.example` domains, no-op payloads, a visible fixture banner).

| File | Rows | Purpose |
| --- | ---: | --- |
| `datasets/code_samples.csv` | 3,000 | Main corpus. ~34% malicious. |
| `datasets/code_samples_challenge.csv` | 1,200 | A shifted cohort with more benign minified `_0x` code, for the drift exercise. |

Columns and the full feature list are in `DATA_DICTIONARY.md`. The short version:
`label` is the answer (1 malicious, 0 benign), `code` is the snippet, and
`sample_id`, `family`, `group_id` are never fed to the model.

The label is drawn first and the code is assembled from fragments that overlap
between the classes, so the problem is genuinely hard: a stealthy malicious
sample can omit every obvious marker, and ordinary benign code can use a
suspicious-looking function for a good reason. That overlap is why there are
false positives and false negatives to investigate, and why moving the threshold
actually changes something.

## 5. The algorithms

`run_classification.py` trains any of these on the same features and split:

| Choice | What it learns | Note |
| --- | --- | --- |
| `logistic` | One weight per feature, turned into a probability | Fast, readable weights, a good baseline |
| `tree` | A sequence of feature thresholds | Easy to overfit on its own |
| `random_forest` | A vote across many trees | Strong, but watch the train/validation gap |
| `gradient_boosting` | Trees built in sequence to fix earlier errors | Strong on tabular features |
| `naive_bayes` | A probability model per feature | Simple probabilistic baseline |

Feature sets with `--features`:

- `lexical` (default): the numeric features, entropy, encoding markers, sink
  token counts. Readable and fast.
- `ngram`: character n-grams of the raw code via TF-IDF, learned on training
  only. Good at catching obfuscation substrings.
- `all`: both together.

## 6. Learning roadmap

The exercises are in `exercises/`, numbered 01 to 10. Each one is a single,
contained step: a command to run, what to look for, one question, one controlled
change, and a short lesson. Worked answers with the reference numbers are in
`solutions/exercise_solutions.md`. Try an exercise before opening the solution.

| Level | Exercises | Focus |
| --- | --- | --- |
| Run and observe | 01, 02, 03 | First model, feature sets, algorithm families |
| Rules into data | 04, 05 | Rules as a labeller; the model versus the raw rule |
| Read the errors | 06, 07 | False positives, false negatives, the decision threshold |
| Do it honestly | 08, 09 | Near-duplicate leakage, overfitting and model capacity |
| Make it yours | 10 | Your own rules, distribution drift, a candidate YARA rule |

Suggested order is simply 01 through 10.

## 7. Command reference

```bash
# Build the synthetic datasets (deterministic)
python scripts/generate_dataset.py

# Look at the data before modelling
python scripts/inspect_data.py --rows 8

# Turn rules into weak labels and score the rules as a labeller
python scripts/ekfiddle_label.py --name weak_labels

# Train a classifier (pick features, algorithm, threshold, split)
python scripts/run_classification.py --features lexical --algorithm logistic --name run_a
python scripts/run_classification.py --features ngram --algorithm random_forest --name run_b
python scripts/run_classification.py --features lexical --algorithm random_forest --split random --name leaky

# Read the actual mistakes from a saved run
python scripts/inspect_errors.py --experiment run_a --type fp
python scripts/inspect_errors.py --experiment run_a --type fn

# Compare saved runs on the same split
python scripts/compare_models.py run_a run_b --name compare_ab

# The headline: raw rules versus the trained model, same validation rows
python scripts/rule_vs_model.py --features all --algorithm logistic --name rule_vs_model

# Train on the main cohort, score the shifted challenge cohort without retraining
python scripts/evaluate_shift.py --features all --algorithm random_forest --name shift

# Turn the strongest learned signals into a CANDIDATE YARA rule (review before use)
python scripts/export_candidate_yara.py --name candidate_js

# Structural checks, and the full command smoke test
python scripts/verify_lab.py
python tests/run_smoke_tests.py
```

Add `--help` to any script to see its options.

## 8. What the metrics mean

Class 1 is malicious (an alert); class 0 is benign.

- **TP / FP / FN / TN**: correct alert, false alarm, missed malicious, correct ignore.
- **Precision** = TP / (TP + FP): of what you flagged, how much was really malicious. Alert quality.
- **Recall** = TP / (TP + FN): of all malicious code, how much you caught. Coverage.
- **FPR** = FP / (FP + TN): of benign code, how much raised a false alarm.
- **F1**: the balance of precision and recall.
- **ROC-AUC** and **PR-AUC (average precision)**: ranking quality across all
  thresholds. They do not change when you only move the decision threshold.
- **train_f1**: F1 on the training rows. If it is near 1.0 while validation F1 is
  much lower, the model has memorised the training data (see Exercise 09).

## 9. Using your own rules and samples

The lab is self-contained with the shipped synthetic corpus and the generic
`rules/sample_rules.txt`. To use your own EKFiddle rules, drop a CustomRegexes
file into `rules/local/`, which is git-ignored, and the labeller picks it up
automatically. See `rules/README.md`.

Keep private rules and any real captured samples out of anything you publish.
The exercises and any model you intend to share use only the synthetic corpus,
so a shared model's training data lives entirely in this repository. If you train
on private rules, keep that model local.

## 10. Safety

Nothing here is live malware. Every sample is synthetic and inert: reserved
`.example` domains, no-op payloads, no sample that does anything if run. The
scripts only read and parse code as text; they never download, install or
execute a sample. If you later point the labeller at your own captured code,
treat it as untrusted and handle it only on an isolated analysis machine.
`SECURITY.md` has the details.

**These synthetic scores are a teaching illustration, not a production detection
rate. Do not treat any number here as expected real world performance.**
