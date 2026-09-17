import json
import subprocess
from fractions import Fraction
from pathlib import Path

from .config import FFPROBE


def _fps(value):
    try:
        result = float(Fraction(value))
        return round(result, 3) if result > 0 else None
    except (ValueError, ZeroDivisionError):
        return None


def probe(path: Path, timeout=90):
    cmd = [
        str(FFPROBE), "-v", "error", "-show_entries",
        "format=duration,format_name:stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate",
        "-of", "json", str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"ffprobe exit {result.returncode}")
    raw = json.loads(result.stdout)
    video = next((s for s in raw.get("streams", []) if s.get("codec_type") == "video"), None)
    if not video:
        raise RuntimeError("未找到视频流")
    duration = float(raw.get("format", {}).get("duration") or 0)
    return {
        "duration": duration,
        "resolution": f'{video.get("width", "?")}x{video.get("height", "?")}',
        "width": video.get("width"),
        "height": video.get("height"),
        "fps": _fps(video.get("avg_frame_rate")) or _fps(video.get("r_frame_rate")),
        "video_codec": video.get("codec_name"),
        "has_audio": any(s.get("codec_type") == "audio" for s in raw.get("streams", [])),
        "audio_codec": next((s.get("codec_name") for s in raw.get("streams", []) if s.get("codec_type") == "audio"), None),
        "format": raw.get("format", {}).get("format_name"),
    }
