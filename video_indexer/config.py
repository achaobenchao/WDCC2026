from pathlib import Path

VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".mkv", ".avi", ".mxf", ".mts", ".m2ts",
    ".ts", ".webm", ".flv", ".wmv", ".m4v",
}

FFMPEG = Path("/opt/homebrew/bin/ffmpeg")
FFPROBE = Path("/opt/homebrew/bin/ffprobe")
SCENE_THRESHOLD = 30.0
LONG_SCENE_SECONDS = 30.0
LONG_SAMPLE_INTERVAL = 25.0
MAX_KEYFRAMES = 18
OCR_MIN_SCORE = 0.55
WHISPER_MODEL = "small"
