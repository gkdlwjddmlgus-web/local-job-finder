from pathlib import Path

import yaml

from src.collect.public_data import BusanPublicJobsSource, DaeguSeoGuSource, GyeongnamJobsSource


def enabled_sources(config_path: str | Path) -> list[str]:
    config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    return [name for name, item in config.get("sources", {}).items() if item.get("enabled")]


def create_source(name: str, raw_dir: str | Path, max_rows: int = 50):
    sources = {
        "busan_jobs": BusanPublicJobsSource,
        "daegu_seogu": DaeguSeoGuSource,
        "gyeongnam_jobs": GyeongnamJobsSource,
    }
    if name not in sources:
        raise ValueError(f"Unknown source: {name}")
    return sources[name](raw_dir=raw_dir, max_rows=max_rows)
