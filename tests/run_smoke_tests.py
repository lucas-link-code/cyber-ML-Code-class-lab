"""Run representative command lines. Invoke from the lab root:
    python tests/run_smoke_tests.py
Writes files prefixed _smoke_ into outputs/ and charts/.
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    cmds = [
        ['scripts/generate_dataset.py'],
        ['scripts/verify_lab.py'],
        ['scripts/inspect_data.py', '--rows', '3'],
        ['scripts/ekfiddle_label.py', '--name', '_smoke_weak'],
        ['scripts/run_classification.py', '--name', '_smoke_lexical'],
        ['scripts/run_classification.py', '--features', 'ngram', '--algorithm', 'random_forest', '--name', '_smoke_ngram'],
        ['scripts/run_classification.py', '--split', 'random', '--name', '_smoke_random'],
        ['scripts/run_classification.py', '--add-rule-hits', '--name', '_smoke_leaky'],
        ['scripts/compare_models.py', '_smoke_lexical', '_smoke_ngram', '--name', '_smoke_compare'],
        ['scripts/inspect_errors.py', '--experiment', '_smoke_lexical', '--type', 'fp', '--rows', '3'],
        ['scripts/rule_vs_model.py', '--name', '_smoke_rvm'],
        ['scripts/export_candidate_yara.py', '--name', '_smoke_yara'],
    ]
    for cmd in cmds:
        print('RUN:', sys.executable, *cmd, flush=True)
        p = subprocess.run([sys.executable, *cmd], cwd=ROOT,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if p.returncode:
            print(p.stdout[-3000:])
            raise SystemExit(f'FAILED: {cmd} (exit {p.returncode})')
        print('PASS', cmd[0], flush=True)
    print('All representative command-line smoke tests passed.')


if __name__ == '__main__':
    main()
