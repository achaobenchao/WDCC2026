---
name: xlsx
description: Create the final Chinese multi-sheet video-material search workbook with openpyxl, timestamps, filters, readable formatting, and source links or paths.
---

# Video index workbook

Use `openpyxl` to create `视频素材检索结果.xlsx` from validated metadata, scene,
OCR, transcript, person, and event records. Use at least these sheets:

- `素材总览`: one row per video; include path/link, duration, resolution, FPS,
  video codec, audio presence, language/status, and summary.
- `关键事件明细`: one row per event; include video, start/end timestamp, event,
  people, organization/location, evidence text, and keyframe path/link.
- `人物索引`: one row per person occurrence or consolidated occurrence range;
  include name, title/organization, video, timestamp, evidence, and frame path.

Store durations/timestamps as Excel day fractions (`seconds / 86400`) and apply
`[h]:mm:ss` (or `hh:mm:ss` when values never exceed 24 hours). Keep raw paths as
text; add `file:///` hyperlinks only when they are useful and correctly escaped.

For every sheet: use Chinese-safe Unicode strings, a bold header, `auto_filter`,
`freeze_panes = "A2"`, sensible capped column widths, and wrapped top-aligned
body cells. Avoid illegal control characters and sheet-name characters. Do not
merge data-table cells.

Save to a temporary `.xlsx`, reopen it with `openpyxl.load_workbook`, verify the
required sheets/headers, row counts, timestamps, and hyperlinks, then atomically
rename it. Excel must open without a repair warning. Preserve an existing workbook
unless the user explicitly requested replacement or a compatible update.
