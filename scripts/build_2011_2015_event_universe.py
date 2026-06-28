from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
import csv
import io

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs_index"
OUTPUT_DIR = ROOT / "data_samples" / "screening_outputs"
DATA_RAW = ROOT / "data_raw"

HAPI_ENDPOINT = "https://cdaweb.gsfc.nasa.gov/hapi/data"
HAPI_DATASET = "OMNI2_H0_MRG1HR"
HAPI_PARAMETERS = "KP1800,DST1800,AE1800"
START_UT = "2011-01-01T00:00:00Z"
END_UT = "2016-01-01T00:00:00Z"

DATA_GROUPS = [
    ("guvi_on2", "TIMED/GUVI L3 O/N2", "TIMED_GUVI", "main O/N2 source"),
    ("dmsp_ssies", "DMSP SSIES", "DMSP_F16_F17_F18_F19", "ion drift and SAPS crossing detection"),
    ("superdarn", "SuperDARN map/fit/grid or quick-look", "SuperDARN", "two-dimensional SAPS channel support"),
    ("ssusi", "DMSP SSUSI", "DMSP_SSUSI", "auroral boundary and optional O/N2-sensitive support"),
    ("indices", "OMNI/Dst/Kp/AE", "OMNI2_H0_MRG1HR", "storm and substorm phase tagging"),
]


@dataclass(frozen=True)
class SeedOpportunity:
    event_id: str
    event_date: str
    include_reason: str
    priority_level: str


SEED_OPPORTUNITIES = [
    SeedOpportunity("available_20150316", "2015-03-16", "opportunity_added_local_smoke_test", "seed_smoke_test"),
    SeedOpportunity("available_20150317", "2015-03-17", "opportunity_added_local_smoke_test", "seed_smoke_test"),
    SeedOpportunity("available_20150318", "2015-03-18", "opportunity_added_local_smoke_test", "seed_smoke_test"),
    SeedOpportunity("validation_20140219", "2014-02-19", "opportunity_added_thesis_superdarn_validation", "thesis_validation"),
    SeedOpportunity("validation_20111025", "2011-10-25", "opportunity_added_thesis_superdarn_validation", "thesis_validation"),
    SeedOpportunity("validation_20130630", "2013-06-30", "opportunity_added_thesis_superdarn_validation", "thesis_validation"),
]


def ensure_dirs() -> None:
    for path in [DOCS_DIR, OUTPUT_DIR, DATA_RAW / "indices" / "global"]:
        path.mkdir(parents=True, exist_ok=True)


def fetch_omni2_hourly() -> pd.DataFrame:
    query = urlencode({"id": HAPI_DATASET, "parameters": HAPI_PARAMETERS, "time.min": START_UT, "time.max": END_UT, "format": "csv"})
    with urlopen(f"{HAPI_ENDPOINT}?{query}", timeout=120) as response:
        text = response.read().decode("utf-8", "replace")
    frame = pd.read_csv(io.StringIO(text), header=None, names=["time_utc", "kp_x10", "dst", "ae"], parse_dates=["time_utc"])
    for column in ["kp_x10", "dst", "ae"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame.loc[frame["dst"].abs() >= 9000, "dst"] = pd.NA
    frame.loc[frame["kp_x10"].abs() >= 9000, "kp_x10"] = pd.NA
    frame.loc[frame["ae"].abs() >= 9000, "ae"] = pd.NA
    return frame


def load_or_fetch_indices(force_fetch: bool = False) -> pd.DataFrame:
    path = DATA_RAW / "indices" / "global" / "omni2_h0_mrg1hr_20110101_20151231.csv"
    if path.exists() and not force_fetch:
        frame = pd.read_csv(path, parse_dates=["time_utc"])
        if not frame.empty:
            frame["time_utc"] = pd.to_datetime(frame["time_utc"], utc=True).dt.tz_convert(None)
            return frame
    frame = fetch_omni2_hourly()
    frame["time_utc"] = pd.to_datetime(frame["time_utc"], utc=True).dt.tz_convert(None)
    frame.to_csv(path, index=False)
    return frame


def storm_class(min_dst: float) -> str:
    if min_dst <= -200:
        return "super_storm"
    if min_dst <= -100:
        return "major_storm"
    return "moderate_storm"


def build_storm_universe(indices: pd.DataFrame) -> pd.DataFrame:
    data = indices.dropna(subset=["dst"]).copy()
    data["storm_flag"] = data["dst"] <= -50
    storms = []
    current = []
    for row in data.itertuples(index=False):
        if row.storm_flag:
            current.append(row)
        elif current:
            storms.append(current)
            current = []
    if current:
        storms.append(current)
    rows = []
    for number, storm_rows in enumerate(storms, start=1):
        storm_frame = pd.DataFrame(storm_rows)
        min_row = storm_frame.loc[storm_frame["dst"].idxmin()]
        min_time = pd.Timestamp(min_row["time_utc"])
        min_dst = float(min_row["dst"])
        klass = storm_class(min_dst)
        pad_before, pad_after = (2, 3) if min_dst <= -100 else (1, 1)
        storm_group_id = f"storm_{number:03d}_{min_time:%Y%m%d%H}"
        for offset in range(-pad_before, pad_after + 1):
            day = (min_time.normalize() + pd.Timedelta(days=offset)).date()
            if day < pd.Timestamp("2011-01-01").date() or day > pd.Timestamp("2015-12-31").date():
                continue
            phase_window = "storm_min_day" if offset == 0 else (f"storm_day_minus_{abs(offset)}" if offset < 0 else f"storm_day_plus_{offset}")
            rows.append({"event_id": f"{storm_group_id}_{day:%Y%m%d}", "event_date": f"{day:%Y-%m-%d}", "storm_group_id": storm_group_id, "storm_min_time_ut": min_time.strftime("%Y-%m-%dT%H:%M:%SZ"), "min_symh_or_dst": min_dst, "storm_class": klass, "include_reason": "dst_threshold_strong_pm2_p3" if min_dst <= -100 else "dst_threshold_pm1", "phase_window": phase_window, "priority_level": "super_storm_subset" if min_dst <= -200 else ("major_subset" if min_dst <= -100 else "primary")})
    return pd.DataFrame(rows)


def build_expanded_universe(storm_universe: pd.DataFrame) -> pd.DataFrame:
    rows = storm_universe.copy()
    rows["opportunity_type"] = "storm_index_selected"
    existing_dates = set(rows["event_date"].astype(str)) if not rows.empty else set()
    additions = []
    for item in SEED_OPPORTUNITIES:
        if item.event_date in existing_dates:
            continue
        additions.append({"event_id": item.event_id, "event_date": item.event_date, "storm_group_id": item.event_id, "storm_min_time_ut": "", "min_symh_or_dst": "", "storm_class": "seed_opportunity_pending_index_context", "include_reason": item.include_reason, "phase_window": "event_day", "priority_level": item.priority_level, "opportunity_type": "opportunity_added"})
    if additions:
        rows = pd.concat([rows, pd.DataFrame(additions)], ignore_index=True)
    return rows.sort_values(["event_date", "event_id"]).reset_index(drop=True)


def date_window(date_text: str, strong: bool) -> list[pd.Timestamp]:
    date = pd.Timestamp(date_text)
    before, after = (2, 3) if strong else (1, 1)
    return list(pd.date_range(date - pd.Timedelta(days=before), date + pd.Timedelta(days=after), freq="D"))


def required_patterns(data_group: str, days: list[pd.Timestamp]) -> str:
    parts = []
    for day in days:
        if data_group == "guvi_on2":
            parts.append(f"timed_guvi_l3-on2_{day.year}{day.dayofyear:03d}_*.nc")
        elif data_group == "dmsp_ssies":
            parts.append(f"dms_{day:%Y%m%d}_*s1.001.nc")
        elif data_group == "superdarn":
            parts.append(f"SuperDARN map/fit/grid or convection_maps_*_{day:%Y%m%d}_*.png")
        elif data_group == "ssusi":
            parts.append(f"dmspf*_ssusi_*_{day.year}{day.dayofyear:03d}*.nc")
        elif data_group == "indices":
            parts.append(f"OMNI2_H0_MRG1HR Dst/Kp/AE covering {day:%Y-%m-%d}")
    return ";".join(parts)


def build_required_manifest(universe: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for event in universe.itertuples(index=False):
        strong = str(event.priority_level) in {"major_subset", "super_storm_subset"}
        days = date_window(event.event_date, strong)
        start, end = days[0], days[-1] + pd.Timedelta(days=1)
        for data_group, source_name, instrument, reason in DATA_GROUPS:
            rows.append({"event_id": event.event_id, "event_date": event.event_date, "storm_group_id": event.storm_group_id, "data_group": data_group, "source_name": source_name, "satellite_or_instrument": instrument, "required_start_ut": start.strftime("%Y-%m-%dT00:00:00"), "required_end_ut": end.strftime("%Y-%m-%dT00:00:00"), "required_files_or_patterns": required_patterns(data_group, days), "priority": "required_for_primary_GUVI_statistics" if data_group in {"guvi_on2", "dmsp_ssies", "indices"} else "support_or_context", "reason": reason})
    return pd.DataFrame(rows)


def remote_source_hint(data_group: str) -> str:
    return {"guvi_on2": "TIMED/GUVI L3 O/N2 archive; verify NASA/SPDF or GUVI data service access.", "dmsp_ssies": "DMSP SSIES/SSJ via CEDAR Madrigal or local DMSP archive; likely manual/authenticated retrieval.", "superdarn": "SuperDARN map/fit/grid via SuperDARN data services/RST or quick-look map archive.", "ssusi": "DMSP SSUSI EDR/SDR archive; verify JHU/APL/SSUSI access and product type.", "indices": "NASA CDAWeb OMNI2_H0_MRG1HR for hourly Dst/Kp/AE; add SYM-H if one-minute phase tagging is required."}[data_group]


def write_download_queues(required: pd.DataFrame) -> None:
    queue_map = {"guvi": "guvi_on2", "dmsp": "dmsp_ssies", "superdarn": "superdarn", "ssusi": "ssusi", "indices": "indices"}
    for queue_name, data_group in queue_map.items():
        rows = []
        for row in required[required["data_group"] == data_group].itertuples(index=False):
            date = pd.Timestamp(row.event_date)
            rows.append({"event_id": row.event_id, "event_date": row.event_date, "storm_group_id": row.storm_group_id, "data_group": row.data_group, "instrument": row.source_name, "required_time_start": row.required_start_ut, "required_time_end": row.required_end_ut, "remote_source_hint": remote_source_hint(row.data_group), "expected_file_pattern": row.required_files_or_patterns, "local_target_dir": str(Path("data_raw") / row.data_group / f"{date.year:04d}" / f"{date:%Y%m%d}"), "automated_download_possible": row.data_group == "indices", "manual_step_required": row.data_group != "indices", "priority": row.priority})
        pd.DataFrame(rows).to_csv(DOCS_DIR / f"download_queue_{queue_name}_2011_2015.csv", index=False)


def write_seed_index_day_files(indices: pd.DataFrame, expanded: pd.DataFrame) -> None:
    selected_days = sorted(set(expanded["event_date"].astype(str)))
    for date_text in selected_days:
        day = pd.Timestamp(date_text)
        subset = indices[(indices["time_utc"] >= day) & (indices["time_utc"] < day + pd.Timedelta(days=1))].copy()
        if subset.empty:
            continue
        target_dir = DATA_RAW / "indices" / f"{day.year:04d}" / f"{day:%Y%m%d}"
        target_dir.mkdir(parents=True, exist_ok=True)
        subset.to_csv(target_dir / f"omni2_h0_mrg1hr_{day:%Y%m%d}.csv", index=False, quoting=csv.QUOTE_MINIMAL)


def main() -> None:
    ensure_dirs()
    indices = load_or_fetch_indices()
    storm_universe = build_storm_universe(indices)
    expanded = build_expanded_universe(storm_universe)
    required = build_required_manifest(expanded)
    write_seed_index_day_files(indices, expanded)
    storm_universe.to_csv(OUTPUT_DIR / "event_universe_2011_2015.csv", index=False)
    expanded.to_csv(OUTPUT_DIR / "event_universe_expanded_2011_2015.csv", index=False)
    required.to_csv(DOCS_DIR / "data_manifest_required_2011_2015.csv", index=False)
    write_download_queues(required)
    print(f"Saved storm universe rows: {len(storm_universe)}")
    print(f"Saved expanded universe rows: {len(expanded)}")
    print(f"Saved required manifest rows: {len(required)}")


if __name__ == "__main__":
    main()
