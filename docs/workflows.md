# Workflows

## WIKI-CREATE: create a summary page

Use this when adding a source from `raw/` into the curated knowledge layer.

1. Read the source file from `raw/`.
2. Create `wiki/summaries/<slug>.md` with frontmatter.
3. Extract key entities and create/update pages in `wiki/entities/`.
4. Extract key concepts and create/update pages in `wiki/concepts/`.
5. Add wikilinks between the summary, entities, and concepts.
6. Add a one-line entry to `index.md`.
7. Append an operation entry to `log.md`.

## LINT-REPORT: audit the wiki layer

Run:

```bash
python tools/lint_wiki.py template-vault
```

The linter checks:

- missing or malformed frontmatter
- required frontmatter fields
- unresolved wikilinks
- orphan wiki pages

The linter reports findings but does not auto-fix.

## ARCHITECTURE-SYNC: update the public template

If you maintain a private vault and this public template separately, sync only architecture-level changes:

- folder conventions
- frontmatter schema
- reusable scripts
- AI assistant rules
- graph boundary rules
- sanitized example pages

Do **not** sync private content, raw source material, logs, attachments, or generated graph output from a private vault.

A safe helper script is included:

```bash
python tools/export_public_template.py --private-vault /path/to/private-vault --public-repo /path/to/this-repo
```

By default, it exports only a sanitized `AGENTS.example.md` and does not copy private notes.
