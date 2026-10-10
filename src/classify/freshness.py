from datetime import date, datetime


SOURCE_FRESHNESS = {
    "busan_jobs": "LIVE",
    "daegu_seogu": "SNAPSHOT",
    "gyeongnam_jobs": "LIVE",
}


def classify_posting_status(deadline: object, today: date | None = None) -> dict:
    text = str(deadline or "").strip()
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return {"posting_status": "UNKNOWN"}
    current = today or date.today()
    return {"posting_status": "EXPIRED" if parsed < current else "ACTIVE"}


def classify_source_freshness(source: object, declared: object = None) -> dict:
    value = str(declared or "").strip().upper()
    if value in {"LIVE", "SNAPSHOT", "HISTORICAL"}:
        return {"source_freshness": value}
    return {"source_freshness": SOURCE_FRESHNESS.get(str(source or ""), "LIVE")}
