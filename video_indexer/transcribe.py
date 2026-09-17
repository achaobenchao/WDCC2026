import json
import os
import subprocess
from pathlib import Path

from .config import FFMPEG, WHISPER_MODEL


def hms(seconds):
    seconds = max(0, int(round(seconds)))
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


class Transcriber:
    def __init__(self):
        self.model = None
        self.error = None

    def _load(self):
        if self.model is None and self.error is None:
            try:
                from faster_whisper import WhisperModel
                self.model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
            except Exception as exc:
                self.error = str(exc)

    def run(self, video: Path, audio_path: Path, txt_path: Path):
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = audio_path.with_name(audio_path.stem + ".tmp.wav")
        result = subprocess.run([
            str(FFMPEG), "-hide_banner", "-loglevel", "error", "-nostdin", "-i", str(video),
            "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", "-y", str(tmp),
        ], capture_output=True, text=True, timeout=max(180, int(video.stat().st_size / 1_000_000)))
        if result.returncode:
            tmp.unlink(missing_ok=True)
            return {"status": "failed", "error": result.stderr.strip(), "segments": []}
        os.replace(tmp, audio_path)
        self._load()
        if self.error:
            return {"status": "failed", "error": self.error, "segments": []}
        try:
            segments_iter, info = self.model.transcribe(
                str(audio_path), language="zh", vad_filter=True, beam_size=1,
                condition_on_previous_text=False,
            )
            segments = [{"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip()}
                        for s in segments_iter if s.text.strip()]
            txt_path.parent.mkdir(parents=True, exist_ok=True)
            with txt_path.open("w", encoding="utf-8") as stream:
                for segment in segments:
                    stream.write(f'[{hms(segment["start"])} - {hms(segment["end"])}] {segment["text"]}\n')
            return {"status": "success", "error": None, "language": getattr(info, "language", "zh"), "segments": segments}
        except Exception as exc:
            return {"status": "failed", "error": str(exc), "segments": []}
        finally:
            audio_path.unlink(missing_ok=True)
