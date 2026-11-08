"""Show the actual false positives or false negatives from a saved run.

Reads outputs/<experiment>_predictions.csv. Does not retrain.

Run:
  python scripts/inspect_errors.py --experiment first_run --type fp
  python scripts/inspect_errors.py --experiment first_run --type fn --rows 15
"""
from __future__ import annotations
import argparse

import pandas as pd

from lab_common import ROOT, out_name


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--experiment', required=True)
    ap.add_argument('--type', choices=['fp', 'fn', 'all_errors', 'correct'], default='fp')
    ap.add_argument('--rows', type=int, default=12)
    args = ap.parse_args()
    name = out_name(args.experiment)
    path = ROOT / 'outputs' / f'{name}_predictions.csv'
    if not path.is_file():
        raise SystemExit(f'Run experiment {name} first (missing {path.name})')
    df = pd.read_csv(path)
    if 'error_type' not in df:
        raise SystemExit('This predictions file has no error_type column')
    want = {'fp': ['FP'], 'fn': ['FN'], 'all_errors': ['FP', 'FN'],
            'correct': ['correct']}[args.type]
    sub = df[df['error_type'].isin(want)]
    print(f'EXPERIMENT: {name} | type: {args.type} | matches: {len(sub)}')
    cols = [c for c in ['sample_id', 'family', 'actual_label', 'predicted_label',
                        'positive_probability', 'code'] if c in sub.columns]
    with pd.option_context('display.max_colwidth', 70, 'display.width', 200):
        print(sub[cols].head(max(1, args.rows)).to_string(index=False))
    if len(sub) and 'family' in sub:
        print('\nBY FAMILY:')
        print(sub['family'].value_counts().to_string())


if __name__ == '__main__':
    main()
