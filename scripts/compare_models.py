"""Compare saved experiments from the same dataset and evaluation split.

Reads the saved metrics JSON, not live models.

Run:  python scripts/compare_models.py run_a run_b run_c --name my_comparison
"""
from __future__ import annotations
import argparse
import json

import pandas as pd

from lab_common import ROOT, out_name


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('experiments', nargs='+')
    ap.add_argument('--name', default='comparison')
    args = ap.parse_args()
    if len(args.experiments) < 2:
        ap.error('give at least two experiment names')
    rows, base = [], None
    for raw in args.experiments:
        name = out_name(raw)
        f = ROOT / 'outputs' / f'{name}_metrics.json'
        if not f.is_file():
            ap.error(f'missing {f.name}: run it first')
        rec = json.loads(f.read_text(encoding='utf8'))
        cfg = rec['config']
        sig = (cfg.get('dataset_file'), cfg.get('evaluation_split'))
        if base is None:
            base = sig
        if sig != base:
            ap.error(f'cannot compare different dataset/split: {name} {sig} != {base}')
        rows.append({'experiment': name, 'algorithm': cfg.get('algorithm'),
                     'features': cfg.get('features'), 'split': cfg.get('split'),
                     'threshold': cfg.get('threshold'), **rec['metrics']})
    cols = ['experiment', 'algorithm', 'features', 'split', 'threshold',
            'precision', 'recall', 'f1', 'fpr', 'fp', 'fn', 'tp', 'tn',
            'roc_auc', 'pr_auc_average_precision', 'train_f1']
    df = pd.DataFrame(rows)
    cols = [c for c in cols if c in df.columns]
    print('COMPARISON (same dataset and evaluation split):')
    print(df[cols].round(4).to_string(index=False))
    (ROOT / 'outputs').mkdir(exist_ok=True)
    df[cols].to_csv(ROOT / 'outputs' / f'{out_name(args.name)}.csv', index=False)
    print(f'\nSaved: outputs/{out_name(args.name)}.csv')


if __name__ == '__main__':
    main()
