from __future__ import annotations

from pathlib import Path

import pandas as pd

from data_acquisition_common import DOCS_DIR, DATA_WORK, now_utc


STATUS_VALUES = {
    "parsed_ok",
    "parsed_with_warnings",
    "file_missing",
    "unsupported_format",
    "missing_required_variable",
    "coordinate_conversion_failed",
    "quality_rejected",
    "empty_after_filtering",
}


def repo_relative(path_text: str) -> str:
    if not path_text:
        return ""
    path = Path(path_text)
    try:
        return str(path.relative_to(Path(__file__).resolve().parents[1]))
    except ValueError:
        return path.name if path.name else ""


def map_parse_status(row: pd.Series) -> tuple[str, str, str, str]:
    status = str(row.get("parse_status", "")).strip()
    file_name = str(row.get("file_name", "")).strip()
    data_group = str(row.get("data_group", "")).strip()
    suffix = Path(file_name).suffix.lower()

    if status == "missing" or not file_name:
        return "file_missing", "not_attempted", "no file available", "manual_download_required"
    if data_group == "superdarn" and suffix in {".png", ".jpg", ".jpeg"}:
        return "parsed_with_warnings", "not_attempted", "quicklook_only", "quantitative_superdarn_file_not_available"
    if suffix and suffix not in {".csv", ".nc", ".cdf", ".txt", ".dat"}:
        return "unsupported_format", "not_attempted", f"unsupported suffix {suffix}", "unsupported_format"
    return "parsed_with_warnings", "not_attempted", "full normalizer pending", "full_normalizer_pending"


def build_status_frame(local_manifest: pd.DataFrame) -> pd.DataFrame:
    rows = []
    run_time = now_utc()
    for row in local_manifest.iterrows():
        item = row[1]
        parse_status, coord_status, quality_summary, failure_reason = map_parse_status(item)
        if parse_status not in STATUS_VALUES:
            parse_status = "parsed_with_warnings"
        source_file = str(item.get("file_name", "")).strip()
        rows.append(
            {
                "event_id": item.get("event_id", ""),
                "event_date": item.get("event_date", ""),
                "data_group": item.get("data_group", ""),
                "source_file": source_file,
                "parse_status": parse_status,
                "normalized_output_path": repo_relative(str(item.get("normalized_output_path", ""))),
                "n_records": 0,
                "n_valid_subauroral_records": 0,
                "missing_required_variables": "",
                "coordinate_conversion_status": coord_status,
                "quality_flag_summary": quality_summary,
                "failure_reason": failure_reason,
                "last_run_utc": run_time,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    local_path = DOCS_DIR / "data_manifest_local.csv"
    if not local_path.exists():
        raise FileNotFoundError(f"Missing local manifest: {local_path}")
    local_manifest = pd.read_csv(local_path)
    status = build_status_frame(local_manifest)
    out_path = DATA_WORK / "normalized" / "normalizer_status_all_events.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    status.to_csv(out_path, index=False)
    print(f"Saved {out_path}")
    print(f"Rows: {len(status)}")


if __name__ == "__main__":
    main()
