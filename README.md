# LLM Wiki Vault Template

A public, sanitized template for building an **LLM-native Obsidian knowledge vault** inspired by Andrej Karpathy's **LLM Wiki** idea: raw source material is kept separate from a curated wiki layer, and optional knowledge-graph outputs are generated into a dedicated `graphify-out/` area.

This repository is a **knowledge-base architecture and workflow template**, not a graph-extraction engine. It can integrate with external tools such as `graphify`, but those tools are not bundled or claimed as original work here. This project is not affiliated with Andrej Karpathy; it applies the LLM Wiki philosophy to an Obsidian-based personal knowledge system.

## Why this exists

Many personal knowledge bases become hard to maintain because source material, summaries, concepts, project notes, and generated artifacts are mixed together. This template proposes a stricter layout:

```text
raw/           # unmodified source material
wiki/          # maintained knowledge layer: concepts, entities, summaries, answers, journals
graphify-out/  # generated graph outputs; do not hand-edit
index.md       # human navigation entrypoint
log.md         # operations/change log
AGENTS.example.md
```

The goal is to make a vault easier for humans and AI assistants to maintain safely.

## Core ideas

- **Separate source from synthesis**: keep raw inputs read-only; write durable understanding into `wiki/`.
- **Use stable schemas**: every wiki page has YAML frontmatter.
- **Prefer small, composable notes**: concepts, entities, and summaries link to each other.
- **Keep graph types separate**: learning graphs, codebase graphs, and vault tooling graphs should not be mixed.
- **Never build a graph from the vault root**: target explicit subdirectories to avoid slow scans and noisy graphs.
- **Publish architecture, not private content**: this repository contains examples and templates only.

## Quick start

```bash
# 1. Copy the template vault somewhere safe
cp -R template-vault my-llm-wiki-vault
cd my-llm-wiki-vault

# 2. Add source material under raw/ without modifying it
mkdir -p raw/clips
cp /path/to/article.md raw/clips/example-article.md

# 3. Create curated pages under wiki/
cp ../template-vault/wiki/summaries/example-summary.md wiki/summaries/my-summary.md

# 4. Lint wiki pages
python ../tools/lint_wiki.py .
```

## Optional graph workflow

If you use an external graph builder such as `graphify`, write outputs to `graphify-out/` and keep generated files out of hand-authored notes. See [docs/graphify-integration.md](docs/graphify-integration.md) for the safety rules.

## Repository contents

```text
docs/                         # architecture and workflow docs
template-vault/               # empty reusable Obsidian vault skeleton
examples/sample-learning-vault # tiny sanitized sample vault
tools/                        # helper scripts for linting/exporting
AGENTS.example.md             # AI assistant operating rules template
```

## What is intentionally excluded

This public repository does **not** include:

- private notes or journals
- course materials, PDFs, slides, or copyrighted clippings
- personal logs
- attachment dumps
- generated full graph files from a private vault
- local machine paths, API keys, or environment secrets

## License

MIT License. See [LICENSE](LICENSE).
