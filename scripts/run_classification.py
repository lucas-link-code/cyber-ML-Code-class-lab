"""Train a malicious-vs-benign code classifier on the synthetic corpus.

Loads labelled code, turns it into features, fits a classifier on the
training split and scores the validation split (the final test split is
reserved). Writes metrics, per-sample predictions and charts, mirroring the
sibling Cyber ML Lab so the workflow feels familiar.

Examples:
  python scripts/run_classification.py --name first_run
  python scripts/run_classification.py --features ngram --algorithm random_forest --name rf_ngram
  python scripts/run_classification.py --split random --name leaky_split
"""
from __future__ import annotations
import argparse

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (ConfusionMatrixDisplay, PrecisionRecallDisplay,
                             RocCurveDisplay)
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
import matplotlib.pyplot as plt

from lab_common import (ROOT, featurize_frame, grouped_split, random_split,
                        classifier_metrics, save_result, format_table,
                        truncate_code, out_name)


def make_model(args):
    if args.algorithm == 'logistic':
        return LogisticRegression(max_iter=2000, C=args.c, random_state=42)
    if args.algorithm == 'tree':
        return DecisionTreeClassifier(max_depth=args.max_depth,
                                      min_samples_leaf=args.min_samples_leaf, random_state=42)
    if args.algorithm == 'random_forest':
        return RandomForestClassifier(n_estimators=args.n_estimators, max_depth=args.max_depth,
                                      min_samples_leaf=args.min_samples_leaf, n_jobs=-1,
                                      random_state=42)
    if args.algorithm == 'gradient_boosting':
        return GradientBoostingClassifier(n_estimators=args.n_estimators,
                                          max_depth=args.max_depth or 3, random_state=42)
    if args.algorithm == 'naive_bayes':
        return GaussianNB()
    raise ValueError(args.algorithm)


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dataset-file', default='datasets/code_samples.csv')
    ap.add_argument('--algorithm', default='logistic',
                    choices=['logistic', 'tree', 'random_forest', 'gradient_boosting', 'naive_bayes'])
    ap.add_argument('--features', default='lexical', choices=['lexical', 'ngram', 'all'])
    ap.add_argument('--split', default='group', choices=['group', 'random'],
                    help="group keeps a template family on one side; random is the leaky split")
    ap.add_argument('--threshold', type=float, default=0.5)
    ap.add_argument('--add-rule-hits', action='store_true',
                    help='add the rule-match count as a feature (demonstrates leakage)')
    ap.add_argument('--n-estimators', type=int, default=200)
    ap.add_argument('--max-depth', type=int, default=None)
    ap.add_argument('--min-samples-leaf', type=int, default=1)
    ap.add_argument('--c', type=float, default=1.0)
    ap.add_argument('--evaluate-test', action='store_true')
    ap.add_argument('--name', default='classification_baseline')
    args = ap.parse_args()
    if not 0 <= args.threshold <= 1:
        ap.error('--threshold must be between 0 and 1')
    return args


def build_matrix(frame, features, add_rule_hits):
    num = featurize_frame(frame)
    numeric_cols = list(num.columns)
    data = num.copy()
    data['code'] = frame['code'].to_numpy()
    if add_rule_hits:
        from ekfiddle_label import resolve_rules, parse_rules, apply_rules
        rules = parse_rules(resolve_rules(None))
        hits, _ = apply_rules(frame['code'].tolist(), rules)
        # store the count of matched rules
        counts = []
        for code in frame['code'].tolist():
            c = 0
            for _, rx, _ in rules:
                try:
                    if rx.search(str(code)):
                        c += 1
                except Exception:
                    pass
            counts.append(c)
        data['rule_hits'] = counts
        numeric_cols = numeric_cols + ['rule_hits']
    transformers = []
    if features in ('lexical', 'all'):
        transformers.append(('num', StandardScaler(), numeric_cols))
    if features in ('ngram', 'all'):
        transformers.append(('txt', TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4),
                                                     min_df=3, max_features=800), 'code'))
    pre = ColumnTransformer(transformers, remainder='drop', sparse_threshold=0)
    return data, pre


def main():
    args = parse_args()
    path = ROOT / args.dataset_file if not str(args.dataset_file).startswith('/') else args.dataset_file
    frame = pd.read_csv(path)
    for col in ('code', 'label', 'family'):
        if col not in frame:
            raise SystemExit(f"Dataset missing required column {col!r}")

    split = grouped_split(frame) if args.split == 'group' else random_split(frame)
    train = split['train']
    scored = split['test'] if args.evaluate_test else split['validation']

    data, pre = build_matrix(frame, args.features, args.add_rule_hits)
    model = Pipeline([('preprocessing', pre), ('model', make_model(args))])

    print(f'DATASET: {path.name} ({len(frame)} rows)')
    print(f'SPLIT: {args.split}  TRAIN {len(train)} | VALIDATION {len(split["validation"])} | TEST {len(split["test"])}')
    print(f'SCORING: {"FINAL TEST" if args.evaluate_test else "validation"}')
    print(f'FEATURES: {args.features}{" + rule_hits(LEAKY)" if args.add_rule_hits else ""}')
    print(f'ALGORITHM: {args.algorithm}; threshold={args.threshold}')

    y = frame['label'].to_numpy()
    model.fit(data.iloc[train], y[train])
    scores = model.predict_proba(data.iloc[scored])[:, 1]
    pred = (scores >= args.threshold).astype(int)
    actual = y[scored]
    metrics = classifier_metrics(actual, pred, scores)
    tr_scores = model.predict_proba(data.iloc[train])[:, 1]
    metrics['train_f1'] = float(classifier_metrics(
        y[train], (tr_scores >= args.threshold).astype(int), tr_scores)['f1'])

    preds = frame.iloc[scored][['sample_id', 'source_type', 'family']].copy()
    preds['actual_label'] = actual
    preds['predicted_label'] = pred
    preds['positive_probability'] = np.round(scores, 6)
    preds['error_type'] = np.select([(actual == 0) & (pred == 1), (actual == 1) & (pred == 0)],
                                     ['FP', 'FN'], default='correct')
    preds['code'] = [truncate_code(c) for c in frame.iloc[scored]['code']]

    print('\nCONFUSION MATRIX (rows=actual, columns=predicted)')
    print(pd.DataFrame([[metrics['tn'], metrics['fp']], [metrics['fn'], metrics['tp']]],
                       index=['actual 0', 'actual 1'], columns=['pred 0', 'pred 1']).to_string())
    format_table('SAMPLE PREDICTIONS', preds[['sample_id', 'family', 'actual_label',
                 'predicted_label', 'positive_probability', 'error_type']].head(12))

    config = {'problem': 'code_classification', 'dataset_file': path.name,
              'algorithm': args.algorithm, 'features': args.features, 'split': args.split,
              'threshold': args.threshold, 'add_rule_hits': args.add_rule_hits,
              'n_estimators': args.n_estimators, 'max_depth': args.max_depth,
              'min_samples_leaf': args.min_samples_leaf, 'c': args.c,
              'evaluation_split': 'test' if args.evaluate_test else 'validation'}

    def plot(prefix):
        fig, ax = plt.subplots(figsize=(5, 4))
        ConfusionMatrixDisplay.from_predictions(actual, pred, labels=[0, 1], ax=ax,
                                                cmap='Blues', colorbar=False)
        ax.set_title('Confusion | ' + args.name)
        fig.tight_layout(); fig.savefig(f'{prefix}_confusion.png', dpi=130); plt.close(fig)
        fig, ax = plt.subplots(figsize=(6, 4))
        PrecisionRecallDisplay.from_predictions(actual, scores, ax=ax)
        ax.set_title('Precision-recall | ' + args.name)
        fig.tight_layout(); fig.savefig(f'{prefix}_precision_recall.png', dpi=130); plt.close(fig)
        fig, ax = plt.subplots(figsize=(6, 4))
        RocCurveDisplay.from_predictions(actual, scores, ax=ax)
        ax.set_title('ROC | ' + args.name)
        fig.tight_layout(); fig.savefig(f'{prefix}_roc.png', dpi=130); plt.close(fig)
        inner = model.named_steps['model']
        try:
            names = model.named_steps['preprocessing'].get_feature_names_out()
        except Exception:
            names = None
        if names is not None and hasattr(inner, 'feature_importances_'):
            imp = np.asarray(inner.feature_importances_)
            order = np.argsort(imp)[-15:]
            fig, ax = plt.subplots(figsize=(7, 5))
            ax.barh(np.array(names)[order], imp[order])
            ax.set_xlabel('Impurity importance (not causal)')
            ax.set_title('Top features | ' + args.name)
            fig.tight_layout(); fig.savefig(f'{prefix}_feature_importance.png', dpi=130); plt.close(fig)
        elif names is not None and hasattr(inner, 'coef_'):
            coef = np.ravel(inner.coef_)
            order = np.argsort(np.abs(coef))[-15:]
            fig, ax = plt.subplots(figsize=(7, 5))
            ax.barh(np.array(names)[order], coef[order])
            ax.set_xlabel('Logistic weight (preprocessed space)')
            ax.set_title('Top weighted features | ' + args.name)
            fig.tight_layout(); fig.savefig(f'{prefix}_feature_importance.png', dpi=130); plt.close(fig)

    save_result(args.name, config, metrics, preds, plot)


if __name__ == '__main__':
    main()
