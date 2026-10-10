import json
import sqlite3
from pathlib import Path


JOB_COLUMNS = (
    "job_id", "source", "source_job_id", "company", "title", "region", "subregion", "region_raw", "company_size",
    "career_text", "education", "employment_type", "posted_at", "deadline", "collected_at",
    "posting_status", "source_freshness",
    "requirement_text", "preference_text", "description", "url", "career_status",
    "required_experience_years", "career_reason", "language_status", "language_type", "language_level",
    "language_reason", "job_categories", "skills_required", "skills_preferred", "job_reason", "manual_review",
    "driving_license_status", "driving_license_type", "driving_reason",
    "data_relevance", "manufacturing_relevance", "automation_relevance", "skill_score", "region_score",
    "company_score", "eligible", "exclude_reason", "apply_score", "recommendation_level",
    "matching_keywords", "score_breakdown", "policy_reason", "profile_id",
)


def connect(path: str | Path) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    initialize(connection)
    return connection


def initialize(connection: sqlite3.Connection) -> None:
    connection.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY, source TEXT, source_job_id TEXT, company TEXT, title TEXT,
            region TEXT, subregion TEXT, region_raw TEXT, company_size TEXT, career_text TEXT, education TEXT,
            employment_type TEXT, posted_at TEXT, deadline TEXT, collected_at TEXT,
            posting_status TEXT, source_freshness TEXT,
            requirement_text TEXT, preference_text TEXT, description TEXT, url TEXT,
            career_status TEXT, required_experience_years INTEGER, career_reason TEXT,
            language_status TEXT, language_type TEXT, language_level TEXT, language_reason TEXT,
            driving_license_status TEXT, driving_license_type TEXT, driving_reason TEXT,
            job_categories TEXT, skills_required TEXT, skills_preferred TEXT, job_reason TEXT,
            manual_review INTEGER, data_relevance REAL, manufacturing_relevance REAL, automation_relevance REAL,
            skill_score INTEGER, region_score INTEGER, company_score INTEGER, eligible INTEGER,
            exclude_reason TEXT, apply_score INTEGER, recommendation_level TEXT,
            matching_keywords TEXT, score_breakdown TEXT, policy_reason TEXT, profile_id TEXT
        )
    """)
    existing = {row[1] for row in connection.execute("PRAGMA table_info(jobs)")}
    additions = {
        "career_status": "TEXT", "subregion": "TEXT", "language_type": "TEXT", "language_level": "TEXT",
        "job_categories": "TEXT", "skills_required": "TEXT", "skills_preferred": "TEXT",
        "job_reason": "TEXT", "policy_reason": "TEXT", "profile_id": "TEXT",
        "posting_status": "TEXT", "source_freshness": "TEXT",
        "driving_license_status": "TEXT", "driving_license_type": "TEXT", "driving_reason": "TEXT",
    }
    for name, column_type in additions.items():
        if name not in existing:
            connection.execute(f"ALTER TABLE jobs ADD COLUMN {name} {column_type}")
    connection.execute("""
        CREATE TABLE IF NOT EXISTS job_status (
            job_id TEXT PRIMARY KEY, application_status TEXT NOT NULL DEFAULT 'UNREVIEWED',
            memo TEXT NOT NULL DEFAULT '', updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(job_id) REFERENCES jobs(job_id)
        )
    """)
    connection.commit()


def save_jobs(connection: sqlite3.Connection, jobs: list[dict]) -> None:
    placeholders = ",".join("?" for _ in JOB_COLUMNS)
    update = ",".join(f"{column}=excluded.{column}" for column in JOB_COLUMNS if column != "job_id")
    sql = f"INSERT INTO jobs ({','.join(JOB_COLUMNS)}) VALUES ({placeholders}) ON CONFLICT(job_id) DO UPDATE SET {update}"
    rows = []
    for job in jobs:
        values = []
        for column in JOB_COLUMNS:
            value = job.get(column, "")
            if column in {"matching_keywords", "job_categories", "skills_required", "skills_preferred"} and not isinstance(value, str):
                value = json.dumps(value, ensure_ascii=False)
            if column in {"eligible", "manual_review"}:
                value = int(bool(value))
            values.append(value)
        rows.append(values)
    connection.executemany(sql, rows)
    connection.commit()


def update_status(connection: sqlite3.Connection, job_id: str, status: str, memo: str) -> None:
    connection.execute("""
        INSERT INTO job_status(job_id, application_status, memo, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(job_id) DO UPDATE SET application_status=excluded.application_status,
        memo=excluded.memo, updated_at=CURRENT_TIMESTAMP
    """, (job_id, status, memo))
    connection.commit()


def fetch_jobs(connection: sqlite3.Connection) -> list[dict]:
    return [dict(row) for row in connection.execute("""
        SELECT j.*, COALESCE(s.application_status, 'UNREVIEWED') application_status,
               COALESCE(s.memo, '') memo
        FROM jobs j LEFT JOIN job_status s USING(job_id)
        ORDER BY eligible DESC, apply_score DESC
    """)]
