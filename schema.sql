PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY,
    source_excel TEXT NOT NULL,
    source_sheet TEXT NOT NULL,
    source_batch TEXT NOT NULL DEFAULT '',
    source_key TEXT NOT NULL,
    filename TEXT NOT NULL,
    relative_path TEXT,
    full_path TEXT,
    folder TEXT,
    file_size TEXT,
    duration TEXT,
    resolution TEXT,
    fps TEXT,
    summary TEXT,
    activity_name TEXT,
    organization TEXT,
    location TEXT,
    important_date TEXT,
    important_text TEXT,
    speech_keywords TEXT,
    search_keywords TEXT,
    overall_confidence TEXT,
    review_required TEXT,
    processing_status TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (source_excel, source_sheet, source_batch, source_key)
);

CREATE TABLE IF NOT EXISTS persons (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT '',
    normalized_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS video_persons (
    id INTEGER PRIMARY KEY,
    video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    person_id INTEGER NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    first_seen TEXT,
    first_seen_seconds REAL,
    time_ranges TEXT,
    related_events TEXT,
    evidence TEXT,
    confidence TEXT,
    source_excel TEXT NOT NULL,
    source_sheet TEXT NOT NULL,
    UNIQUE (video_id, person_id, first_seen, time_ranges, related_events, source_excel, source_sheet)
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    event_number TEXT NOT NULL DEFAULT '',
    event_type TEXT,
    event_name TEXT,
    start_time TEXT,
    end_time TEXT,
    start_seconds REAL,
    end_seconds REAL,
    description TEXT,
    persons_text TEXT,
    organization TEXT,
    location TEXT,
    evidence TEXT,
    confidence TEXT,
    review_required TEXT,
    source_excel TEXT NOT NULL,
    source_sheet TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (video_id, event_number, event_type, event_name, start_time, end_time, source_excel, source_sheet)
);

CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY,
    video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    keyword TEXT NOT NULL,
    keyword_type TEXT NOT NULL,
    UNIQUE (video_id, keyword, keyword_type)
);

CREATE TABLE IF NOT EXISTS import_sources (
    id INTEGER PRIMARY KEY,
    source_filename TEXT NOT NULL,
    source_path TEXT NOT NULL UNIQUE,
    import_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    rows_read TEXT,
    rows_imported TEXT,
    rows_skipped TEXT,
    duplicate_count TEXT,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_videos_filename ON videos(filename);
CREATE INDEX IF NOT EXISTS idx_videos_full_path ON videos(full_path);
CREATE INDEX IF NOT EXISTS idx_videos_source_batch ON videos(source_batch);
CREATE INDEX IF NOT EXISTS idx_videos_review_required ON videos(review_required);
CREATE INDEX IF NOT EXISTS idx_persons_name ON persons(name);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_name ON events(event_name);
CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword);
