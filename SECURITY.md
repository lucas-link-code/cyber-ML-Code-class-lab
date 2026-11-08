# Security and safe handling

This lab is a teaching environment. It does not contain live malware.

## What ships here

- A synthetic, inert corpus of JavaScript and HTML. Every network reference
  uses the reserved `.example` domain space, every encoded blob decodes to a
  harmless no-op, and no sample performs a real action if executed. The code
  is written to carry the *shape* of suspicious browser script so a model can
  learn it, not to do anything.
- Generic, publicly documented sample detection rules in `rules/sample_rules.txt`.
- Python scripts that only read and parse code as text. Nothing in this lab
  downloads, executes, installs or evaluates a sample.

## If you bring your own samples

If you point the labeller at your own captured JavaScript or HTML, treat those
files as untrusted:

- Keep them under `rules/local/` or another git-ignored folder. Nothing in
  `rules/local/` is committed.
- Open and process them only on an isolated analysis machine or VM, never a
  production or daily-driver host.
- This lab never executes a sample. Do not add code that does.

## Reporting

For any concern about the content of this repository, open an issue or contact
the maintainer through the repository profile.
