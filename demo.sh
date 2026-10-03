#!/usr/bin/env bash
#
# demo.sh - the non-interactive, end-to-end demo of words.py.
#
# It prints the help screen, counts every bundled sample file, proves that
# stdout carries one integer even through a pipe, and walks the failure
# contract (one line on stderr, exit 1 or 2). No prompts, no network, no state
# written to disk; it always exits 0.
set -uo pipefail
cd "$(dirname "$0")"

PY="${PY:-python3}"
RULE="─────────────────────────────────────────────────"

run_step() {
  printf '\n$ %s\n' "$*"
  "$@"
  printf '[exit %d]\n' "$?"
  return 0
}

printf 'words.py — count the words in one UTF-8 text file\n%s\n' "$RULE"

run_step "$PY" words.py --help

printf '\ncounts\n'
for path in sample.txt examples/notes.txt examples/café.txt examples/empty.txt examples/whitespace.txt; do
  count="$("$PY" words.py "$path")"
  printf '%7s  %s\n' "$count" "$path"
done

printf '\none integer on stdout, so pipes and command substitution keep working\n'
printf '$ %s\n' "$PY words.py sample.txt | wc -l"
"$PY" words.py sample.txt | wc -l
printf '$ %s\n' 'count=$('"$PY"' words.py sample.txt); echo "$count words"'
count="$("$PY" words.py sample.txt)"
printf '%s words\n' "$count"

printf '\nfailures: one line on stderr, never a traceback\n'
run_step "$PY" words.py missing.txt
run_step "$PY" words.py examples
run_step "$PY" words.py examples/not_utf8.bin
run_step "$PY" words.py -x
run_step "$PY" words.py

printf '\ndone — exit codes: 0 success, 1 file or decoding error, 2 usage error\n'
exit 0
