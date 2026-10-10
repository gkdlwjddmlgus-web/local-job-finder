import hashlib
import re
from datetime import datetime, timezone


FIELDS = (
    "source", "source_job_id", "company", "title", "region", "company_size",
    "career_text", "education", "employment_type", "posted_at", "deadline",
    "requirement_text", "preference_text", "description", "url", "source_freshness",
)


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_region(value: object) -> str:
    text = clean(value).lower()
    if "부산" in text:
        return "BUSAN"
    if any(keyword in text for keyword in ("경남", "경상남", "김해", "양산", "창원", "거제", "진주")):
        return "GYEONGNAM"
    if "울산" in text:
        return "ULSAN"
    if "대구" in text:
        return "DAEGU"
    return "OTHER"


def normalize_subregion(value: object) -> str:
    text = clean(value).lower()
    for keyword, code in (("김해", "GIMHAE"), ("양산", "YANGSAN"), ("창원", "CHANGWON"),
                          ("거제", "GEOJE"), ("진주", "JINJU")):
        if keyword in text:
            return code
    if "경남" in text or "경상남" in text:
        return "OTHER_GYEONGNAM"
    return ""


def normalize_company_size(value: object) -> str:
    text = clean(value).upper()
    if text in {"SME", "MID", "LARGE", "STARTUP", "UNKNOWN"}:
        return text
    if "중소" in text:
        return "SME"
    if "스타트업" in text or "벤처" in text:
        return "STARTUP"
    if "중견" in text:
        return "MID"
    if "대기업" in text:
        return "LARGE"
    return "UNKNOWN"


def _iso_date(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:10], fmt).date().isoformat()
        except ValueError:
            pass
    return text


def normalize_job(raw: dict) -> dict:
    job = {field: clean(raw.get(field, "")) for field in FIELDS}
    job["region_raw"] = job["region"]
    job["subregion"] = normalize_subregion(job["region"])
    job["region"] = normalize_region(job["region"])
    job["company_size"] = normalize_company_size(job["company_size"])
    job["posted_at"] = _iso_date(job["posted_at"])
    job["deadline"] = _iso_date(job["deadline"])
    identity = "|".join((job["source"], job["source_job_id"], job["url"], job["company"], job["title"]))
    job["job_id"] = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
    job["collected_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return job
