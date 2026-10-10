import pytest

from src.classify.career import classify_career
from src.classify.driving import classify_driving_license
from src.classify.language import classify_language


@pytest.mark.parametrize("text,status,years", [
    ("경력무관", "CAREER_IRRELEVANT", 0),
    ("신입", "ENTRY", 0),
    ("신입/경력", "ENTRY_AND_CAREER", 0),
    ("경력 1년 이상", "EXPERIENCED", 1),
    ("관련 경력 3년 이상", "EXPERIENCED", 3),
])
def test_career_extracts_facts(text, status, years):
    result = classify_career(text)
    assert result["career_status"] == status
    assert result["required_experience_years"] == years
    assert "eligible" not in result


@pytest.mark.parametrize("text,status,language_type,level", [
    ("TOEIC 700점 이상 필수", "REQUIRED", "TOEIC", "700"),
    ("영어 가능자 우대", "PREFERRED", "ENGLISH", None),
    ("해외출장 가능자", "NONE", "NONE", None),
    ("어학 언급 없음", "NONE", "NONE", None),
    ("영어 활용 가능", "REVIEW", "ENGLISH", None),
])
def test_language_extracts_facts(text, status, language_type, level):
    result = classify_language(text)
    assert result["language_status"] == status
    assert result["language_type"] == language_type
    assert result["language_level"] == level
    assert "eligible" not in result


@pytest.mark.parametrize("text,status,license_type", [
    ("운전면허 필수", "REQUIRED", "ANY"),
    ("1종 보통 운전면허 필수", "REQUIRED", "CLASS_1_NORMAL"),
    ("2종 보통 이상 필수", "REQUIRED", "CLASS_2_NORMAL"),
    ("운전 가능자 우대", "PREFERRED", "ANY"),
    ("출장 가능자", "REVIEW", "UNKNOWN"),
    ("운전 관련 언급 없음", "NONE", "NONE"),
])
def test_driving_license_extracts_facts(text, status, license_type):
    result = classify_driving_license(text)
    assert result["driving_license_status"] == status
    assert result["driving_license_type"] == license_type
    assert "eligible" not in result
