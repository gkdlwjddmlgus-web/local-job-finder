from datetime import date, timedelta

import pytest

from src.classify.freshness import classify_posting_status
from src.pipeline import ROOT
from src.policy.eligibility import evaluate_eligibility
from src.profile.loader import load_profile


PROFILE = load_profile(ROOT / "config" / "profiles" / "default.yml")


def facts(posting_status: str) -> dict:
    return {
        "posting_status": posting_status,
        "career_status": "ENTRY",
        "required_experience_years": 0,
        "language_status": "NONE",
        "language_reason": "명시적 어학 조건 없음",
        "driving_license_status": "NONE",
        "driving_license_type": "NONE",
    }


@pytest.mark.parametrize("offset,expected", [(-1, "EXPIRED"), (0, "ACTIVE"), (1, "ACTIVE")])
def test_posting_status_uses_deadline(offset, expected):
    today = date(2026, 10, 10)
    deadline = (today + timedelta(days=offset)).isoformat()
    assert classify_posting_status(deadline, today)["posting_status"] == expected


@pytest.mark.parametrize("deadline", [None, "", "채용시까지", "2026-13-40"])
def test_missing_or_invalid_deadline_is_unknown(deadline):
    assert classify_posting_status(deadline)["posting_status"] == "UNKNOWN"


def test_expired_is_excluded_without_deleting_fact():
    result = evaluate_eligibility(facts("EXPIRED"), PROFILE)
    assert result["eligible"] is False
    assert "채용 마감일 경과" in result["exclude_reason"]


def test_unknown_requires_manual_review_without_exclusion():
    result = evaluate_eligibility(facts("UNKNOWN"), PROFILE)
    assert result["eligible"] is True
    assert result["manual_review"] is True
