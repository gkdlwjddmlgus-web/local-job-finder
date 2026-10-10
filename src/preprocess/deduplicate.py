import re


def _key(value: object) -> str:
    return re.sub(r"[^0-9a-z가-힣]", "", str(value or "").lower())


def deduplicate(jobs: list[dict]) -> list[dict]:
    seen_urls: set[str] = set()
    seen_source_ids: set[tuple[str, str]] = set()
    seen_content: set[tuple[str, str, str, str]] = set()
    result = []
    for job in jobs:
        url = str(job.get("url", "")).strip()
        source_id = (str(job.get("source", "")), str(job.get("source_job_id", "")))
        content = (_key(job.get("company")), _key(job.get("title")), str(job.get("region", "")), str(job.get("subregion", "")))
        if url and url in seen_urls:
            continue
        if source_id[1] and source_id in seen_source_ids:
            continue
        if content in seen_content:
            continue
        result.append(job)
        if url:
            seen_urls.add(url)
        if source_id[1]:
            seen_source_ids.add(source_id)
        seen_content.add(content)
    return result
