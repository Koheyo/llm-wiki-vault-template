#!/usr/bin/env python3
"""Lint an LLM Wiki style Obsidian vault.

Checks:
- wiki pages have YAML frontmatter
- required fields are present
- wikilinks resolve to existing Markdown files when possible
- orphan wiki pages with no inbound wiki links

This script is intentionally conservative: it reports issues but does not modify files.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

REQUIRED = {"type", "title", "created", "updated", "tags", "status", "related"}
SUMMARY_REQUIRED = REQUIRED | {"source"}
WIKILINK_RE = re.compile(r"!?(?<!`)\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")


def parse_frontmatter(text: str) -> tuple[dict[str, str], bool]:
    if not text.startswith("---\n"):
        return {}, False
    end = text.find("\n---", 4)
    if end == -1:
        return {}, False
    block = text[4:end].strip().splitlines()
    data: dict[str, str] = {}
    for line in block:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip()
    return data, True


def wiki_pages(root: Path) -> list[Path]:
    return sorted((root / "wiki").glob("**/*.md")) if (root / "wiki").exists() else []


def possible_targets(root: Path, link: str) -> Iterable[Path]:
    clean = link.strip().strip('"').strip("'")
    if not clean:
        return []
    candidates = []
    raw = Path(clean)
    if raw.suffix != ".md":
        raw = raw.with_suffix(".md")
    candidates.append(root / raw)
    candidates.append(root / "wiki" / raw)
    candidates.append(root / "wiki" / "concepts" / raw.name)
    candidates.append(root / "wiki" / "entities" / raw.name)
    candidates.append(root / "wiki" / "summaries" / raw.name)
    candidates.append(root / "wiki" / "answers" / raw.name)
    candidates.append(root / "wiki" / "journals" / raw.name)
    return candidates


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("vault", nargs="?", default=".", help="vault root to lint")
    args = ap.parse_args()
    root = Path(args.vault).resolve()

    pages = wiki_pages(root)
    issues: list[str] = []
    inbound = {p: 0 for p in pages}

    for page in pages:
        text = page.read_text(encoding="utf-8", errors="replace")
        fm, has_fm = parse_frontmatter(text)
        rel = page.relative_to(root)
        if not has_fm:
            issues.append(f"MISSING_FRONTMATTER {rel}")
            continue
        required = SUMMARY_REQUIRED if fm.get("type") == "summary" else REQUIRED
        missing = sorted(k for k in required if k not in fm)
        if missing:
            issues.append(f"MISSING_FIELDS {rel}: {', '.join(missing)}")

        for link in WIKILINK_RE.findall(text):
            if link.startswith("http"):
                continue
            candidates = list(possible_targets(root, link))
            existing = [c.resolve() for c in candidates if c.exists()]
            if not existing:
                issues.append(f"UNRESOLVED_LINK {rel}: [[{link}]]")
                continue
            for target in existing:
                for p in inbound:
                    if p.resolve() == target:
                        inbound[p] += 1

    for page, count in inbound.items():
        if count == 0 and page.name != "index.md":
            issues.append(f"ORPHAN {page.relative_to(root)}")

    if issues:
        print("Lint issues found:")
        for issue in issues:
            print("-", issue)
        return 1

    print(f"OK: {len(pages)} wiki pages checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
