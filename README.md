# DocSearch

Find a word inside **every document in a folder** (subfolders included), from a web page in your browser.

DocSearch runs a small web server **on your own computer only** (`127.0.0.1`). Your files never leave your
machine, and nobody else on the network can open the page.

## What it can search

| Type | Extensions |
| --- | --- |
| PDF | `.pdf` (needs `pypdf`) |
| Word | `.docx .odt .rtf` |
| Excel | `.xlsx .ods .csv .tsv` |
| PowerPoint | `.pptx .odp` |
| Text & code | `.txt .md .log .json .xml .html .yaml .ini .py .js .sql ...` |

Old binary formats (`.doc`, `.xls`, `.ppt`) and scanned PDFs (images with no text layer) are not supported.

## Install

You need Python 3.8 or newer. For PDF support:

```bash
pip install -r requirements.txt
```

## Start the website

```bash
python docsearch_web.py
```

Your browser opens at `http://localhost:8765/`. Keep the Python window open while you use the page. Press
**Ctrl+C** in it to stop.

On the page:

1. Type or paste a folder path, or click **Browse…** to pick one.
2. Type the word and press **Enter** or **Search**. Results appear while the search runs. Press **Stop** to cancel.
3. Results are **grouped by file**, with the number of matches and the searched word **highlighted**.
   Each line shows where the match is (line, page, slide or sheet).
4. Click **Open** to open a file in its normal app (Word, Acrobat, Excel...), or **Show folder** to open the folder it is in.

Options:

- **Match case**, **Whole word**, **Regular expression**
- **File types**: click the PDF / Word / Excel / PowerPoint / Text & code chips to include or exclude them.

The page remembers the last folder, options and file types you used. At most 5,000 matches are shown; if you
reach that limit, search for something more specific.

Options for the server:

| Option | Meaning |
| --- | --- |
| `--port 9000` | use another port (default 8765; the next free one is picked if it's busy) |
| `--no-browser` | don't open the browser automatically |

## Command line (optional)

The same search also works without the website:

```bash
python docsearch.py "C:\Users\me\Documents" invoice
python docsearch.py ~/Documents invoice --whole-word --type pdf --type word
python docsearch.py ~/Documents "inv(oice)?s?" --regex --files-only
```

| Option | Meaning |
| --- | --- |
| `-c`, `--match-case` | case-sensitive search |
| `-w`, `--whole-word` | match whole words only |
| `-r`, `--regex` | treat the search text as a regular expression |
| `-l`, `--files-only` | print only the names of matching files |
| `-t`, `--type` | only search `pdf`, `word`, `excel`, `powerpoint` or `text` files (repeatable) |

Running `python docsearch.py` with no arguments starts the website.

## Files

| File | Purpose |
| --- | --- |
| `docsearch.py` | search engine (reads the documents) and command line |
| `docsearch_web.py` | local web server for the website |
| `web/index.html` | the web page |
