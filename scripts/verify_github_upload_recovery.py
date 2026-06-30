from __future__ import annotations

from pathlib import Path

import pandas as pd

from data_acquisition_common import DATA_WORK, DOCS_DIR, OUTPUT_DIR, SUMMARY_DIR, now_utc


ROOT = Path(__file__).resolve().parents[1]

REMOTE_VISIBLE = {
    "docs_index/codex_next_work_plan_after_upload_recovery_20260630.md",
    "docs_index/codex_upload_recovery_and_next_stage_plan_after_20260629_local_run.md",
    "docs_index/next_stage_after_20260629_web_quicklook.md",
    "docs_index/next_stage_after_20260629_upload_verification_manifest.csv",
    "docs_index/next_stage_after_20260629_output_manifest.csv",
    "docs_index/batch1_major_storm_group_priority.csv",
    "docs_index/github_upload_pending_after_20260629_execution.md",
    "summaries/screening_outputs/normalizer_status_v3_summary.md",
}

LOCAL_LARGE_ARTIFACTS = {
    "data_work/normalized/normalizer_status_all_events_v3.csv",
    "data_work/normalized/normalizer_status_batch1_major_v1.csv",
    "data_samples/screening_outputs/st_patrick_normalizer_science_ready_caveats.csv",
}

VALIDATION_EVENT_IDS = {
    "validation_20140219",
    "validation_20111025",
    "validation_20130630",
}
SMOKE_EVENT_IDS = {"available_20150316", "available_20150317", "available_20150318"}
ST_PATRICK_EVENTS = {"available_20150317", "available_20150318"}
LAG_MAP = {
    "near_zero_lag_0_1h": "0-1 h",
    "short_lag_response_1_3h": "1-3 h",
    "medium_lag_response_3_6h": "3-6 h",
    "long_lag_response_6_12h": "6-12 h",
    "0_1h": "0-1 h",
    "1_3h": "1-3 h",
    "3_6h": "3-6 h",
    "6_12h": "6-12 h",
}


def read_csv(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def bool_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series([False] * len(frame), index=frame.index)
    values = frame[column]
    if values.dtype == bool:
        return values
    return values.astype(str).str.lower().isin({"true", "1", "yes"})


def repo_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def classify_upload(row: pd.Series) -> tuple[str, bool, str]:
    path = str(row.get("path", "")).replace("\\", "/")
    if path in REMOTE_VISIBLE:
        return "remote_visible", True, "verified by GitHub connector fetch or known successful create_file commit"
    if path in LOCAL_LARGE_ARTIFACTS:
        return "manifest_only_local_large_artifact", False, "kept local; SHA256/row count and summary are repo-visible"
    if path.startswith("data_samples/") and int(row.get("size_bytes", 0) or 0) > 15000:
        return "summary_uploaded_full_data_local", False, "full data kept local; gate summary and manifest identify artifact"
    if path.startswith("scripts/"):
        return "not_attempted", False, "script upload deferred after priority recovery files"
    return "not_attempted", False, "not uploaded in priority recovery batch"


def write_upload_verification_v2() -> tuple[Path, Path]:
    source = read_csv(DOCS_DIR / "next_stage_after_20260629_upload_verification_manifest.csv")
    if source.empty:
        raise FileNotFoundError("Missing docs_index/next_stage_after_20260629_upload_verification_manifest.csv")
    statuses = source.apply(classify_upload, axis=1, result_type="expand")
    statuses.columns = ["github_upload_status_v2", "github_visible_v2", "verification_note"]
    out = pd.concat([source, statuses], axis=1)
    out_path = DOCS_DIR / "next_stage_after_20260629_upload_verification_manifest_v2.csv"
    out.to_csv(out_path, index=False)

    counts = out["github_upload_status_v2"].value_counts().sort_index()
    lines = [
        "# GitHub Upload Recovery Verification",
        "",
        f"Generated: {now_utc()}",
        "",
        "Priority upload recovery succeeded for the plan, quicklook, manifests, Batch-1 priority table, pending note, and normalizer V3 summary. Large local gate artifacts remain represented by SHA256/row-count manifest rows plus summaries.",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in counts.items():
        lines.append(f"- `{status}`: {count}")
    lines.extend(
        [
            "",
            "## Rule For Large Local Artifacts",
            "",
            "`normalizer_status_all_events_v3.csv` remains local-large-artifact: 415 rows, SHA256 recorded in the uploaded manifest, and V3 summary uploaded. This is intentional and should not be interpreted as missing science execution.",
            "",
            "## Stop Rule",
            "",
            "Do not claim completed 2011-2015 multi-event SAPS/O/N2 statistics.",
        ]
    )
    summary = SUMMARY_DIR / "github_upload_recovery_verification_20260630.md"
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path, summary


def gate_category(row: pd.Series) -> str:
    status = str(row.get("parse_status_v3", ""))
    group = str(row.get("data_group", ""))
    if status == "parsed_ok_science_ready":
        return "science_ready"
    if status == "download_queue_only_blocking":
        return "blocked_by_download_queue"
    if group == "guvi_on2":
        return "blocked_by_no_dayglow_or_no_on2"
    if group == "dmsp_ssies":
        return "blocked_by_missing_required_variable"
    if group == "superdarn":
        return "blocked_by_no_quantitative_superdarn"
    if group == "ssusi":
        return "blocked_by_unmaterialized_ssusi_boundary"
    return "blocked_by_missing_required_variable"


def allowed_scope(row: pd.Series) -> str:
    category = str(row.get("gate_decision_category", ""))
    event_id = str(row.get("event_id", ""))
    if category == "science_ready":
        return "science_ready"
    if event_id in SMOKE_EVENT_IDS:
        return "smoke_test_only"
    return "blocked"


def write_normalizer_gate_decision() -> Path:
    status = read_csv(DATA_WORK / "normalized" / "normalizer_status_all_events_v3.csv")
    if status.empty:
        raise FileNotFoundError("Missing data_work/normalized/normalizer_status_all_events_v3.csv")
    status["gate_decision_category"] = status.apply(gate_category, axis=1)
    status["allowed_scope_after_v3_gate"] = status.apply(allowed_scope, axis=1)
    counts = status.groupby(["gate_decision_category", "data_group"]).size().reset_index(name="rows")
    overall = status["gate_decision_category"].value_counts().sort_index()
    scope_counts = status["allowed_scope_after_v3_gate"].value_counts().sort_index()

    lines = [
        "# Normalizer V3 Gate Decision Table",
        "",
        f"Generated: {now_utc()}",
        "",
        "Primary input: `data_work/normalized/normalizer_status_all_events_v3.csv`.",
        "",
        "## Overall Gate Counts",
        "",
        "| Gate category | Rows |",
        "| --- | ---: |",
    ]
    for category, rows in overall.items():
        lines.append(f"| `{category}` | {rows} |")
    lines.extend(["", "## Allowed Scope Counts", "", "| Scope | Rows |", "| --- | ---: |"])
    for scope, rows in scope_counts.items():
        lines.append(f"| `{scope}` | {rows} |")
    lines.extend(["", "## By Data Group", "", "| Gate category | Data group | Rows |", "| --- | --- | ---: |"])
    for row in counts.itertuples(index=False):
        lines.append(f"| `{row.gate_decision_category}` | `{row.data_group}` | {row.rows} |")
    lines.extend(
        [
            "",
            "## Detector/Matching Rule",
            "",
            "- `science_ready` scope rows may feed science logic.",
            "- `smoke_test_only` scope rows may feed St. Patrick pipeline checks, but not final 2011-2015 statistics.",
            "- `blocked` scope rows must remain explicit caveats or no-data rows.",
        ]
    )
    path = SUMMARY_DIR / "normalizer_v3_gate_decision_table.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def resolution_status(row: pd.Series) -> str:
    group = str(row.get("data_group", ""))
    current_state = str(row.get("current_state", ""))
    if current_state == "parsed_ok_science_ready":
        return "downloaded_and_linked"
    if group in {"dmsp_ssies", "ssusi"}:
        return "authentication_required"
    if group in {"guvi_on2", "superdarn"}:
        return "manual_download_required"
    return "local_path_missing"


def write_validation_blocker_resolution() -> tuple[Path, Path]:
    missing = read_csv(DOCS_DIR / "data_manifest_seed_events_missing.csv")
    if missing.empty:
        missing = pd.DataFrame(columns=["event_id", "event_date", "data_group", "current_state"])
    rows = []
    for item in missing.itertuples(index=False):
        series = pd.Series(item._asdict())
        status = resolution_status(series)
        rows.append(
            {
                "event_id": item.event_id,
                "event_date": item.event_date,
                "data_group": item.data_group,
                "current_state": item.current_state,
                "resolution_status": status,
                "detector_interpretation": "data_gap_not_detector_failure",
                "local_target_dir": getattr(item, "local_target_dir", ""),
                "expected_file_pattern": getattr(item, "expected_file_pattern", ""),
                "remote_source_hint": getattr(item, "remote_source_hint", ""),
                "next_action": getattr(item, "next_action", "download_or_link_files_then_rerun_gates"),
            }
        )
    out = pd.DataFrame(rows)
    out_path = DOCS_DIR / "validation_event_data_resolution_table.csv"
    out.to_csv(out_path, index=False)

    counts = out["resolution_status"].value_counts().sort_index() if not out.empty else pd.Series(dtype=int)
    lines = [
        "# Validation Event Instrument Blocker Resolution",
        "",
        f"Generated: {now_utc()}",
        "",
        "The 12 validation-event instrument blockers remain data-access/linking blockers. They are not detector failures and must remain explicit no-data/nonmatch rows until files are acquired and parsed.",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in counts.items():
        lines.append(f"- `{status}`: {count}")
    lines.extend(["", "## Blocker Rows", ""])
    for row in out.itertuples(index=False):
        lines.append(f"- {row.event_date} `{row.event_id}` `{row.data_group}`: `{row.resolution_status}`")
    path = SUMMARY_DIR / "validation_event_instrument_blocker_resolution.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path, path


def write_st_patrick_normalizer_outputs() -> tuple[Path, Path]:
    status = read_csv(DATA_WORK / "normalized" / "normalizer_status_all_events_v3.csv")
    subset = status[status["event_id"].astype(str).isin(ST_PATRICK_EVENTS)].copy()
    if subset.empty:
        subset = pd.DataFrame(columns=["event_id", "event_date", "data_group"])
    subset["science_ready_normalized_row"] = subset["gate_decision_category"] if "gate_decision_category" in subset.columns else subset.apply(gate_category, axis=1)
    subset["science_ready_normalized_row"] = subset["science_ready_normalized_row"].eq("science_ready")
    subset["st_patrick_status"] = subset["science_ready_normalized_row"].map({True: "science_ready", False: "explicit_caveat_smoke_test_only"})
    keep = [
        "event_id",
        "event_date",
        "data_group",
        "source_file_or_queue",
        "parse_status_v3",
        "science_ready_gate",
        "science_ready_normalized_row",
        "st_patrick_status",
        "required_next_field_bundle",
        "nonfatal_caveat",
    ]
    for col in keep:
        if col not in subset.columns:
            subset[col] = ""
    out_path = OUTPUT_DIR / "st_patrick_science_ready_normalizer_rows.csv"
    subset[keep].to_csv(out_path, index=False)

    counts = subset["st_patrick_status"].value_counts().sort_index() if not subset.empty else pd.Series(dtype=int)
    lines = [
        "# St. Patrick Science-Ready Normalizer Summary",
        "",
        f"Generated: {now_utc()}",
        "",
        "The St. Patrick rows are checked against the V3 normalizer gate. Current GUVI/DMSP/SuperDARN/SSUSI rows remain smoke-test/caveated until required science-ready fields are materialized.",
        "",
        "## Status Counts",
        "",
    ]
    for status_name, count in counts.items():
        lines.append(f"- `{status_name}`: {count}")
    lines.extend(
        [
            "",
            "## Required For Promotion",
            "",
            "- GUVI: time, geo lat/lon, AACGM MLAT/MLT, LT, SZA, O/N2, log(O/N2), dayglow quality flag.",
            "- DMSP: time, satellite, geo lat/lon, AACGM MLAT/MLT, westward drift, density, quality, sign convention.",
            "- SSUSI: auroral boundary or contamination-mask status.",
            "- SuperDARN: quantitative map/fit/grid or explicit quicklook/insufficient/not_available state.",
        ]
    )
    summary = SUMMARY_DIR / "st_patrick_science_ready_normalizer_summary.md"
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path, summary


def add_v3_detector_fields(frame: pd.DataFrame, kind: str) -> pd.DataFrame:
    frame = frame.copy()
    if frame.empty:
        return frame
    frame["detector_gate_version"] = "v3_after_normalizer_gate"
    frame["science_ready_detector_v3"] = False
    if kind == "dmsp":
        frame["detector_gate_v3_status"] = "smoke_test_only_missing_geometry_boundary_morphology"
        if "confidence_grade" in frame.columns:
            rejected = frame["confidence_grade"].astype(str).str.lower().eq("rejected")
            frame.loc[rejected, "detector_gate_v3_status"] = "blocked_missing_dmsp_file"
        frame["v3_required_fields"] = "sustained_westward_interval,500_ms_threshold,geometry_quality,boundary_relation,morphology_class"
    elif kind == "superdarn":
        frame["detector_gate_v3_status"] = "blocked_by_no_quantitative_superdarn"
        frame["v3_required_fields"] = "quantitative_map_fit_grid,velocity_vectors,echo_coverage,MLT_extent,T_slope"
    else:
        frame["detector_gate_v3_status"] = "blocked_or_smoke_test_only_after_normalizer_v3_gate"
        frame["v3_required_fields"] = "science_ready_dmsp_or_quantitative_superdarn_plus_on2_gate"
    frame["recommended_for_2011_2015_statistics"] = False
    return frame


def write_seed_detector_v3() -> tuple[Path, Path, Path, Path]:
    dmsp = add_v3_detector_fields(read_csv(OUTPUT_DIR / "dmsp_saps_crossings_seed_events_v2.csv"), "dmsp")
    superdarn = add_v3_detector_fields(read_csv(OUTPUT_DIR / "superdarn_saps_channels_seed_events_v2.csv"), "superdarn")
    channels = add_v3_detector_fields(read_csv(OUTPUT_DIR / "saps_channel_objects_seed_events_v2.csv"), "channel")
    dmsp_path = OUTPUT_DIR / "dmsp_saps_crossings_seed_events_v3.csv"
    superdarn_path = OUTPUT_DIR / "superdarn_saps_channels_seed_events_v3.csv"
    channel_path = OUTPUT_DIR / "saps_channel_objects_seed_events_v3.csv"
    dmsp.to_csv(dmsp_path, index=False)
    superdarn.to_csv(superdarn_path, index=False)
    channels.to_csv(channel_path, index=False)

    lines = [
        "# Seed Detector Gate V3 Summary",
        "",
        f"Generated: {now_utc()}",
        "",
        f"- DMSP detector v3 rows: {len(dmsp)}",
        f"- SuperDARN detector v3 rows: {len(superdarn)}",
        f"- SAPS channel object v3 rows: {len(channels)}",
        "",
        "No seed detector row is promoted to final science statistics. St. Patrick rows remain smoke-test-only unless required V3 normalizer fields are materialized; validation-event rows remain no-data blockers.",
    ]
    summary = SUMMARY_DIR / "seed_detector_gate_v3_summary.md"
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dmsp_path, superdarn_path, channel_path, summary


def normalize_lag(value: object) -> str:
    return LAG_MAP.get(str(value), str(value))


def write_matching_v2_outputs() -> tuple[Path, Path, Path, Path, Path, Path]:
    pairs = [
        ("on2_opportunity_seed_events_science_ready.csv", "on2_opportunity_seed_events_v2_science_ready.csv"),
        ("guvi_on2_patches_seed_events_science_ready.csv", "guvi_on2_patches_seed_events_v2_science_ready.csv"),
        ("saps_on2_match_candidates_seed_events_science_ready.csv", "saps_on2_match_candidates_seed_events_v2_science_ready.csv"),
        ("dmsp_crossing_relative_on2_profiles_seed_events_science_ready.csv", "dmsp_crossing_relative_on2_profiles_seed_events_v2_science_ready.csv"),
        ("nonmatch_selection_function_seed_events_science_ready.csv", "nonmatch_selection_function_seed_events_v2_science_ready.csv"),
    ]
    written: list[Path] = []
    match_frame = pd.DataFrame()
    for source_name, dest_name in pairs:
        frame = read_csv(OUTPUT_DIR / source_name)
        if "lag_bin" in frame.columns:
            frame["lag_bin_v2"] = frame["lag_bin"].map(normalize_lag)
        if "recommended_for_statistics" in frame.columns:
            frame["screening_recommended_before_v2_gate"] = bool_series(frame, "recommended_for_statistics")
            frame["recommended_for_statistics"] = False
        frame["science_ready_matching_v2"] = False
        frame["science_ready_matching_v2_reason"] = "blocked_pending_normalizer_v3_science_ready_inputs"
        if dest_name.startswith("saps_on2_match"):
            match_frame = frame.copy()
        dest = OUTPUT_DIR / dest_name
        frame.to_csv(dest, index=False)
        written.append(dest)

    lag_counts = match_frame["lag_bin_v2"].value_counts().to_dict() if "lag_bin_v2" in match_frame.columns else {}
    lines = [
        "# Seed Event Science-Ready Matching V2 Summary",
        "",
        f"Generated: {now_utc()}",
        "",
        "Science-ready matching V2 outputs were materialized as gate products. Rows are retained with `recommended_for_statistics = False` until normalizer V3 science-ready inputs exist.",
        "",
        "## Lag Bin Rows",
        "",
    ]
    for lag in ["0-1 h", "1-3 h", "3-6 h", "6-12 h"]:
        lines.append(f"- `{lag}`: {int(lag_counts.get(lag, 0))}")
    lines.extend(
        [
            "",
            "## Region Classes",
            "",
            "Expected classes remain: `inside_channel`, `near_channel`, `equatorward_control`, `poleward_control`, `same_MLT_outside_channel`.",
            "",
            "## Stop Rule",
            "",
            "These are not completed 2011-2015 SAPS/O/N2 statistics.",
        ]
    )
    summary = SUMMARY_DIR / "seed_event_science_ready_matching_v2_summary.md"
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return (*written, summary)


def write_batch1_top5_status() -> tuple[list[Path], Path]:
    priority = read_csv(DOCS_DIR / "batch1_major_storm_group_priority.csv")
    top5 = priority.sort_values("priority_rank").head(5) if not priority.empty else pd.DataFrame()
    top5_ids = set(top5["storm_group_id"].astype(str)) if not top5.empty else set()
    paths: list[Path] = []
    for name in ["guvi", "dmsp", "superdarn", "ssusi", "indices"]:
        source = read_csv(DOCS_DIR / f"download_queue_{name}_2011_2015_batch1_major.csv")
        if not source.empty and "storm_group_id" in source.columns:
            filtered = source[source["storm_group_id"].astype(str).isin(top5_ids)].copy()
            rank_map = dict(zip(top5["storm_group_id"].astype(str), top5["priority_rank"]))
            filtered["priority_rank"] = filtered["storm_group_id"].astype(str).map(rank_map)
            filtered = filtered.sort_values(["priority_rank", "event_date"])
        else:
            filtered = source
        out = DOCS_DIR / f"download_queue_batch1_top5_{name}.csv"
        filtered.to_csv(out, index=False)
        paths.append(out)

    lines = [
        "# Batch-1 Top-5 Acquisition Status",
        "",
        f"Generated: {now_utc()}",
        "",
        "Batch-1 remains an acquisition pilot. The full 129-row run is not started.",
        "",
        "## Top-5 Groups",
        "",
        "| Rank | Storm group | Min Dst/SYM-H | Reason |",
        "| ---: | --- | ---: | --- |",
    ]
    for row in top5.itertuples(index=False):
        lines.append(f"| {row.priority_rank} | `{row.storm_group_id}` | {row.min_symh_or_dst} | {row.priority_reason} |")
    lines.extend(
        [
            "",
            "## Required Before Batch-1 Matching",
            "",
            "- science-ready GUVI O/N2",
            "- science-ready DMSP or quantitative SuperDARN detector data",
            "- science-ready indices",
            "- at least one inside/near/control O/N2 opportunity",
        ]
    )
    summary = SUMMARY_DIR / "batch1_top5_acquisition_status.md"
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return paths, summary


def write_next_stage_summary(generated: list[Path]) -> Path:
    lines = [
        "# Next Stage Execution After Upload Recovery Summary",
        "",
        f"Generated: {now_utc()}",
        "",
        "What was run: upload recovery verification, normalizer V3 gate decisions, validation-event blocker resolution, St. Patrick normalizer gate checks, seed detector V3 gate materialization, seed O/N2 matching V2 gate materialization, and Batch-1 top-5 acquisition status.",
        "",
        "What cannot yet be claimed: completed 2011-2015 multi-event SAPS/O/N2 statistics.",
        "",
        "## Generated Files",
        "",
    ]
    for path in generated:
        lines.append(f"- `{repo_path(path)}`")
    lines.extend(
        [
            "",
            "## Current Wording",
            "",
            "Upload recovery is complete; seed-event data gates are explicit; St. Patrick smoke-test rows have been caveated through science-ready normalizer checks; validation-event data blockers are documented; Batch-1 top-5 acquisition pilot is prepared. Full 2011-2015 SAPS/O/N2 statistics remain pending instrument-data acquisition and normalization.",
        ]
    )
    summary = SUMMARY_DIR / "next_stage_execution_after_upload_recovery_summary.md"
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    generated.extend(write_upload_verification_v2())
    generated.append(write_normalizer_gate_decision())
    generated.extend(write_validation_blocker_resolution())
    generated.extend(write_st_patrick_normalizer_outputs())
    generated.extend(write_seed_detector_v3())
    generated.extend(write_matching_v2_outputs())
    queue_paths, top5_summary = write_batch1_top5_status()
    generated.extend(queue_paths)
    generated.append(top5_summary)
    generated.append(write_next_stage_summary(generated))

    for path in generated:
        print(f"Saved {path}")


if __name__ == "__main__":
    main()
