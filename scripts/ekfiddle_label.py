"""Turn EKFiddle-style regex rules into dataset labels (weak supervision).

This is the bridge from detection rules to a training set. It reads an
EKFiddle CustomRegexes file, applies the SourceCode rules to each code
sample, and writes a labelled CSV plus a per-rule coverage report.

Why this matters: a regex is an exact matcher. Treating it as a *labelling
function* lets you build a training set cheaply, then train a classifier
that generalises beyond the exact patterns. Exercise 04 and 05 build on this.

Rules file resolution order:
  1. --rules PATH if given
  2. the first *.txt in rules/local/ (git-ignored, your private rules)
  3. rules/sample_rules.txt (generic, shipped)

Run:
  python scripts/ekfiddle_label.py
  python scripts/ekfiddle_label.py --rules rules/local/CustomRegexes.txt --name mylabels
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path

import pandas as pd

from lab_common import ROOT, classifier_metrics, format_table, out_name

MAX_CODE = 20000  # cap scanned length to avoid pathological regex cost


def resolve_rules(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit)
        if not p.is_absolute():
            p = ROOT / p
        if not p.is_file():
            raise SystemExit(f'Rules file not found: {p}')
        return p
    local = sorted((ROOT / 'rules' / 'local').glob('*.txt'))
    if local:
        return local[0]
    return ROOT / 'rules' / 'sample_rules.txt'


def parse_rules(path: Path, types=('SourceCode',)):
    """Return list of (name, compiled_regex, raw) for the requested types."""
    rules = []
    for ln in path.read_text(encoding='utf8', errors='replace').splitlines():
        if not ln.strip() or ln.lstrip().startswith('#'):
            continue
        parts = ln.split('\t')
        if len(parts) < 3:
            continue
        rtype, name, pattern = parts[0].strip(), parts[1].strip(), parts[2]
        if types and rtype not in types:
            continue
        try:
            rules.append((name, re.compile(pattern), pattern))
        except re.error as exc:
            print(f'  skipped rule {name!r}: bad regex ({exc})')
    return rules


def apply_rules(codes, rules):
    weak = []
    matched = []
    for code in codes:
        c = str(code)[:MAX_CODE]
        hits = []
        for name, rx, _ in rules:
            try:
                if rx.search(c):
                    hits.append(name)
            except re.error:
                continue
        weak.append(1 if hits else 0)
        matched.append(';'.join(hits))
    return weak, matched


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', default='datasets/code_samples.csv',
                    help='CSV with a code column (and optional label column)')
    ap.add_argument('--rules', default=None)
    ap.add_argument('--types', default='SourceCode',
                    help='comma list of rule types to apply, e.g. SourceCode,URI')
    ap.add_argument('--name', default='weak_labels')
    args = ap.parse_args()
    name = out_name(args.name)

    inp = Path(args.input)
    if not inp.is_absolute():
        inp = ROOT / inp
    if not inp.is_file():
        raise SystemExit(f'Input not found: {inp}. Run generate_dataset.py first.')
    frame = pd.read_csv(inp)
    if 'code' not in frame:
        raise SystemExit("Input needs a 'code' column")

    rules_path = resolve_rules(args.rules)
    rules = parse_rules(rules_path, tuple(t.strip() for t in args.types.split(',')))
    if not rules:
        raise SystemExit(f'No usable rules of type {args.types} in {rules_path}')
    print(f'RULES: {rules_path.relative_to(ROOT) if ROOT in rules_path.parents else rules_path}'
          f' ({len(rules)} rule(s), types={args.types})')
    print(f'INPUT: {inp.name} ({len(frame)} rows)')

    weak, matched = apply_rules(frame['code'].tolist(), rules)
    frame = frame.copy()
    frame['weak_label'] = weak
    frame['matched_rules'] = matched
    frame['n_rule_hits'] = [0 if not m else m.count(';') + 1 for m in matched]

    flagged = int(sum(weak))
    print(f'\nFLAGGED by rules: {flagged} / {len(frame)} ({flagged/len(frame):.1%})')

    # Per-rule coverage.
    counts = {name: 0 for name, _, _ in rules}
    for m in matched:
        for nm in filter(None, m.split(';')):
            counts[nm] = counts.get(nm, 0) + 1
    cov = pd.DataFrame(sorted(counts.items(), key=lambda kv: -kv[1]),
                       columns=['rule', 'matches'])
    format_table('PER-RULE COVERAGE', cov)

    # Score the rules as a labeller only when every row has a 0/1 ground truth.
    # A blank label column (unlabelled captured code) is not ground truth.
    if 'label' in frame:
        numeric = pd.to_numeric(frame['label'], errors='coerce')
        usable = numeric.notna()
        values = set(numeric[usable].astype(int).tolist())
        if len(frame) and bool(usable.all()) and values and values.issubset({0, 1}):
            y = numeric.astype(int).to_numpy()
            m = classifier_metrics(y, frame['weak_label'].to_numpy(),
                                   frame['weak_label'].to_numpy())
            print('\nRULES AS A LABELLER (vs ground-truth label):')
            print(f'  precision {m["precision"]:.4f}  recall {m["recall"]:.4f}  '
                  f'f1 {m["f1"]:.4f}  fp {m["fp"]}  fn {m["fn"]}')
            print('  precision = of samples the rules flag, how many are really malicious')
            print('  recall    = of malicious samples, how many the rules catch')
        else:
            print('\nLabel column is blank or not 0/1 on every row; skipped labeller score.')

    (ROOT / 'outputs').mkdir(exist_ok=True)
    keep = [c for c in ['sample_id', 'source_type', 'family', 'label',
                        'weak_label', 'n_rule_hits', 'matched_rules', 'code'] if c in frame]
    frame[keep].to_csv(ROOT / 'outputs' / f'{name}.csv', index=False)
    print(f'\nSaved: outputs/{name}.csv (weak_label, matched_rules, n_rule_hits)')
    print('Use this file as training labels, or compare weak_label with label.')


if __name__ == '__main__':
    main()
