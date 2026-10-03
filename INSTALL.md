# INSTALL.md

`words.py` is one file on the Python standard library. There is **nothing to
install**: no package manager, no lockfile, no virtualenv, no build step and no
configuration file.

## 1. Prerequisite

- Python **3.9 or newer**, available as `python3` (3.11 is what it is tested on).

Check it:

```bash
python3 --version
```

If the command is missing, install Python from your operating system's own
package source. `install.sh` will not do that for you: it never installs system
packages and never needs `sudo`.

There is no package manager step, because there is no dependency manifest: the
program imports only `os` and `sys` from the standard library.

## 2. Verify the checkout (optional, safe to re-run)

```bash
bash install.sh
```

It checks the interpreter version, imports `words.py`, counts `sample.txt` once
as a smoke test, prints the two run commands, and exits 0. It installs nothing,
writes no config, and never starts a long-running process.

## 3. Use it

```bash
python3 words.py sample.txt      # -> 30
python3 words.py --help
```

Point it at any file you like:

```bash
python3 words.py ~/draft.md
```

## 4. Try the demo (non-interactive)

```bash
bash demo.sh
```

Prints help, counts every bundled sample, shows the pipeline contract and every
failure case with its exit code. It always exits 0 and never prompts.

## 5. Run the tests

```bash
python3 -m unittest test_words -v
```

Standard library only (`unittest`, `subprocess`, `tempfile`, `ast`); `pytest`
runs the same suite if it happens to be installed. The suite works offline.

## Environment variables

None are required — the tool reads its input from the path you pass, writes the
count to stdout, errors to stderr, and keeps no state on disk. `NO_COLOR` is
honoured for the `--help` screen; `PY` overrides the interpreter used by
`demo.sh` and `install.sh` chooses `PYTHON` for the same purpose.
