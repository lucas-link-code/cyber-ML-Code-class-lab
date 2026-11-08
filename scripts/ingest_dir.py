"""Read a directory of untrusted code as text and write a lab CSV.

Walks --input for .js, .htm, .html and .txt. Each file is opened as bytes,
decoded as UTF-8 with invalid bytes replaced, and capped at 20000 characters.
Nothing is executed, imported, evaluated or fetched.

Example:
  python scripts/ingest_dir.py --input /path/to/samples --name my_samples
"""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path

import pandas as pd

from lab_common import ROOT, out_name

MAX_CHARS = 20000
TEXT_EXTS = {'.js', '.htm', '.html', '.txt'}


def resolve_dir(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_dir():
        raise SystemExit(f'Input directory not found: {path}')
    return path


def read_capped(path: Path, limit: int) -> tuple[str, bool]:
    """Return (text, truncated). Reads at most limit*4 bytes, then caps chars."""
    max_bytes = limit * 4
    with path.open('rb') as fh:
        blob = fh.read(max_bytes + 1)
    truncated = len(blob) > max_bytes
    text = blob[:max_bytes].decode('utf-8', errors='replace')
    if len(text) > limit:
        text = text[:limit]
        truncated = True
    return text, truncated


def make_sample_id(rel: str, source_type: str, used: set[str]) -> str:
    prefix = 'CHT' if source_type == 'html' else 'CJS'
    digest = hashlib.sha256(rel.encode('utf-8')).hexdigest()
    for width in range(8, len(digest) + 1):
        sample_id = f'{prefix}-{digest[:width]}'
        if sample_id not in used:
            used.add(sample_id)
            return sample_id
    raise SystemExit(f'Could not build a unique sample_id for {rel}')


def iter_code_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames.sort()
        for name in sorted(filenames):
            path = Path(dirpath) / name
            if not path.is_file():
                continue
            if path.suffix.lower() not in TEXT_EXTS:
                continue
            yield path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', required=True, help='directory of untrusted code files')
    ap.add_argument('--name', default='my_samples')
    ap.add_argument('--max-chars', type=int, default=MAX_CHARS)
    args = ap.parse_args()
    name = out_name(args.name)
    if args.max_chars < 1:
        ap.error('--max-chars must be positive')

    root = resolve_dir(args.input)
    used: set[str] = set()
    rows = []
    skipped = 0
    for path in iter_code_files(root):
        rel = path.relative_to(root).as_posix()
        source_type = 'html' if path.suffix.lower() in {'.htm', '.html'} else 'js'
        try:
            text, truncated = read_capped(path, args.max_chars)
        except OSError as exc:
            skipped += 1
            print(f'SKIP {rel}: {exc}')
            continue
        sample_id = make_sample_id(rel, source_type, used)
        rows.append({
            'sample_id': sample_id,
            'source_type': source_type,
            'family': 'unknown',
            'group_id': rel,
            'code': text,
            'label': '',
            '_chars': len(text),
            '_truncated': truncated,
        })

    if not rows:
        raise SystemExit(f'No .js, .htm, .html or .txt files under {root}')

    out_dir = ROOT / 'local'
    out_dir.mkdir(exist_ok=True)
    frame = pd.DataFrame(rows)
    dest = out_dir / f'{name}.csv'
    frame[['sample_id', 'source_type', 'family', 'group_id', 'code', 'label']].to_csv(
        dest, index=False)
    n_trunc = int(frame['_truncated'].sum())
    print(f'INPUT: {root} ({len(frame)} files, skipped {skipped})')
    print(f'TRUNCATED to {args.max_chars} chars: {n_trunc}')
    show = frame[['sample_id', 'source_type', 'group_id', '_chars', '_truncated']].rename(
        columns={'_chars': 'chars', '_truncated': 'truncated'})
    print(show.to_string(index=False))
    print(f'Saved: local/{name}.csv')


if __name__ == '__main__':
    main()
