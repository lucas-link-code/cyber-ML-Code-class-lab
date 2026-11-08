"""The headline comparison: the raw regex rules versus a trained classifier.

A regex either matches or it does not. A classifier learns the shape of
suspicious code from many features and can flag variants the exact pattern
misses, at some false-positive cost. This script scores both on the SAME
held-out validation rows and shows where they differ.

Run:
  python scripts/rule_vs_model.py --name rule_vs_model
  python scripts/rule_vs_model.py --features all --algorithm random_forest --name rvm_rf
"""
from __future__ import annotations
import argparse

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.pipeline import Pipeline

from lab_common import (ROOT, grouped_split, classifier_metrics, truncate_code, out_name)
from run_classification import build_matrix, make_model
from ekfiddle_label import resolve_rules, parse_rules, apply_rules


class _A:  # tiny arg holder for make_model
    def __init__(self, **kw):
        self.__dict__.update(kw)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dataset-file', default='datasets/code_samples.csv')
    ap.add_argument('--features', default='all', choices=['lexical', 'ngram', 'all'])
    ap.add_argument('--algorithm', default='logistic',
                    choices=['logistic', 'tree', 'random_forest', 'gradient_boosting', 'naive_bayes'])
    ap.add_argument('--threshold', type=float, default=0.5)
    ap.add_argument('--rules', default=None)
    ap.add_argument('--name', default='rule_vs_model')
    args = ap.parse_args()
    name = out_name(args.name)

    frame = pd.read_csv(ROOT / args.dataset_file)
    split = grouped_split(frame)
    train, val = split['train'], split['validation']
    y = frame['label'].to_numpy()

    # Model.
    data, pre = build_matrix(frame, args.features, add_rule_hits=False)
    margs = _A(algorithm=args.algorithm, c=1.0, max_depth=None, min_samples_leaf=1, n_estimators=200)
    model = Pipeline([('preprocessing', pre), ('model', make_model(margs))])
    model.fit(data.iloc[train], y[train])
    m_scores = model.predict_proba(data.iloc[val])[:, 1]
    m_pred = (m_scores >= args.threshold).astype(int)

    # Regex baseline on the same validation rows.
    rules = parse_rules(resolve_rules(args.rules))
    r_pred, r_matched = apply_rules(frame.iloc[val]['code'].tolist(), rules)
    r_pred = np.asarray(r_pred)

    actual = y[val]
    m_met = classifier_metrics(actual, m_pred, m_scores)
    r_met = classifier_metrics(actual, r_pred, r_pred.astype(float))

    table = pd.DataFrame([
        {'detector': 'regex rules', **{k: r_met[k] for k in ['precision', 'recall', 'f1', 'fp', 'fn', 'tp', 'tn']}},
        {'detector': f'{args.algorithm}/{args.features}', **{k: m_met[k] for k in ['precision', 'recall', 'f1', 'fp', 'fn', 'tp', 'tn']}},
    ])
    print(f'DATASET: {args.dataset_file} | validation rows: {len(val)} | rules: {len(rules)}')
    print('\nDETECTOR COMPARISON (same validation rows):')
    print(table.round(4).to_string(index=False))

    caught_by_model_only = (actual == 1) & (r_pred == 0) & (m_pred == 1)
    missed_by_both = (actual == 1) & (r_pred == 0) & (m_pred == 0)
    model_false_alarms = (actual == 0) & (m_pred == 1)
    print(f'\nMalicious rows the regex missed but the model caught: {int(caught_by_model_only.sum())}')
    print(f'Malicious rows both missed:                           {int(missed_by_both.sum())}')
    print(f'Benign rows the model false-alarmed on:               {int(model_false_alarms.sum())}')

    gen = frame.iloc[val][caught_by_model_only]
    if len(gen):
        print('\nGENERALISATION EXAMPLES (regex miss, model catch):')
        for _, r in gen.head(6).iterrows():
            print(f'  {r["family"]:22s} {truncate_code(r["code"], 90)}')

    out = frame.iloc[val][['sample_id', 'source_type', 'family']].copy()
    out['actual_label'] = actual
    out['regex_pred'] = r_pred
    out['model_pred'] = m_pred
    out['model_prob'] = np.round(m_scores, 6)
    out['matched_rules'] = r_matched
    out['code'] = [truncate_code(c) for c in frame.iloc[val]['code']]
    (ROOT / 'outputs').mkdir(exist_ok=True)
    out.to_csv(ROOT / 'outputs' / f'{name}.csv', index=False)

    (ROOT / 'charts').mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4))
    idx = np.arange(3)
    labels = ['precision', 'recall', 'f1']
    ax.bar(idx - 0.2, [r_met[k] for k in labels], width=0.4, label='regex rules')
    ax.bar(idx + 0.2, [m_met[k] for k in labels], width=0.4, label=f'{args.algorithm}')
    ax.set_xticks(idx, labels); ax.set_ylim(0, 1.05)
    ax.set_title('Regex rules vs trained model (validation)'); ax.legend()
    fig.tight_layout(); fig.savefig(ROOT / 'charts' / f'{name}.png', dpi=130); plt.close(fig)
    print(f'\nSaved: outputs/{name}.csv and charts/{name}.png')
    print('Lesson: rules give high precision on known patterns; the model trades a')
    print('little precision for recall on variants. Use them together, not one alone.')


if __name__ == '__main__':
    main()
