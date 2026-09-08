"""Embed a hash-verified reader report without importing executable HTML."""

import hashlib
import html
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit


class _ReaderBody(HTMLParser):
    allowed = {"p", "section", "article", "h1", "h2", "h3", "div", "span",
               "strong", "em", "figure", "img", "figcaption", "table", "caption",
               "thead", "tbody", "tr", "th", "td", "a", "br", "ul", "ol", "li"}
    blocked = {"script", "style", "nav", "iframe", "object", "template", "svg", "math"}

    def __init__(self, root):
        super().__init__(convert_charrefs=True)
        self.root = root.resolve()
        self.body = False
        self.hidden = []
        self.parts = []

    def _link(self, value):
        url = urlsplit(value)
        if url.scheme or url.netloc or url.query:
            return None
        if value.startswith("#"):
            return "#reader-" + value[1:]
        relative = Path(unquote(url.path))
        if not relative.parts or relative.is_absolute() or ".." in relative.parts:
            return None
        path = self.root / relative
        if not path.resolve().is_relative_to(self.root) or not path.is_file():
            return None
        return "evidence/" + quote(relative.as_posix()) + ("#" + url.fragment if url.fragment else "")

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.body = True
            return
        if not self.body:
            return
        if tag in self.blocked:
            self.hidden.append(tag)
        if self.hidden or tag not in self.allowed:
            return
        safe = []
        for name, value in attrs:
            if value is None:
                continue
            if name == "id":
                safe.append((name, "reader-" + value))
            elif name in {"href", "src"}:
                value = self._link(value)
                if value is not None:
                    safe.append((name, value))
            elif name in {"alt", "title", "colspan", "rowspan", "scope"}:
                safe.append((name, value))
        self.parts.append("<" + tag + "".join(f' {key}="{html.escape(value, quote=True)}"' for key, value in safe) + ">")

    def handle_endtag(self, tag):
        if tag == "body":
            self.body = False
            return
        if self.hidden:
            if tag == self.hidden[-1]:
                self.hidden.pop()
            return
        if self.body and tag in self.allowed and tag not in {"img", "br"}:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        if self.body and not self.hidden:
            self.parts.append(html.escape(data))


def reader_panel(root: Path):
    """Return inert, local-link-only body HTML or None for legacy reports.

    A mismatched reader hash never enters the dashboard. Raw source files remain
    untouched, and no script, style, iframe, handler, or external URL is imported.
    """
    path = root / "prioritized_findings.html"
    checks = root / "finding_reader_report_checks.json"
    if not path.is_file() or not checks.is_file() or path.stat().st_size > 10_000_000:
        return None
    try:
        record = json.loads(checks.read_text(encoding="utf-8"))
        expected = record.get("generated_files", {}).get(path.name)
        raw = path.read_bytes()
        if not expected or hashlib.sha256(raw).hexdigest() != expected:
            return None
        parser = _ReaderBody(root)
        parser.feed(raw.decode("utf-8"))
        parser.close()
        return "".join(parser.parts) or None
    except (ValueError, UnicodeError, OSError, AttributeError):
        return None
