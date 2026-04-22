# PPTX/PDF Slide Ingest Workflow

This workflow turns slide decks into Obsidian-native learning assets without mixing raw sources, generated media, and curated wiki notes.

## Pipeline

```text
PPTX/PDF source
  -> fixed-layout PDF
  -> slide/page PNG images
  -> extracted text Markdown
  -> visual slide digest
  -> optional lecture summary and concept links
  -> optional guided review / review pack / quiz
```

## Why PDF-first?

Slide decks often contain diagrams, arrows, tables, equations, screenshots, and layouts that text extraction cannot preserve. Exporting to PDF first gives a stable visual representation before rendering each page to an image.

## Output conventions

```text
raw/pdfs/<course>/...              # derived fixed-layout PDFs
raw/clips/<course>/...             # extracted slide text
wiki/assets/<course>/<deck>/...    # slide images and metadata
wiki/summaries/<lecture>-slides.md # visual digest
wiki/answers/...                   # guided walkthroughs/review outputs
```

## Safety

- Do not modify original raw decks.
- Use dry-run before new configs.
- Do not run graph builders from the vault root.
- Do not auto-start guided teaching after ingest; ask the user to choose a learning mode.
