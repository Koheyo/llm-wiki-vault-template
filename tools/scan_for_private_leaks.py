#!/usr/bin/env python3
"""Simple leak scan for public vault-template repositories."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

PATTERNS = {
    "absolute_user_path": re.compile("/" + "Users/" + r"[^\s`)]+"),
    "api_key_like": re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[^\s'\"]+"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "private_owner_name_example": re.compile("Guo" + "huaiyu", re.IGNORECASE),
    "private_owner_alias_example": re.compile("Ho" + "wie", re.IGNORECASE),
    "private_course_code_example": re.compile("US" + "C|CS" + "CI|DS" + "CI", re.IGNORECASE),
}

SKIP_DIRS = {".git", "node_modules", "__pycache__"}
TEXT_EXTS = {".md", ".txt", ".py", ".yml", ".yaml", ".json", ".gitignore", ""}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    findings = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.suffix not in TEXT_EXTS and path.name != ".gitignore":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for name, pattern in PATTERNS.items():
            for m in pattern.finditer(text):
                line_no = text.count("\n", 0, m.start()) + 1
                findings.append((name, path.relative_to(root), line_no, m.group(0)[:120]))

    if findings:
        print("Possible leaks found:")
        for name, path, line, snippet in findings:
            print(f"- {name}: {path}:{line}: {snippet}")
        return 1
    print("OK: no configured private leak patterns found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
