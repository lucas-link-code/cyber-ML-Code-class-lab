# Verification and reproducibility

The lab was generated and command-line tested in a clean environment on the
synthetic datasets. The figures quoted in `solutions/exercise_solutions.md` are
actual recorded validation outputs, not illustrative numbers. Exact decimals can
differ slightly between library versions.

- Python: `3.13.18`
- numpy: `2.5.3`
- pandas: `3.0.5`
- scikit-learn: `1.9.1`
- matplotlib: `3.11.2`
- Dataset generator base seed: `20261108`
- Split seed: `42`; near-duplicate clusters grouped by `group_id`.

The lab targets Python 3.11+ and the ranges in `requirements.txt`. The numbers
above are the environment used to record the reference results.

## Reference results (validation split, main cohort, 596 rows)

| Experiment | precision | recall | F1 | train F1 |
| --- | ---: | ---: | ---: | ---: |
| logistic, lexical, 0.50 | 0.897 | 0.838 | 0.867 | 0.892 |
| logistic, ngram, 0.50 | 0.928 | 0.790 | 0.854 | 0.879 |
| logistic, all, 0.50 | 0.906 | 0.838 | 0.871 | 0.894 |
| random_forest, lexical, group | 0.897 | 0.834 | 0.864 | 0.998 |
| random_forest, lexical, random (leaky) | 0.940 | 0.879 | 0.908 | 0.997 |
| random_forest, all, unrestricted | 0.863 | 0.795 | 0.827 | 0.998 |
| random_forest, all, max depth 6 | 0.903 | 0.769 | 0.830 | 0.956 |

Rules as a labeller (`sample_rules.txt`, 3,000 rows): precision 0.441, recall
0.954, flagged 2,316. Rule versus model (logistic/all, validation): the model
cut false positives from 239 to 20 at similar recall.

## Tests performed

- Generated both datasets and ran `scripts/verify_lab.py`: PASS.
- Regenerated both datasets into a temporary directory and compared SHA-256
  byte-for-byte: PASS (identical).
- Ran `tests/run_smoke_tests.py`, which exercises the generator, the labeller,
  classification across feature sets, algorithms and splits, comparison, error
  inspection, the rule-versus-model script and the candidate YARA export: PASS.
- Confirmed training preprocessing and the TF-IDF vocabulary are fitted on the
  training split only, and that near-duplicate clusters do not span splits.

## Dataset SHA-256 checksums

```text
a4963e4d98940b9a53d1ab573da6ed288a19ed6f5c4bb3966205289a49490ad5  datasets/code_samples.csv
e468f7f39d0c536fa39a4277f40ae6e1506d33b91ce3c4debad3bc45300ee056  datasets/code_samples_challenge.csv
```

## Re-run

```bash
python scripts/generate_dataset.py
python scripts/verify_lab.py
python tests/run_smoke_tests.py
```

The smoke test writes files prefixed `_smoke_` into `outputs/` and `charts/`,
which are git-ignored. Nothing in the lab executes a sample, downloads anything,
or requires network access after install.
