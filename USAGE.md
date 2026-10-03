# USAGE.md

Walkthroughs of what `words.py` actually does. Every command below was run
against this checkout.

## Count a file

```console
$ python3 words.py sample.txt
30
$ echo $?
0
```

One integer, one newline, nothing else, and nothing on stderr.

## Count a non-ASCII UTF-8 file

```console
$ python3 words.py examples/café.txt
3
```

The file is opened as UTF-8 explicitly, so the result does not depend on the
machine's locale:

```console
$ LC_ALL=C python3 words.py examples/café.txt
3
```

## Empty and whitespace-only files

```console
$ python3 words.py examples/empty.txt
0
$ python3 words.py examples/whitespace.txt
0
```

## Help

```console
$ python3 words.py --help
usage: words.py <file>
───────────────────────────────────────
Count the words in one UTF-8 text file.
run it as: python words.py <file>

options
  -h, --help   Show this message and exit.
  --           Treat every later argument as a file path.

examples
  python words.py sample.txt
  python words.py "examples/café.txt"
  count=$(python words.py sample.txt)

exit codes
  0  success
  1  file or decoding error
  2  usage error
```

`-h` prints exactly the same text on stdout and exits 0. A help flag wins over a
path, so `python3 words.py --help bogus.txt` still exits 0 and reads no file.

## Feed the count to something else

```console
$ python3 words.py sample.txt | wc -l
1
$ count=$(python3 words.py sample.txt); echo "$count words"
30 words
```

## Failures, one line each

```console
$ python3 words.py missing.txt
words.py: missing.txt: file not found
$ echo $?
1

$ python3 words.py examples
words.py: examples: is a directory, not a file
$ echo $?
1

$ python3 words.py examples/not_utf8.bin
words.py: examples/not_utf8.bin: not UTF-8 text
$ echo $?
1

$ python3 words.py -x
words.py: unknown option '-x'
usage: words.py <file>
run it as: python words.py <file>
$ echo $?
2

$ python3 words.py
words.py: missing file argument
usage: words.py <file>
run it as: python words.py <file>
$ echo $?
2
```

No traceback reaches the user in any of these cases.

## A file whose name starts with a dash

`--` ends option parsing:

```console
$ python3 words.py -- -x
```

## Tests

```bash
python3 -m unittest test_words -v
```
