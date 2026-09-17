#!/usr/bin/env python3
"""Simple UTF-8 CLI queries for the local WDCC SQLite video index."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database.db import DEFAULT_DB_PATH, connect  # noqa: E402


def print_rows(rows) -> None:
    rows = list(rows)
    if not rows:
        print("未找到匹配记录。")
        return
    for row in rows:
        print(" | ".join(f"{key}={row[key] or ''}" for key in row.keys()))


def like(term: str) -> str:
    return f"%{term}%"


def main() -> None:
    parser = argparse.ArgumentParser(description="查询 WDCC 视频素材 SQLite 索引")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--limit", type=int, default=50, help="最多显示记录数（默认 50）")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (("person", "按人物姓名/描述查询视频"), ("event", "按事件类型或名称查询视频"), ("keyword", "按关键词查询视频"), ("file", "按文件名查询"), ("video", "查看某视频的人物与事件")):
        command = sub.add_parser(name, help=help_text); command.add_argument("term")
    sub.add_parser("review", help="列出需要人工复核的视频")
    args = parser.parse_args()
    conn = connect(args.db)
    try:
        if args.command == "person":
            print_rows(conn.execute("SELECT p.name AS 人物,p.role AS 身份,v.filename AS 文件名,v.full_path AS 完整路径,vp.first_seen AS 首次出现,vp.time_ranges AS 主要出现时间,vp.related_events AS 相关事件,vp.confidence AS 置信度 FROM video_persons vp JOIN persons p ON p.id=vp.person_id JOIN videos v ON v.id=vp.video_id WHERE p.name LIKE ? ORDER BY p.name,v.filename LIMIT ?", (like(args.term), args.limit)))
        elif args.command == "event":
            print_rows(conn.execute("SELECT e.event_type AS 事件类型,e.event_name AS 事件名称,v.filename AS 文件名,v.full_path AS 完整路径,e.start_time AS 开始,e.end_time AS 结束,e.confidence AS 置信度 FROM events e JOIN videos v ON v.id=e.video_id WHERE e.event_type LIKE ? OR e.event_name LIKE ? ORDER BY v.filename,e.start_seconds LIMIT ?", (like(args.term), like(args.term), args.limit)))
        elif args.command == "keyword":
            print_rows(conn.execute("SELECT k.keyword AS 关键词,k.keyword_type AS 类型,v.filename AS 文件名,v.full_path AS 完整路径 FROM keywords k JOIN videos v ON v.id=k.video_id WHERE k.keyword LIKE ? ORDER BY k.keyword,v.filename LIMIT ?", (like(args.term), args.limit)))
        elif args.command == "file":
            print_rows(conn.execute("SELECT id,filename,source_batch,full_path,summary,review_required,processing_status FROM videos WHERE filename LIKE ? ORDER BY filename LIMIT ?", (like(args.term), args.limit)))
        elif args.command == "review":
            print_rows(conn.execute("SELECT id,filename,source_batch,full_path,summary,notes FROM videos WHERE review_required LIKE '%是%' OR review_required LIKE '%需要%' ORDER BY source_batch,filename LIMIT ?", (args.limit,)))
        else:
            videos = list(conn.execute("SELECT id,filename,source_batch,full_path,summary FROM videos WHERE filename LIKE ? OR full_path LIKE ? ORDER BY filename LIMIT ?", (like(args.term), like(args.term), args.limit)))
            print_rows(videos)
            for video in videos:
                print(f"\n人物 — {video['filename']}")
                print_rows(conn.execute("SELECT p.name,p.role,vp.first_seen,vp.time_ranges,vp.related_events,vp.confidence FROM video_persons vp JOIN persons p ON p.id=vp.person_id WHERE vp.video_id=?", (video["id"],)))
                print(f"事件 — {video['filename']}")
                print_rows(conn.execute("SELECT event_type,event_name,start_time,end_time,description,confidence FROM events WHERE video_id=? ORDER BY start_seconds", (video["id"],)))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
