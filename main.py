import argparse
import json
import logging
import os
import time
from pathlib import Path

from .analyze import fuse
from .cache import atomic_json, cache_id, fingerprint, load_json, reusable
from .excel import export
from .frames import extract
from .ocr import OCRRunner
from .scanner import scan
from .scenes import detect_scenes
from .transcribe import Transcriber
from .video_info import probe

PIPELINE_VERSION = "0.1.4"
OCR_VERSION = "paddleocr-v5-mobile"


def setup_logging(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(path, encoding="utf-8"), logging.StreamHandler()],
                        force=True)


def main():
    parser = argparse.ArgumentParser(description="视频素材智能检索与 Excel 索引")
    parser.add_argument("root", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--match", help="只处理相对路径中包含此文本的视频（用于测试）")
    parser.add_argument("--resume", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--no-excel", action="store_true")
    parser.add_argument("--run-name", help="隔离本次运行的 cache/output/logs，例如 顾珣")
    parser.add_argument("--excel-name", help="输出 Excel 文件名，不含路径")
    parser.add_argument("--shard-count", type=int, default=1, help="固定分片总数（用于本机受控并行）")
    parser.add_argument("--shard-index", type=int, default=0, help="当前分片编号，从 0 开始")
    args = parser.parse_args()
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        parser.error("--shard-count 必须 >= 1，且 0 <= --shard-index < --shard-count")
    project = Path.cwd()
    if args.run_name:
        cache = project / "cache" / args.run_name
        output = project / "output" / args.run_name
        log_path = project / "logs" / args.run_name / "process.log"
        excel_name = args.excel_name or f"视频素材检索结果_{args.run_name}.xlsx"
    else:
        cache = project / "cache"
        output = project / "output"
        log_path = project / "logs/process.log"
        excel_name = args.excel_name or "视频素材检索结果_蔡坤测试.xlsx"
    setup_logging(log_path)
    started = time.time(); videos = scan(args.root)
    atomic_json(output / "manifest.json", {"root": str(args.root.resolve()), "count": len(videos), "videos": videos})
    logging.info("素材根目录: %s", args.root.resolve()); logging.info("本次测试共发现 %d 个视频", len(videos))
    work = [v for v in videos if not args.match or args.match in v["relative_path"]]
    work = work[:args.limit] if args.limit else work
    work = [v for index, v in enumerate(work) if index % args.shard_count == args.shard_index]
    logging.info("分片: %d/%d，本分片 %d 个视频", args.shard_index + 1, args.shard_count, len(work))
    ocr_runner, transcriber, records = OCRRunner(), Transcriber(), []
    for pos, item in enumerate(work, 1):
        one_started = time.time(); path = Path(item["path"]); cid = cache_id(path); source = fingerprint(path)
        result_path = output / "index" / f"{cid}.json"; existing = load_json(result_path)
        if args.resume and reusable(existing, source) and existing.get("pipeline_version") == PIPELINE_VERSION:
            records.append(existing); logging.info("[%d/%d] REUSED %s", pos, len(work), item["relative_path"]); continue
        logging.info("[%d/%d] Processing %s", pos, len(work), item["relative_path"])
        quality = {"ffprobe": "pending", "scenes": "pending", "frames": "pending", "ocr": "pending", "transcription": "pending",
                   "persons": "pending", "events": "pending", "errors": ""}
        base = {"pipeline_version": PIPELINE_VERSION, "source": source, "file": item, "persons": [], "events": [], "organizations": [], "locations": [], "activities": [],
                "ocr_keywords": [], "speech_keywords": [], "search_keywords": [], "summary": "", "confidence": "低",
                "needs_review": True, "quality": quality, "status": "processing", "error": None}
        atomic_json(result_path, base)
        errors = []
        try:
            meta_path = cache / "metadata" / f"{cid}.json"; meta_cache = load_json(meta_path)
            if reusable(meta_cache, source): meta = meta_cache["data"]
            else:
                meta = probe(path); atomic_json(meta_path, {"source": source, "status": "success", "data": meta})
            base["file"].update(meta); quality["ffprobe"] = "success"
        except Exception as exc:
            quality["ffprobe"] = "failed"; errors.append(f"ffprobe: {exc}")
            base.update(status="failed", error=" | ".join(errors)); quality["errors"] = base["error"]; atomic_json(result_path, base); records.append(base); continue
        try:
            scene_path = cache / "scenes" / f"{cid}.json"; scene_cache = load_json(scene_path)
            if reusable(scene_cache, source): scenes, candidates = scene_cache["scenes"], scene_cache["candidates"]
            else:
                scenes, candidates = detect_scenes(path, meta["duration"])
                atomic_json(scene_path, {"source": source, "status": "success", "scenes": scenes, "candidates": candidates})
            quality["scenes"] = "success"
            frames = extract(path, candidates, cache / "frames" / cid); quality["frames"] = "success" if frames else "failed"
            if not frames: errors.append("未提取到可读关键帧")
        except Exception as exc:
            frames = []; quality["scenes"] = "failed"; quality["frames"] = "failed"; errors.append(f"场景/关键帧: {exc}")
        ocr_path = cache / "ocr" / f"{cid}.json"; ocr_cache = load_json(ocr_path)
        if args.resume and reusable(ocr_cache, source) and ocr_cache.get("ocr_version") == OCR_VERSION: ocr_data = ocr_cache["data"]
        elif frames:
            ocr_data = ocr_runner.run(frames); atomic_json(ocr_path, {"ocr_version": OCR_VERSION, "source": source, "status": ocr_data["status"], "data": ocr_data})
        else: ocr_data = {"status": "skipped", "error": "无关键帧", "frames": []}
        quality["ocr"] = ocr_data["status"]
        if ocr_data.get("error"): errors.append("OCR: " + ocr_data["error"])
        transcript_path = cache / "transcripts" / f"{cid}.json"; transcript_cache = load_json(transcript_path)
        if not meta["has_audio"]: transcript = {"status": "no_audio", "segments": [], "error": None}
        elif args.resume and reusable(transcript_cache, source): transcript = transcript_cache["data"]
        else:
            transcript = transcriber.run(path, cache / "audio" / f"{cid}.wav", output / "transcripts" / f"{cid}.txt")
            atomic_json(transcript_path, {"source": source, "status": transcript["status"], "data": transcript})
        quality["transcription"] = transcript["status"]
        if transcript.get("error"): errors.append("ASR: " + transcript["error"])
        analysis = fuse(base["file"], ocr_data, transcript); base.update(analysis)
        quality["persons"] = "success" if base["persons"] else "无重要人物"
        quality["events"] = "success" if base["events"] else "无明确重要事件"
        quality["errors"] = " | ".join(errors)
        base["status"] = "success" if quality["ffprobe"] == "success" else "failed"
        base["error"] = quality["errors"] or None; base["processing_seconds"] = round(time.time() - one_started, 2)
        atomic_json(result_path, base); records.append(base)
        logging.info("[%d/%d] %s %.1fs", pos, len(work), base["status"].upper(), base["processing_seconds"])
    if not args.no_excel:
        all_records = []
        for item in videos:
            record = load_json(output / "index" / f'{cache_id(Path(item["path"]))}.json')
            if record: all_records.append(record)
        export(all_records, output / excel_name)
    elapsed = time.time() - started
    summary = {"video_total": len(videos), "records": len(records), "success": sum(r.get("status") == "success" for r in records),
               "failed": sum(r.get("status") == "failed" for r in records), "needs_review": sum(bool(r.get("needs_review")) for r in records),
               "ocr_effective": sum(bool(r.get("ocr_keywords")) for r in records), "asr_effective": sum(bool(r.get("speech_keywords")) for r in records),
               "persons_effective": sum(bool(r.get("persons")) for r in records), "events_effective": sum(bool(r.get("events")) for r in records),
               "elapsed_seconds": round(elapsed, 2), "average_seconds": round(elapsed / len(records), 2) if records else 0}
    atomic_json(output / "run_summary.json", summary); logging.info("完成: %s", json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
