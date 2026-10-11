---
Area: Governance
datetime_stamp: 2026-10-11T00:00:00-05:00
status: complete
confidence: vetted
tags:
  - governance
  - frontmatter
links:
  - "[[Rules]]"
  - "[[Canonical Values]]"
summary: Standard frontmatter template and field definitions for every Markdown note in the vault.
canonical: true
---

# Frontmatter Standard

Use this template for every Markdown note:

```yaml
---
Area: 
datetime_stamp: 2026-10-11T00:00:00-05:00
status: draft
confidence: tentative
tags:
  - 
links: []
summary: 
canonical: false
---
```

## Field expectations

- `Area`: the note's primary subject area.
- `datetime_stamp`: the latest substantive review or update, in ISO 8601 format.
- `status`: the note's lifecycle state.
- `confidence`: how settled or trustworthy the note's claims are.
- `tags`: Obsidian tags that support discovery.
- `links`: related notes, written as Obsidian wikilinks.
- `summary`: one short sentence describing the note.
- `canonical`: whether the note is authoritative.

Use the exact `status` and `confidence` values from [[Canonical Values]]. `status`, `confidence`, and `canonical` are independent fields.

When normalizing an older note, preserve its original date and wording in the body where useful. `datetime_stamp` records review history; it is not necessarily the note's creation date.
