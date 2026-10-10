from pathlib import Path

from src.pipeline import ROOT, process, run_csv
from src.preprocess.deduplicate import deduplicate
from src.preprocess.normalize import normalize_job, normalize_region, normalize_subregion
from src.storage.sqlite import connect, fetch_jobs


def test_busan_normalization():
    assert normalize_region("부산광역시 해운대구") == "BUSAN"


def test_gyeongnam_subregion_normalization():
    assert normalize_region("경남 김해시") == "GYEONGNAM"
    assert normalize_subregion("경남 김해시") == "GIMHAE"


def test_deduplicate_cross_source():
    first = normalize_job({"company": "A 회사", "title": "데이터 분석", "region": "부산", "source": "a", "url": "x"})
    second = normalize_job({"company": "A회사", "title": "데이터분석", "region": "부산", "source": "b", "url": "y"})
    assert len(deduplicate([first, second])) == 1


def test_scoring_range():
    jobs, _ = process([{"company": "A", "title": "Python SQL 데이터 분석", "region": "부산", "career_text": "신입", "source": "test"}])
    assert 0 <= jobs[0]["apply_score"] <= 100


def test_end_to_end_sqlite(tmp_path: Path):
    db = tmp_path / "jobs.db"
    jobs, stats = run_csv(ROOT / "data" / "sample" / "sample_jobs.csv", db)
    connection = connect(db)
    stored = fetch_jobs(connection)
    connection.close()
    assert stats == {"collected": 5, "deduplicated": 4, "career_excluded": 1, "language_excluded": 1, "eligible": 2, "recommended": 2}
    assert len(stored) == len(jobs) == 4
    assert all(job["posting_status"] == "ACTIVE" for job in jobs)
    assert all(row["source_freshness"] == "LIVE" for row in stored)
    assert all("driving_license_status" in row for row in stored)
