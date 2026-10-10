import re


REQUIRED = [
    r"(?:[12]종\s*(?:보통)?\s*)?(?:자동차\s*)?운전면허[^\n|,.;]*필수",
    r"[12]종\s*(?:보통)?(?:\s*이상)?\s*필수",
    r"(?:실제\s*)?운전\s*가능자?[^\n|,.;]*필수",
    r"차량\s*운전[^\n|,.;]*필수",
]
PREFERRED = [
    r"운전\s*가능자?[^\n|,.;]*우대",
    r"운전면허\s*소지자?[^\n|,.;]*우대",
    r"\d종\s*보통\s*소지자?[^\n|,.;]*우대",
    r"자차\s*운전자?[^\n|,.;]*우대",
]
AMBIGUOUS = [
    r"자차\s*보유[^\n|,.;]*필수",
    r"운전\s*가능자",
    r"차량\s*운행\s*가능자",
    r"현장\s*방문\s*가능자",
    r"출장\s*가능자",
]


def _license_type(text: str) -> str:
    if re.search(r"1종\s*보통", text):
        return "CLASS_1_NORMAL"
    if re.search(r"2종\s*보통", text):
        return "CLASS_2_NORMAL"
    if re.search(r"1종", text):
        return "CLASS_1"
    if re.search(r"2종", text):
        return "CLASS_2"
    if re.search(r"운전면허|운전\s*가능|차량\s*운전", text):
        return "ANY"
    return "UNKNOWN"


def classify_driving_license(*texts: object) -> dict:
    text = " ".join(str(item or "") for item in texts)
    for status, patterns in (("REQUIRED", REQUIRED), ("PREFERRED", PREFERRED), ("REVIEW", AMBIGUOUS)):
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                matched = match.group(0)
                return {
                    "driving_license_status": status,
                    "driving_license_type": _license_type(matched),
                    "driving_reason": matched,
                }
    return {
        "driving_license_status": "NONE",
        "driving_license_type": "NONE",
        "driving_reason": "명시적 운전면허 조건 없음",
    }
