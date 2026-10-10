import json


def score_job(job: dict, profile: dict) -> dict:
    if not job["eligible"]:
        job.update(apply_score=0, recommendation_level="EXCLUDED", score_breakdown="{}")
        return job
    parts = {}
    location = job.get("subregion") or job["region"]
    parts["지역"] = profile["regions"].get(location, profile["regions"].get(job["region"], 0))
    parts["회사규모"] = profile["company_preferences"].get(job["company_size"], 0)
    category_groups = {
        "데이터직무": {"DATA_ANALYSIS", "DATA_OPERATION", "BI", "DATA_ENGINEERING"},
        "제조데이터": {"SMART_FACTORY", "QUALITY_DATA", "PROCESS_DATA"},
        "자동화": {"DX", "AUTOMATION"},
    }
    for label, codes in category_groups.items():
        parts[label] = max(
            (profile["target_job_categories"].get(code, 0) for code in job["job_categories"] if code in codes),
            default=0,
        )
    skill_values = [profile["skills"].get(code, 0) for code in job["skills_required"] + job["skills_preferred"]]
    parts["기술"] = min(sum(skill_values), profile["scoring"]["skill_cap"])
    parts["연관업무"] = profile["scoring"]["related_score"] if job["matching_keywords"].get("related") else 0
    if job.get("negative_keywords"):
        parts["비관련직무"] = -profile["scoring"]["negative_penalty"]
    total = max(0, min(100, sum(parts.values())))
    thresholds = profile["scoring"]["recommendation_thresholds"]
    level = "HIGH" if total >= thresholds["HIGH"] else "GOOD" if total >= thresholds["GOOD"] else "REVIEW" if total >= thresholds["REVIEW"] else "LOW"
    job.update(
        skill_score=parts["기술"], region_score=parts["지역"], company_score=parts["회사규모"],
        apply_score=total, recommendation_level=level,
        score_breakdown=json.dumps(parts, ensure_ascii=False),
    )
    return job
