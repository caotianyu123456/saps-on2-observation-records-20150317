from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import re
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs_index"
OUTPUT_DIR = ROOT / "data_samples" / "screening_outputs"
SUMMARY_DIR = ROOT / "summaries" / "screening_outputs"
DATA_RAW = ROOT / "data_raw"
DATA_WORK = ROOT / "data_work"


def configured_path(env_name: str, default_relative: str) -> Path:
    raw = os.environ.get(env_name)
    return Path(raw) if raw else ROOT / default_relative


DEFAULT_WORKSPACE = configured_path("SAPS_ON2_EXTERNAL_WORKSPACE", "data_external/saps_sar_arcs")
DEFAULT_DMSP_DIR = configured_path("SAPS_ON2_DMSP_DIR", "data_external/dmsp")
DEFAULT_SUPERDARN_DIRS = [
    ROOT / "event_overlay_figures" / "superdarn",
    DEFAULT_WORKSPACE / "chat_outputs_superdarn_guvi_20260618",
]
DEFAULT_SSUSI_DIRS = [ROOT / "event_overlay_figures" / "ssusi_data"]
DEFAULT_INDICES_DIRS = [DEFAULT_WORKSPACE / "chat_outputs_superdarn_guvi_20260618"]


@dataclass(frozen=True)
class EventSpec:
    event_id: str
    event_date: pd.Timestamp
    label: str
    tier: str
    storm_class: str
    reason: str


SEED_EVENTS = [
    EventSpec("available_20150316", pd.Timestamp("2015-03-16"), "Local smoke-test day 2015-03-16", "A_local_smoke", "2015_st_patrick_context", "local St. Patrick smoke-test group"),
    EventSpec("available_20150317", pd.Timestamp("2015-03-17"), "Local smoke-test day 2015-03-17", "A_local_smoke", "2015_st_patrick_main", "local St. Patrick smoke-test group"),
    EventSpec("available_20150318", pd.Timestamp("2015-03-18"), "Local smoke-test day 2015-03-18", "A_local_smoke", "2015_st_patrick_recovery", "local St. Patrick smoke-test group"),
    EventSpec("validation_20140219", pd.Timestamp("2014-02-19"), "Thesis-inspired validation case 2014-02-19", "B_thesis_validation", "unknown_until_indices", "Zhang-thesis SuperDARN SAPS validation case"),
    EventSpec("validation_20111025", pd.Timestamp("2011-10-25"), "Thesis-inspired validation case 2011-10-25", "B_thesis_validation", "unknown_until_indices", "Zhang-thesis SuperDARN SAPS validation case"),
    EventSpec("validation_20130630", pd.Timestamp("2013-06-30"), "Thesis-inspired validation case 2013-06-30", "B_thesis_validation", "unknown_until_indices", "Zhang-thesis SuperDARN SAPS validation case"),
]


DATA_GROUPS = [
    ("guvi_on2", "TIMED/GUVI L3 O/N2", "TIMED_GUVI", "main O/N2 source"),
    ("dmsp_ssies", "DMSP SSIES", "DMSP_F16_F17_F18_F19", "ion drift and SAPS crossing detection"),
    ("superdarn", "SuperDARN map/fit/grid or quick-look", "SuperDARN", "two-dimensional SAPS channel support"),
    ("ssusi", "DMSP SSUSI", "DMSP_SSUSI", "auroral boundary and optional O/N2-sensitive support"),
    ("indices", "OMNI/SYM-H/AE/Dst/Kp", "Geomagnetic_indices", "storm and substorm phase tagging"),
]

DOWNLOAD_GROUPS = {
    "guvi": ["guvi_on2"],
    "dmsp": ["dmsp_ssies"],
    "superdarn": ["superdarn"],
    "ssusi": ["ssusi"],
    "indices": ["indices"],
    "gold": ["gold_on2"],
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def event_days(date: pd.Timestamp, pad_before: int = 1, pad_after: int = 1) -> list[pd.Timestamp]:
    start = date.normalize() - pd.Timedelta(days=pad_before)
    end = date.normalize() + pd.Timedelta(days=pad_after)
    return list(pd.date_range(start, end, freq="D"))


def ensure_dirs() -> None:
    for path in [DOCS_DIR, OUTPUT_DIR, SUMMARY_DIR, DATA_RAW, DATA_WORK / "normalized"]:
        path.mkdir(parents=True, exist_ok=True)


def normalized_path(data_group: str, day: pd.Timestamp) -> Path:
    y = f"{day.year:04d}"
    d = f"{day:%Y%m%d}"
    names = {
        "guvi_on2": f"guvi_on2_normalized_{d}.csv",
        "dmsp_ssies": f"dmsp_ssies_normalized_{d}.csv",
        "superdarn": f"superdarn_normalized_{d}.csv",
        "ssusi": f"ssusi_normalized_{d}.csv",
        "indices": f"geomag_indices_{d}.csv",
        "gold_on2": f"gold_on2_normalized_{d}.csv",
    }
    return DATA_WORK / "normalized" / data_group / y / d / names.get(data_group, f"{data_group}_normalized_{d}.csv")


def required_patterns(data_group: str, days: Iterable[pd.Timestamp]) -> str:
    parts: list[str] = []
    for day in days:
        if data_group == "guvi_on2":
            parts.append(f"timed_guvi_l3-on2_{day.year}{day.dayofyear:03d}_*.nc")
        elif data_group == "dmsp_ssies":
            parts.append(f"dms_{day:%Y%m%d}_*s1.001.nc")
        elif data_group == "superdarn":
            parts.append(f"convection_maps_*_{day:%Y%m%d}_*.png OR SuperDARN map/fit/grid {day:%Y%m%d}")
        elif data_group == "ssusi":
            parts.append(f"dmspf*_ssusi_*_{day.year}{day.dayofyear:03d}*.nc")
        elif data_group == "indices":
            parts.append(f"OMNI/SYM-H/AE/Dst/Kp covering {day:%Y-%m-%d}")
        elif data_group == "gold_on2":
            parts.append(f"GOLD_L2_ON2_{day:%Y%m%d}*")
    return ";".join(parts)


def find_local_files_for_group(data_group: str, date: pd.Timestamp, pad_before: int = 1, pad_after: int = 1) -> list[Path]:
    files: list[Path] = []
    days = event_days(date, pad_before=pad_before, pad_after=pad_after)
    for day in days:
        if data_group == "guvi_on2":
            files.extend(DEFAULT_WORKSPACE.glob(f"timed_guvi_l3-on2_{day.year}{day.dayofyear:03d}_*.nc"))
            files.extend((DATA_RAW / "guvi" / "on2" / f"{day.year:04d}" / f"{day:%Y%m%d}").glob("*.nc"))
        elif data_group == "dmsp_ssies":
            files.extend(DEFAULT_DMSP_DIR.glob(f"dms_{day:%Y%m%d}_*s1.001.nc"))
            files.extend((DATA_RAW / "dmsp" / "ssies" / f"{day.year:04d}" / f"{day:%Y%m%d}").glob("*.nc"))
        elif data_group == "superdarn":
            for directory in DEFAULT_SUPERDARN_DIRS:
                files.extend(directory.glob(f"convection_maps_*_{day:%Y%m%d}_*.png"))
            files.extend((DATA_RAW / "superdarn" / f"{day.year:04d}" / f"{day:%Y%m%d}").glob("*"))
        elif data_group == "ssusi":
            stamp = f"{day.year}{day.dayofyear:03d}"
            for directory in DEFAULT_SSUSI_DIRS:
                files.extend(directory.glob(f"dmspf*_ssusi_*_{stamp}*.nc"))
            files.extend((DATA_RAW / "dmsp" / "ssusi" / f"{day.year:04d}" / f"{day:%Y%m%d}").glob("*.nc"))
        elif data_group == "indices":
            for directory in DEFAULT_INDICES_DIRS:
                files.extend(path for path in directory.glob("*.csv") if f"{day:%Y%m%d}" in path.name)
            files.extend((DATA_RAW / "indices" / f"{day.year:04d}" / f"{day:%Y%m%d}").glob("*"))
        elif data_group == "gold_on2":
            files.extend((DATA_RAW / "gold" / "on2" / f"{day.year:04d}" / f"{day:%Y%m%d}").glob("*"))
    return sorted({p for p in files if p.exists()})


def day_from_file(data_group: str, path: Path) -> set[str]:
    name = path.name
    days: set[str] = set()
    if data_group == "guvi_on2":
        match = re.search(r"timed_guvi_l3-on2_(\d{4})(\d{3})_", name)
        if match:
            day = pd.Timestamp(datetime(int(match.group(1)), 1, 1)) + pd.Timedelta(days=int(match.group(2)) - 1)
            days.add(day.strftime("%Y-%m-%d"))
    elif data_group == "dmsp_ssies":
        match = re.search(r"dms_(\d{8})_", name)
        if match:
            days.add(pd.Timestamp(match.group(1)).strftime("%Y-%m-%d"))
    elif data_group == "superdarn":
        match = re.search(r"_(\d{8})_", name)
        if match:
            days.add(pd.Timestamp(match.group(1)).strftime("%Y-%m-%d"))
    elif data_group == "ssusi":
        match = re.search(r"_(\d{4})(\d{3})T", name)
        if match:
            day = pd.Timestamp(datetime(int(match.group(1)), 1, 1)) + pd.Timedelta(days=int(match.group(2)) - 1)
            days.add(day.strftime("%Y-%m-%d"))
    elif data_group in {"indices", "gold_on2"}:
        for stamp in re.findall(r"(\d{8})", name):
            days.add(pd.Timestamp(stamp).strftime("%Y-%m-%d"))
    return days


def covered_days(data_group: str, date: pd.Timestamp) -> set[str]:
    days: set[str] = set()
    for path in find_local_files_for_group(data_group, date):
        days.update(day_from_file(data_group, path))
    return days


def build_required_manifest() -> pd.DataFrame:
    rows = []
    for event in SEED_EVENTS:
        start = event.event_date - pd.Timedelta(days=1)
        end = event.event_date + pd.Timedelta(days=2)
        for data_group, source_name, instrument, reason in DATA_GROUPS:
            rows.append({
                "event_id": event.event_id,
                "event_date": event.event_date.strftime("%Y-%m-%d"),
                "data_group": data_group,
                "source_name": source_name,
                "satellite_or_instrument": instrument,
                "required_start_ut": start.isoformat(),
                "required_end_ut": end.isoformat(),
                "required_files_or_patterns": required_patterns(data_group, event_days(event.event_date)),
                "priority": "required_for_primary_GUVI_statistics" if data_group in {"guvi_on2", "dmsp_ssies", "indices"} else "support_or_context",
                "reason": reason,
            })
    return pd.DataFrame(rows)


def build_local_manifest() -> pd.DataFrame:
    rows = []
    checked = now_utc()
    for event in SEED_EVENTS:
        for data_group, source_name, _, _ in DATA_GROUPS:
            files = find_local_files_for_group(data_group, event.event_date)
            if not files:
                rows.append({
                    "event_id": event.event_id,
                    "event_date": event.event_date.strftime("%Y-%m-%d"),
                    "data_group": data_group,
                    "source_name": source_name,
                    "local_path": "",
                    "file_name": "",
                    "file_size_mb": 0.0,
                    "parse_status": "missing",
                    "normalized_output_path": str(normalized_path(data_group, event.event_date)),
                    "last_checked_utc": checked,
                })
                continue
            for path in files:
                parse_status = "present_quicklook_only" if data_group == "superdarn" and path.suffix.lower() == ".png" else "present"
                rows.append({
                    "event_id": event.event_id,
                    "event_date": event.event_date.strftime("%Y-%m-%d"),
                    "data_group": data_group,
                    "source_name": source_name,
                    "local_path": str(path.parent),
                    "file_name": path.name,
                    "file_size_mb": round(path.stat().st_size / 1024 / 1024, 4),
                    "parse_status": parse_status,
                    "normalized_output_path": str(normalized_path(data_group, event.event_date)),
                    "last_checked_utc": checked,
                })
    return pd.DataFrame(rows)


def remote_source_hint(data_group: str) -> str:
    return {
        "guvi_on2": "TIMED/GUVI L3 O/N2 archive; verify NASA/SPDF or GUVI data service access.",
        "dmsp_ssies": "DMSP SSIES/SSJ via CEDAR Madrigal or local DMSP archive; likely manual/authenticated retrieval.",
        "superdarn": "SuperDARN map/fit/grid via SuperDARN data services/RST or quick-look map archive.",
        "ssusi": "DMSP SSUSI EDR/SDR archive; verify JHU/APL/SSUSI access and product type.",
        "indices": "OMNIWeb, WDC Kyoto Dst, SYM-H/AE/AL, GFZ Kp.",
        "gold_on2": "NASA GOLD L2 O/N2 archive; future branch only.",
    }.get(data_group, "manual source identification required")


def build_missing_manifest(required: pd.DataFrame, local: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for req in required.itertuples(index=False):
        required_days = {day.strftime("%Y-%m-%d") for day in event_days(pd.Timestamp(req.event_date))}
        present_days = covered_days(req.data_group, pd.Timestamp(req.event_date))
        missing_days = sorted(required_days - present_days)
        if not missing_days:
            continue
        blocking = req.data_group in {"guvi_on2", "dmsp_ssies", "indices"}
        rows.append({
            "event_id": req.event_id,
            "event_date": req.event_date,
            "data_group": req.data_group,
            "source_name": req.source_name,
            "missing_reason": "Missing required day(s): " + ";".join(missing_days),
            "download_priority": "high" if blocking else "medium",
            "manual_download_url_or_note": remote_source_hint(req.data_group),
            "automated_download_possible": False,
            "blocking_for_science_run": blocking,
        })
    return pd.DataFrame(rows)


def build_event_universe_frame(local: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for event in SEED_EVENTS:
        exact_day = event.event_date.strftime("%Y-%m-%d")
        has = lambda group: exact_day in covered_days(group, event.event_date)
        rows.append({
            "event_id": event.event_id,
            "event_date": event.event_date.strftime("%Y-%m-%d"),
            "storm_start_ut": event.event_date.isoformat(),
            "storm_end_ut": (event.event_date + pd.Timedelta(days=1)).isoformat(),
            "min_symh_or_dst": "",
            "time_min_symh_or_dst": "",
            "max_ae_or_kp": "",
            "storm_phase_tags": event.tier,
            "has_guvi": has("guvi_on2"),
            "has_dmsp_ssies": has("dmsp_ssies"),
            "has_superdarn": has("superdarn"),
            "has_ssusi": has("ssusi"),
            "has_gold_future_branch": False,
            "priority_level": "screen" if has("guvi_on2") and has("dmsp_ssies") else "data_acquisition_needed",
            "notes": event.reason,
        })
    return pd.DataFrame(rows)


def classify_ready(row: pd.Series) -> tuple[str, str, str]:
    missing = []
    if not row["has_guvi_on2"]:
        missing.append("GUVI O/N2")
    if not row["has_dmsp_ssies"] and not row["has_superdarn_quantitative"] and not row["has_superdarn_quicklook"]:
        missing.append("SAPS detector data")
    if not row["has_indices"]:
        missing.append("geomagnetic indices")
    if row["has_guvi_on2"] and row["has_dmsp_ssies"] and (row["has_superdarn_quantitative"] or row["has_superdarn_quicklook"]) and row["has_indices"]:
        return "A_ready_for_full_SAPS_ON2_matching", "", "run full SAPS/O/N2 matching after normalization"
    if row["has_dmsp_ssies"] and row["has_guvi_on2"]:
        return "B_ready_for_DMSP_GUVI_only", "; ".join(missing), "run DMSP-GUVI screening; acquire SuperDARN/indices for grading"
    if (row["has_superdarn_quantitative"] or row["has_superdarn_quicklook"]) and row["has_guvi_on2"]:
        return "C_ready_for_SuperDARN_GUVI_only", "; ".join(missing), "acquire DMSP SSIES or run SuperDARN-first screening"
    if row["has_dmsp_ssies"] or row["has_superdarn_quantitative"] or row["has_superdarn_quicklook"]:
        return "D_SAPS_available_no_ON2", "; ".join(missing), "acquire GUVI/GOLD O/N2"
    if row["has_guvi_on2"]:
        return "E_ON2_available_no_SAPS_data", "; ".join(missing), "acquire DMSP/SuperDARN SAPS data"
    if row["has_indices"]:
        return "F_indices_only", "; ".join(missing), "acquire instrument data"
    return "G_missing_or_unusable", "; ".join(missing), "download required data and rerun inventory"


def build_event_data_availability(local: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for event in SEED_EVENTS:
        exact_day = event.event_date.strftime("%Y-%m-%d")
        has = lambda group: exact_day in covered_days(group, event.event_date)
        exact_superdarn = [path for path in find_local_files_for_group("superdarn", event.event_date) if exact_day in day_from_file("superdarn", path)]
        quicklook = bool(any(path.suffix.lower() == ".png" for path in exact_superdarn))
        quantitative_sd = bool(any(path.suffix.lower() != ".png" for path in exact_superdarn))
        row = {
            "event_id": event.event_id,
            "event_date": event.event_date.strftime("%Y-%m-%d"),
            "storm_class": event.storm_class,
            "storm_phase_coverage": "not_tagged_until_indices",
            "has_dmsp_ssies": has("dmsp_ssies"),
            "has_dmsp_ssj": False,
            "has_guvi_on2": has("guvi_on2"),
            "has_superdarn_quantitative": quantitative_sd,
            "has_superdarn_quicklook": quicklook,
            "has_ssusi_boundary": has("ssusi"),
            "has_ssusi_on2_or_proxy": False,
            "has_indices": has("indices"),
            "has_gold_on2": False,
        }
        ready, blocking, action = classify_ready(pd.Series(row))
        row["ready_class"] = ready
        row["blocking_missing_data"] = blocking
        row["recommended_next_action"] = action
        rows.append(row)
    return pd.DataFrame(rows)


def build_event_catalog(local: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for event in SEED_EVENTS:
        rows.append({
            "event_id": event.event_id,
            "label": event.label,
            "start": event.event_date.isoformat(),
            "end": (event.event_date + pd.Timedelta(days=1)).isoformat(),
            "aacgm_date": (event.event_date + pd.Timedelta(hours=12)).isoformat(),
            "workspace": str(DEFAULT_WORKSPACE),
            "dmsp_dir": str(DEFAULT_DMSP_DIR),
            "guvi_glob": ";".join(str(p) for p in find_local_files_for_group("guvi_on2", event.event_date, 0, 0)),
            "dmsp_glob": ";".join(str(p) for p in find_local_files_for_group("dmsp_ssies", event.event_date, 0, 0)),
            "omni_file": "",
            "superdarn_dirs": ";".join(str(p) for p in DEFAULT_SUPERDARN_DIRS),
        })
    return pd.DataFrame(rows)


def queue_frame(missing: pd.DataFrame, queue_name: str) -> pd.DataFrame:
    rows = []
    source = missing[missing["data_group"].isin(DOWNLOAD_GROUPS[queue_name])]
    if source.empty and queue_name == "gold":
        for event in SEED_EVENTS:
            rows.append({
                "event_id": event.event_id,
                "event_date": event.event_date.strftime("%Y-%m-%d"),
                "data_group": "gold_on2",
                "instrument": "GOLD",
                "required_time_start": (event.event_date - pd.Timedelta(days=1)).isoformat(),
                "required_time_end": (event.event_date + pd.Timedelta(days=2)).isoformat(),
                "remote_source_hint": remote_source_hint("gold_on2"),
                "expected_file_pattern": required_patterns("gold_on2", event_days(event.event_date)),
                "local_target_dir": str(DATA_RAW / "gold" / "on2" / f"{event.event_date.year:04d}" / f"{event.event_date:%Y%m%d}"),
                "automated_download_possible": False,
                "manual_step_required": True,
                "priority": "future_branch_not_required_for_GUVI_statistics",
            })
        return pd.DataFrame(rows)
    for row in source.itertuples(index=False):
        date = pd.Timestamp(row.event_date)
        rows.append({
            "event_id": row.event_id,
            "event_date": row.event_date,
            "data_group": row.data_group,
            "instrument": row.source_name,
            "required_time_start": (date - pd.Timedelta(days=1)).isoformat(),
            "required_time_end": (date + pd.Timedelta(days=2)).isoformat(),
            "remote_source_hint": remote_source_hint(row.data_group),
            "expected_file_pattern": required_patterns(row.data_group, event_days(date)),
            "local_target_dir": str(DATA_RAW / row.data_group / f"{date.year:04d}" / f"{date:%Y%m%d}"),
            "automated_download_possible": False,
            "manual_step_required": True,
            "priority": row.download_priority,
        })
    return pd.DataFrame(rows)


def write_core_manifests() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ensure_dirs()
    required = build_required_manifest()
    local = build_local_manifest()
    missing = build_missing_manifest(required, local)
    availability = build_event_data_availability(local)
    universe = build_event_universe_frame(local)
    catalog = build_event_catalog(local)
    required.to_csv(DOCS_DIR / "data_manifest_required.csv", index=False)
    local.to_csv(DOCS_DIR / "data_manifest_local.csv", index=False)
    missing.to_csv(DOCS_DIR / "data_manifest_missing.csv", index=False)
    availability.to_csv(OUTPUT_DIR / "event_data_availability.csv", index=False)
    universe.to_csv(OUTPUT_DIR / "event_universe.csv", index=False)
    catalog.to_csv(OUTPUT_DIR / "event_catalog_auto_available_dates.csv", index=False)
    return required, local, missing, availability


def write_download_queues(missing: pd.DataFrame) -> None:
    ensure_dirs()
    for name in DOWNLOAD_GROUPS:
        queue_frame(missing, name).to_csv(DOCS_DIR / f"download_queue_{name}.csv", index=False)


def write_data_gap_report(missing: pd.DataFrame, availability: pd.DataFrame) -> Path:
    ensure_dirs()
    missing_counts = missing.groupby(["event_date", "data_group"]).size().reset_index(name="missing_rows") if not missing.empty else pd.DataFrame(columns=["event_date", "data_group", "missing_rows"])
    lines = [
        "# Data Gap Report",
        "",
        "This report implements `docs_index/codex_data_acquisition_and_event_expansion_plan.md` from commit `3cb2b7843c26c286bbb0fead724ed0893a71af4f`.",
        "",
        "Current science status: local-data smoke test for 2015-03-16 to 2015-03-18 only; not the planned 2011-2015 statistics.",
        "",
        "## Event Readiness",
        "",
    ]
    for row in availability.itertuples(index=False):
        lines.append(f"- {row.event_date} `{row.event_id}`: {row.ready_class}; missing: {row.blocking_missing_data or 'none'}; next: {row.recommended_next_action}")
    lines.extend(["", "## Missing Data Counts", ""])
    if missing_counts.empty:
        lines.append("No missing required data rows.")
    else:
        for row in missing_counts.itertuples(index=False):
            lines.append(f"- {row.event_date} {row.data_group}: {row.missing_rows}")
    lines.extend([
        "",
        "## Blocking Items Before 2011-2015 Statistics",
        "",
        "- Build or import a 2011-2015 storm list with SYM-H/Dst <= -50 nT.",
        "- Acquire GUVI O/N2, DMSP SSIES/SSJ/SSUSI, SuperDARN quantitative or quick-look support, and geomagnetic indices for the seed validation events.",
        "- Normalize raw files into `data_work/normalized/` before claiming multi-event statistics.",
    ])
    path = SUMMARY_DIR / "data_gap_report.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_normalization_status(data_group: str) -> Path:
    ensure_dirs()
    local = build_local_manifest()
    subset = local[local["data_group"] == data_group].copy()
    if subset.empty:
        subset = pd.DataFrame([{"event_id": "", "event_date": "", "data_group": data_group, "source_name": data_group, "local_path": "", "file_name": "", "file_size_mb": 0.0, "parse_status": "missing", "normalized_output_path": "", "last_checked_utc": now_utc()}])
    subset["normalizer_status"] = subset["parse_status"].map(lambda status: "pending_full_normalizer" if status != "missing" else "missing_raw_input")
    subset["normalizer_note"] = "Screening pipeline can read current smoke-test raw files; full reusable normalizer is queued by the data acquisition plan."
    out_dir = DATA_WORK / "normalized" / data_group
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{data_group}_normalization_status.csv"
    subset.to_csv(path, index=False)
    return path
