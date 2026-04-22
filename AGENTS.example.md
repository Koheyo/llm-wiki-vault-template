# AGENTS.example.md

Instructions for AI assistants operating inside an LLM Wiki style Obsidian vault.

## Vault identity

This vault is a personal knowledge base built around a layered LLM Wiki model.

- `raw/` stores unmodified source material and should be treated as read-only.
- `wiki/` stores curated knowledge pages maintained by humans and AI assistants.
- `graphify-out/` stores generated knowledge-graph outputs.
- `legacy/` stores historical notes and should not be modified unless explicitly requested.
- `Attachments/` stores binary assets and should not be scanned by default.

## Path rules

Use relative paths for files inside the vault. Do not assume a specific local absolute path.

## Frontmatter schema

All `wiki/` pages must include:

```yaml
---
type: summary | entity | concept | answer | journal
title: "Human-readable title"
created: YYYY-MM-DD
updated: YYYY-MM-DD
source: raw/clips/example.md   # required for summaries
labels: []                     # optional, project-specific
tags: [domain/subdomain]
status: draft | curated | stale
related: []
---
```

## Graph boundaries

This vault may use an external tool such as `graphify` for multiple graph types. Keep them separate.

### Learning knowledge graphs

For course, paper, reading, and wiki knowledge. Intended nodes include concepts, definitions, models, claims, algorithms, entities, lectures, and source summaries.

### Project/codebase graphs

For external software projects where code structure matters. Intended nodes include modules, classes, functions, calls, and dependency relationships.

### Vault tooling

Infrastructure scripts that support this vault should usually be excluded from learning graphs.

## Graph safety rules

- Never build a graph from the vault root `.`.
- Build learning graphs only from explicit knowledge subdirectories or curated `wiki/` subsets.
- Build codebase graphs only for explicit project/code directories.
- Exclude `.obsidian/`, `Attachments/`, `graphify-out/`, `legacy/`, and tooling directories from learning graphs by default.
- Before answering architecture questions about an existing graph, read its `GRAPH_REPORT.md` if available.

## Workflows

### WIKI-CREATE

1. Read a source from `raw/`.
2. Create a `wiki/summaries/<slug>.md` page.
3. Create or update relevant entity and concept pages.
4. Add wikilinks between touched pages.
5. Append a concise entry to `index.md`.
6. Append an operation entry to `log.md`.

### LINT-REPORT

Audit `wiki/**/*.md` for missing frontmatter, unresolved wikilinks, and orphan pages. Report findings; do not auto-fix unless requested.

## Safety

- Never delete notes automatically; mark stale content with `status: stale`.
- Never modify `raw/` files unless the user explicitly asks.
- Never push to a remote repository automatically.
- Do not expose private paths, personal identifiers, or copyrighted source content in public exports.
