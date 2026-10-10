import argparse
import csv
from pathlib import Path

from src.pipeline import ROOT, run_csv, run_source
from src.storage.sqlite import connect, fetch_jobs
from src.validation import format_summary, validate_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Local Job Finder")
    sub = parser.add_subparsers(dest="command", required=True)
    refresh = sub.add_parser("refresh")
    refresh.add_argument("--input")
    refresh.add_argument("--source", default="daegu_seogu")
    refresh.add_argument("--limit", type=int, default=50)
    refresh.add_argument("--profile", default="default")
    manual = sub.add_parser("import-manual")
    manual.add_argument("path", nargs="?", default=str(ROOT / "data" / "manual" / "manual_jobs.csv"))
    manual.add_argument("--profile", default="default")
    export = sub.add_parser("export-csv")
    export.add_argument("--output", default=str(ROOT / "exports" / "jobs.csv"))
    validate = sub.add_parser("validate")
    validate.add_argument("--input", default=str(ROOT / "data" / "manual" / "validation_jobs.csv"))
    validate.add_argument("--output", default=str(ROOT / "data" / "processed" / "validation_report.csv"))
    args = parser.parse_args()
    if args.command in {"refresh", "import-manual"}:
        profile_path = ROOT / "config" / "profiles" / f"{args.profile}.yml"
        if args.command == "refresh" and not args.input:
            _, stats = run_source(args.source, profile_path=profile_path, max_rows=args.limit)
        else:
            path = args.input if args.command == "refresh" else args.path
            _, stats = run_csv(path, profile_path=profile_path)
        print(" ".join(f"{key}={value}" for key, value in stats.items()))
        return
    if args.command == "validate":
        print(format_summary(validate_csv(args.input, args.output)))
        return
    connection = connect(ROOT / "data" / "local_job_finder.db")
    rows = fetch_jobs(connection)
    connection.close()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        with output.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    print(output)


if __name__ == "__main__":
    main()
