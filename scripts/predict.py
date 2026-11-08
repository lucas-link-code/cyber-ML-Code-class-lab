"""Score an unlabelled code CSV with a model trained on the synthetic corpus.

Fits on the synthetic training split only (grouped by group_id unless
--split random), using the same feature pipeline as run_classification.py,
then predicts each row of --input. Writes local/<name>.csv.

The probabilities are a triage signal from a model trained on synthetic
data, not ground truth. This script reads code as text. It does not
execute, import, evaluate or fetch a sample.

Example:
  python scripts/predict.py --model-dataset datasets/code_samples.csv \\
      --features all --algorithm logistic --threshold 0.5 \\
      --input local/my_samples.csv --name my_scored
"""
from __future__ import annotations
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from lab_common import (ROOT, grouped_split, random_split, classifier_metrics,
                        truncate_code, out_name, format_table)
from run_classification import build_matrix, make_model


def resolve_path(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    return path


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--model-dataset', default='datasets/code_samples.csv')
    ap.add_argument('--input', required=True, help='CSV with a code column to score')
    ap.add_argument('--features', default='all', choices=['lexical', 'ngram', 'all'])
    ap.add_argument('--algorithm', default='logistic',
                    choices=['logistic', 'tree', 'random_forest', 'gradient_boosting', 'naive_bayes'])
    ap.add_argument('--split', default='group', choices=['group', 'random'])
    ap.add_argument('--threshold', type=float, default=0.5)
    ap.add_argument('--n-estimators', type=int, default=200)
    ap.add_argument('--max-depth', type=int, default=None)
    ap.add_argument('--min-samples-leaf', type=int, default=1)
    ap.add_argument('--c', type=float, default=1.0)
    ap.add_argument('--name', default='my_scored')
    args = ap.parse_args()
    if not 0 <= args.threshold <= 1:
        ap.error('--threshold must be between 0 and 1')
    return args


def main():
    args = parse_args()
    name = out_name(args.name)
    model_path = resolve_path(args.model_dataset)
    input_path = resolve_path(args.input)
    if not model_path.is_file():
        raise SystemExit(f'Model dataset not found: {model_path}')
    if not input_path.is_file():
        raise SystemExit(f'Input not found: {input_path}')

    corpus = pd.read_csv(model_path)
    for col in ('code', 'label', 'group_id'):
        if col not in corpus:
            raise SystemExit(f'Model dataset missing required column {col!r}')
    incoming = pd.read_csv(input_path)
    if 'code' not in incoming:
        raise SystemExit("Input needs a 'code' column")
    if 'sample_id' not in incoming:
        raise SystemExit("Input needs a 'sample_id' column")
    incoming = incoming.copy()
    incoming['code'] = incoming['code'].fillna('').astype(str)
    if 'source_type' not in incoming:
        incoming['source_type'] = 'js'

    split = grouped_split(corpus) if args.split == 'group' else random_split(corpus)
    train_idx = split['train']
    val_idx = split['validation']
    y = corpus['label'].to_numpy()

    train_data, pre = build_matrix(corpus, args.features, False)
    model = Pipeline([('preprocessing', pre), ('model', make_model(args))])
    model.fit(train_data.iloc[train_idx], y[train_idx])

    val_scores = model.predict_proba(train_data.iloc[val_idx])[:, 1]
    val_pred = (val_scores >= args.threshold).astype(int)
    val_metrics = classifier_metrics(y[val_idx], val_pred, val_scores)
    print(f'MODEL DATASET: {model_path.name} train {len(train_idx)} | validation {len(val_idx)}')
    print(f'FEATURES: {args.features}  ALGORITHM: {args.algorithm}  threshold={args.threshold}')
    print(f'VALIDATION CHECK: precision {val_metrics["precision"]:.4f}  '
          f'recall {val_metrics["recall"]:.4f}  f1 {val_metrics["f1"]:.4f}')

    score_data, _ = build_matrix(incoming, args.features, False)
    scores = model.predict_proba(score_data)[:, 1]
    pred = (scores >= args.threshold).astype(int)

    out = pd.DataFrame({
        'sample_id': incoming['sample_id'].astype(str).to_numpy(),
        'source_type': incoming['source_type'].astype(str).to_numpy(),
        'positive_probability': np.round(scores, 6),
        'predicted_label': pred.astype(int),
        'code': [truncate_code(c) for c in incoming['code'].tolist()],
    })
    dest_dir = ROOT / 'local'
    dest_dir.mkdir(exist_ok=True)
    dest = dest_dir / f'{name}.csv'
    out.to_csv(dest, index=False)

    above = int(pred.sum())
    print(f'\nSCORED: {len(out)} rows from {input_path.name}')
    print(f'ABOVE THRESHOLD {args.threshold}: {above} / {len(out)}')
    view = out[['sample_id', 'source_type', 'positive_probability', 'predicted_label']].copy()
    if 'group_id' in incoming:
        view.insert(1, 'group_id', incoming['group_id'].astype(str).to_numpy())
    format_table('SCORES (code omitted from this table)', view)
    print(f'Saved: local/{name}.csv')
    print('These probabilities are a triage signal from a synthetic-data model, not ground truth.')


if __name__ == '__main__':
    main()
