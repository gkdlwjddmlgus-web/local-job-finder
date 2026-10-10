import csv
import json
import re
from pathlib import Path

from src.classify.career import classify_career
from src.classify.job import classify_relevance
from src.classify.language import classify_language
from src.collect.manual import load_csv
from src.pipeline import ROOT, load_config
from src.preprocess.normalize import normalize_job


FIELD_MAP = {
    "human_career_status": "career_status",
    "human_required_experience_years": "required_experience_years",
    "human_language_status": "language_status",
    "human_language_type": "language_type",
    "human_region": "region",
    "human_job_categories": "job_categories",
    "human_skills": "skills",
}
MULTI_FIELDS = {"human_job_categories", "human_skills"}


def _labels(value: object) -> set[str]:
    text = str(value or "").strip()
    if not text:
        return set()
    if text.startswith("["):
        try:
            return {str(item).strip().upper() for item in json.loads(text) if str(item).strip()}
        except (json.JSONDecodeError, TypeError):
            pass
    return {item.strip().upper() for item in re.split(r"[|,;]", text) if item.strip()}


def _years(value: object) -> int | None:
    text = str(value or "").strip()
    if text.upper() in {"NONE", "NULL"}:
        return None
    return int(float(text))


def extract_job_facts(raw: dict, keywords: dict) -> dict:
    job = normalize_job(raw)
    job.update(classify_career(job["career_text"], job["requirement_text"], job["description"]))
    job.update(classify_language(job["requirement_text"], job["preference_text"], job["description"]))
    job.update(classify_relevance(job, keywords))
    job["skills"] = sorted(set(job["skills_required"]) | set(job["skills_preferred"]))
    return job


def validate_rows(raw_rows: list[dict]) -> tuple[list[dict], dict]:
    keywords = load_config(ROOT / "config" / "keywords.yml")
    mismatches = []
    counts = {system: {"correct": 0, "total": 0} for system in FIELD_MAP.values()}
    for raw in raw_rows:
        facts = extract_job_facts(raw, keywords)
        for human_field, system_field in FIELD_MAP.items():
            raw_human = str(raw.get(human_field, "")).strip()
            if not raw_human:
                continue
            system_value = facts.get(system_field)
            overlap = ""
            if human_field in MULTI_FIELDS:
                human_value = _labels(raw_human)
                actual_value = {str(item).upper() for item in system_value}
                matched = human_value == actual_value
                overlap = len(human_value & actual_value) / len(human_value | actual_value) if human_value | actual_value else 1.0
                shown_human = "|".join(sorted(human_value))
                shown_system = "|".join(sorted(actual_value))
            elif human_field == "human_required_experience_years":
                human_value = _years(raw_human)
                matched = human_value == system_value
                shown_human, shown_system = human_value, system_value
            else:
                human_value = raw_human.upper()
                actual_value = str(system_value or "").upper()
                matched = human_value == actual_value
                shown_human, shown_system = human_value, actual_value
            counts[system_field]["total"] += 1
            counts[system_field]["correct"] += int(matched)
            if not matched:
                mismatches.append({
                    "company": facts["company"], "title": facts["title"], "field": system_field,
                    "human_value": shown_human, "system_value": shown_system,
                    "overlap": overlap,
                })
    summary = {"validation_row_count": len(raw_rows), "mismatch_count": len(mismatches)}
    for field, values in counts.items():
        summary[f"{field}_correct"] = values["correct"]
        summary[f"{field}_total"] = values["total"]
        summary[f"{field}_accuracy"] = values["correct"] / values["total"] if values["total"] else None
    return mismatches, summary


def validate_csv(input_path: str | Path, output_path: str | Path) -> dict:
    mismatches, summary = validate_rows(load_csv(input_path))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    columns = ["company", "title", "field", "human_value", "system_value", "overlap"]
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(mismatches)
    return summary


def format_summary(summary: dict) -> str:
    labels = (
        ("career status accuracy", "career_status"),
        ("experience years accuracy", "required_experience_years"),
        ("language status accuracy", "language_status"),
        ("language type accuracy", "language_type"),
        ("region accuracy", "region"),
        ("job categories exact accuracy", "job_categories"),
        ("skills exact accuracy", "skills"),
    )
    lines = [f"validation row count: {summary['validation_row_count']}"]
    for label, field in labels:
        accuracy = summary[f"{field}_accuracy"]
        value = "N/A" if accuracy is None else f"{accuracy:.3f} ({summary[f'{field}_correct']}/{summary[f'{field}_total']})"
        lines.append(f"{label}: {value}")
    lines.append(f"mismatch count: {summary['mismatch_count']}")
    return "\n".join(lines)
