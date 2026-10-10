import pytest

from src.collect.public_data import BusanPublicJobsSource, DaeguSeoGuSource, GyeongnamJobsSource
from src.pipeline import process


CSV_BYTES = ("""순번,업체명,업종,채용공고명,회사주소,급여형태,임금,학력,경력,마감일,채용정보 상세보기 URL
1,대구데이터,정보서비스업,Python 데이터 분석,대구광역시 서구,월급,300만원,대졸,신입,채용시까지 2026-12-31,https://example.com/1
2,대구데이터,정보서비스업,Python 데이터 분석,대구광역시 서구,월급,300만원,대졸,신입,2026-12-31,https://example.com/1
3,필드누락기업,,사무원,대구광역시 서구,,,,채용시까지,https://example.com/3
""").encode("utf-8-sig")


def test_daegu_response_parsing_and_schema():
    rows = DaeguSeoGuSource.parse_csv(CSV_BYTES)
    jobs = DaeguSeoGuSource.normalize_raw_response(rows)
    assert jobs[0]["company"] == "대구데이터"
    assert jobs[0]["title"] == "Python 데이터 분석"
    assert jobs[0]["career_text"] == "신입"
    assert jobs[0]["deadline"] == "2026-12-31"
    assert jobs[0]["url"] == "https://example.com/1"
    assert jobs[0]["source_freshness"] == "SNAPSHOT"
    assert jobs[2]["education"] == ""


def test_daegu_jobs_normalize_region_and_deduplicate():
    jobs = DaeguSeoGuSource.normalize_raw_response(DaeguSeoGuSource.parse_csv(CSV_BYTES))
    processed, stats = process(jobs)
    assert stats["deduplicated"] == 2
    assert all(job["region"] == "DAEGU" for job in processed)


def test_gyeongnam_waits_for_key(monkeypatch, tmp_path):
    monkeypatch.delenv("GYEONGNAM_JOB_API_KEY", raising=False)
    monkeypatch.delenv("DATA_GO_KR_SERVICE_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GYEONGNAM_JOB_API_KEY"):
        GyeongnamJobsSource(tmp_path).collect()


def test_busan_response_maps_official_fields():
    rows = [{
        "recruitAgencyName": "부산기관", "title": "데이터 담당자", "workregiontxt": "부산광역시",
        "reqDate_s": "2026-10-01", "reqDate_e": "2026-10-31", "regDate": "2026-10-01",
        "workDate_nm": "기간제", "bunya": "전산", "content": "<p>Python 업무</p>",
    }]
    job = BusanPublicJobsSource.normalize_raw_response(rows)[0]
    assert job["company"] == "부산기관"
    assert job["deadline"] == "2026-10-31"
    assert job["description"] == "Python 업무"
    assert job["source_freshness"] == "LIVE"


def test_gyeongnam_contents_extract_explicit_deadline_and_region():
    rows = [{
        "entid": "1", "author": "작성자", "title": "채용",
        "regDate": "2026-10-01", "contents": "근무지역: 경상남도 창원시 | 접수 마감일: 2026.10.31까지",
    }]
    job = GyeongnamJobsSource.normalize_raw_response(rows)[0]
    assert job["company"] is None
    assert job["region"].startswith("경상남도 창원시")
    assert job["deadline"] == "2026-10-31"
