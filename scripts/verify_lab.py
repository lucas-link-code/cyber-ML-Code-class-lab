"""Structural checks: data present, splits disjoint, features finite, rules parse.

Run:  python scripts/verify_lab.py
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from lab_common import ROOT, featurize_frame, grouped_split
from ekfiddle_label import resolve_rules, parse_rules, apply_rules


def main():
    datasets = ['code_samples.csv', 'code_samples_challenge.csv']
    for name in datasets:
        path = ROOT / 'datasets' / name
        assert path.is_file(), f'missing {name}; run generate_dataset.py'
        df = pd.read_csv(path)
        assert df['sample_id'].is_unique, f'{name}: ids not unique'
        assert set(df['label'].unique()) == {0, 1}, f'{name}: need both classes'
        assert df['code'].notna().all(), f'{name}: null code'
        # grouped split: rows disjoint AND no duplicate cluster spans splits
        s = grouped_split(df)
        keys = list(s)
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                assert set(s[a]).isdisjoint(s[b]), f'{name}: {a}/{b} overlap'
                ga = set(df.iloc[s[a]]['group_id'])
                gb = set(df.iloc[s[b]]['group_id'])
                assert ga.isdisjoint(gb), f'{name}: group_id spans {a}/{b}'
        # every family should appear in the training split (mixed, not held out)
        assert set(df['family']) == set(df.iloc[s['train']]['family']), \
            f'{name}: some family missing from training split'
        feats = featurize_frame(df)
        assert np.isfinite(feats.to_numpy()).all(), f'{name}: non-finite features'
        print(f'PASS {name:30s} rows={len(df):5d} malicious={int(df["label"].sum()):4d} '
              f'families={df["family"].nunique()} features={feats.shape[1]}')
    rules = parse_rules(resolve_rules(None))
    assert rules, 'no rules parsed'
    df = pd.read_csv(ROOT / 'datasets' / 'code_samples.csv')
    weak, _ = apply_rules(df['code'].tolist(), rules)
    assert sum(weak) > 0, 'rules flagged nothing'
    print(f'PASS rules parse ({len(rules)}) and flag {sum(weak)} / {len(df)} samples')
    print('PASS structural checks. No model is trained or evaluated in this script.')


if __name__ == '__main__':
    main()
