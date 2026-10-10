from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_loads():
    app = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
    at = AppTest.from_file(str(app), default_timeout=10).run()
    assert not at.exception
    assert at.title[0].value == "부산·울산·경남·대구 신입 데이터 직무"
    assert at.selectbox[0].value == "default"
