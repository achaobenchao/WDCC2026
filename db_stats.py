#!/usr/bin/env python3
"""Print concise statistics for the local video-index SQLite database."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database.db import DEFAULT_DB_PATH, connect  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="显示视频索引数据库统计")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()
    conn = connect(args.db)
    try:
        statements = {
            "视频数量": "SELECT COUNT(*) FROM videos",
            "人物数量": "SELECT COUNT(*) FROM persons",
            "人物-视频关系数量": "SELECT COUNT(*) FROM video_persons",
            "事件数量": "SELECT COUNT(*) FROM events",
            "关键词数量": "SELECT COUNT(*) FROM keywords",
            "需要人工复核视频数量": "SELECT COUNT(*) FROM videos WHERE review_required LIKE '%是%' OR review_required LIKE '%需要%'",
            "导入来源数量": "SELECT COUNT(*) FROM import_sources",
        }
        for label, statement in statements.items():
            print(f"{label}：{conn.execute(statement).fetchone()[0]}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
