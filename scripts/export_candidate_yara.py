"""Turn the strongest learned text signals into a CANDIDATE YARA rule.

This is a teaching aid, not a finished detection. It trains a character
n-gram logistic model, takes the n-grams that push hardest toward the
malicious class, keeps the printable ones, and writes them as YARA strings
with a simple "N of them" condition. A human must review and tighten the
result before any real use; raw n-grams over-trigger.

Run:  python scripts/export_candidate_yara.py --top 12 --name candidate_js
"""
from __future__ import annotations
import argparse
import re

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from lab_common import ROOT, grouped_split, out_name

PRINTABLE = re.compile(r'^[\x20-\x7e]+$')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dataset-file', default='datasets/code_samples.csv')
    ap.add_argument('--top', type=int, default=12)
    ap.add_argument('--name', default='candidate_js')
    args = ap.parse_args()
    name = out_name(args.name)

    frame = pd.read_csv(ROOT / args.dataset_file)
    split = grouped_split(frame)
    tr = split['train']
    y = frame['label'].to_numpy()
    vec = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), min_df=5, max_features=1500)
    pipe = Pipeline([('tfidf', vec), ('model', LogisticRegression(max_iter=2000, random_state=42))])
    pipe.fit(frame.iloc[tr]['code'], y[tr])
    names = np.array(pipe.named_steps['tfidf'].get_feature_names_out())
    coef = np.ravel(pipe.named_steps['model'].coef_)

    picked, seen = [], set()
    for i in np.argsort(coef)[::-1]:
        s = names[i].strip()
        if len(s) < 3 or not PRINTABLE.match(s):
            continue
        if s in seen:
            continue
        seen.add(s)
        picked.append(s)
        if len(picked) >= args.top:
            break

    def esc(s):
        return s.replace('\\', '\\\\').replace('"', '\\"')

    lines = [
        'rule Candidate_Suspicious_JS',
        '{',
        '    meta:',
        '        author = "cyber ML code class lab"',
        '        description = "CANDIDATE only - review and tighten before use"',
        '        note = "derived from char n-gram model weights on synthetic data"',
        '    strings:',
    ]
    for i, s in enumerate(picked):
        lines.append(f'        $s{i} = "{esc(s)}" nocase')
    need = max(2, min(4, len(picked)))
    lines += ['    condition:', f'        {need} of them', '}']
    text = '\n'.join(lines) + '\n'

    (ROOT / 'outputs').mkdir(exist_ok=True)
    (ROOT / 'outputs' / f'{name}.yar').write_text(text, encoding='utf8')
    print(text)
    print(f'Saved: outputs/{name}.yar  (CANDIDATE - review before any deployment)')
    print('These n-grams come from synthetic fixtures; expect over-triggering on real code.')


if __name__ == '__main__':
    main()
