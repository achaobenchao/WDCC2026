# Video Analysis Agent Instructions

For video-material indexing tasks, use the repository skills below and read the
matching `SKILL.md` before acting:

- `skills/ffmpeg/SKILL.md`: metadata, audio extraction, and frame extraction
- `skills/video-scene-analysis/SKILL.md`: scene detection and keyframe planning
- `skills/paddleocr/SKILL.md`: OCR on selected keyframes
- `skills/transcription/SKILL.md`: timestamped speech transcription
- `skills/xlsx/SKILL.md`: final Excel index generation

Use only the skills relevant to the current step. Do not search GitHub for a
replacement tool or reimplement capabilities already covered here unless the
current skill cannot meet the task; document that limitation before changing
tools. This avoids repeated research, duplicate code, and unnecessary token use.

Do not analyze videos merely because the repository is opened. Never commit
virtual environments, caches, FFmpeg binaries, model files, API keys, or media
outputs. Models are downloaded to local caches only when an actual run needs
them.
