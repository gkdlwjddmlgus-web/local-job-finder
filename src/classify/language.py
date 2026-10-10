import re


REQUIRED = [
    r"TOEIC\s*(\d+)\s*점?\s*이상\s*필수", r"토익\s*(\d+)\s*점?\s*이상\s*필수",
    r"OPIc\s*([A-Z0-9+]+)\s*이상\s*필수", r"공인\s*어학\s*성적.*필수",
    r"영어\s*회화\s*필수", r"비즈니스\s*영어\s*필수", r"외국어\s*능력.*필수",
]
PREFERRED = [r"영어.*우대", r"외국어.*우대", r"TOEIC.*우대", r"토익.*우대", r"OPIc.*우대", r"어학\s*성적.*우대"]
AMBIGUOUS = [r"영어\s*활용\s*가능", r"글로벌\s*커뮤니케이션", r"해외\s*업무\s*대응\s*가능"]


def classify_language(*texts: object) -> dict:
    text = " ".join(str(item or "") for item in texts)
    for pattern in REQUIRED:
        match = re.search(pattern, text, re.I)
        if match:
            matched = match.group(0)
            language_type = "TOEIC" if re.search(r"TOEIC|토익", matched, re.I) else "OPIC" if re.search(r"OPIc", matched, re.I) else "ENGLISH" if "영어" in matched else "FOREIGN_LANGUAGE"
            level = match.group(1) if match.lastindex else None
            return {"language_status": "REQUIRED", "language_reason": match.group(0),
                    "language_type": language_type, "language_level": level}
    for pattern in PREFERRED:
        match = re.search(pattern, text, re.I)
        if match:
            return {"language_status": "PREFERRED", "language_reason": match.group(0),
                    "language_type": "TOEIC" if re.search(r"TOEIC|토익", match.group(0), re.I) else "OPIC" if re.search(r"OPIc", match.group(0), re.I) else "ENGLISH" if "영어" in match.group(0) else "FOREIGN_LANGUAGE", "language_level": None}
    for pattern in AMBIGUOUS:
        match = re.search(pattern, text, re.I)
        if match:
            return {"language_status": "REVIEW", "language_reason": match.group(0),
                    "language_type": "ENGLISH" if "영어" in match.group(0) else "UNKNOWN", "language_level": None}
    return {"language_status": "NONE", "language_reason": "명시적 어학 조건 없음",
            "language_type": "NONE", "language_level": None}
