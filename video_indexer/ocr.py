from pathlib import Path

from .config import OCR_MIN_SCORE


class OCRRunner:
    def __init__(self):
        self.engine = None
        self.error = None

    def _load(self):
        if self.engine is None and self.error is None:
            try:
                from paddleocr import PaddleOCR
                self.engine = PaddleOCR(lang="ch", use_doc_orientation_classify=False, use_doc_unwarping=False,
                                        use_textline_orientation=False, text_detection_model_name="PP-OCRv5_mobile_det",
                                        text_recognition_model_name="PP-OCRv5_mobile_rec")
            except Exception as exc:
                self.error = str(exc)

    @staticmethod
    def _parse(result):
        payload = getattr(result, "json", result)
        if callable(payload):
            payload = payload()
        if isinstance(payload, dict) and "res" in payload:
            payload = payload["res"]
        if not isinstance(payload, dict):
            return []
        texts = payload.get("rec_texts") or []
        scores = payload.get("rec_scores") or []
        boxes = payload.get("rec_polys") or payload.get("dt_polys") or []
        lines = []
        for i, text in enumerate(texts):
            score = float(scores[i]) if i < len(scores) else None
            if str(text).strip() and (score is None or score >= OCR_MIN_SCORE):
                box = boxes[i].tolist() if i < len(boxes) and hasattr(boxes[i], "tolist") else (boxes[i] if i < len(boxes) else None)
                lines.append({"text": str(text).strip(), "score": score, "box": box})
        return lines

    def run(self, frames):
        self._load()
        if self.error:
            return {"status": "failed", "error": self.error, "frames": []}
        output = []
        failures = []
        for frame in frames:
            try:
                results = list(self.engine.predict(frame["frame_path"]))
                lines = []
                for result in results:
                    lines.extend(self._parse(result))
                output.append({**frame, "lines": lines})
            except Exception as exc:
                failures.append(f'{Path(frame["frame_path"]).name}: {exc}')
        status = "success" if output else "failed"
        return {"status": status, "error": " | ".join(failures) or None, "frames": output}
