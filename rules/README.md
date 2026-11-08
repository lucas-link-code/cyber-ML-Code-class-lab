# Detection rules

This folder holds the regex rules the labeller turns into training labels.

## Files

- `sample_rules.txt` — generic, publicly documented indicators of suspicious
  browser JavaScript and HTML, in EKFiddle CustomRegexes format. Shipped so the
  lab runs out of the box. Not anyone's production rule set.
- `local/` — your own rules go here. This folder is git-ignored, so nothing you
  drop in it is ever committed or published.

## Format

One rule per line, tab separated:

```
Type <TAB> RuleName <TAB> Regex <TAB> optional comment
```

`Type` is one of `IP`, `URI`, `SourceCode`, `Headers`, `Hash`. Lines starting
with `#` are ignored. The labeller applies `SourceCode` rules to the `code`
column by default; pass `--types SourceCode,URI` to apply more.

## Using your own rules

Drop a CustomRegexes file into `local/`:

```
cp /path/to/CustomRegexes.txt rules/local/
python scripts/ekfiddle_label.py            # auto-detects the file in local/
```

The labeller resolves rules in this order: `--rules PATH`, then the first
`*.txt` in `rules/local/`, then `sample_rules.txt`.

## A note on provenance

The shipped lab, its synthetic corpus and every exercise use only
`sample_rules.txt`. If you train a model with your own private rules, keep that
model and its training data out of any repository you publish. The cleanest
public artefact is one trained on the shipped synthetic corpus, whose
provenance is entirely in this repository.
