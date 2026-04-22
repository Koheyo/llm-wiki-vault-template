# Slide Guided Review

Guided learning workflow for reading lecture slides **with slide images interleaved into the explanation**.

This workflow assumes slides have already been ingested by `pptx_visual_ingest` into visual slide digest pages and rendered slide images. It is not a raw PPT importer. It is the learning layer: the assistant acts like a tutor and explains key slides by looking at the actual slide image, not only extracted text.

## When to use

Use when the user asks for:

- slide-by-slide explanation
- key-slide explanation
- visual explanation of diagrams/formulas
- lecture review with embedded slide images
- OCR fallback for unclear slide text
- exam-focused review from rendered slides

## Mode selection rule

When a user asks to learn/review a deck but does not specify a mode, ask them to choose before producing learning outputs. Do not assume key-slide review by default.

## Modes

### Mode A — Live slide tutor

Use when the user wants to proceed one slide or a small group of slides at a time.

Behavior:

1. Work in small chunks, normally 1–4 slides.
2. Show/embed the current slide images first.
3. Explain: main idea → diagram/formula reading → why it matters → exam angle → memory line.
4. Stop and wait for pacing commands such as “next”, “continue”, “explain formula”, or “quiz me”.
5. Persist only compact session notes: current slide, covered chunks, weak points, and review status.

### Mode B — Auto detailed walkthrough

Use when the user wants a complete lecture-style explanation without interactive pacing.

Behavior:

1. Process the deck in slide order or coherent concept chunks.
2. Interleave slide images with explanation.
3. Explain: main idea → diagram/formula reading → why it matters → exam angle → memory line.
4. Be more detailed than key-slide review, but avoid dumping raw OCR/extracted text.
5. Save as `wiki/answers/<course>-<topic>-auto-detailed-walkthrough.md` when persistence is requested.

### Mode C — Key-slide walkthrough

Use for focused learning/review. Select important slides based on core definitions, algorithm diagrams, formulas, worked examples, edge cases, and exam-likely comparisons.

### Mode D — Exam review

Use for formulas, problem types, common mistakes, and short quizzes.

### Mode E — Algorithm-first walkthrough

Group slides by algorithm/concept rather than slide order. Useful for homework and exam prep.

## Reading priority

For each selected slide, use this order:

1. Visual reading of the rendered slide image.
2. Existing extracted slide text.
3. OCR fallback when uncertain.
4. Course context from summaries and concept pages.

## OCR fallback

OCR is a fallback, not the primary reader. Use it when:

- extracted text is missing or suspiciously short
- the image contains embedded screenshots/figures with text
- formula/matrix details are ambiguous
- visual reading is uncertain

Example command:

```bash
tesseract "wiki/assets/example-course-slides/week-01-introduction/slide-008.png" stdout -l eng --psm 6
```

## Output shape

Generated static walkthroughs and live session notes should be saved under `wiki/answers/`.

Recommended slide explanation structure:

```markdown
## Slide 008 — Topic

![[wiki/assets/.../slide-008.png]]

### Visual reading
### What this slide means
### How to read the diagram/formula
### Connection to nearby slides
### What to remember
### Likely exam angle
### Self-check
```

## Verification

After generating a walkthrough:

1. Verify frontmatter.
2. Verify slide image embeds exist.
3. Verify wikilinks exist.
4. Append `log.md`.
