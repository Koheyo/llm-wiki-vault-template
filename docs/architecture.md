# Vault Architecture

This template follows a layered knowledge architecture.

## 1. `raw/`: source layer

`raw/` stores unmodified inputs. Treat it as read-only after ingest.

Recommended subfolders:

```text
raw/clips/   # web article or page clippings converted to Markdown
raw/videos/  # transcript summaries or video notes
raw/papers/  # papers or paper-derived Markdown
raw/books/   # book excerpts
raw/chats/   # AI conversation exports and thought fragments
```

Do not edit these files to make them “clean.” Instead, create summary and concept pages under `wiki/`.

## 2. `wiki/`: maintained knowledge layer

`wiki/` contains durable, curated pages.

```text
wiki/entities/   # named things: people, courses, tools, projects, organizations
wiki/concepts/   # abstract ideas: algorithms, models, methods, definitions
wiki/summaries/  # one page per source item or source collection
wiki/answers/    # archived long-form answers or synthesized study guides
wiki/journals/   # weekly/monthly reflections
```

Every `wiki/` page should include YAML frontmatter.

```yaml
---
type: summary | entity | concept | answer | journal
title: "Human-readable title"
created: YYYY-MM-DD
updated: YYYY-MM-DD
source: raw/clips/example.md   # required for type: summary
tags: [domain/subdomain]
status: draft | curated | stale
related: []
---
```

## 3. `graphify-out/`: generated graph layer

`graphify-out/` is for generated graph files and reports. Do not hand-edit it. If you regenerate graphs, update reports and logs together.

Recommended structure:

```text
graphify-out/
  graph.json
  GRAPH_REPORT.md
  pilots/
    topic-or-course-graph/
      graph.json
      GRAPH_REPORT.md
```

## 4. Root navigation

- `index.md`: human-facing navigation and major entrypoints.
- `log.md`: operation log for ingests, refactors, graph rebuilds, and audits.
- `AGENTS.example.md`: rules for AI assistants operating in the vault.

## Design principle

The vault should be useful even if graph tools are unavailable. The `wiki/` layer is the source of curated knowledge; graph output is an accelerator, not the canonical content store.
