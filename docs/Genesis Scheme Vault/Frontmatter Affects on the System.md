---
area: CFD Engine
date: 2026-05-01
status: completed
confidence: medium
tags:
  - frontmatter
  - notes
  - retrieval
---


---

Short version: **frontmatter is quietly shaping retrieval more than you probably realize.** Specifically:

**What the system actually does with it ([utils.py:_read_frontmatter_tags](vscode-webview://0lo17r9qvsne1l55u4vdg1vj0bd22tkf6p0vs3rke2vaf47agvr8/rag_app/api/utils.py#L7)):**

- Only during `/ingest_folder` — reads the first `---...---` block and extracts the `tags: [a, b, c]` array (regex, not a real YAML parser).
- Those tags get appended to `[dir_tag, ext_tag]` and stored as a scalar comma-joined string in Chroma metadata.
- `/ingest` (single-doc) does NOT parse frontmatter — you pass tags explicitly.

**What it does NOT do:**

- Does not strip the `---...---` block before chunking. The entire YAML block stays inside chunk 0 of every doc and **gets embedded as if it were content**.
- Does not extract `area`, `date`, `status`, `summary`, `links`, `confidence`, or anything other than `tags`. Those fields exist only as embedded text — they're not queryable metadata.
- The extraction regex only matches `tags: [a, b]` inline form. The YAML list form (`tags:\n - a\n - b`) is silently ignored.

**Practical consequences for your PoolSoftware corpus:**

- **Good:** `area: Push Notifications`, `tags: [push-notifications, ...]`, and `summary: ...` lines inside chunk 0 boost retrieval on queries like "push notifications" because those exact words sit in the embedding input. That's why the top-10 for "push notifications" is so cleanly dominated by push-notification docs.
- **Bad:** my title-match reranker only looks at `title` and `doc_id` metadata fields — not frontmatter tags. A query like "show me the Entra stuff" won't get a boost from `tags: [entra]`; it'd only benefit from the embedded body text.
- **Bad:** the frontmatter burns ~200–500 chars of your 2000-char target, compressing the content signal in chunk 0 of short docs.
- **Neutral:** your existing tag-based filters (`/collection/items?tags_contains=entra`) DO work because those scalar tags are in Chroma metadata.

**If you want to improve this,** three options in order of impact:

1. **Strip frontmatter before chunking** but promote `area`, `summary`, `tags` into the title-prefix header we already prepend. Best retrieval quality, one-time re-ingest.
2. **Extend the reranker** to match query terms against frontmatter tags in Chroma metadata — no re-ingest, chat-only.
3. **Upgrade the parser** to real YAML (PyYAML) so list-form tags and richer metadata extraction work. Mechanical improvement, requires re-ingest to capture retroactively.

Want me to spec any of these?