# Science Chapter 12 inline drawing pilot — Beyond Earth

This is a **draft-only sample** for CBSE / NCERT Class 6 Science Chapter 12, *Beyond Earth*.

It creates three topic-owned visuals:
1. Earth, Moon and Sun — two orbital paths, with an explicit not-to-scale note.
2. Day and night — the illuminated and dark sides of a rotating Earth.
3. Phases of the Moon — a simplified phase sketch and a teacher prompt.

## Generate sample files

From the repository root:

\`\`\`bash
python tools/visual_engine/samples/science_beyond_earth_inline.py --format both --out-dir build/visuals/science-beyond-earth
\`\`\`

The output contains one SVG and one editable Excalidraw-compatible JSON storyboard per module, plus a manifest describing each narration/caption/visual relationship.

## Inline tutor contract

- Visual belongs to its exact teaching module.
- Render it **below that module's explanation** in normal scroll flow.
- Do not show it as an overlay, modal, floating card, or separate window.
- Advance the drawing with the active narration/module, not an independent animation loop.
- Keep each asset compact, legible, pastel-accented, and teacher-notebook-like.

## Safety / review gate

- Source reference: [NCERT Class 6 Science, Chapter 12 PDF](https://ncert.nic.in/textbook/pdf/fecu112.pdf).
- All assets remain \`draft\`, \`active=false\`, and \`needs_review\`; this script does not connect to Neon, write to the database, or activate learner-facing content.
- Check exact labels, orbital/phase relationships, and wording against the official textbook before approving.
- These are original schematic drawings, not copied textbook illustrations; the Moon phase positions are simplified and marked schematic.
- This is a visual-asset pilot, not proof that the live Android tutor currently renders it. End-to-end integration still needs a PR review, backend tests, Android build, and emulator/device acceptance.
