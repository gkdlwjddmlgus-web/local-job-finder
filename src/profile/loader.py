from pathlib import Path

import yaml


REQUIRED_SECTIONS = (
    "profile", "career", "language", "driving", "regions", "target_job_categories",
    "skills", "company_preferences", "scoring",
)


def load_profile(path: str | Path) -> dict:
    profile_path = Path(path)
    if not profile_path.exists():
        raise ValueError(f"Profile file not found: {profile_path}")
    data = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Profile must be a YAML mapping: {profile_path}")
    missing = [section for section in REQUIRED_SECTIONS if section not in data]
    if missing:
        raise ValueError(f"Profile missing required sections: {', '.join(missing)}")
    if not data["profile"].get("id"):
        raise ValueError("Profile field 'profile.id' is required")
    if not isinstance(data["career"].get("accepted_status"), list):
        raise ValueError("Profile field 'career.accepted_status' must be a list")
    for section in ("regions", "target_job_categories", "skills", "company_preferences"):
        if not isinstance(data[section], dict):
            raise ValueError(f"Profile section '{section}' must be a mapping")
    return data
