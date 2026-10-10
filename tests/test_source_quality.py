from src.source_quality import source_quality, target_related_count, write_live_validation_candidates


def job(job_id: str, status: str = "ACTIVE", title: str = "일반 사무") -> dict:
    return {
        "job_id": job_id, "company": "기관", "title": title, "region": "BUSAN",
        "region_raw": "부산", "career_text": "", "deadline": "2026-12-31",
        "posting_status": status, "description": "업무 설명", "url": "",
        "source": "busan_jobs", "career_status": "REVIEW", "language_status": "NONE",
        "driving_license_status": "NONE", "requirement_text": "", "preference_text": "",
    }


def test_source_quality_uses_raw_region_presence():
    jobs = [job("1"), {**job("2"), "company": "", "region_raw": "", "deadline": ""}]
    result = source_quality(jobs)
    assert result["company"] == 50.0
    assert result["region"] == 50.0
    assert result["deadline"] == 50.0


def test_target_related_counts_active_only():
    jobs = [job("1", title="Python 데이터"), job("2", "EXPIRED", "SQL 개발")]
    assert target_related_count(jobs) == 1


def test_live_candidates_exclude_expired_and_unknown(tmp_path):
    jobs = [job("1"), job("2", "EXPIRED"), job("3", "UNKNOWN")]
    selected = write_live_validation_candidates(jobs, tmp_path / "candidates.csv")
    assert [item["job_id"] for item in selected] == ["1"]
