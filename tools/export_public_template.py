#!/usr/bin/env python3
"""Safely export architecture-level files from a private vault to this public template.

This script intentionally does NOT copy private notes, raw source material, attachments,
logs, or generated graphs. It exports only a sanitized AGENTS example.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

PRIVATE_PATTERNS = [
    re.compile("/" + "Users/" + r"[^\s`]+"),
    re.compile(r"Owner:\s*.*", re.IGNORECASE),
    re.compile(r"university|student", re.IGNORECASE),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
]

REPLACEMENTS = [
    (re.compile("/" + "Users/" + r"[^\s`]+"), "/path/to/private-vault"),
    (re.compile(r"Owner:\s*.*", re.IGNORECASE), "Owner: <redacted>"),
]


def sanitize(text: str) -> str:
    out = text
    for pat, repl in REPLACEMENTS:
        out = pat.sub(repl, out)
    out = out.replace("Guo" + "huaiyu", "<owner>")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--private-vault", required=True, type=Path)
    ap.add_argument("--public-repo", required=True, type=Path)
    args = ap.parse_args()

    src = args.private_vault / "AGENTS.md"
    dst = args.public_repo / "AGENTS.example.md"
    if not src.exists():
        raise SystemExit(f"No AGENTS.md found at {src}")

    sanitized = sanitize(src.read_text(encoding="utf-8", errors="replace"))
    remaining = [p.pattern for p in PRIVATE_PATTERNS if p.search(sanitized)]
    if remaining:
        print("Warning: possible private patterns remain; review manually:")
        for pat in remaining:
            print("-", pat)

    dst.write_text(sanitized, encoding="utf-8")
    print(f"Wrote {dst}")
    print("Review manually before publishing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
