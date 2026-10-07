#!/usr/bin/env python3
"""DocSearch - find a word inside every document in a folder.

Searches plain-text files (txt, md, csv, json, code, ...), Office documents
(docx, xlsx, pptx), OpenDocument files (odt, ods, odp) and PDFs (needs the
optional `pypdf` package). Subfolders are searched too.

Usage:
    python docsearch.py                      # open the website (same as docsearch_web.py)
    python docsearch.py FOLDER WORD [opts]   # search from the command line
"""

import argparse
import os
import re
import sys
import zipfile
from dataclasses import dataclass
from xml.etree import ElementTree

TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".rst", ".csv", ".tsv", ".log", ".json",
    ".xml", ".html", ".htm", ".yaml", ".yml", ".ini", ".cfg", ".conf", ".toml",
    ".py", ".js", ".ts", ".java", ".c", ".h", ".cpp", ".cs", ".go", ".rb",
    ".php", ".sh", ".bat", ".ps1", ".sql", ".css", ".rtf", ".tex",
}
OFFICE_EXTENSIONS = {".docx", ".xlsx", ".pptx", ".odt", ".ods", ".odp"}
PDF_EXTENSIONS = {".pdf"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | OFFICE_EXTENSIONS | PDF_EXTENSIONS

# File-type groups the user can pick from (CLI --type and the website filters).
FILE_TYPES = {
    "pdf": {".pdf"},
    "word": {".docx", ".odt", ".rtf"},
    "excel": {".xlsx", ".ods", ".csv", ".tsv"},
    "powerpoint": {".pptx", ".odp"},
    "text": TEXT_EXTENSIONS - {".rtf", ".csv", ".tsv"},
}


def extensions_for(types):
    """Extensions belonging to the given FILE_TYPES names."""
    return set().union(*(FILE_TYPES[t] for t in types))

# Parts of each zipped format that hold the visible text.
OFFICE_PARTS = {
    ".docx": re.compile(r"word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml$"),
    ".xlsx": re.compile(r"xl/(sharedStrings|worksheets/sheet\d+)\.xml$"),
    ".pptx": re.compile(r"ppt/(slides/slide\d+|notesSlides/notesSlide\d+)\.xml$"),
    ".odt": re.compile(r"content\.xml$"),
    ".ods": re.compile(r"content\.xml$"),
    ".odp": re.compile(r"content\.xml$"),
}
# XML elements that end a line/paragraph, so matches can be shown in context.
BLOCK_TAGS = {"p", "tr", "row", "si", "br", "h", "list-item", "table-row", "sp"}


@dataclass
class Match:
    path: str
    location: str  # "line 12", "page 3", ...
    snippet: str


class ExtractionError(Exception):
    pass


def _xml_lines(data):
    """Turn an Office/OpenDocument XML part into lines of plain text."""
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as exc:
        raise ExtractionError(f"bad XML: {exc}") from exc
    lines, current = [], []

    def walk(elem):
        tag = elem.tag.rsplit("}", 1)[-1]
        if tag == "c" and elem.get("t") == "s":
            # Excel cell holding an index into sharedStrings.xml (searched separately).
            return
        if elem.text and tag in ("t", "v", "span", "p", "h", "s"):
            current.append(elem.text)
        elif tag == "tab":
            current.append("\t")
        for child in elem:
            walk(child)
            if child.tail and tag in ("p", "h", "span"):
                current.append(child.tail)
        if tag in BLOCK_TAGS:
            line = "".join(current).strip()
            if line:
                lines.append(line)
            current.clear()
        elif tag in ("c", "tc", "table-cell"):
            current.append("  ")

    walk(root)
    tail = "".join(current).strip()
    if tail:
        lines.append(tail)
    return lines


def _natural_key(name):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", name)]


def extract(path):
    """Yield (location, text) pairs for every line of readable text in a file."""
    ext = os.path.splitext(path)[1].lower()
    if ext in TEXT_EXTENSIONS:
        with open(path, "rb") as fh:
            raw = fh.read()
        encodings = ("utf-16",) if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else ("utf-8-sig", "cp1252")
        text = None
        for encoding in encodings:
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            text = raw.decode("latin-1")
        for number, line in enumerate(text.splitlines(), 1):
            yield f"line {number}", line
    elif ext in OFFICE_EXTENSIONS:
        try:
            with zipfile.ZipFile(path) as archive:
                parts = sorted((n for n in archive.namelist() if OFFICE_PARTS[ext].search(n)), key=_natural_key)
                for part in parts:
                    label = os.path.splitext(os.path.basename(part))[0]
                    for number, line in enumerate(_xml_lines(archive.read(part)), 1):
                        yield f"{label} #{number}", line
        except zipfile.BadZipFile as exc:
            raise ExtractionError("not a valid document (corrupt or password protected)") from exc
    elif ext in PDF_EXTENSIONS:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ExtractionError("install 'pypdf' to search PDFs (pip install pypdf)") from exc
        try:
            reader = PdfReader(path)
            for page_number, page in enumerate(reader.pages, 1):
                for line in (page.extract_text() or "").splitlines():
                    yield f"page {page_number}", line
        except Exception as exc:  # pypdf raises many different error types
            raise ExtractionError(f"could not read PDF: {exc}") from exc


def build_pattern(word, match_case=False, whole_word=False, use_regex=False):
    expression = word if use_regex else re.escape(word)
    if whole_word:
        expression = rf"(?<!\w){expression}(?!\w)"
    return re.compile(expression, 0 if match_case else re.IGNORECASE)


def iter_files(folder, extensions=None):
    allowed = SUPPORTED_EXTENSIONS if extensions is None else extensions
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in sorted(filenames):
            # Skip Office lock files such as "~$report.docx".
            if name.startswith("~$"):
                continue
            if os.path.splitext(name)[1].lower() in allowed:
                yield os.path.join(dirpath, name)


def search_folder(folder, pattern, on_match=None, on_error=None, on_file=None, stop_event=None,
                  extensions=None):
    """Search every supported file under `folder`. Returns (matches, files_scanned)."""
    matches, scanned = [], 0
    for path in iter_files(folder, extensions):
        if stop_event is not None and stop_event.is_set():
            break
        scanned += 1
        if on_file:
            on_file(path, scanned)
        try:
            for location, line in extract(path):
                if pattern.search(line):
                    match = Match(path, location, _snippet(line, pattern))
                    matches.append(match)
                    if on_match:
                        on_match(match)
                    if stop_event is not None and stop_event.is_set():
                        break
        except (OSError, ExtractionError) as exc:
            if on_error:
                on_error(path, str(exc))
    return matches, scanned


def _snippet(line, pattern, width=160):
    line = " ".join(line.split())
    if len(line) <= width:
        return line
    found = pattern.search(line)
    start = max(0, found.start() - width // 3) if found else 0
    text = line[start:start + width]
    return ("..." if start else "") + text + ("..." if start + width < len(line) else "")


def open_with_default_app(path):
    if sys.platform.startswith("win"):
        os.startfile(path)  # noqa: S606 - opening a user-selected file
    else:
        import subprocess
        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", path])


# --------------------------------------------------------------------------- CLI

def run_cli(args):
    if not os.path.isdir(args.folder):
        print(f"Folder not found: {args.folder}", file=sys.stderr)
        return 2
    try:
        pattern = build_pattern(args.word, args.match_case, args.whole_word, args.regex)
    except re.error as exc:
        print(f"Invalid regular expression: {exc}", file=sys.stderr)
        return 2

    files_with_hits = set()

    def show(match):
        rel = os.path.relpath(match.path, args.folder)
        if args.files_only:
            if match.path not in files_with_hits:
                print(rel)
        else:
            print(f"{rel} [{match.location}]: {match.snippet}")
        files_with_hits.add(match.path)

    def warn(path, message):
        print(f"! skipped {os.path.relpath(path, args.folder)}: {message}", file=sys.stderr)

    extensions = extensions_for(args.type) if args.type else None
    matches, scanned = search_folder(args.folder, pattern, on_match=show, on_error=warn, extensions=extensions)
    print(f"\n{len(matches)} match(es) in {len(files_with_hits)} of {scanned} file(s).", file=sys.stderr)
    return 0 if matches else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description="Search for a word inside all documents in a folder.")
    parser.add_argument("folder", nargs="?", help="folder to search (subfolders included)")
    parser.add_argument("word", nargs="?", help="word or phrase to find")
    parser.add_argument("-c", "--match-case", action="store_true", help="case-sensitive search")
    parser.add_argument("-w", "--whole-word", action="store_true", help="match whole words only")
    parser.add_argument("-r", "--regex", action="store_true", help="treat WORD as a regular expression")
    parser.add_argument("-l", "--files-only", action="store_true", help="only list the matching file names")
    parser.add_argument("-t", "--type", action="append", choices=sorted(FILE_TYPES),
                        help="only search this kind of file (repeat for several)")
    args = parser.parse_args(argv)

    if args.word is None:
        if args.folder:
            parser.error("give both FOLDER and WORD, or neither to open the website")
        import docsearch_web
        return docsearch_web.main([])
    return run_cli(args)


if __name__ == "__main__":
    sys.exit(main())
