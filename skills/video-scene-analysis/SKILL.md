---
name: video-scene-analysis
description: Detect video scenes with PySceneDetect and select timestamp-preserving representative keyframes while minimizing downstream OCR and vision workload.
---

# Scene-aware keyframe planning

Never send every frame of a video to an AI model. Use this sequence:

`video → PySceneDetect scenes → representative timestamps → FFmpeg frames → OCR → later visual analysis`

Use the installed Python API (`scenedetect.detect` with `ContentDetector`) and
record every scene's start/end seconds. Tune the detector only when inspection
shows excessive cuts or missed transitions; preserve the chosen threshold in run
metadata. If detection returns no cuts, treat the full duration as one scene.

Choose one representative frame near each scene midpoint, avoiding the exact cut
boundary. For a long static scene, add interval samples so overlays, slides, or
people changes are not missed: when a scene exceeds roughly 20–30 seconds, sample
additional interior timestamps at a configurable interval in that range. Deduplicate
near-identical frames when safe, but keep enough samples to catch transient titles.
Use the FFmpeg skill for extraction.

Each filename and JSON record must retain the original-video timestamp. Example:

```text
video_001/frame_0001_00-01-25.jpg
```

```json
{"timestamp": 85.0, "scene": 3, "frame_path": "video_001/frame_0001_00-01-25.jpg"}
```

Also keep scene start/end and selection reason (`midpoint` or `interval`) in the
manifest. Validate timestamps are within video duration and frames are readable.
Do not renumber scenes differently between the manifest, OCR, and final index.
