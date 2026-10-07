# DocSearch

A small app that finds a word inside **every document in a folder** (subfolders included).

## What it can search

| Type | Extensions |
| --- | --- |
| Plain text & code | `.txt .md .csv .tsv .log .json .xml .html .yaml .ini .py .js .sql ...` |
| Microsoft Office | `.docx .xlsx .pptx` |
| OpenDocument | `.odt .ods .odp` |
| PDF | `.pdf` (needs `pypdf`) |

Old binary formats (`.doc`, `.xls`, `.ppt`) and scanned PDFs (images, no text layer) are not supported.

## Install

Python 3.8+ is all you need. For PDF support:

```bash
pip install -r requirements.txt
```

## Use the desktop window

```bash
python docsearch.py
```

1. Click **Browse...** and pick the folder.
2. Type the word and press **Enter** or **Search**.
3. Results show the file, where in the file (line / page / slide / sheet) and the surrounding text.
4. Double-click a result to open the file.

Options: **Match case**, **Whole word**, **Regular expression**. Press **Stop** to cancel a long search.

> The window uses Tkinter, which ships with Python on Windows and macOS.
> On Linux install it with `sudo apt install python3-tk` (or your distro's equivalent).

## Use the command line

```bash
python docsearch.py "C:\Users\me\Documents" invoice
python docsearch.py ~/Documents invoice --whole-word
python docsearch.py ~/Documents "inv(oice)?s?" --regex --files-only
```

| Option | Meaning |
| --- | --- |
| `-c`, `--match-case` | case-sensitive search |
| `-w`, `--whole-word` | match whole words only |
| `-r`, `--regex` | treat the search text as a regular expression |
| `-l`, `--files-only` | print only the names of matching files |
| `--gui` | open the window, with the folder pre-filled |

Example output:

```
letter.docx [document #2]: Please pay the invoice today
report.pdf [page 2]: An invoice on page two
sub/book.xlsx [sheet1 #2]: Invoice 42

3 match(es) in 3 of 9 file(s).
```

The exit code is `0` when something was found and `1` when nothing was found.
