#!/usr/bin/env python3
"""
Keeps The Word Café's offline fallback in sync with words.json.

Why this exists:
  index.html already fetches words.json at runtime, so as long as both
  files sit in the same folder on your host, editing words.json alone
  is enough — the menu updates itself automatically, no script needed.

  This script only handles the SAFETY NET: a full copy of words.json is
  also embedded inside index.html (in a <script id="fallback-json"> tag)
  so the game still works if the fetch ever fails (offline, wrong path,
  a host that blocks relative fetches, etc). That embedded copy doesn't
  update itself — this script re-embeds it from words.json.

Usage (run this every time you finish editing words.json):
  python3 sync_fallback.py

Or point it at different files:
  python3 sync_fallback.py --html path/to/index.html --json path/to/words.json
"""
import argparse
import json
import re
import sys
from pathlib import Path

FALLBACK_OPEN = re.compile(
    r'(<script id="fallback-json" type="application/json">\n)(.*?)(\n</script>)',
    re.DOTALL,
)


def sync(html_path: Path, json_path: Path) -> None:
    if not html_path.exists():
        sys.exit(f"error: {html_path} not found")
    if not json_path.exists():
        sys.exit(f"error: {json_path} not found")

    # Validate the JSON before touching the HTML — a bad edit to words.json
    # should fail loudly here, not get silently baked into the fallback.
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"error: {json_path} is not valid JSON — {e}")

    html = html_path.read_text(encoding="utf-8")
    match = FALLBACK_OPEN.search(html)
    if not match:
        sys.exit(
            f"error: couldn't find the fallback-json <script> block in {html_path}. "
            "Has the tag's id or type attribute changed?"
        )

    pretty = json.dumps(data, indent=2, ensure_ascii=False)
    new_html = html[: match.start()] + match.group(1) + pretty + match.group(3) + html[match.end():]

    if new_html == html:
        print("Already in sync — no changes made.")
        return

    html_path.write_text(new_html, encoding="utf-8")
    categories = ", ".join(data.keys())
    print(f"Synced. Fallback now has {len(data)} categories: {categories}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--html", default="index.html", type=Path)
    parser.add_argument("--json", default="words.json", type=Path)
    args = parser.parse_args()
    sync(args.html, args.json)
