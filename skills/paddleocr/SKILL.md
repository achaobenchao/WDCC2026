---
name: paddleocr
description: Run local PaddleOCR on selected video keyframes to recover names, titles, organizations, locations, events, dates, captions, slides, banners, and on-screen headings.
---

# Local keyframe OCR

Use the installed Python `paddleocr` package and a platform-appropriate local
PaddlePaddle runtime. Do not require a cloud API, token, or document-parsing
pipeline. Process only keyframes selected by the scene-analysis skill.

Initialize the OCR pipeline once per batch, with Chinese as the default language
(`lang="ch"`) and orientation handling enabled when supported by the installed
version. PaddleOCR APIs differ across major versions: inspect the installed
package/help and use its current local `PaddleOCR(...).predict(...)` or compatible
local inference call; do not silently switch to `paddleocr api` or upload images.

For each frame, preserve:

- video-relative timestamp, scene number, and frame path
- recognized text in reading order
- confidence and polygon/bounding box when returned

Save UTF-8 JSON. Keep low-confidence text marked rather than inventing a
correction. Pay special attention to 人名、职务、公司、机构、地点、活动/会议名称、日期、
新闻字幕、采访姓名条、PPT 标题、横幅和画面标题. Merge exact or near-identical
repeats across adjacent frames later; retain the clearest observation and its
timestamp. If no text is found, record an empty result. A corrupt frame or model
error must be logged separately and must not erase successful OCR from other
frames.
