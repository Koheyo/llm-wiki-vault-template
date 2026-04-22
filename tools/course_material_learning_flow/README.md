# Course Material Learning Flow

Meta-workflow for turning new course material into a learnable and reviewable Obsidian knowledge asset.

This is an **orchestration playbook**, not a single extractor. It can call lower-level tools such as `pptx_visual_ingest`, then create learning outputs such as lecture summaries, concept notes, guided slide walkthroughs, review packs, cheat sheets, and quizzes.

## When to use

Use this workflow when the user says things like:

- “process this new lecture deck and make it studyable”
- “ingest this course material, then create review material”
- “connect this lecture into the course map and concept pages”
- “generate a review pack and quiz from these slides”

Do **not** use this workflow for a quick one-off factual answer.

## Mental model

```text
new course material
  -> ingest / preserve source context
  -> visual or textual digest
  -> lecture summary
  -> concept linking
  -> ask user to choose learning mode
  -> chosen learning mode: live tutor / detailed walkthrough / key-slide / exam review / algorithm-first
  -> review pack
  -> optional cheat sheet / quiz
  -> verify + log
```

## Relationship to other tools

- For PPTX/PDF slide decks, call `tools/pptx_visual_ingest` first.
- For rendered slide decks, call `tools/slide_guided_review` for the learning explanation layer.
- This workflow owns the learning outputs and linking strategy after ingest.

## Default phases

### Phase 0 — Identify material and target course

1. Determine material type: PPTX, PDF, Markdown, transcript, homework, code, or mixed.
2. Determine target course/project and existing hub pages.
3. Determine whether the material is a new lecture, update, supplement, or standalone reference.
4. Find existing course hub, overview page, and matching configs.

### Phase 1 — Ingest

If PPTX/PDF slides:

1. Use `pptx_visual_ingest`.
2. Prefer dry-run first.
3. Generate/update raw text extraction, fixed-layout PDF, rendered slide images, and visual slide digest.

If Markdown/transcript:

1. Preserve source path/URL.
2. Create a readable source digest.
3. Keep raw material separate from `wiki/` synthesis.

### Phase 2 — Lecture summary

Create or update one `wiki/summaries/...md` page using `templates/lecture-summary.md`.

It should include:

- source path
- visual digest link if available
- main storyline
- core concepts
- study/review handles
- links to course hub and concept pages

### Phase 3 — Concept linking

1. Identify new concepts, algorithms, formulas, datasets, or systems.
2. Create/update `wiki/concepts/...md` using `templates/concept-note.md`.
3. Link lecture summary ↔ concept pages ↔ course hub.
4. Prefer one durable concept page per reusable abstraction.

### Phase 4 — Learning mode selection gate

Do not automatically start guided teaching after ingest. If the user asks to learn/review, ask which learning mode they want unless already specified:

```text
Which learning mode do you want?
A. Live slide tutor: proceed slide by slide; user can interrupt anytime.
B. Auto detailed walkthrough: generate a complete lecture-style explanation.
C. Key-slide walkthrough: explain only the most important slides.
D. Exam review: formulas, problem types, pitfalls, and quiz.
E. Algorithm-first: reorganize by algorithm/concept rather than slide order.
```

### Phase 5 — Guided learning layer

For slide decks, prefer `tools/slide_guided_review`.

The generated learning output should answer:

1. What problem does this lecture solve?
2. Which slides are must-read and why?
3. What do diagrams, matrices, formulas, and examples mean?
4. Which algorithms/formulas need hand calculation?
5. How does this material connect to previous/next lectures and concept pages?

Reading priority:

1. Visual reading of rendered slide/page images.
2. Extracted slide text as support.
3. OCR fallback only when image text/formulas are uncertain.
4. Course summaries and concept pages for context.

### Phase 6 — Review pack

When the user wants review material, create `wiki/answers/...-review.md` using `templates/review-pack.md`.

Recommended structure:

1. Chapter storyline
2. Definitions
3. Core formulas
4. Algorithm-by-algorithm explanation
5. Worked examples
6. Common mistakes
7. Cram sheet

### Phase 7 — Optional outputs

Optionally create:

- cheat sheet via `templates/cheat-sheet.md`
- quiz via `templates/quiz.md`
- homework-oriented topic map
- keyword-to-reaction checklist

### Phase 8 — Verify and log

Before finishing:

1. Verify required frontmatter on new `wiki/` pages.
2. Verify wikilinks point to existing files.
3. Verify image embeds point to existing rendered images.
4. Do not modify raw originals.
5. Append `log.md`.

## Output storage conventions

- Lecture summary: `wiki/summaries/<course>-lecture-XX-topic.md`
- Visual slide digest: `wiki/summaries/<course>-lecture-XX-topic-slides.md`
- Concept note: `wiki/concepts/<concept-slug>.md`
- Guided walkthrough: `wiki/answers/<course>-lecture-XX-topic-guided-walkthrough.md`
- Live session state: `wiki/answers/<course>-lecture-XX-topic-live-session.md`
- Auto detailed walkthrough: `wiki/answers/<course>-lecture-XX-topic-auto-detailed-walkthrough.md`
- Review pack: `wiki/answers/<course>-lecture-XX-topic-review.md`
- Cheat sheet: `wiki/answers/<course>-lecture-XX-topic-cheat-sheet.md`
- Quiz: `wiki/answers/<course>-lecture-XX-topic-quiz.md`
