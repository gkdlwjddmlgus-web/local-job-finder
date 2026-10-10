import csv
import html
import io
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

from src.collect.base import JobSource


load_dotenv()


def _request_json(session, endpoint: str, params: dict) -> dict:
    try:
        response = session.get(endpoint, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        raise RuntimeError(f"공식 API 요청 실패: {type(error).__name__}") from None


def _response_items(payload: dict, root_key: str | None = None) -> list[dict]:
    root = payload.get(root_key, {}) if root_key else payload.get("response", payload)
    header = root.get("header", {})
    if str(header.get("resultCode", "00")) != "00":
        raise RuntimeError(f"공식 API 오류: {header.get('resultCode')} {header.get('resultMsg', '')}".strip())
    body = root.get("body", {})
    items = body.get("items", {})
    rows = items.get("item", items) if isinstance(items, dict) else items
    if isinstance(rows, dict):
        return [rows]
    return rows or []


def _extract_deadline(text: str) -> str:
    patterns = (
        r"(?:접수\s*)?(?:마감일?|기간)[^0-9]{0,20}(\d{4})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})",
        r"(\d{4})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})[^\n]{0,12}(?:까지|마감)",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            year, month, day = (int(value) for value in match.groups())
            try:
                return datetime(year, month, day).date().isoformat()
            except ValueError:
                return ""
    return ""


def _extract_region(text: str) -> str:
    match = re.search(
        r"(?:근무\s*(?:지역|지|장소)|주소)[^가-힣]{0,10}((?:경상남도|경남|부산광역시|부산|울산광역시|울산|대구광역시|대구)[^\n|]{0,40})",
        text,
    )
    return match.group(1).strip() if match else ""


class BusanPublicJobsSource(JobSource):
    name = "busan_jobs"
    endpoint = "https://apis.data.go.kr/6260000/BusanJobOpnngInfoService/getJobOpnngInfo"

    def __init__(self, raw_dir: str | Path, max_rows: int = 20, session=None):
        self.raw_dir = Path(raw_dir)
        self.max_rows = max_rows
        self.session = session or requests

    @staticmethod
    def normalize_raw_response(rows: list[dict]) -> list[dict]:
        jobs = []
        for row in rows:
            content = GyeongnamJobsSource._plain_text(row.get("content"))
            source_id = "|".join(str(row.get(key) or "") for key in (
                "recruitAgencyName", "title", "reqDate_s", "reqDate_e", "regDate"
            ))
            jobs.append({
                "source": "busan_jobs", "source_job_id": source_id,
                "company": row.get("recruitAgencyName"), "title": row.get("title"),
                "region": row.get("workregiontxt"), "company_size": None,
                "career_text": None, "education": None,
                "employment_type": row.get("workDate_nm") or row.get("workDate_type"),
                "posted_at": row.get("reqDate_s") or row.get("regDate"),
                "deadline": row.get("reqDate_e"), "requirement_text": row.get("bunya"),
                "preference_text": None, "description": content, "url": None,
                "source_freshness": "LIVE",
            })
        return jobs

    def save_raw(self, payload: dict) -> Path:
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = self.raw_dir / f"{self.name}_{stamp}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def collect(self) -> list[dict]:
        service_key = os.getenv("BUSAN_JOB_API_KEY")
        if not service_key:
            raise RuntimeError("BUSAN_JOB_API_KEY가 없습니다.")
        payload = _request_json(self.session, self.endpoint, {
            "ServiceKey": service_key, "pageNo": 1,
            "numOfRows": self.max_rows, "resultType": "json",
        })
        rows = _response_items(payload)
        self.save_raw(payload)
        return self.normalize_raw_response(rows)


class DaeguSeoGuSource(JobSource):
    name = "daegu_seogu"
    download_url = (
        "https://www.data.go.kr/cmm/cmm/fileDownload.do?"
        "atchFileId=FILE_000000007619186&fileDetailSn=1&insertDataPrcus=N"
    )

    def __init__(self, raw_dir: str | Path, max_rows: int = 50, session=None):
        self.raw_dir = Path(raw_dir)
        self.max_rows = max_rows
        self.session = session or requests

    @staticmethod
    def parse_csv(content: bytes) -> list[dict]:
        text = content.decode("utf-8-sig")
        return list(csv.DictReader(io.StringIO(text)))

    @staticmethod
    def normalize_raw_response(rows: list[dict]) -> list[dict]:
        jobs = []
        for row in rows:
            address = row.get("회사주소") or ""
            details = [
                f"업종: {row['업종']}" if row.get("업종") else "",
                f"급여: {row.get('급여형태', '')} {row.get('임금', '')}".strip() if row.get("급여형태") or row.get("임금") else "",
                f"회사주소: {address}" if address else "",
            ]
            deadline_text = row.get("마감일") or ""
            deadline_match = re.search(r"\d{4}-\d{2}-\d{2}", deadline_text)
            jobs.append({
                "source": "daegu_seogu", "source_job_id": row.get("순번"),
                "company": row.get("업체명"), "title": row.get("채용공고명"),
                "region": address, "company_size": None, "career_text": row.get("경력"),
                "education": row.get("학력"), "employment_type": None, "posted_at": None,
                "deadline": deadline_match.group(0) if deadline_match else deadline_text, "requirement_text": None,
                "preference_text": None, "description": " | ".join(item for item in details if item),
                "url": row.get("채용정보 상세보기 URL"),
                "source_freshness": "SNAPSHOT",
            })
        return jobs

    def save_raw(self, rows: list[dict]) -> Path:
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = self.raw_dir / f"{self.name}_{stamp}.json"
        payload = {"source": self.name, "collected_at": datetime.now(timezone.utc).isoformat(), "rows": rows}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def collect(self) -> list[dict]:
        response = self.session.get(self.download_url, timeout=30)
        response.raise_for_status()
        rows = self.parse_csv(response.content)[: self.max_rows]
        self.save_raw(rows)
        return self.normalize_raw_response(rows)


class GyeongnamJobsSource(JobSource):
    name = "gyeongnam_jobs"
    endpoint = "https://apis.data.go.kr/6480000/gyeongnamwork/gyeongnamworkList"

    def __init__(self, raw_dir: str | Path, max_rows: int = 50, session=None):
        self.raw_dir = Path(raw_dir)
        self.max_rows = max_rows
        self.session = session or requests

    def save_raw(self, payload: dict) -> Path:
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = self.raw_dir / f"{self.name}_{stamp}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    @staticmethod
    def _plain_text(value: object) -> str:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(str(value or "")))).strip()

    @classmethod
    def normalize_raw_response(cls, rows: list[dict]) -> list[dict]:
        jobs = []
        for row in rows:
            content = cls._plain_text(row.get("contents"))
            jobs.append({
                "source": "gyeongnam_jobs", "source_job_id": row.get("entid"),
                "company": None, "author": row.get("author"), "title": row.get("title"),
                "region": _extract_region(content), "company_size": None,
                "career_text": None, "education": None, "employment_type": None,
                "posted_at": row.get("regDate"), "deadline": _extract_deadline(content),
                "requirement_text": None, "preference_text": None,
                "description": content, "url": None, "source_freshness": "LIVE",
            })
        return jobs

    def collect(self) -> list[dict]:
        service_key = os.getenv("GYEONGNAM_JOB_API_KEY") or os.getenv("DATA_GO_KR_SERVICE_KEY")
        if not service_key:
            raise RuntimeError("GYEONGNAM_JOB_API_KEY가 없습니다.")
        payload = _request_json(self.session, self.endpoint, {
            "ServiceKey": service_key, "pageNo": 1, "numOfRows": self.max_rows, "resultType": "json",
        })
        self.save_raw(payload)
        return self.normalize_raw_response(_response_items(payload, "gyeongnamworkList"))
