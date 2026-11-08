"""Level 1: look at the code corpus before training anything.

Prints shape, label balance, source types, template families and the
numeric features for a few rows, so you can see what the classifier sees.

Run:  python scripts/inspect_data.py --rows 6
"""
from __future__ import annotations
import argparse

import pandas as pd

from lab_common import ROOT, featurize_frame, truncate_code


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dataset-file', default='datasets/code_samples.csv')
    ap.add_argument('--rows', type=int, default=6)
    args = ap.parse_args()
    path = ROOT / args.dataset_file
    if not path.is_file():
        raise SystemExit(f'Missing {path}. Run: python scripts/generate_dataset.py')
    frame = pd.read_csv(path)

    print(f'DATASET: {path.name}')
    print(f'SHAPE: {len(frame):,} rows x {len(frame.columns)} columns')
    print(f'COLUMNS: {", ".join(frame.columns)}')
    print(f'TARGET: label (1 = malicious, 0 = benign). Never a training input.')
    print('\nLABEL BALANCE:')
    print(frame['label'].value_counts().sort_index().to_string())
    print(f'Malicious prevalence: {frame["label"].mean():.2%}')
    print('\nSOURCE TYPE:')
    print(frame['source_type'].value_counts().to_string())
    print('\nTEMPLATE FAMILIES (used for grouped splitting, never a feature):')
    print(frame.groupby('family')['label'].agg(['size', 'mean']).rename(
        columns={'size': 'rows', 'mean': 'malicious_share'}).round(2).to_string())

    print(f'\nFIRST {args.rows} SAMPLES (code shortened):')
    for _, r in frame.head(args.rows).iterrows():
        print(f'  [{r["label"]}] {r["family"]:22s} {truncate_code(r["code"], 90)}')

    print('\nNUMERIC FEATURES for those rows (a subset of columns):')
    feats = featurize_frame(frame.head(args.rows))
    show = ['length', 'entropy', 'bracket_density', 'hex_escape_count',
            'b64_blob_count', 'hex_array_obf_count', 'kw_eval', 'kw_atob']
    show = [c for c in show if c in feats.columns]
    preview = feats[show].round(3)
    preview.insert(0, 'label', frame.head(args.rows)['label'].values)
    print(preview.to_string(index=False))
    print('\nThese numeric features, not the raw text, are what the lexical model trains on.')


if __name__ == '__main__':
    main()
