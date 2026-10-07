#!/usr/bin/env python3
"""DocSearch website - search inside documents from your browser.

Starts a small web server on this computer only (127.0.0.1) and opens the
page in your browser. Nobody else on the network can reach it.

Usage:
    python docsearch_web.py [--port 8765] [--no-browser]
"""

import argparse
import json
import os
import re
import string
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import docsearch

HOST = "127.0.0.1"
MAX_MATCHES = 5000  # keeps the page responsive; the user is asked to narrow the search
PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "index.html")
# Opening these with the default app would run them (e.g. .bat on Windows), so we show their folder instead.
RUNNABLE_EXTENSIONS = {".bat", ".ps1", ".sh", ".js", ".py", ".rb", ".php"}
TYPE_LABELS = {"pdf": "PDF", "word": "Word", "excel": "Excel", "powerpoint": "PowerPoint", "text": "Text & code"}


def _pdf_available():
    try:
        import pypdf  # noqa: F401
        return True
    except ImportError:
        return False


def _roots():
    """Starting points for the folder picker: drives on Windows, / elsewhere."""
    if sys.platform.startswith("win"):
        return [f"{letter}:\\" for letter in string.ascii_uppercase if os.path.isdir(f"{letter}:\\")]
    return ["/"]


def list_folders(path):
    path = os.path.abspath(os.path.expanduser(path or "~"))
    if not os.path.isdir(path):
        raise ValueError(f"Folder not found: {path}")
    folders = []
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.name.startswith((".", "$")):
                    continue
                try:
                    if entry.is_dir():
                        folders.append({"name": entry.name, "path": entry.path})
                except OSError:
                    continue
    except PermissionError as exc:
        raise ValueError(f"No permission to open {path}") from exc
    folders.sort(key=lambda f: f["name"].lower())
    parent = os.path.dirname(path)
    return {
        "path": path,
        "parent": parent if parent != path else None,
        "folders": folders,
        "home": os.path.expanduser("~"),
        "roots": _roots(),
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "DocSearch"

    # ------------------------------------------------------------ helpers
    def log_message(self, fmt, *args):  # keep the console quiet
        pass

    def _host_ok(self):
        # Blocks DNS-rebinding attacks: only answer requests addressed to this machine.
        port = self.server.server_address[1]
        return self.headers.get("Host", "") in (f"127.0.0.1:{port}", f"localhost:{port}")

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, message, status=400):
        self._send_json({"error": message}, status)

    # ------------------------------------------------------------ routes
    def do_GET(self):
        if not self._host_ok():
            return self._error("Forbidden", 403)
        url = urlparse(self.path)
        query = {k: v[-1] for k, v in parse_qs(url.query).items()}
        if url.path in ("/", "/index.html"):
            with open(PAGE, "rb") as fh:
                body = fh.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif url.path == "/api/info":
            self._send_json({
                "types": [{"id": t, "label": TYPE_LABELS[t], "extensions": sorted(docsearch.FILE_TYPES[t])}
                          for t in TYPE_LABELS],
                "pdf": _pdf_available(),
                "home": os.path.expanduser("~"),
            })
        elif url.path == "/api/folders":
            try:
                self._send_json(list_folders(query.get("path", "")))
            except ValueError as exc:
                self._error(str(exc))
        elif url.path == "/api/search":
            self._search(query)
        else:
            self._error("Not found", 404)

    def do_POST(self):
        if not self._host_ok():
            return self._error("Forbidden", 403)
        # A JSON content type cannot be sent cross-site without the browser asking first,
        # so other websites cannot make this server open files.
        if not self.headers.get("Content-Type", "").startswith("application/json"):
            return self._error("Expected JSON", 415)
        if urlparse(self.path).path != "/api/open":
            return self._error("Not found", 404)
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length) or b"{}")
            path = os.path.abspath(str(data["path"]))
        except (ValueError, KeyError, TypeError):
            return self._error("Bad request")
        if not os.path.isfile(path) or os.path.splitext(path)[1].lower() not in docsearch.SUPPORTED_EXTENSIONS:
            return self._error("File not found")
        runnable = os.path.splitext(path)[1].lower() in RUNNABLE_EXTENSIONS
        target = os.path.dirname(path) if data.get("what") == "folder" or runnable else path
        try:
            docsearch.open_with_default_app(target)
        except OSError as exc:
            return self._error(f"Could not open: {exc}", 500)
        self._send_json({"ok": True})

    # ------------------------------------------------------------ search (streamed)
    def _search(self, query):
        raw_folder = query.get("folder", "").strip()
        folder = os.path.abspath(os.path.expanduser(raw_folder)) if raw_folder else ""
        word = query.get("q", "")
        if not folder or not os.path.isdir(folder):
            return self._error("Please choose a folder that exists.")
        if not word:
            return self._error("Please type a word to search for.")
        types = [t for t in query.get("types", "").split(",") if t in docsearch.FILE_TYPES]
        if not types:
            return self._error("Please tick at least one file type.")
        try:
            pattern = docsearch.build_pattern(
                word, query.get("case") == "1", query.get("whole") == "1", query.get("regex") == "1")
        except re.error as exc:
            return self._error(f"Invalid regular expression: {exc}")

        # One JSON object per line; the page shows results while the search runs.
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        stop = threading.Event()
        client_gone = threading.Event()
        count = [0]

        def send(event):
            if client_gone.is_set():
                return
            try:
                self.wfile.write((json.dumps(event) + "\n").encode("utf-8"))
            except OSError:
                client_gone.set()  # the page pressed Stop or was closed
                stop.set()

        def rel(path):
            return os.path.relpath(path, folder)

        def on_match(match):
            count[0] += 1
            if count[0] >= MAX_MATCHES:
                stop.set()
            spans = [[m.start(), m.end()] for m in pattern.finditer(match.snippet) if m.end() > m.start()]
            send({"type": "match", "path": match.path, "rel": rel(match.path),
                  "location": match.location, "snippet": match.snippet, "highlights": spans})

        matches, scanned = docsearch.search_folder(
            folder, pattern,
            on_match=on_match,
            on_error=lambda path, message: send({"type": "skipped", "path": path, "rel": rel(path), "message": message}),
            on_file=lambda path, count: send({"type": "progress", "scanned": count, "rel": rel(path)}),
            stop_event=stop,
            extensions=docsearch.extensions_for(types),
        )
        send({"type": "done", "matches": len(matches), "files": len({m.path for m in matches}), "scanned": scanned,
              "limited": count[0] >= MAX_MATCHES})


def main(argv=None):
    parser = argparse.ArgumentParser(description="Search inside documents from your browser.")
    parser.add_argument("--port", type=int, default=8765, help="port to use (default 8765)")
    parser.add_argument("--no-browser", action="store_true", help="don't open the browser automatically")
    args = parser.parse_args(argv)

    server = None
    for port in range(args.port, args.port + 20):
        try:
            server = ThreadingHTTPServer((HOST, port), Handler)
            break
        except OSError:
            continue
    if server is None:
        print(f"No free port found between {args.port} and {args.port + 19}.", file=sys.stderr)
        return 1
    server.daemon_threads = True
    url = f"http://localhost:{server.server_address[1]}/"
    print(f"DocSearch is running at {url}")
    print("Keep this window open while you use it. Press Ctrl+C to stop.")
    if not args.no_browser:
        threading.Timer(0.5, webbrowser.open, [url]).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
