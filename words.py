#!/usr/bin/env python3
"""words.py - count the words in one UTF-8 text file.

The product is this single file. It takes one positional path, reads the file
with an explicit ``encoding='utf-8'`` (so the count never depends on the host
locale), counts whitespace-separated tokens with ``str.split()`` and writes one
integer plus a newline to stdout. Errors are one short line on stderr.

Exit codes: 0 success, 1 file or decoding error, 2 usage error.
"""

from __future__ import annotations

import os
import sys
from typing import IO, Sequence

PROGRAM = "words.py"
USAGE = f"usage: {PROGRAM} <file>"
DESCRIPTION = "Count the words in one UTF-8 text file."
INVOCATION = f"python {PROGRAM} <file>"
RUN_IT_AS = f"run it as: {INVOCATION}"

EXIT_OK = 0
EXIT_FILE_ERROR = 1
EXIT_USAGE_ERROR = 2

# Design tokens for this tool's only surface, the terminal: dark background,
# one monospace ramp, one accent. The accent is #008e9a (oklch(0.58 0.12 203)).
# Colour is emitted only for an interactive stdout, so piped output stays plain
# text and `words.py f.txt | wc -l` keeps working.
ACCENT_HEX = "#008e9a"
_ACCENT_ANSI = "\x1b[38;2;0;142;154m"
_RESET_ANSI = "\x1b[0m"
_RULE = "\u2500" * len(DESCRIPTION)


class UsageError(Exception):
    """The command line itself was wrong; the caller exits with code 2."""


class HelpRequested(Exception):
    """``-h`` / ``--help`` was used; print help and exit 0."""


def use_color(stream: IO[str]) -> bool:
    """True only when colour may safely reach an interactive terminal."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return bool(getattr(stream, "isatty", lambda: False)())


def style_accent(text: str, *, color: bool) -> str:
    """Wrap ``text`` in the accent colour when colour is enabled."""
    return f"{_ACCENT_ANSI}{text}{_RESET_ANSI}" if color else text


def help_text(*, color: bool = False) -> str:
    """The full help body. The usage line comes first so it can be copied."""
    lines = [
        USAGE,
        _RULE,
        DESCRIPTION,
        RUN_IT_AS,
        "",
        style_accent("options", color=color),
        "  -h, --help   Show this message and exit.",
        "  --           Treat every later argument as a file path.",
        "",
        style_accent("examples", color=color),
        f"  python {PROGRAM} sample.txt",
        f'  python {PROGRAM} "examples/caf\u00e9.txt"',
        f"  count=$(python {PROGRAM} sample.txt)",
        "",
        style_accent("exit codes", color=color),
        f"  {style_accent('0', color=color)}  success",
        f"  {style_accent('1', color=color)}  file or decoding error",
        f"  {style_accent('2', color=color)}  usage error",
    ]
    return "\n".join(lines) + "\n"


def parse_args(argv: Sequence[str]) -> str:
    """Return the single file path to count, or raise UsageError.

    ``-h``/``--help`` wins over any path and reads no file. A ``--`` token ends
    option parsing so a file may legitimately be named ``-x``.
    """
    positional: list[str] = []
    options_ended = False
    for token in argv:
        if options_ended:
            positional.append(token)
        elif token == "--":
            options_ended = True
        elif token in ("-h", "--help"):
            raise HelpRequested()
        elif token == "-":
            raise UsageError("reading from stdin is not supported, pass a file path")
        elif token.startswith("-"):
            raise UsageError(f"unknown option '{token}'")
        else:
            positional.append(token)

    if not positional:
        raise UsageError("missing file argument")
    if len(positional) > 1:
        raise UsageError(f"unexpected extra argument '{positional[1]}'")
    return positional[0]


def read_text(path: str) -> str:
    """Read ``path`` as UTF-8, whatever locale the machine happens to use."""
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def count_words(text: str) -> int:
    """Count whitespace-separated tokens; every run of whitespace separates."""
    return len(text.split())


def report_error(message: str) -> int:
    """One short line on stderr naming what was wrong; stderr, never stdout."""
    print(f"{PROGRAM}: {message}", file=sys.stderr)
    return EXIT_FILE_ERROR


def report_usage_error(message: str) -> int:
    """Name the misuse, repeat the usage line, exit 2."""
    print(f"{PROGRAM}: {message}", file=sys.stderr)
    print(USAGE, file=sys.stderr)
    print(RUN_IT_AS, file=sys.stderr)
    return EXIT_USAGE_ERROR


def count_file(path: str) -> int:
    """Print the word count for ``path`` and return the process exit code."""
    if os.path.isdir(path):
        return report_error(f"{path}: is a directory, not a file")
    try:
        text = read_text(path)
    except FileNotFoundError:
        return report_error(f"{path}: file not found")
    except IsADirectoryError:
        return report_error(f"{path}: is a directory, not a file")
    except UnicodeDecodeError:
        return report_error(f"{path}: not UTF-8 text")
    except PermissionError:
        return report_error(f"{path}: permission denied")
    except OSError as error:
        reason = error.strerror or type(error).__name__
        return report_error(f"{path}: cannot read file ({reason})")
    print(count_words(text))
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return the process exit code."""
    tokens = list(sys.argv[1:] if argv is None else argv)
    try:
        path = parse_args(tokens)
    except HelpRequested:
        print(help_text(color=use_color(sys.stdout)), end="")
        return EXIT_OK
    except UsageError as error:
        return report_usage_error(str(error))
    return count_file(path)


if __name__ == "__main__":
    sys.exit(main())
