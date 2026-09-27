#!/usr/bin/env python3
"""Check that a (subset) font covers every character of your on-screen copy.

    python3 check_glyphs.py path/to/font.woff2 plan.json [--field headline --field headlineEn]
    python3 check_glyphs.py font.ttf --text "读到好的，直接进笔记。"

Missing glyphs silently fall back to another font in the render; catch them before review.
Needs fontTools (and brotli for .woff2): `python3 -m venv .venv && .venv/bin/pip install fonttools brotli`.

Copyright (c) 向阳乔木 — MIT License.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("font")
    ap.add_argument("plan", nargs="?")
    ap.add_argument("--field", action="append", help="plan.shots fields to check (default: headline)")
    ap.add_argument("--text", action="append", default=[])
    args = ap.parse_args()
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        print(json.dumps({"ok": False, "error": "fontTools not installed; see --help"}))
        return 2
    cmap = TTFont(args.font).getBestCmap()
    texts = list(args.text)
    if args.plan:
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        for s in plan.get("shots", []):
            for f in args.field or ["headline"]:
                if s.get(f):
                    texts.append(str(s[f]))
    missing = {}
    for t in texts:
        miss = sorted({c for c in t if not c.isspace() and ord(c) not in cmap})
        if miss:
            missing[t] = "".join(miss)
    print(json.dumps({"ok": not missing, "font": args.font, "glyphs": len(cmap), "checked": len(texts), "missing": missing}, ensure_ascii=False, indent=2))
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
