#!/usr/bin/env python3
"""Check local href/src targets and in-page anchors in the static site."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = sorted(ROOT.glob("*.html"))


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.targets = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])
        for attr in ("href", "src"):
            value = values.get(attr)
            if value:
                self.targets.append((attr, value))


errors = []
parsed = {}
for page in PAGES:
    parser = LinkParser()
    parser.feed(page.read_text(encoding="utf-8"))
    parsed[page.resolve()] = parser

for page, parser in parsed.items():
    for attr, raw in parser.targets:
        url = urlsplit(raw)
        if url.scheme or url.netloc or raw.startswith(("data:", "javascript:")):
            continue
        fragment = unquote(url.fragment)
        if not url.path:
            target = page
        else:
            target = (page.parent / unquote(url.path)).resolve()
        if not target.exists():
            errors.append(f"{page.relative_to(ROOT)}: missing {attr} target {raw!r}")
            continue
        if fragment and target.suffix.lower() in {".html", ".htm"}:
            target_parser = parsed.get(target)
            if target_parser is None:
                target_parser = LinkParser()
                target_parser.feed(target.read_text(encoding="utf-8"))
                parsed[target] = target_parser
            if fragment not in target_parser.ids:
                errors.append(f"{page.relative_to(ROOT)}: missing #{fragment} in {target.relative_to(ROOT)}")

if errors:
    print("\n".join(errors))
    raise SystemExit(1)

print(f"Checked {len(PAGES)} HTML pages: local links and referenced assets are valid.")
