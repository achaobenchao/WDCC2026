"""Connection, schema and small shared helpers for the local SQLite index."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "database" / "video_index.db"
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def initialize(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    connection = connect(db_path)
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return connection


def normalize_text(value: object) -> str:
    return re.sub(r"\s+", "", str(value or "")).casefold()


def parse_timestamp(value: object) -> float | None:
    """Return seconds for HH:MM:SS-like values; preserve unparseable text elsewhere."""
    text = str(value or "").strip()
    match = re.fullmatch(r"(\d{1,3}):(\d{1,2}):(\d{1,2})(?:\.\d+)?", text)
    if not match:
        return None
    hours, minutes, seconds = map(int, match.groups())
    if minutes >= 60 or seconds >= 60:
        return None
    return float(hours * 3600 + minutes * 60 + seconds)


def parse_range(value: object) -> tuple[float | None, float | None]:
    text = str(value or "").strip().replace("–", "-").replace("—", "-")
    pieces = re.split(r"\s*-\s*", text, maxsplit=1)
    if len(pieces) == 2:
        return parse_timestamp(pieces[0]), parse_timestamp(pieces[1])
    start = parse_timestamp(text)
    return start, start
