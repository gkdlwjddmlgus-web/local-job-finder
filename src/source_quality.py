import csv
from pathlib import Path


QUALITY_FIELDS = ("company", "title", "region", "deadline", "description", "url")
TARGET_KEYWORDS = (
    "data", "데이터", "python", "sql", "ai", "전산", "it", "dx",
    "스마트팩토리", "생산", "공정", "품질", "자동화", "bi",
)
DIFFICULT_KEYWORDS = (
    "신입/경력", "신입 및 경력", "경력무관", "경력 무관", "운전면허",
    "운전 가능", "어학", "영어", "토익", "해외출장", "데이터", "전산", "dx",
)
CANDIDATE_COLUMNS = (
    "job_id", "company", "title", "region", "career_text", "deadline",
    "posting_status", "description", "url", "source",
)


def _present(job: dict, field: str) -> bool:
    value = job.get("region_raw") if field == "region" else job.get(field)
    return bool(str(value or "").strip())


def source_quality(jobs: list[dict]) -> dict:
    total = len(jobs)

    def percentage(count: int) -> float:
        return round(count * 100 / total, 1) if total else 0.0

    result = {
        field: percentage(sum(_present(job, field) for job in jobs))
        for field in QUALITY_FIELDS
    }
    result.update({
        "career_fact": percentage(sum(job.get("career_status") != "REVIEW" for job in jobs)),
        "language_observable": percentage(sum(job.get("language_status") != "NONE" for job in jobs)),
        "driving_observable": percentage(sum(job.get("driving_license_status") != "NONE" for job in jobs)),
    })
    return result


def target_related_count(jobs: list[dict]) -> int:
    count = 0
    for job in jobs:
        if job.get("posting_status") != "ACTIVE":
            continue
        text = " ".join(str(job.get(field) or "") for field in (
            "title", "description", "requirement_text", "preference_text"
        )).casefold()
        if any(keyword.casefold() in text for keyword in TARGET_KEYWORDS):
            count += 1
    return count


def write_live_validation_candidates(jobs: list[dict], output: str | Path, limit: int = 15) -> list[dict]:
    active = [job for job in jobs if job.get("posting_status") == "ACTIVE"]

    def is_difficult(job: dict) -> bool:
        text = " ".join(str(job.get(field) or "") for field in (
            "title", "career_text", "description", "requirement_text", "preference_text"
        )).casefold()
        return any(keyword.casefold() in text for keyword in DIFFICULT_KEYWORDS)

    regular = [job for job in active if not is_difficult(job)][:10]
    difficult = [job for job in active if is_difficult(job)][:5]
    selected = regular + difficult
    selected_ids = {job["job_id"] for job in selected}
    if len(selected) < limit:
        selected.extend(job for job in active if job["job_id"] not in selected_ids)
    selected = selected[:limit]

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_COLUMNS)
        writer.writeheader()
        writer.writerows({column: job.get(column, "") for column in CANDIDATE_COLUMNS} for job in selected)
    return selected
