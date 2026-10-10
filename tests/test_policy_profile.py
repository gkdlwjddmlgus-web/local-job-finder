from pathlib import Path

import pytest

from src.classify.career import classify_career
from src.classify.driving import classify_driving_license
from src.classify.language import classify_language
from src.pipeline import ROOT, process
from src.policy.eligibility import evaluate_eligibility
from src.profile.loader import load_profile


DEFAULT = load_profile(ROOT / "config" / "profiles" / "default.yml")
EXPERIENCED = load_profile(Path(__file__).parent / "fixtures" / "profile_experienced.yml")


def facts(text: str) -> dict:
    result = classify_career(text)
    result.update(classify_language(text))
    result.update(classify_driving_license(text))
    return result


def test_same_experienced_job_changes_by_profile():
    job = facts("관련 경력 2년 이상")
    assert job["required_experience_years"] == 2
    assert evaluate_eligibility(job, DEFAULT)["eligible"] is False
    assert evaluate_eligibility(job, EXPERIENCED)["eligible"] is True


def test_required_language_changes_by_profile():
    job = facts("신입, TOEIC 700점 이상 필수")
    assert job["language_status"] == "REQUIRED"
    assert evaluate_eligibility(job, DEFAULT)["eligible"] is False
    assert evaluate_eligibility(job, EXPERIENCED)["eligible"] is True


def test_preferred_language_is_allowed_by_default():
    assert evaluate_eligibility(facts("신입, 영어 가능자 우대"), DEFAULT)["eligible"] is True


def test_required_driving_license_is_excluded_by_default():
    result = evaluate_eligibility(facts("신입, 운전면허 필수"), DEFAULT)
    assert result["eligible"] is False
    assert "운전면허 필수" in result["exclude_reason"]


def test_preferred_driving_license_remains_eligible_by_default():
    assert evaluate_eligibility(facts("신입, 운전 가능자 우대"), DEFAULT)["eligible"] is True


def test_general_required_driving_license_passes_for_licensed_profile():
    assert evaluate_eligibility(facts("신입, 운전면허 필수"), EXPERIENCED)["eligible"] is True


def test_specific_license_mismatch_requires_review():
    result = evaluate_eligibility(facts("신입, 1종 보통 운전면허 필수"), EXPERIENCED)
    assert result["eligible"] is True
    assert result["manual_review"] is True


def test_profile_changes_score_without_code_change():
    raw = [{"company": "A", "company_size": "중소기업", "title": "Python SQL 데이터 분석", "region": "부산", "career_text": "신입", "source": "test"}]
    default_jobs, _ = process(raw, DEFAULT)
    experienced_jobs, _ = process(raw, EXPERIENCED)
    assert default_jobs[0]["apply_score"] != experienced_jobs[0]["apply_score"]


def test_profile_validation_is_clear(tmp_path: Path):
    path = tmp_path / "invalid.yml"
    path.write_text("profile:\n  id: invalid\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required sections"):
        load_profile(path)
