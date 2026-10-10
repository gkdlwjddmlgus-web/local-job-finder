import re


YEAR_PATTERN = re.compile(r"(?:경력|실무\s*경력|관련\s*경력|최소)\s*(\d+)\s*년(?:\s*이상)?", re.I)
ENTRY_PATTERN = re.compile(r"신입(?:\s*(?:지원\s*)?가능)?|경력\s*무관|경력\s*관계\s*없", re.I)
ENTRY_TRACK_PATTERN = re.compile(r"신입\s*(?:지원\s*)?가능|신입\s*(?:별도|트랙)", re.I)
ENTRY_AND_PATTERN = re.compile(r"신입\s*[/·및,]\s*경력|신입\s*및\s*경력", re.I)


def classify_career(*texts: object) -> dict:
    text = " ".join(str(item or "") for item in texts)
    years = [int(value) for value in YEAR_PATTERN.findall(text)]
    minimum = max(years) if years else 0
    reason_match = YEAR_PATTERN.search(text)
    if minimum >= 1 and not ENTRY_TRACK_PATTERN.search(text):
        return {"career_status": "EXPERIENCED", "required_experience_years": minimum,
                "career_reason": reason_match.group(0)}
    if ENTRY_AND_PATTERN.search(text) or (minimum >= 1 and ENTRY_TRACK_PATTERN.search(text)):
        return {"career_status": "ENTRY_AND_CAREER", "required_experience_years": minimum,
                "career_reason": "신입 지원 가능 트랙 명시"}
    if ENTRY_PATTERN.search(text):
        status = "CAREER_IRRELEVANT" if re.search(r"경력\s*(?:무관|관계\s*없)", text) else "ENTRY"
        return {"career_status": status, "required_experience_years": 0,
                "career_reason": "신입 또는 경력무관 명시"}
    return {"career_status": "REVIEW", "required_experience_years": None,
            "career_reason": "신입 지원 가능 여부 불명확"}
