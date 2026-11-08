# Worked solutions and reference numbers

> Spoilers. Work through each exercise in `exercises/` first.

The numbers below are from a reference run with the shipped seeds, on the
versions listed in `VERIFICATION.md`. The data and models are deterministic, so
your figures should match, give or take the last decimal across library
versions. Validation split is 596 rows for the main cohort.

## How to read this

Each section gives the point of the exercise, the observed result, and the
conclusion it supports. Run the command, look at your own output, then compare.

---

## 01. First look and first classifier

Logistic regression, lexical features, validation at threshold 0.5:

| metric | value |
| --- | ---: |
| precision | 0.897 |
| recall | 0.838 |
| F1 | 0.867 |
| FPR | 0.060 |
| ROC-AUC | 0.945 |
| train F1 | 0.892 |
| TP / FP / FN / TN | 192 / 22 / 37 / 345 |

Precision above recall means the alerts are fairly reliable but 37 of 229
malicious snippets are missed. The train-to-validation F1 gap is small
(0.892 vs 0.867), so this model is not memorising. The missed samples are mostly
the `M_stealth_dualonly` family; the false positives are mostly `B_suspicious`.

---

## 02. Feature sets

Logistic regression, threshold 0.5, same split:

| features | precision | recall | F1 | ROC-AUC | PR-AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| lexical | 0.897 | 0.838 | 0.867 | 0.945 | 0.932 |
| ngram | 0.928 | 0.790 | 0.854 | 0.951 | 0.940 |
| all | 0.906 | 0.838 | 0.871 | 0.947 | 0.935 |

Character n-grams raise precision and drop recall; they are good at catching
obfuscation substrings but miss the stealth family that has no distinctive
characters. Combining both (`all`) edges out lexical alone on F1 but only
slightly. More features are not automatically better; here the gain from adding
n-grams to lexical is marginal.

---

## 03. Algorithms

Lexical features, threshold 0.5:

| algorithm | F1 | train F1 | precision | recall | note |
| --- | ---: | ---: | ---: | ---: | --- |
| logistic | 0.867 | 0.892 | 0.897 | 0.838 | small gap |
| tree | 0.815 | 0.998 | 0.856 | 0.777 | large gap, overfits |
| random_forest | 0.864 | 0.998 | 0.897 | 0.834 | large gap |
| gradient_boosting | 0.862 | 0.984 | 0.893 | 0.834 | moderate gap |
| naive_bayes | 0.839 | 0.811 | 0.824 | 0.856 | higher recall, FPR 0.114 |

The strongest validation F1 (logistic) is not the strongest training F1 (tree
and forest sit at 0.998 on training). The widest train-to-validation gap is the
single tree and the unrestricted forest. Naive Bayes trades precision for recall
because of its independence assumption, which is wrong for correlated code
features.

---

## 04. Rules as a labelling function

Shipped `sample_rules.txt` applied to the 3,000-row corpus:

- Flagged 2,316 of 3,000 (77.2%).
- As a labeller against the true label: precision 0.441, recall 0.954, F1 0.604,
  false positives 1,294, false negatives 49.
- The busiest rule is `Eval_Or_Function_Constructor`.

The rules catch almost everything malicious (recall 0.95) but flag a huge number
of benign snippets (precision 0.44), because benign `B_dual` code legitimately
uses `eval`, `atob` and `new Function`. This is the realistic failure of a broad
pattern set: high coverage, heavy over-alerting. The false positives are the
training-label noise a classifier has to see past.

---

## 05. Rule versus model

Same validation rows, model = logistic on `all` features:

| detector | precision | recall | F1 | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: |
| regex rules | 0.478 | 0.956 | 0.638 | 239 | 10 |
| model (logistic/all) | 0.906 | 0.838 | 0.871 | 20 | 37 |

The model cuts false positives from 239 to 20 on these rows, a roughly twelve-fold
reduction, while keeping strong recall. It gives up a little recall (37 misses
versus 10) because it learned to be sceptical of lone suspicious tokens. The
"regex miss, model catch" count is small here precisely because the broad rules
already have near-perfect recall; the model's contribution is precision, not
coverage. The practical answer is to run both: rules to catch the known and to
label, the model to filter the false alarms.

---

## 06. False positives

Logistic lexical. Threshold 0.5 gives FP 22, FN 37. Threshold 0.70 gives:

| threshold | precision | recall | FP | FN |
| --- | ---: | ---: | ---: | ---: |
| 0.50 | 0.897 | 0.838 | 22 | 37 |
| 0.70 | 0.928 | 0.790 | 14 | 48 |

Raising the threshold removes 8 false positives and adds 11 misses. ROC-AUC
stays at 0.945 because the ranking did not change, only the cut. The false
positives are the `B_suspicious` family: benign code that used `createElement`,
`eval` on a config, or a submit handler. The model is reacting to real tokens it
cannot place in context.

---

## 07. Missed malicious

Logistic lexical. Threshold 0.5 gives FN 37. Threshold 0.30 gives:

| threshold | precision | recall | FP | FN |
| --- | ---: | ---: | ---: | ---: |
| 0.50 | 0.897 | 0.838 | 22 | 37 |
| 0.30 | 0.873 | 0.869 | 29 | 30 |

Lowering the cut recovers 7 malicious samples and adds 7 false positives.
ROC-AUC is unchanged. The misses are dominated by `M_stealth_dualonly`, malicious
code assembled from only dual-use or ordinary fragments, so it has little
obfuscation and no strong sink. A lower threshold helps a little; a real fix
needs more signal or more labelled stealth examples, not just a cutoff change.

---

## 08. Leaky split

Random forest, lexical features:

| split | F1 | ROC-AUC | PR-AUC |
| --- | ---: | ---: | ---: |
| group (honest) | 0.864 | 0.944 | 0.899 |
| random (leaky) | 0.908 | 0.981 | 0.973 |

Splitting by row instead of by duplicate cluster raises F1 by about 0.044 and
ROC-AUC by about 0.037, with the same model and data. The random split lets a
near-duplicate sit in training and its twin in validation, so part of the score
is recognition of a seen sample, not generalisation. The grouped number is the
honest one, which is why it is the default everywhere else.

---

## 09. Overfitting

Random forest, `all` features:

| model | train F1 | validation F1 |
| --- | ---: | ---: |
| unrestricted depth | 0.998 | 0.827 |
| max depth 6 | 0.956 | 0.830 |

The unrestricted forest is almost perfect on training and far lower on
validation, a gap of about 0.17. Limiting depth to 6 drops the training score
and closes most of the gap, with validation steady or very slightly better. The
training score alone told you nothing useful; the gap is the signal. The goal is
the level of held-out performance, not the smallest possible gap.

---

## 10. Your rules, drift, candidate rule

Frozen model (random forest, `all`) trained on the main training rows:

| cohort | precision | recall | F1 | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: |
| main validation | 0.863 | 0.795 | 0.827 | 29 | 47 |
| challenge cohort | 0.885 | 0.819 | 0.851 | 41 | 70 |

The frozen model holds up on the shifted cohort, with precision roughly steady
and more alerts in absolute terms because the cohort is larger. The challenge
cohort's benign mix has more `_0x` minified code, the pattern the regex rules
over-trigger on, yet the model is not fooled by it the way the raw rules are.
Read precision against each cohort's own malicious prevalence, not the training
mix.

The candidate YARA rule from `export_candidate_yara.py` lists the strongest
malicious-leaning n-grams as strings. Some are meaningful (`atob`, `eval(`,
hex-escape fragments); others are noise from the synthetic templates. It is a
drafting aid for an analyst, and it will over-trigger on real code until a human
tightens it.

---

**The point of the lab:** rules and models are not rivals. Rules label data
cheaply and catch the known with high precision when written tightly. A model
learns context from those labels, cuts false alarms, and generalises to variants.
Measure both honestly, on grouped splits, against the real base rate, and never
treat a synthetic score as a deployment estimate.
