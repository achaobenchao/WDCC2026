import os
import subprocess
from pathlib import Path

import cv2

from .config import FFMPEG


def hms(seconds):
    seconds = max(0, int(round(seconds)))
    return f"{seconds // 3600:02d}-{seconds % 3600 // 60:02d}-{seconds % 60:02d}"


def _difference(a, b):
    if a is None or b is None:
        return 1.0
    aa = cv2.resize(a, (32, 32)).astype("float32")
    bb = cv2.resize(b, (32, 32)).astype("float32")
    return float(cv2.absdiff(aa, bb).mean() / 255.0)


def extract(path: Path, candidates, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    kept, previous = [], None
    for i, item in enumerate(candidates, 1):
        final = output_dir / f'frame_{i:04d}_{hms(item["timestamp"])}.jpg'
        existing = cv2.imread(str(final), cv2.IMREAD_GRAYSCALE) if final.exists() else None
        needs_extract = existing is None or max(existing.shape[:2]) > 1920
        if needs_extract:
            tmp = final.with_name(final.stem + ".tmp.jpg")
            cmd = [str(FFMPEG), "-hide_banner", "-loglevel", "error", "-nostdin",
                   "-ss", f'{item["timestamp"]:.3f}', "-i", str(path), "-map", "0:v:0", "-frames:v", "1",
                   "-vf", "scale=1920:1920:force_original_aspect_ratio=decrease", "-q:v", "2", "-y", str(tmp)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode or not tmp.exists() or tmp.stat().st_size == 0:
                tmp.unlink(missing_ok=True)
                continue
            os.replace(tmp, final)
        image = cv2.imread(str(final), cv2.IMREAD_GRAYSCALE)
        if image is None:
            final.unlink(missing_ok=True)
            continue
        if previous is not None and _difference(previous, image) < 0.018:
            final.unlink(missing_ok=True)
            continue
        previous = image
        kept.append({**item, "frame_path": str(final)})
    return kept
