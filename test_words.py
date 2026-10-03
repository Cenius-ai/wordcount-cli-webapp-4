"""Contract tests for words.py.

Every test runs the shipped CLI as a subprocess, because the contract is what
the process does: the bytes on stdout, the text on stderr and the exit code.
Only the standard library is used, so `python3 -m unittest test_words -v` and
`pytest` both work on a checkout with nothing installed.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import words

REPO_ROOT = Path(__file__).resolve().parent
CLI = REPO_ROOT / "words.py"
SAMPLE = REPO_ROOT / "sample.txt"
SAMPLE_WORDS = 30
USAGE_LINE = "usage: words.py <file>"
INVOCATION_LINE = "run it as: python words.py <file>"
STDLIB_IMPORTS = {"os", "sys", "typing", "__future__"}

C_LOCALE_ENV = {
    **os.environ,
    "LC_ALL": "C",
    "LANG": "C",
    "PYTHONUTF8": "0",
    "PYTHONCOERCECLOCALE": "0",
}


def run_cli(*args: str, cwd: Path | None = None, env: dict[str, str] | None = None):
    """Run the CLI in a subprocess and capture stdout, stderr and exit code."""
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=str(cwd or REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class TempFilesTestCase(unittest.TestCase):
    """Shared scratch directory for tests that need throwaway input files."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory(prefix="words-test-")
        cls.tmp = Path(cls._tmp.name)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def write(self, name: str, text: str) -> Path:
        path = self.tmp / name
        path.write_text(text, encoding="utf-8")
        return path


class CountTests(TempFilesTestCase):
    """F1 - count words in a text file."""

    def assert_counts(self, path: Path, expected: int) -> None:
        result = run_cli(str(path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, f"{expected}\n")

    def test_counts_ascii_words(self) -> None:
        path = self.write("fox.txt", "the quick brown fox")
        result = run_cli(str(path))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "4\n")

    def test_newline_separates_words(self) -> None:
        self.assert_counts(self.write("lines.txt", "hello world\nbye"), 3)

    def test_whitespace_run_counts_once(self) -> None:
        self.assert_counts(self.write("tabs.txt", "hello\t\tworld   bye"), 3)

    def test_trailing_newline_does_not_add_a_word(self) -> None:
        self.assert_counts(self.write("trailing.txt", "one two three\n"), 3)

    def test_empty_file_is_zero(self) -> None:
        self.assert_counts(self.write("empty.txt", ""), 0)

    def test_whitespace_only_file_is_zero(self) -> None:
        self.assert_counts(self.write("spaces.txt", "   \n\t \n"), 0)

    def test_counts_non_ascii_utf8_text(self) -> None:
        self.assert_counts(self.write("utf8.txt", "caf\u00e9 d\u00e9j\u00e0 vu"), 3)

    def test_counts_non_ascii_utf8_text_under_c_locale(self) -> None:
        path = self.write("utf8-c.txt", "caf\u00e9 d\u00e9j\u00e0 vu")
        result = run_cli(str(path), env=C_LOCALE_ENV)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "3\n")
        # Control: if the host's default codec really is not UTF-8, reading
        # without the explicit encoding fails — which is exactly what the
        # explicit encoding in words.py prevents.
        control = subprocess.run(
            [sys.executable, "-c", "open(__import__('sys').argv[1]).read()", str(path)],
            env=C_LOCALE_ENV,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if control.returncode != 0:
            self.assertIn("UnicodeDecodeError", control.stderr)

    def test_stdout_is_exactly_one_integer_line(self) -> None:
        result = run_cli(str(self.write("format.txt", "alpha beta gamma")))
        self.assertRegex(result.stdout, re.compile(r"\A\d+\n\Z"))

    def test_success_writes_nothing_to_stderr(self) -> None:
        result = run_cli(str(self.write("quiet.txt", "alpha beta")))
        self.assertEqual(result.stderr, "")

    def test_counts_bundled_sample_file(self) -> None:
        self.assert_counts(SAMPLE, SAMPLE_WORDS)

    def test_runs_as_a_module_with_dash_m(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "words", str(SAMPLE)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, f"{SAMPLE_WORDS}\n")

    def test_counts_a_megabyte_in_well_under_two_seconds(self) -> None:
        path = self.write("big.txt", "word " * 200_000)
        started = time.monotonic()
        self.assert_counts(path, 200_000)
        self.assertLess(time.monotonic() - started, 2.0)


class FailureTests(TempFilesTestCase):
    """F2 - readable failures for bad input, never a traceback."""

    def assert_no_traceback(self, result) -> None:
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_path(self) -> None:
        result = run_cli(str(self.tmp / "nope.txt"))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("nope.txt", result.stderr)
        self.assertIn("file not found", result.stderr)
        self.assert_no_traceback(result)

    def test_directory(self) -> None:
        result = run_cli(str(self.tmp))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn(self.tmp.name, result.stderr)
        self.assertIn("directory", result.stderr)
        self.assert_no_traceback(result)

    def test_non_utf8_bytes(self) -> None:
        path = self.tmp / "not_utf8.bin"
        path.write_bytes(b"\xff\xfe\x00hi")
        result = run_cli(str(path))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("not_utf8.bin", result.stderr)
        self.assertIn("UTF-8", result.stderr)
        self.assert_no_traceback(result)

    def test_no_argument(self) -> None:
        result = run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn(USAGE_LINE, result.stderr)
        self.assertIn(INVOCATION_LINE, result.stderr)
        self.assert_no_traceback(result)

    def test_unknown_option(self) -> None:
        result = run_cli("-x")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn(USAGE_LINE, result.stderr)
        self.assertIn(INVOCATION_LINE, result.stderr)
        self.assertIn("-x", result.stderr)
        self.assert_no_traceback(result)

    def test_unknown_option_is_not_opened_as_a_filename(self) -> None:
        scratch = self.tmp / "dashfile"
        scratch.mkdir(exist_ok=True)
        (scratch / "-x").write_text("one two three", encoding="utf-8")
        result = run_cli("-x", cwd=scratch)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")

    def test_double_dash_allows_a_dash_named_file(self) -> None:
        scratch = self.tmp / "dashes"
        scratch.mkdir(exist_ok=True)
        (scratch / "-x").write_text("one two three", encoding="utf-8")
        result = run_cli("--", "-x", cwd=scratch)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "3\n")

    def test_extra_positional_argument(self) -> None:
        first = self.write("first.txt", "one")
        result = run_cli(str(first), str(first))
        self.assertEqual(result.returncode, 2)
        self.assertIn(USAGE_LINE, result.stderr)

    def test_stdin_is_not_read(self) -> None:
        result = run_cli("-")
        self.assertEqual(result.returncode, 2)
        self.assertIn(USAGE_LINE, result.stderr)


class HelpTests(unittest.TestCase):
    """F3 - -h / --help."""

    def test_long_help(self) -> None:
        result = run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertTrue(result.stdout.startswith(USAGE_LINE + "\n"), result.stdout)
        self.assertIn("Count the words in one UTF-8 text file.", result.stdout)
        self.assertIn(INVOCATION_LINE, result.stdout)
        self.assertIn("exit codes", result.stdout)

    def test_short_help_matches_long_help(self) -> None:
        self.assertEqual(run_cli("-h").stdout, run_cli("--help").stdout)

    def test_help_wins_over_a_path_without_reading_it(self) -> None:
        result = run_cli("--help", "bogus.txt")
        self.assertEqual(result.returncode, 0)
        self.assertIn(USAGE_LINE, result.stdout)
        self.assertNotIn("bogus.txt", result.stdout)
        self.assertNotIn("bogus.txt", result.stderr)
        self.assertEqual(result.stderr, "")

    def test_help_wins_when_the_flag_comes_last(self) -> None:
        result = run_cli("bogus.txt", "--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn(USAGE_LINE, result.stdout)


class SourceTests(unittest.TestCase):
    """Invariants about the single shipped file that must not regress."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.source = CLI.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_every_open_call_specifies_utf8(self) -> None:
        opens = [
            node
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "open"
        ]
        self.assertTrue(opens, "words.py should open the input file explicitly")
        for call in opens:
            encodings = [
                keyword.value.value
                for keyword in call.keywords
                if keyword.arg == "encoding" and isinstance(keyword.value, ast.Constant)
            ]
            self.assertEqual(
                encodings,
                ["utf-8"],
                f"open() at line {call.lineno} must pass encoding='utf-8'",
            )

    def test_imports_only_the_standard_library(self) -> None:
        imported: set[str] = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertTrue(imported <= STDLIB_IMPORTS, imported - STDLIB_IMPORTS)

    def test_no_single_file_violations(self) -> None:
        self.assertEqual(sorted(REPO_ROOT.glob("words*.py")), [CLI])


class UnitTests(unittest.TestCase):
    """The pure helpers, exercised in-process."""

    def test_count_words_collapses_whitespace(self) -> None:
        self.assertEqual(words.count_words("  a\t\tb\n\nc  "), 3)
        self.assertEqual(words.count_words(""), 0)
        self.assertEqual(words.count_words("caf\u00e9 d\u00e9j\u00e0 vu"), 3)

    def test_parse_args_returns_the_single_path(self) -> None:
        self.assertEqual(words.parse_args(["a.txt"]), "a.txt")
        self.assertEqual(words.parse_args(["--", "-x"]), "-x")

    def test_parse_args_rejects_misuse(self) -> None:
        for argv in ([], ["-x"], ["a.txt", "b.txt"], ["-"]):
            with self.subTest(argv=argv):
                with self.assertRaises(words.UsageError):
                    words.parse_args(argv)

    def test_parse_args_raises_help_requested(self) -> None:
        for argv in (["-h"], ["--help"], ["path.txt", "--help"]):
            with self.subTest(argv=argv):
                with self.assertRaises(words.HelpRequested):
                    words.parse_args(argv)

    def test_usage_line_is_the_documented_one(self) -> None:
        self.assertEqual(words.USAGE, USAGE_LINE)

    def test_help_renders_the_copy_pasteable_invocation(self) -> None:
        body = words.help_text()
        self.assertIn("python words.py <file>", body)
        self.assertEqual(words.INVOCATION, "python words.py <file>")


if __name__ == "__main__":
    unittest.main(verbosity=2)
