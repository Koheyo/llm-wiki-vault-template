# PPTX/PDF Visual Ingest

Reusable workflow for turning lecture PPTX/PDF decks into Obsidian-native visual slide digest pages.

## Why this exists

Plain text extraction from slides loses diagrams, arrows, matrices, tables, examples, and layout. This workflow uses a **PDF-first fixed-layout renderer** by default and keeps three layers:

1. **Visual context** — each slide/page rendered as an image embed.
2. **Search context** — extracted text remains available in generated Markdown.
3. **Semantic context** — generated digest pages can link to course hubs, summaries, and concept pages.

## Requirements

Default PDF-first renderer:

- Python 3.10+
- LibreOffice `soffice` for PPTX → PDF export
- PyMuPDF (`fitz`) for PDF → PNG rendering

Fallback QuickLook renderer, only when `render_method` is `quicklook_chrome`:

- macOS `qlmanage`
- `sips`
- Google Chrome + Node.js for Chrome DevTools screenshots

## Typical commands

From the vault root:

```bash
python3 tools/pptx_visual_ingest/pipeline.py \
  --config tools/pptx_visual_ingest/configs/example.json \
  --dry-run

python3 tools/pptx_visual_ingest/pipeline.py \
  --config tools/pptx_visual_ingest/configs/example.json \
  --all
```

## What `--all` does

1. Detect PPTX/PDF decks from `source_root`.
2. Optionally extract PPTX XML text to `raw_text_root`.
3. For PPTX, export to a fixed-layout PDF under `raw_pdf_root`.
4. For PDF sources, copy or use the PDF as the fixed-layout source.
5. Render each PDF page to `asset_root/<deck-slug>/slide-001.png`.
6. Create/update visual digest pages in `summary_root`.
7. Optionally update existing lecture summary pages with links to the visual digest and rendered PDF.
8. Append a log entry when writes complete.

## Config model

See `configs/example.json`.

Important fields:

- `source_root`: folder containing PPTX/PDF files. It can be outside the vault.
- `render_method`: `pdf_first` by default; `quicklook_chrome` is fallback only.
- `raw_pdf_root`: vault-relative directory for fixed-layout PDFs.
- `asset_root`: vault-relative output directory for slide/page images.
- `raw_text_root`: vault-relative output directory for PPTX XML text extraction.
- `summary_root`: vault-relative directory for generated digest pages.
- `course_hub`: wiki page to link from generated pages.
- `decks`: explicit mapping from source files to titles, slugs, tags, and related pages.

## Safety notes

- Does not move original PPTX/PDF files.
- Does not delete raw source files.
- Use `--overwrite` only when replacing rendered assets is intended.
- Generated digest pages live in `wiki/summaries/`; tool docs remain under `tools/`.
- Avoid running this from a cloud-synced vault root without explicit input/output subdirectories.
