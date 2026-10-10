from pathlib import Path

import pandas as pd


def load_csv(path: str | Path) -> list[dict]:
    frame = pd.read_csv(path, keep_default_na=False)
    return frame.to_dict(orient="records")

