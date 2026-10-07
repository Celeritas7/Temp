#!/usr/bin/env python3
"""DocSearch - find a word inside every document in a folder.

Searches plain-text files (txt, md, csv, json, code, ...), Office documents
(docx, xlsx, pptx), OpenDocument files (odt, ods, odp) and PDFs (needs the
optional `pypdf` package). Subfolders are searched too.

Usage:
    python docsearch.py                      # open the desktop window
    python docsearch.py FOLDER WORD [opts]   # search from the command line
"""

import argparse
import os
import re
import sys
import threading
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
    allowed = extensions or SUPPORTED_EXTENSIONS
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in sorted(filenames):
            # Skip Office lock files such as "~$report.docx".
            if name.startswith("~$"):
                continue
            if os.path.splitext(name)[1].lower() in allowed:
                yield os.path.join(dirpath, name)


def search_folder(folder, pattern, on_match=None, on_error=None, on_file=None, stop_event=None):
    """Search every supported file under `folder`. Returns (matches, files_scanned)."""
    matches, scanned = [], 0
    for path in iter_files(folder):
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

    matches, scanned = search_folder(args.folder, pattern, on_match=show, on_error=warn)
    print(f"\n{len(matches)} match(es) in {len(files_with_hits)} of {scanned} file(s).", file=sys.stderr)
    return 0 if matches else 1


# --------------------------------------------------------------------------- GUI

def run_gui(initial_folder=""):
    import queue
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title("DocSearch - find words in documents")
    root.geometry("980x600")
    root.minsize(640, 400)

    folder_var = tk.StringVar(value=initial_folder)
    word_var = tk.StringVar()
    case_var = tk.BooleanVar()
    whole_var = tk.BooleanVar()
    regex_var = tk.BooleanVar()
    status_var = tk.StringVar(value="Choose a folder, type a word and press Search.")
    events = queue.Queue()
    state = {"stop": None}

    top = ttk.Frame(root, padding=10)
    top.pack(fill="x")
    top.columnconfigure(1, weight=1)

    ttk.Label(top, text="Folder:").grid(row=0, column=0, sticky="w")
    ttk.Entry(top, textvariable=folder_var).grid(row=0, column=1, sticky="ew", padx=6)

    def browse():
        chosen = filedialog.askdirectory(initialdir=folder_var.get() or os.path.expanduser("~"))
        if chosen:
            folder_var.set(chosen)

    ttk.Button(top, text="Browse...", command=browse).grid(row=0, column=2)

    ttk.Label(top, text="Search for:").grid(row=1, column=0, sticky="w", pady=(8, 0))
    word_entry = ttk.Entry(top, textvariable=word_var)
    word_entry.grid(row=1, column=1, sticky="ew", padx=6, pady=(8, 0))
    search_button = ttk.Button(top, text="Search")
    search_button.grid(row=1, column=2, pady=(8, 0))

    options = ttk.Frame(top)
    options.grid(row=2, column=1, sticky="w", pady=(6, 0))
    ttk.Checkbutton(options, text="Match case", variable=case_var).pack(side="left")
    ttk.Checkbutton(options, text="Whole word", variable=whole_var).pack(side="left", padx=12)
    ttk.Checkbutton(options, text="Regular expression", variable=regex_var).pack(side="left")

    table_frame = ttk.Frame(root, padding=(10, 0))
    table_frame.pack(fill="both", expand=True)
    columns = ("file", "where", "text")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")
    for column, title, width in (("file", "File", 260), ("where", "Location", 110), ("text", "Text", 560)):
        tree.heading(column, text=title)
        tree.column(column, width=width, anchor="w", stretch=column != "where")
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    ttk.Label(root, textvariable=status_var, padding=10).pack(fill="x")
    paths = {}

    def open_selected(_event=None):
        for item in tree.selection():
            try:
                open_with_default_app(paths[item])
            except OSError as exc:
                messagebox.showerror("DocSearch", f"Could not open file:\n{exc}")

    tree.bind("<Double-1>", open_selected)
    tree.bind("<Return>", open_selected)

    def start_search(_event=None):
        if state["stop"] is not None:  # a search is running: this button stops it
            state["stop"].set()
            return
        folder, word = folder_var.get().strip(), word_var.get()
        if not os.path.isdir(folder):
            messagebox.showwarning("DocSearch", "Please choose an existing folder.")
            return
        if not word:
            messagebox.showwarning("DocSearch", "Please type a word to search for.")
            return
        try:
            pattern = build_pattern(word, case_var.get(), whole_var.get(), regex_var.get())
        except re.error as exc:
            messagebox.showerror("DocSearch", f"Invalid regular expression:\n{exc}")
            return

        tree.delete(*tree.get_children())
        paths.clear()
        stop = threading.Event()
        state.update(stop=stop, folder=folder, errors=0)
        search_button.configure(text="Stop")

        def worker():
            result = search_folder(
                folder, pattern,
                on_match=lambda m: events.put(("match", m)),
                on_error=lambda p, e: events.put(("error", p)),
                on_file=lambda p, n: events.put(("file", n)),
                stop_event=stop,
            )
            events.put(("done", result))

        threading.Thread(target=worker, daemon=True).start()

    def poll():
        try:
            while True:
                kind, payload = events.get_nowait()
                if kind == "match":
                    item = tree.insert("", "end", values=(
                        os.path.relpath(payload.path, state["folder"]), payload.location, payload.snippet))
                    paths[item] = payload.path
                elif kind == "file":
                    status_var.set(f"Searching... {payload} file(s) checked, {len(paths)} match(es)")
                elif kind == "error":
                    state["errors"] += 1
                elif kind == "done":
                    matches, scanned = payload
                    files = len({m.path for m in matches})
                    stopped = " (stopped)" if state["stop"].is_set() else ""
                    skipped = f", {state['errors']} unreadable file(s) skipped" if state["errors"] else ""
                    status_var.set(f"{len(matches)} match(es) in {files} of {scanned} file(s){stopped}{skipped}."
                                   " Double-click a result to open the file.")
                    state["stop"] = None
                    search_button.configure(text="Search")
        except queue.Empty:
            pass
        root.after(100, poll)

    search_button.configure(command=start_search)
    word_entry.bind("<Return>", start_search)
    word_entry.focus_set()
    poll()
    root.mainloop()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Search for a word inside all documents in a folder.")
    parser.add_argument("folder", nargs="?", help="folder to search (subfolders included)")
    parser.add_argument("word", nargs="?", help="word or phrase to find")
    parser.add_argument("-c", "--match-case", action="store_true", help="case-sensitive search")
    parser.add_argument("-w", "--whole-word", action="store_true", help="match whole words only")
    parser.add_argument("-r", "--regex", action="store_true", help="treat WORD as a regular expression")
    parser.add_argument("-l", "--files-only", action="store_true", help="only list the matching file names")
    parser.add_argument("--gui", action="store_true", help="open the desktop window")
    args = parser.parse_args(argv)

    if args.gui or args.word is None:
        try:
            run_gui(args.folder or "")
        except ImportError:
            parser.error("the desktop window needs Tkinter; pass FOLDER and WORD to use the command line")
        return 0
    return run_cli(args)


if __name__ == "__main__":
    sys.exit(main())
