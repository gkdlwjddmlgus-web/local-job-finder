def classify_relevance(job: dict, keyword_config: dict) -> dict:
    required_text = " ".join(str(job.get(field, "")) for field in ("title", "requirement_text", "description"))
    preferred_text = str(job.get("preference_text", ""))
    text = f"{required_text} {preferred_text}"
    lowered = text.lower()
    matches = {}
    for category, keywords in keyword_config["categories"].items():
        matches[category] = [word for word in keywords if word.lower() in lowered]
    negatives = [word for word in keyword_config.get("negative", []) if word.lower() in lowered]
    job_categories = [code for code, words in keyword_config["job_categories"].items() if any(word.lower() in lowered for word in words)]
    skills_required = [code for code, words in keyword_config["skills"].items() if any(word.lower() in required_text.lower() for word in words)]
    skills_preferred = [code for code, words in keyword_config["skills"].items() if any(word.lower() in preferred_text.lower() for word in words) and code not in skills_required]
    reason = ", ".join(job_categories + skills_required + skills_preferred) or "직무/기술 키워드 없음"
    return {
        "matching_keywords": matches, "negative_keywords": negatives,
        "job_categories": job_categories, "skills_required": skills_required,
        "skills_preferred": skills_preferred, "job_reason": reason,
        "data_relevance": float(bool(matches.get("data"))),
        "manufacturing_relevance": float(bool(matches.get("manufacturing"))),
        "automation_relevance": float(bool(matches.get("automation"))),
    }
