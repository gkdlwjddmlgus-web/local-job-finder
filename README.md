# Local Job Finder

부산·울산·경남·대구 지역의 신입 및 경력무관 채용공고를 수집·정규화하고, 사용자 Profile을 기준으로 지원 가능 여부와 직무 적합도를 분석하는 개인용 취업지원 데이터 프로젝트다.

핵심 특징:

- 공식 API 및 허용된 공개데이터 사용
- 공고 수집 → 정규화 → Job Facts 추출
- User Profile과 Policy Engine 분리
- 경력·어학·운전면허·Freshness 조건 처리
- 직무 적합도 scoring, SQLite 저장, Streamlit 조회
- rule-based validation
- API Key는 환경변수로만 관리

개인 취업 준비와 데이터 분석·데이터 엔지니어링 학습을 위한 비상업적 포트폴리오다. API Key 및 실제 개인 데이터는 repository에 포함하지 않는다.

## 실행

Python 3.12와 Git이 필요하다.

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
python main.py refresh
python main.py refresh --profile default
streamlit run app/streamlit_app.py
```

수동 공고는 별도로 만든 `data/manual/manual_jobs.csv`에 저장하거나 다음 명령으로 가져온다. `data/manual/`과 실행 산출물은 Git에서 제외된다.

```bash
python main.py import-manual path/to/jobs.csv
python main.py export-csv
python main.py validate
pytest
```

`validate`는 `data/manual/validation_jobs.csv`의 선택적 `human_*` 라벨과 현재 Job Facts extractor 결과를 비교하고 `data/processed/validation_report.csv`에 mismatch를 저장한다.

`refresh`는 기본적으로 대구광역시 서구 공개 CSV에서 최대 50건을 수집한다. 저장소에 포함된 데이터는 완전히 synthetic한 실행 예제뿐이며 `python main.py refresh --input data/sample/sample_jobs.csv`로 실행한다. 부산 공공부문 채용 Open API와 경상남도 일자리 Open API는 `.env`에 `BUSAN_JOB_API_KEY`, `GYEONGNAM_JOB_API_KEY`를 설정한 뒤 아래처럼 실행한다.

```bash
python main.py refresh --source busan_jobs --limit 20
python main.py refresh --source gyeongnam_jobs --limit 10
```

자동 수집은 공식 API, 공개 파일, 명시적으로 허용된 데이터만 대상으로 한다. API가 실시간으로 제공되더라도 현재 지원 가능한 공고를 항상 보장하지 않으므로 deadline 기반 Freshness를 별도로 검증한다. 실제 API 키가 담긴 `.env`는 Git에 커밋하지 않는다.

공고의 객관적 사실 추출과 사용자별 지원 정책은 분리되어 있다. `config/profiles/*.yml`의 profile을 바꾸면 코드 수정 없이 지원 가능 여부와 추천 점수가 다시 계산된다.

## 샘플 실행 지표

- 수집 공고 수: 5
- 중복 제거 후: 4
- 경력조건 제외: 1
- 어학필수 제외: 1
- 최종 지원가능: 2
- HIGH/GOOD 추천: 2
