def evaluate_eligibility(job_facts: dict, profile: dict) -> dict:
    reasons = []
    policy_notes = []
    posting_status = job_facts.get("posting_status", "ACTIVE")
    if posting_status == "EXPIRED":
        reasons.append("채용 마감일 경과")
    elif posting_status == "ACTIVE":
        policy_notes.append("공고 마감일 유효")

    career = profile["career"]
    status = job_facts["career_status"]
    required_years = job_facts.get("required_experience_years")
    career_limit = max(
        int(career.get("current_experience_years", 0)),
        int(career.get("max_required_experience_years", 0)),
    )
    if status not in career["accepted_status"]:
        reasons.append(f"경력 상태 {status} 미허용")
    elif required_years is not None and required_years > career_limit and status != "ENTRY_AND_CAREER":
        reasons.append(f"요구 경력 {required_years}년 > 허용 {career_limit}년")
    else:
        policy_notes.append("경력 조건 허용")

    language = profile["language"]
    language_status = job_facts["language_status"]
    if language_status == "REQUIRED" and not language.get("allow_required_language", False):
        reasons.append(f"필수 어학 조건 미허용: {job_facts['language_reason']}")
    elif language_status == "PREFERRED" and not language.get("allow_preferred_language", True):
        reasons.append("우대 어학 조건 미허용")
    else:
        policy_notes.append("어학 조건 허용")

    driving = profile.get("driving", {})
    driving_status = job_facts.get("driving_license_status", "NONE")
    license_type = job_facts.get("driving_license_type", "NONE")
    has_license = bool(driving.get("has_driving_license", False))
    licenses = set(driving.get("licenses", []))
    if driving_status == "REQUIRED" and not has_license:
        if not driving.get("allow_required_without_license", False):
            reasons.append("운전면허 필수")
    elif driving_status == "REQUIRED" and license_type not in {"ANY", "UNKNOWN", "NONE"}:
        if license_type in licenses:
            policy_notes.append("요구 운전면허 등급 보유")
    elif driving_status == "PREFERRED" and not has_license:
        if not driving.get("allow_preferred_without_license", True):
            reasons.append("운전면허 우대 조건 미허용")

    manual_review = (
        posting_status == "UNKNOWN"
        or status == "REVIEW"
        or language_status == "REVIEW"
        or driving_status == "REVIEW"
        or (
            driving_status == "REQUIRED"
            and has_license
            and license_type not in {"ANY", "UNKNOWN", "NONE"}
            and license_type not in licenses
        )
    )
    if language_status == "REVIEW" and not language.get("allow_review_language", True):
        reasons.append("검토 필요 어학 조건 미허용")
    if driving_status == "REVIEW" and not driving.get("allow_review", True):
        reasons.append("검토 필요 운전 조건 미허용")
    return {
        "eligible": not reasons,
        "manual_review": manual_review,
        "exclude_reason": " | ".join(reasons),
        "policy_reason": " | ".join(reasons or policy_notes),
        "profile_id": profile["profile"]["id"],
    }
