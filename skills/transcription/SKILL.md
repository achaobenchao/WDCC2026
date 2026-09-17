---
name: transcription
description: Transcribe local video audio with faster-whisper into timestamped JSON and readable TXT, prioritizing Chinese and falling back safely from GPU to CPU.
---

# Timestamped transcription

1. Use the FFmpeg skill to confirm an audio stream and extract mono 16 kHz WAV.
2. If a prior transcript JSON exists and is valid for the same source file
   (record source path plus size/mtime or a hash), skip it.
3. Load `faster_whisper.WhisperModel` once per batch. Prefer CUDA with a supported
   compute type (usually `float16`); if initialization/inference shows CUDA is
   unavailable, retry on CPU with `compute_type="int8"` and record the fallback.
4. Call `transcribe(..., language="zh", vad_filter=True)` when Chinese is known.
   When language is unknown, omit `language` and record the detected language and
   probability. Materialize the returned segment generator before declaring
   success.
5. Atomically write UTF-8 JSON and readable TXT. Do not overwrite a valid result
   with a failed or empty retry.

JSON must contain at least this segment schema (extra run metadata may wrap it):

```json
[
  {"start": 12.5, "end": 17.2, "text": "下面有请张教授发表讲话"}
]
```

Store seconds as numbers, ensure `0 <= start <= end`, strip surrounding
whitespace, and keep original wording rather than hallucinating corrections.
TXT should render each non-empty segment as `[HH:MM:SS - HH:MM:SS] text`.
No-audio files are recorded as skipped. Models remain in the normal local cache
and are never committed.
