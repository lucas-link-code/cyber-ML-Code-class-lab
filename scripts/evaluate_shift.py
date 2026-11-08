"""Train on the main cohort, freeze the model, score the challenge cohort.

This measures how a model trained on one distribution holds up on a shifted
one, without retraining. The challenge cohort carries more benign minified
code with _0x hex-array identifiers, so false positives are expected to rise.

Run:  python scripts/evaluate_shift.py --features all --algorithm random_forest --name shift_rf
"""
from __future__ import annotations
import argparse
import json

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from lab_common import ROOT, grouped_split, classifier_metrics, out_name
from run_classification import build_matrix, make_model


class _A:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--features', default='all', choices=['lexical', 'ngram', 'all'])
    ap.add_argument('--algorithm', default='random_forest',
                    choices=['logistic', 'tree', 'random_forest', 'gradient_boosting', 'naive_bayes'])
    ap.add_argument('--threshold', type=float, default=0.5)
    ap.add_argument('--name', default='shift')
    args = ap.parse_args()
    name = out_name(args.name)

    main_df = pd.read_csv(ROOT / 'datasets' / 'code_samples.csv')
    chal_df = pd.read_csv(ROOT / 'datasets' / 'code_samples_challenge.csv')
    combined = pd.concat([main_df, chal_df], ignore_index=True)

    data, pre = build_matrix(combined, args.features, add_rule_hits=False)
    split = grouped_split(main_df)  # indices into main_df / first block of combined
    margs = _A(algorithm=args.algorithm, c=1.0, max_depth=None, min_samples_leaf=1, n_estimators=200)
    model = Pipeline([('preprocessing', pre), ('model', make_model(margs))])
    y_main = main_df['label'].to_numpy()
    model.fit(data.iloc[split['train']], y_main[split['train']])

    def score(idx, labels):
        s = model.predict_proba(data.iloc[idx])[:, 1]
        return classifier_metrics(labels, (s >= args.threshold).astype(int), s)

    old_idx = split['validation']
    old = score(old_idx, y_main[old_idx])
    chal_idx = np.arange(len(main_df), len(combined))
    new = score(chal_idx, chal_df['label'].to_numpy())

    print(f'FROZEN MODEL: trained on main training rows, no refit on challenge.')
    print(f'FEATURES={args.features} ALGORITHM={args.algorithm} THRESHOLD={args.threshold}')
    print('COHORT            N     precision recall   f1     fpr    fp   fn')
    for title, m in [('main_validation', old), ('challenge', new)]:
        print(f'{title:16s} {m["n"]:5d}   {m["precision"]:.3f}    {m["recall"]:.3f}  '
              f'{m["f1"]:.3f}  {m["fpr"]:.3f}  {m["fp"]:4d} {m["fn"]:4d}')
    (ROOT / 'outputs').mkdir(exist_ok=True)
    (ROOT / 'outputs' / f'{name}_shift_metrics.json').write_text(
        json.dumps({'main_validation': old, 'challenge': new}, indent=2), encoding='utf8')
    print(f'\nSaved: outputs/{name}_shift_metrics.json')
    print('A shifted input distribution can change precision and FPR even when the model is unchanged.')


if __name__ == '__main__':
    main()
