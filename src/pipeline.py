from pathlib import Path

import yaml

from src.classify.career import classify_career
from src.classify.driving import classify_driving_license
from src.classify.freshness import classify_posting_status, classify_source_freshness
from src.classify.job import classify_relevance
from src.classify.language import classify_language
from src.collect.manual import load_csv
from src.collect.registry import create_source
from src.preprocess.deduplicate import deduplicate
from src.preprocess.normalize import normalize_job
from src.profile.loader import load_profile
from src.policy.eligibility import evaluate_eligibility
from src.score.scoring import score_job
from src.storage.sqlite import connect, save_jobs


ROOT = Path(__file__).resolve().parents[1]


def load_config(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def process(raw_jobs: list[dict], profile: dict | None = None) -> tuple[list[dict], dict]:
    keywords = load_config(ROOT / "config" / "keywords.yml")
    profile = profile or load_profile(ROOT / "config" / "profiles" / "default.yml")
    normalized = [normalize_job(item) for item in raw_jobs]
    jobs = deduplicate(normalized)
    for job in jobs:
        career = classify_career(job["career_text"], job["requirement_text"], job["description"])
        language = classify_language(job["requirement_text"], job["preference_text"], job["description"])
        driving = classify_driving_license(
            job["title"], job["requirement_text"], job["preference_text"], job["description"]
        )
        relevance = classify_relevance(job, keywords)
        job.update(classify_posting_status(job["deadline"]))
        job.update(classify_source_freshness(job["source"], job.get("source_freshness")))
        job.update(career)
        job.update(language)
        job.update(driving)
        job.update(relevance)
        job.update(evaluate_eligibility(job, profile))
        score_job(job, profile)
    stats = {
        "collected": len(raw_jobs), "deduplicated": len(jobs),
        "career_excluded": sum(j["career_status"] == "EXPERIENCED" and not j["eligible"] for j in jobs),
        "language_excluded": sum(j["language_status"] == "REQUIRED" and not j["eligible"] for j in jobs),
        "eligible": sum(j["eligible"] for j in jobs),
        "recommended": sum(j["recommendation_level"] in {"HIGH", "GOOD"} for j in jobs),
    }
    return jobs, stats


def run_csv(csv_path: str | Path, db_path: str | Path | None = None, profile_path: str | Path | None = None) -> tuple[list[dict], dict]:
    profile = load_profile(profile_path or ROOT / "config" / "profiles" / "default.yml")
    jobs, stats = process(load_csv(csv_path), profile)
    connection = connect(db_path or ROOT / "data" / "local_job_finder.db")
    try:
        save_jobs(connection, jobs)
    finally:
        connection.close()
    return jobs, stats


def run_source(source_name: str = "daegu_seogu", db_path: str | Path | None = None,
               profile_path: str | Path | None = None, max_rows: int = 50) -> tuple[list[dict], dict]:
    source = create_source(source_name, ROOT / "data" / "raw", max_rows=max_rows)
    raw_jobs = source.collect()
    profile = load_profile(profile_path or ROOT / "config" / "profiles" / "default.yml")
    jobs, base_stats = process(raw_jobs, profile)
    connection = connect(db_path or ROOT / "data" / "local_job_finder.db")
    try:
        save_jobs(connection, jobs)
    finally:
        connection.close()
    if source_name == "daegu_seogu":
        candidate_path = ROOT / "data" / "processed" / "validation_candidates_real.csv"
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        candidate_columns = ["job_id", "company", "title", "region", "career_text", "deadline", "url", "source"]
        import csv
        with candidate_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=candidate_columns)
            writer.writeheader()
            writer.writerows([{column: job.get(column, "") for column in candidate_columns} for job in jobs[:15]])
    stats = {
        "requested": max_rows, "received": len(raw_jobs),
        "loaded": len(raw_jobs), "normalized": len(raw_jobs), "deduplicated": len(jobs),
        "active": sum(job["posting_status"] == "ACTIVE" for job in jobs),
        "expired": sum(job["posting_status"] == "EXPIRED" for job in jobs),
        "unknown": sum(job["posting_status"] == "UNKNOWN" for job in jobs),
        "career_facts_extracted": sum(bool(job.get("career_status")) for job in jobs),
        "eligible": sum(job["eligible"] for job in jobs),
        "excluded": sum(not job["eligible"] for job in jobs),
        "review": sum(job["manual_review"] for job in jobs),
        "high": sum(job["recommendation_level"] == "HIGH" for job in jobs),
        "good": sum(job["recommendation_level"] == "GOOD" for job in jobs),
        **{f"pipeline_{key}": value for key, value in base_stats.items()},
    }
    return jobs, stats
