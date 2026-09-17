import math
import subprocess
from pathlib import Path

import cv2
import numpy as np
from scenedetect import ContentDetector, SceneManager, open_video

from .config import FFMPEG, LONG_SAMPLE_INTERVAL, LONG_SCENE_SECONDS, MAX_KEYFRAMES, SCENE_THRESHOLD

SPARSE_SCAN_SECONDS = 0
SPARSE_SCAN_MAX_FRAMES = 120


def _sparse_scenes(path: Path, duration: float):
    """Run PySceneDetect's content detector on bounded, original-timeline samples."""
    step = max(5.0, duration / SPARSE_SCAN_MAX_FRAMES)
    timestamps = [min(duration - 0.1, i * step) for i in range(int(duration / step) + 1)]
    timestamps = [t for t in timestamps if t >= 0 and t < duration]
    detector = ContentDetector(threshold=SCENE_THRESHOLD, min_scene_len=1)
    cuts = []
    for index, stamp in enumerate(timestamps):
        result = subprocess.run([
            str(FFMPEG), "-hide_banner", "-loglevel", "error", "-nostdin", "-ss", f"{stamp:.3f}",
            "-i", str(path), "-frames:v", "1", "-vf", "scale=320:-2", "-f", "image2pipe", "-vcodec", "mjpeg", "-",
        ], capture_output=True, timeout=45)
        if result.returncode or not result.stdout:
            continue
        frame = cv2.imdecode(np.frombuffer(result.stdout, dtype=np.uint8), cv2.IMREAD_COLOR)
        if frame is not None and detector.process_frame(index, frame):
            cuts.append(stamp)
    bounds = [0.0] + sorted({round(t, 3) for t in cuts if 0 < t < duration}) + [duration]
    return [{"scene": i, "start": bounds[i - 1], "end": bounds[i]} for i in range(1, len(bounds))]


def detect_scenes(path: Path, duration: float):
    if duration > SPARSE_SCAN_SECONDS:
        scenes = _sparse_scenes(path, duration)
        return _candidate_frames(scenes, duration)
    # 4K NAS originals are expensive to decode frame-by-frame. Sampling every
    # fifth frame still checks scene content at about 5 Hz for the common 25fps
    # footage while keeping timestamps on the original video timeline.
    video = open_video(str(path), backend="opencv")
    manager = SceneManager()
    manager.add_detector(ContentDetector(threshold=SCENE_THRESHOLD))
    manager.detect_scenes(video, show_progress=False, frame_skip=4)
    raw = manager.get_scene_list(start_in_scene=True)
    scenes = [
        {"scene": i, "start": a.get_seconds(), "end": b.get_seconds()}
        for i, (a, b) in enumerate(raw, 1)
    ]
    return _candidate_frames(scenes, duration)


def _candidate_frames(scenes, duration):
    if not scenes and duration > 0:
        scenes = [{"scene": 1, "start": 0.0, "end": duration}]
    candidates = []
    for scene in scenes:
        start, end = scene["start"], min(scene["end"], duration)
        span = max(0.0, end - start)
        if span <= 0:
            continue
        candidates.append({"timestamp": start + span / 2, "scene": scene["scene"], "reason": "midpoint"})
        if span > LONG_SCENE_SECONDS:
            count = int(math.floor(span / LONG_SAMPLE_INTERVAL))
            for n in range(1, count + 1):
                stamp = start + n * LONG_SAMPLE_INTERVAL
                if stamp < end - 1:
                    candidates.append({"timestamp": stamp, "scene": scene["scene"], "reason": "interval"})
    candidates.sort(key=lambda x: x["timestamp"])
    if len(candidates) > MAX_KEYFRAMES:
        indexes = sorted({round(i * (len(candidates) - 1) / (MAX_KEYFRAMES - 1)) for i in range(MAX_KEYFRAMES)})
        candidates = [candidates[i] for i in indexes]
    return scenes, candidates
