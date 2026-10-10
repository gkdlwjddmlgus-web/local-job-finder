import csv

from src.validation import validate_csv, validate_rows


def test_validation_compares_labeled_facts_and_reports_mismatch():
    rows = [{
        "company": "A", "title": "데이터 분석", "region": "부산", "career_text": "경력 2년 이상",
        "requirement_text": "Python 데이터 분석", "preference_text": "", "description": "", "source": "test",
        "human_career_status": "ENTRY", "human_required_experience_years": "2",
        "human_language_status": "", "human_region": "BUSAN",
        "human_job_categories": "DATA_ANALYSIS", "human_skills": "PYTHON",
    }]
    mismatches, summary = validate_rows(rows)
    assert summary["validation_row_count"] == 1
    assert summary["career_status_accuracy"] == 0
    assert summary["required_experience_years_accuracy"] == 1
    assert summary["mismatch_count"] == 1
    assert mismatches[0]["field"] == "career_status"


def test_validation_writes_report_csv(tmp_path):
    input_path = tmp_path / "validation.csv"
    output_path = tmp_path / "report.csv"
    with input_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["company", "title", "region", "career_text", "human_region"])
        writer.writeheader()
        writer.writerow({"company": "A", "title": "분석", "region": "부산", "career_text": "신입", "human_region": "DAEGU"})
    summary = validate_csv(input_path, output_path)
    report = output_path.read_text(encoding="utf-8-sig")
    assert summary["mismatch_count"] == 1
    assert "company,title,field,human_value,system_value,overlap" in report
    assert "region,DAEGU,BUSAN" in report
