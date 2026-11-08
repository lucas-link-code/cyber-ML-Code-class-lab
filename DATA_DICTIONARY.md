# Data dictionary

All data is UTF-8 CSV, fully synthetic and inert. The generator draws the
label first, then assembles each sample from code fragments that appear with a
class-conditional probability. Because those probabilities overlap, no single
token decides the class.

## `datasets/code_samples.csv` (3,000 rows)

| Column | Meaning | Modelling role |
| --- | --- | --- |
| `sample_id` | Unique `CJS-######` record key | Identifier; never a feature |
| `source_type` | `js` or `html` (html if the sample writes a tag) | Context; not a training feature here |
| `family` | Template family, e.g. `M_obf_eval`, `B_suspicious` | Grouping and error analysis; never a feature |
| `group_id` | Near-duplicate cluster id | Split grouping only; never a feature |
| `code` | The synthetic JavaScript or HTML snippet | Raw input; features are derived from it |
| `label` | `1` malicious, `0` benign | Target; never a training input |

`datasets/code_samples_challenge.csv` (1,200 rows) uses the same schema with a
distribution shift: more benign minified code carrying a `_0x` hex-array
identifier, which raises false positives for pattern-based detection.

## Families

Family names are for inspection, not training. Malicious families are named
after the dominant suspicious fragment the sample used:

- `M_obf_eval`, `M_fromchar`, `M_hexblob`, `M_iframe`, `M_beacon`,
  `M_hexarr_exec`, `M_unescape`, `M_settimeout_uni` — a strong marker is present.
- `M_stealth_dualonly` — a malicious sample that used only dual-use or ordinary
  fragments and therefore looks benign. These are the realistic false negatives.

Benign families:

- `B_plain` — ordinary script, no suspicious tokens.
- `B_dual` — benign code that legitimately uses a dual-use token (eval of a
  config literal, `new Function` templating, `atob` of data, a written script tag).
- `B_suspicious` — benign code that happened to include a strong-looking marker.
  These are the realistic false positives.

## Features

`scripts/lab_common.py` turns each `code` string into ~48 numeric features.
They are generic and publicly documented, not an encoding of any private rule:

- Size and shape: length, line count, longest line, bracket density.
- Obfuscation signals: Shannon entropy, hex escapes (`\xHH`), unicode escapes
  (`\uHHHH`), percent escapes (`%HH`), base64-looking blobs, `_0x` hex-array
  markers, long string literals, string-concatenation operators,
  non-ASCII ratio, digit ratio, average and unique identifier length.
- Sink-token frequencies (normalised per 1,000 characters): `eval`, `atob`,
  `unescape`, `fromCharCode`, `document.write`, `setTimeout`, `Function`,
  `createElement`, `addEventListener`, `fetch`, `cookie` and more.

The character n-gram feature set (`--features ngram`) is learned by a TF-IDF
vectoriser on the training split only.

## Safeguards

1. Every network reference uses the reserved `.example` space. No live
   indicator, real host or working payload appears anywhere.
2. Every encoded blob decodes to a harmless no-op such as `void 0;`.
3. `sample_id`, `family`, `group_id` and `label` are never training features.
4. Preprocessing (scaling, the TF-IDF vocabulary) is fitted on training rows
   only. Near-duplicate clusters share a `group_id` so the honest split keeps
   them on one side.
5. The data regenerates deterministically from fixed seeds. Numbers may differ
   in the last decimals across library versions.
