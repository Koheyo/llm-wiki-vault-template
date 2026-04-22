# Graphify Integration

This repository can be used with external graph builders such as `graphify`, but it does not include or reimplement them.

## Attribution

If you use `graphify`, credit it as an external dependency. This template contributes the vault architecture, schema, safety rules, and workflow conventions.

## Graph types

Keep different graph types separate.

### 1. Learning knowledge graphs

Use for course notes, papers, readings, and wiki knowledge.

Intended nodes:

- concepts
- algorithms
- models
- definitions
- formulas
- claims
- entities
- courses or lectures
- source summaries

Recommended inputs:

```text
raw/clips/
raw/videos/
raw/papers/       # preferably converted to Markdown first
raw/books/
raw/chats/
wiki/             # curated subsets only
```

### 2. Project/codebase graphs

Use for software projects where code structure matters.

Intended nodes:

- modules
- classes
- functions
- method calls
- dependencies
- project-level concepts

Store these separately, for example:

```text
graphify-out/pilots/example-codebase-graph/
```

or inside the external project repository itself.

### 3. Vault tooling

Scripts that maintain the vault should usually be excluded from learning graphs. Analyze them only if you explicitly want a tooling/codebase graph.

## Safety rules

- Never build from the vault root `.`.
- Never mix learning graphs with codebase graphs.
- Exclude `.obsidian/`, `Attachments/`, `graphify-out/`, `legacy/`, and tool directories unless explicitly analyzing them.
- Prefer Markdown/text inputs over binary PDFs and images.
- Build in batches for large corpora.
- Read `GRAPH_REPORT.md` before answering architecture questions about an existing graph.
- Treat graph output as generated artifacts, not canonical notes.

## Example commands

Adjust paths to your local environment.

```bash
VAULT="/path/to/my-llm-wiki-vault"
PYTHON="python3"
GRAPHIFY_BIN="graphify"
TARGET="./raw/clips"
OUTPUT="graphify-out/pilots/clips-learning-graph"

cd "$VAULT"

# Detect before building
"$PYTHON" -c "
import json
from pathlib import Path
from graphify.detect import detect
r = detect(Path('$TARGET'))
print(json.dumps(r, indent=2, ensure_ascii=False))
"

# Query an existing graph
"$GRAPHIFY_BIN" query "What are the main concepts?" --graph "$VAULT/$OUTPUT/graph.json"
```
