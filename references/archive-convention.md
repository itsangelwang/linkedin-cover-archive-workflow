# Article archive convention

Store every article under `articles/YYYY-MM-DD-slug/`.

```text
articles/YYYY-MM-DD-slug/
├── source/          Original article files; never overwrite
├── brief.md         Thesis, audience, evidence limits, cover focus
├── strategy.md      Titles, three directions, recommendation, risks
├── prompts.md       Approved prompts and generation restrictions
├── decision.md      Selection, revisions, final title and placement
├── candidates/      Original generated directions
├── previews/        Approximately 360px-wide mobile previews
└── final/           Approved, text-free publishing master
```

## Naming

- Use lowercase ASCII slugs with hyphens.
- Name candidates `01-scene.png`, `02-minimal-concept.png`, and `03-editorial-metaphor.png`, adapting the descriptors to the actual concepts.
- Name revisions after their source: `02-minimal-concept-v2.png`.
- Keep only approved masters in `final/`; do not delete rejected candidates.
- If two articles share a date and slug, add a short differentiator rather than overwriting.

## Record keeping

- Preserve the author's source file byte-for-byte.
- Update each Markdown record in place; images are immutable.
- Record why the winner was chosen and why alternatives were rejected.
- Record title guidance separately because generated images remain text-free.
- Add no reusable lesson to the skill until the user explicitly confirms it.
