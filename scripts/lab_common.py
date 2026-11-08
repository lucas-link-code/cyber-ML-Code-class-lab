"""Shared helpers: feature extraction, splitting, metrics and saving.

This module is imported by every run script. It is deliberately plain
Python plus numpy, pandas, scikit-learn and matplotlib, the same stack as
the sibling Cyber ML Lab, so there is nothing extra to install.

The feature extractor below uses only generic, publicly documented
indicators of suspicious JavaScript and HTML (entropy, encoding markers,
counts of well known sink functions). It does not encode any private
detection rule set.
"""
from __future__ import annotations
import json
import math
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, average_precision_score, confusion_matrix,
                             f1_score, precision_score, recall_score, roc_auc_score)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RANDOM_SEED = 42

# Well known sink / loader / decode tokens seen in both benign and malicious
# code. Counting them is standard practice; their presence is not a verdict.
KEYWORDS = [
    'eval', 'atob', 'btoa', 'unescape', 'escape', 'decodeURIComponent',
    'encodeURIComponent', 'fromCharCode', 'charCodeAt', 'String.fromCharCode',
    'document.write', 'window.location', 'location.href', 'setTimeout',
    'setInterval', 'Function', 'ActiveXObject', 'WScript', 'XMLHttpRequest',
    'fetch', 'createElement', 'appendChild', 'addEventListener', 'iframe',
    'replace', 'concat', 'parseInt', 'navigator', 'cookie',
]

_IDENT = re.compile(r'[A-Za-z_$][\w$]*')
_HEX_ESC = re.compile(r'\\x[0-9A-Fa-f]{2}')
_UNI_ESC = re.compile(r'\\u[0-9A-Fa-f]{4}')
_PCT_ESC = re.compile(r'%[0-9A-Fa-f]{2}')
_B64_BLOB = re.compile(r'[A-Za-z0-9+/]{40,}={0,2}')
_STR_LIT = re.compile(r'"[^"\n]*"|\'[^\'\n]*\'')
_URL = re.compile(r'https?://', re.IGNORECASE)
_HEX_ARR = re.compile(r'_0x[0-9A-Fa-f]{2,}')
_SCRIPT = re.compile(r'<script\b', re.IGNORECASE)
_IFRAME = re.compile(r'<iframe\b', re.IGNORECASE)
_WORD = re.compile(r'\w+')


def shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text)
    n = len(text)
    return float(-sum((c / n) * math.log2(c / n) for c in counts.values()))


def _ratio(num: int, den: int) -> float:
    return float(num) / float(den) if den else 0.0


def extract_features(code) -> dict:
    """Return an ordered dict of numeric features for one code string.

    Every value is a plain float. Counts of sink tokens are normalised per
    1,000 characters so that long files do not dominate purely by length.
    """
    code = '' if code is None else str(code)
    n = len(code)
    lines = code.split('\n')
    idents = _IDENT.findall(code)
    ident_lens = [len(i) for i in idents]
    strings = _STR_LIT.findall(code)
    nonascii = sum(1 for ch in code if ord(ch) > 127)
    digits = sum(ch.isdigit() for ch in code)
    brackets = sum(code.count(ch) for ch in '[]{}();')
    per_k = 1000.0

    feats: dict[str, float] = {
        'length': float(n),
        'n_lines': float(len(lines)),
        'max_line_length': float(max((len(l) for l in lines), default=0)),
        'entropy': shannon_entropy(code),
        'nonascii_ratio': _ratio(nonascii, n),
        'digit_ratio': _ratio(digits, n),
        'bracket_density': _ratio(brackets, n),
        'avg_identifier_length': float(np.mean(ident_lens)) if ident_lens else 0.0,
        'unique_identifier_ratio': _ratio(len(set(idents)), len(idents)) if idents else 0.0,
        'hex_escape_count': float(len(_HEX_ESC.findall(code))),
        'unicode_escape_count': float(len(_UNI_ESC.findall(code))),
        'pct_escape_count': float(len(_PCT_ESC.findall(code))),
        'b64_blob_count': float(len(_B64_BLOB.findall(code))),
        'long_string_count': float(sum(1 for s in strings if len(s) > 40)),
        'string_concat_ops': float(code.count("'+'") + code.count('"+"') + code.count("' +") + code.count('" +')),
        'hex_array_obf_count': float(len(_HEX_ARR.findall(code))),
        'url_count': float(len(_URL.findall(code))),
        'script_tag_count': float(len(_SCRIPT.findall(code))),
        'iframe_count': float(len(_IFRAME.findall(code))),
    }
    # Normalised sink-token frequencies.
    for kw in KEYWORDS:
        key = 'kw_' + re.sub(r'[^A-Za-z0-9]+', '_', kw).strip('_').lower()
        feats[key] = _ratio(code.count(kw), n) * per_k
    return feats


FEATURE_NAMES = list(extract_features('var x = 1;').keys())


def featurize_frame(frame: pd.DataFrame, text_col: str = 'code') -> pd.DataFrame:
    rows = [extract_features(c) for c in frame[text_col].tolist()]
    out = pd.DataFrame(rows, columns=FEATURE_NAMES).fillna(0.0)
    out.index = frame.index
    return out


def grouped_split(frame: pd.DataFrame, group_col: str = 'group_id',
                  label_col: str = 'label', seed: int = RANDOM_SEED) -> dict:
    """Disjoint 60/20/20 split where a whole group stays on one side.

    Grouping by near-duplicate cluster id stops a snippet and its slight
    variants from landing in both training and validation, which would
    flatter the scores. Every template family still appears on both sides.
    """
    from sklearn.model_selection import GroupShuffleSplit
    idx = np.arange(len(frame))
    groups = frame[group_col].astype(str).to_numpy()
    g1 = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=seed)
    rest, test = next(g1.split(idx, groups=groups))
    g2 = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed + 1)
    tr_local, va_local = next(g2.split(rest, groups=groups[rest]))
    out = {'train': rest[tr_local], 'validation': rest[va_local], 'test': test}
    assert set(out['train']).isdisjoint(out['validation'])
    assert set(out['train']).isdisjoint(out['test'])
    assert set(out['validation']).isdisjoint(out['test'])
    return {k: np.asarray(v) for k, v in out.items()}


def random_split(frame: pd.DataFrame, label_col: str = 'label',
                 seed: int = RANDOM_SEED) -> dict:
    """Stratified 60/20/20 split by row, ignoring groups.

    This is the deliberately leaky split used to teach group leakage.
    """
    from sklearn.model_selection import train_test_split
    idx = np.arange(len(frame))
    y = frame[label_col].to_numpy()
    rest, test = train_test_split(idx, test_size=0.20, random_state=seed, stratify=y)
    tr, va = train_test_split(rest, test_size=0.25, random_state=seed + 1,
                              stratify=y[rest])
    return {'train': np.asarray(tr), 'validation': np.asarray(va), 'test': np.asarray(test)}


def classifier_metrics(y, pred, scores) -> dict:
    y = np.asarray(y)
    pred = np.asarray(pred)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    out = {
        'n': int(len(y)), 'positives': int(np.sum(y)),
        'tp': int(tp), 'fp': int(fp), 'tn': int(tn), 'fn': int(fn),
        'accuracy': float(accuracy_score(y, pred)),
        'precision': float(precision_score(y, pred, zero_division=0)),
        'recall': float(recall_score(y, pred, zero_division=0)),
        'f1': float(f1_score(y, pred, zero_division=0)),
        'fpr': float(fp / (fp + tn)) if (fp + tn) else None,
        'predicted_positive_rate': float(np.mean(pred)),
    }
    if len(np.unique(y)) == 2:
        out['roc_auc'] = float(roc_auc_score(y, scores))
        out['pr_auc_average_precision'] = float(average_precision_score(y, scores))
    else:
        out['roc_auc'] = None
        out['pr_auc_average_precision'] = None
    return out


def out_name(raw: str) -> str:
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', raw or ''):
        raise ValueError('--name must be 1-64 chars: letters, digits, _ or -')
    return raw


def truncate_code(code, width: int = 160) -> str:
    code = '' if code is None else str(code)
    one_line = re.sub(r'\s+', ' ', code).strip()
    return one_line if len(one_line) <= width else one_line[:width - 3] + '...'


def save_result(name, config, metrics, predictions, chart_fn=None) -> None:
    name = out_name(name)
    (ROOT / 'outputs').mkdir(exist_ok=True)
    (ROOT / 'charts').mkdir(exist_ok=True)
    payload = {'name': name, 'config': config, 'metrics': metrics}
    with (ROOT / 'outputs' / f'{name}_metrics.json').open('w', encoding='utf8') as fh:
        json.dump(payload, fh, indent=2, allow_nan=False)
    predictions.to_csv(ROOT / 'outputs' / f'{name}_predictions.csv', index=False)
    if chart_fn is not None:
        chart_fn(ROOT / 'charts' / name)
    print('\nEXPERIMENT METRICS')
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f'  {key:27s} {value:.4f}')
        elif not isinstance(value, (dict, list)):
            print(f'  {key:27s} {value}')
    print(f'  Saved: outputs/{name}_metrics.json')
    print(f'  Saved: outputs/{name}_predictions.csv')
    if chart_fn is not None:
        print(f'  Charts: charts/{name}_*.png')


def format_table(title: str, table: pd.DataFrame) -> None:
    if title:
        print('\n' + title)
    print(table.to_string(index=False, max_colwidth=60))
