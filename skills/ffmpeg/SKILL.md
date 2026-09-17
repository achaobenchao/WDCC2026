---
name: ffmpeg
description: Probe local video metadata and safely extract audio or timestamped frames with FFmpeg/ffprobe for this repository's video-indexing workflow.
---

# FFmpeg for video indexing

Use local `ffprobe`/`ffmpeg`; never install or commit binaries. Quote every path
because names may contain Chinese characters, spaces, or shell metacharacters.
Prefer Python `subprocess.run([...])` argument lists for batches; never construct
commands by concatenating paths.

## Probe once

Run before extraction and retain the JSON:

```bash
ffprobe -v error -show_entries format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate -of json "INPUT"
```

Read duration from `format.duration`; select the primary `video` stream for
resolution/codec and prefer `avg_frame_rate` (a rational such as `30000/1001`)
for FPS, falling back to `r_frame_rate`. Presence of any `audio` stream means the
file has audio. Treat missing/`N/A` fields explicitly, not as zero.

## Extract

Representative frame at timestamp seconds (accurate seek):

```bash
ffmpeg -hide_banner -loglevel error -nostdin -i "INPUT" -ss TIMESTAMP -map 0:v:0 -frames:v 1 -q:v 2 -y "FRAME.jpg"
```

Audio for speech recognition (mono 16 kHz PCM):

```bash
ffmpeg -hide_banner -loglevel error -nostdin -i "INPUT" -map 0:a:0 -vn -ac 1 -ar 16000 -c:a pcm_s16le -y "AUDIO.wav"
```

For batches, enumerate files with Python/pathlib or null-delimited shell input;
do not parse `ls`. Create per-video output directories, write to a temporary
file, and rename only after success. Skip an existing validated output unless
overwrite was requested.

Check the exit code and capture stderr. On failure, report the input and stderr;
remove partial temporary output and continue other independent files. A missing
audio stream is a valid “no audio” result, not a transcription failure. Validate
frames are non-empty/readable and probe extracted audio before marking success.
