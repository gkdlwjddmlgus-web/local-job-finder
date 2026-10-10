from src.preprocess.normalize import normalize_company_size


def classify_company(value: object) -> str:
    return normalize_company_size(value)

