CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_url TEXT NOT NULL UNIQUE,
    reported_date TEXT,
    raw_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    question TEXT NOT NULL,
    normalized_question TEXT NOT NULL,
    topic TEXT,
    question_type TEXT,
    interview_round TEXT,
    difficulty TEXT,
    reported_date TEXT,
    source_name TEXT,
    source_url TEXT,
    confidence TEXT,

    question_origin TEXT NOT NULL DEFAULT 'reported',
    report_count INTEGER NOT NULL DEFAULT 1,
    duplicate_of INTEGER,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(company, role, normalized_question)
);
