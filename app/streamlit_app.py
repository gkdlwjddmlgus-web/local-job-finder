import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline import run_csv, run_source  # noqa: E402
from src.storage.sqlite import connect, fetch_jobs, update_status  # noqa: E402


DB_PATH = ROOT / "data" / "local_job_finder.db"
PROFILE_DIR = ROOT / "config" / "profiles"
STATUS_LABELS = {"미검토": "UNREVIEWED", "검토중": "REVIEWING", "지원예정": "APPLY", "지원완료": "APPLIED", "제외": "SKIP"}

st.set_page_config(page_title="Local Job Finder", page_icon="🔎", layout="wide")
st.title("부산·울산·경남·대구 신입 데이터 직무")

profile_names = [path.stem for path in sorted(PROFILE_DIR.glob("*.yml"))]
selected_profile = st.selectbox("Profile", profile_names, index=profile_names.index("default") if "default" in profile_names else 0)
profile_path = PROFILE_DIR / f"{selected_profile}.yml"

left, right = st.columns([1, 3])
if left.button("공고 새로고침", type="primary", width="stretch"):
    _, stats = run_source("daegu_seogu", DB_PATH, profile_path, max_rows=50)
    st.success(f"수집 완료: {stats['loaded']}건, 지원 가능 {stats['eligible']}건")
upload = right.file_uploader("수동 CSV 추가", type="csv")
if upload and right.button("업로드 CSV 가져오기"):
    temp_path = ROOT / "data" / "manual" / "uploaded_jobs.csv"
    temp_path.write_bytes(upload.getvalue())
    _, stats = run_csv(temp_path, DB_PATH, profile_path)
    st.success(f"수동 입력 {stats['deduplicated']}건 처리 완료")

connection = connect(DB_PATH)
jobs = fetch_jobs(connection)
connection.close()
if not jobs:
    st.info("공고 새로고침을 눌러 샘플 파이프라인을 실행하세요.")
    st.stop()

frame = pd.DataFrame(jobs)
kpis = st.columns(6)
kpis[0].metric("전체 수집", len(frame))
kpis[1].metric("지원 가능", int(frame["eligible"].sum()))
kpis[2].metric("경력 제외", int(((frame["career_status"] == "EXPERIENCED") & (frame["eligible"] == 0)).sum()))
kpis[3].metric("어학 필수 제외", int((frame["language_status"] == "REQUIRED").sum()))
kpis[4].metric("수동검토 필요", int(frame["manual_review"].sum()))
kpis[5].metric("HIGH 추천", int((frame["recommendation_level"] == "HIGH").sum()))

with st.expander("필터", expanded=True):
    cols = st.columns(5)
    regions = cols[0].multiselect("지역", sorted(frame["region"].unique()))
    sizes = cols[1].multiselect("회사규모", sorted(frame["company_size"].unique()))
    languages = cols[2].multiselect("어학상태", sorted(frame["language_status"].unique()))
    levels = cols[3].multiselect("추천등급", ["HIGH", "GOOD", "REVIEW", "LOW"])
    minimum = cols[4].slider("최소 점수", 0, 100, 0)
    keyword = st.text_input("직무 키워드")
    include_expired = st.checkbox("마감 공고 포함", value=False)

visible = frame["eligible"] == 1
if include_expired:
    visible = visible | (frame["posting_status"] == "EXPIRED")
filtered = frame[visible].copy()
if regions:
    filtered = filtered[filtered["region"].isin(regions)]
if sizes:
    filtered = filtered[filtered["company_size"].isin(sizes)]
if languages:
    filtered = filtered[filtered["language_status"].isin(languages)]
if levels:
    filtered = filtered[filtered["recommendation_level"].isin(levels)]
filtered = filtered[filtered["apply_score"] >= minimum]
if keyword:
    filtered = filtered[filtered[["title", "description", "requirement_text"]].fillna("").agg(" ".join, axis=1).str.contains(keyword, case=False, regex=False)]
filtered = filtered.sort_values("apply_score", ascending=False)

display_columns = [
    "company", "title", "region", "company_size", "posting_status", "career_status",
    "language_status", "driving_license_status", "apply_score", "recommendation_level", "deadline",
]
st.dataframe(filtered[display_columns], hide_index=True, alt="지원 가능한 채용공고 추천 목록")

for row in filtered.to_dict(orient="records"):
    with st.expander(f"{row['apply_score']}점 · {row['company']} · {row['title']}"):
        st.write(f"경력 판정: {row['career_reason']}")
        st.write(f"어학 판정: {row['language_reason']}")
        st.write(f"공고 상태: {row['posting_status']} ({row['source_freshness']})")
        st.write(f"운전면허 판정: {row['driving_license_status']} · {row['driving_reason']}")
        st.write("점수 구성:", json.loads(row["score_breakdown"] or "{}"))
        st.write("일치 키워드:", json.loads(row["matching_keywords"] or "{}"))
        if row["url"]:
            st.link_button("원문 공고", row["url"])
        status_col, memo_col, save_col = st.columns([1, 3, 1])
        reverse = {value: key for key, value in STATUS_LABELS.items()}
        current = reverse.get(row["application_status"], "미검토")
        status = status_col.selectbox("지원 상태", STATUS_LABELS, index=list(STATUS_LABELS).index(current), key=f"status-{row['job_id']}")
        memo = memo_col.text_input("메모", row["memo"], key=f"memo-{row['job_id']}")
        if save_col.button("저장", key=f"save-{row['job_id']}"):
            connection = connect(DB_PATH)
            update_status(connection, row["job_id"], STATUS_LABELS[status], memo)
            connection.close()
            st.toast("저장했습니다.")
