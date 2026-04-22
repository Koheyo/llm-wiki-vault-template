# Publishing Safety Checklist

Before publishing a vault-derived repository, verify that it contains architecture only.

## Do not publish

- personal journals or reflections
- raw course materials, PDFs, slides, or textbooks
- copyrighted article clippings
- private AI conversations
- attachments, screenshots, images, and exported PDFs
- full generated graphs from private content
- local absolute paths
- API keys, tokens, credentials, or environment secrets
- private names, school/work identifiers, or personal schedules

## Safe to publish

- folder layout
- frontmatter schema
- generic workflows
- scripts that do not encode private paths or secrets
- sanitized `AGENTS.example.md`
- small synthetic example notes
- a sample `GRAPH_REPORT.md` made from synthetic data

## Suggested release process

1. Build public files in a separate folder outside the private vault.
2. Run the leak scan:

   ```bash
   python tools/scan_for_private_leaks.py .
   ```

3. Manually inspect `README.md`, `AGENTS.example.md`, and examples.
4. Initialize git only in the public repository, never inside a cloud-synced private vault.
5. Push to GitHub only after review.
