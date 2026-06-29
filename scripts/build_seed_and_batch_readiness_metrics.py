from __future__ import annotations

from pathlib import Path

import pandas as pd

from data_acquisition_common import DOCS_DIR, OUTPUT_DIR, SUMMARY_DIR, now_utc


ROOT = Path(__file__).resolve().parents[1]
VALIDATION_EVENT_IDS = {
    "validation_20140219",
    "validation_20111025",
    "validation_20130630",
}
DATA_GROUPS = ["guvi_on2", "dmsp_ssies", "superdarn", "ssusi", "indices"]


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


def true_count(frame: pd.DataFrame, column: str) -> int:
    if frame.empty:
        return 0
    return int(bool_series(frame, column).sum())


def valid_events(frame: pd.DataFrame, event_col: str = "event_id") -> set[str]:
    if frame.empty or event_col not in frame.columns:
        return set()
    return set(frame[event_col].dropna().astype(str))


def events_with_nonrejected_channels(channels: pd.DataFrame) -> set[str]:
    if channels.empty or "event_id" not in channels.columns:
        return set()
    grade = channels.get("saps_grade", pd.Series([""] * len(channels))).astype(str).str.lower()
    pathway = channels.get("source_pathway", pd.Series([""] * len(channels))).astype(str).str.lower()
    mask = (grade != "rejected") & (pathway != "no_data")
    return set(channels.loc[mask, "event_id"].astype(str))


def events_with_valid_on2(on2: pd.DataFrame) -> set[str]:
    if on2.empty or "event_id" not in on2.columns:
        return set()
    n_valid = pd.to_numeric(on2.get("n_on2_valid", 0), errors="coerce").fillna(0)
    return set(on2.loc[n_valid > 0, "event_id"].astype(str))


def events_with_matches(matches: pd.DataFrame, pattern: str) -> set[str]:
    if matches.empty or "event_id" not in matches.columns or "lag_bin" not in matches.columns:
        return set()
    recommended = bool_series(matches, "recommended_for_statistics")
    mask = recommended & matches["lag_bin"].astype(str).str.contains(pattern, case=False, na=False)
    return set(matches.loc[mask, "event_id"].astype(str))


def write_metric_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


def build_seed_metrics() -> pd.DataFrame:
    availability = read_csv(OUTPUT_DIR / "event_data_availability_reconciled.csv")
    channels = read_csv(OUTPUT_DIR / "saps_channel_objects_seed_events.csv")
    on2 = read_csv(OUTPUT_DIR / "on2_opportunity_seed_events.csv")
    matches = read_csv(OUTPUT_DIR / "saps_on2_match_candidates_seed_events.csv")
    superdarn = read_csv(OUTPUT_DIR / "superdarn_saps_channels_seed_events.csv")

    all_seed_events = valid_events(availability)
    saps_events = events_with_nonrejected_channels(channels)
    on2_events = events_with_valid_on2(on2)
    match_0_1 = events_with_matches(matches, "0_1h|0-1")
    match_1_3 = events_with_matches(matches, "1_3h|1-3")
    match_3_6 = events_with_matches(matches, "3_6h|3-6")

    on2_no_saps = set()
    if not availability.empty:
        on2_mask = availability["ready_class_reconciled"].astype(str).str.contains("ON2_available_no_SAPS", na=False)
        on2_no_saps = set(availability.loc[on2_mask, "event_id"].astype(str))

    superdarn_rejected = 0
    if not superdarn.empty:
        caveat = superdarn.get("failure_or_caveat", pd.Series([""] * len(superdarn))).astype(str)
        superdarn_rejected = int(caveat.str.contains("download_queue_only|no_quantitative_superdarn|insufficient_echo", case=False, na=False).sum())

    missing_dmsp = 0
    if not availability.empty and "dmsp_ssies_state" in availability.columns:
        missing_dmsp = int(availability["dmsp_ssies_state"].astype(str).eq("download_queue_only").sum())

    metrics = [
        ("N_seed_events_checked", len(all_seed_events), "All seed events in reconciled availability table."),
        ("N_seed_events_with_SAPS_channel", len(saps_events), "Events with non-rejected seed SAPS channel object rows; currently smoke-test only."),
        ("N_seed_events_with_GUVI_ON2", len(on2_events), "Events with n_on2_valid > 0 in seed O/N2 opportunity table."),
        ("N_seed_events_with_SAPS_and_ON2_0_1h", len(match_0_1), "Events with recommended 0-1 h SAPS/O/N2 matches."),
        ("N_seed_events_with_SAPS_and_ON2_1_3h", len(match_1_3), "Events with recommended 1-3 h SAPS/O/N2 matches."),
        ("N_seed_events_with_SAPS_and_ON2_3_6h", len(match_3_6), "Events with recommended 3-6 h SAPS/O/N2 matches."),
        ("N_seed_events_with_SAPS_no_ON2", 0, "No validation SAPS channel is currently confirmed without O/N2; validation events are instrument-missing."),
        ("N_ON2_opportunity_no_SAPS", len(on2_no_saps), "Events with O/N2 available but SAPS detector data unavailable."),
        ("N_rejected_due_to_no_SuperDARN_echo_or_quantitative_data", superdarn_rejected, "Rejected/no-data SuperDARN validation rows."),
        ("N_rejected_due_to_missing_DMSP", missing_dmsp, "Seed events whose DMSP state is download_queue_only."),
    ]
    return pd.DataFrame(
        [
            {
                "metric": name,
                "value": value,
                "interpretation": note,
                "last_run_utc": now_utc(),
            }
            for name, value, note in metrics
        ]
    )


def build_batch1_metrics() -> pd.DataFrame:
    batch = read_csv(OUTPUT_DIR / "event_universe_2011_2015_batch1_major.csv")
    matches = read_csv(OUTPUT_DIR / "saps_on2_match_candidates_seed_events.csv")
    queue_counts = {}
    for name in ["guvi", "dmsp", "superdarn", "ssusi", "indices"]:
        queue = read_csv(DOCS_DIR / f"download_queue_{name}_2011_2015_batch1_major.csv")
        queue_counts[name] = len(queue)

    rows = [
        ("N_batch1_major_event_rows", len(batch), "Batch-1 rows selected by min(Dst) <= -100 nT."),
        (
            "N_batch1_storm_groups",
            int(batch["storm_group_id"].nunique()) if not batch.empty and "storm_group_id" in batch.columns else 0,
            "Unique storm groups in Batch-1.",
        ),
        ("N_batch1_with_GUVI", 0, "No Batch-1-wide GUVI instrument acquisition has been verified yet; queues exist."),
        ("N_batch1_with_DMSP", 0, "No Batch-1-wide DMSP instrument acquisition has been verified yet; queues exist."),
        ("N_batch1_with_SuperDARN", 0, "No Batch-1-wide quantitative SuperDARN acquisition has been verified yet; queues exist."),
        ("N_batch1_science_ready", 0, "Batch-1 science matching is blocked until instrument data are acquired and normalized."),
        ("N_batch1_SAPS_ON2_matches", 0, "No Batch-1 SAPS/O/N2 matching run has been executed."),
        ("N_batch1_GUVI_queue_rows", queue_counts["guvi"], "Batch-1 GUVI download queue rows."),
        ("N_batch1_DMSP_queue_rows", queue_counts["dmsp"], "Batch-1 DMSP download queue rows."),
        ("N_batch1_SuperDARN_queue_rows", queue_counts["superdarn"], "Batch-1 SuperDARN download queue rows."),
        ("N_batch1_SSUSI_queue_rows", queue_counts["ssusi"], "Batch-1 SSUSI download queue rows."),
        ("N_batch1_indices_queue_rows", queue_counts["indices"], "Batch-1 indices queue/status rows."),
        (
            "N_seed_smoke_test_matches_available_for_reference",
            true_count(matches, "recommended_for_statistics"),
            "Existing 2015 smoke-test recommended match rows, not Batch-1 statistics.",
        ),
    ]
    return pd.DataFrame(
        [
            {
                "metric": name,
                "value": value,
                "interpretation": note,
                "last_run_utc": now_utc(),
            }
            for name, value, note in rows
        ]
    )


def build_acquisition_matrix() -> pd.DataFrame:
    availability = read_csv(OUTPUT_DIR / "event_data_availability_reconciled.csv")
    queue_by_group = {
        "guvi_on2": read_csv(DOCS_DIR / "download_queue_seed_events_guvi.csv"),
        "dmsp_ssies": read_csv(DOCS_DIR / "download_queue_seed_events_dmsp.csv"),
        "superdarn": read_csv(DOCS_DIR / "download_queue_seed_events_superdarn.csv"),
        "ssusi": read_csv(DOCS_DIR / "download_queue_seed_events_ssusi.csv"),
        "indices": read_csv(DOCS_DIR / "download_queue_seed_events_indices.csv"),
    }
    rows = []
    if availability.empty:
        return pd.DataFrame()
    for event in availability.itertuples(index=False):
        for group in DATA_GROUPS:
            state = getattr(event, f"{group}_state", "not_required")
            queue = queue_by_group[group]
            qrow = queue[queue["event_id"].astype(str) == str(event.event_id)] if not queue.empty and "event_id" in queue.columns else pd.DataFrame()
            queue_status = qrow.iloc[0].get("queue_status", "") if not qrow.empty else ""
            priority_window = ""
            expected = ""
            target = ""
            source = ""
            if not qrow.empty:
                priority_window = f"{qrow.iloc[0].get('priority_window_start_ut', '')} to {qrow.iloc[0].get('priority_window_end_ut', '')}"
                expected = qrow.iloc[0].get("expected_file_pattern", "")
                target = qrow.iloc[0].get("local_target_dir", "")
                source = qrow.iloc[0].get("remote_source_hint", "")
            blocking = group in {"guvi_on2", "dmsp_ssies", "superdarn"} and state in {"download_queue_only", "file_missing"}
            rows.append(
                {
                    "event_id": event.event_id,
                    "event_date": event.event_date,
                    "data_group": group,
                    "current_state": state,
                    "queue_status": queue_status,
                    "priority_window_ut": priority_window,
                    "expected_file_pattern": expected,
                    "local_target_dir": target,
                    "remote_source_hint": source,
                    "blocking_for_detector_or_matching": blocking,
                    "next_action": next_action_for_state(group, state),
                }
            )
    return pd.DataFrame(rows)


def next_action_for_state(group: str, state: str) -> str:
    if state == "parsed_ok_science_ready":
        return "Use for storm/substorm tagging."
    if state == "download_queue_only":
        return "Acquire or link files from seed-event queue, then rerun reconciliation and normalizer."
    if state == "raw_file_present_missing_variables":
        return "Complete missing event-window coverage or required variables, then rerun normalizer."
    if state == "raw_file_present_not_parsed":
        return f"Run/finish {group} reusable normalizer and science-quality checks."
    return "Inspect file state and update manifest."


def build_detector_gates() -> pd.DataFrame:
    availability = read_csv(OUTPUT_DIR / "event_data_availability_reconciled.csv")
    rows = []
    if availability.empty:
        return pd.DataFrame()
    for event in availability.itertuples(index=False):
        rows.append(
            {
                "event_id": event.event_id,
                "event_date": event.event_date,
                "dmsp_detector_gate": gate_status(event.dmsp_ssies_state, "dmsp"),
                "superdarn_detector_gate": gate_status(event.superdarn_state, "superdarn"),
                "on2_opportunity_gate": gate_status(event.guvi_on2_state, "guvi"),
                "seed_matching_gate": matching_gate(event),
                "gate_note": gate_note(event),
            }
        )
    return pd.DataFrame(rows)


def gate_status(state: str, group: str) -> str:
    if state == "download_queue_only":
        return "blocked_download_queue_only"
    if state == "parsed_ok_science_ready":
        return "ready"
    if state == "raw_file_present_not_parsed":
        return "raw_present_normalizer_pending"
    if state == "raw_file_present_missing_variables":
        return "partial_or_missing_required_variables"
    return "not_ready"


def matching_gate(event: object) -> str:
    ready_class = str(getattr(event, "ready_class_reconciled", ""))
    if ready_class == "A_ready_for_full_SAPS_ON2_matching":
        return "smoke_test_matching_available_not_final"
    if "ON2_available_no_SAPS" in ready_class:
        return "on2_nonmatch_only_until_saps_data"
    if "missing" in ready_class or "unusable" in ready_class:
        return "blocked_missing_instrument_data"
    return "not_ready"


def gate_note(event: object) -> str:
    if str(event.event_id) in VALIDATION_EVENT_IDS:
        return "Thesis-inspired validation event; must acquire GUVI and SAPS detector data before detector validation."
    return "St. Patrick smoke-test seed event; useful for pipeline validation but not multi-year statistics."


def write_summary(seed: pd.DataFrame, batch: pd.DataFrame, gates: pd.DataFrame) -> Path:
    lines = [
        "# Seed And Batch Readiness Metrics",
        "",
        f"Generated: {now_utc()}",
        "",
        "Basis: latest GitHub action plan and 2026-06-29 quicklook. This report records measurable next-stage readiness without claiming completed 2011-2015 statistics.",
        "",
        "## Seed Metrics",
        "",
        "| Metric | Value | Interpretation |",
        "| --- | ---: | --- |",
    ]
    for row in seed.itertuples(index=False):
        lines.append(f"| `{row.metric}` | {row.value} | {row.interpretation} |")
    lines.extend(["", "## Batch-1 Metrics", "", "| Metric | Value | Interpretation |", "| --- | ---: | --- |"])
    for row in batch.itertuples(index=False):
        lines.append(f"| `{row.metric}` | {row.value} | {row.interpretation} |")
    lines.extend(
        [
            "",
            "## Detector Gates",
            "",
            "| Event | DMSP | SuperDARN | O/N2 | Matching |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in gates.itertuples(index=False):
        lines.append(
            f"| {row.event_date} `{row.event_id}` | `{row.dmsp_detector_gate}` | `{row.superdarn_detector_gate}` | "
            f"`{row.on2_opportunity_gate}` | `{row.seed_matching_gate}` |"
        )
    lines.extend(
        [
            "",
            "## Next Action",
            "",
            "The next real unlock remains data acquisition/linking for 2014-02-19, 2011-10-25, and 2013-06-30. Until those instrument files exist locally and parse successfully, detector validation rows must remain explicit blocked/rejected rows.",
        ]
    )
    path = SUMMARY_DIR / "seed_and_batch_readiness_metrics_20260629.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

    seed = build_seed_metrics()
    batch = build_batch1_metrics()
    acquisition = build_acquisition_matrix()
    gates = build_detector_gates()

    seed_path = OUTPUT_DIR / "seed_event_readiness_metrics_20260629.csv"
    batch_path = OUTPUT_DIR / "batch1_major_readiness_metrics_20260629.csv"
    acquisition_path = DOCS_DIR / "seed_event_acquisition_execution_matrix_20260629.csv"
    gates_path = OUTPUT_DIR / "seed_detector_validation_gates_20260629.csv"

    seed.to_csv(seed_path, index=False)
    batch.to_csv(batch_path, index=False)
    acquisition.to_csv(acquisition_path, index=False)
    gates.to_csv(gates_path, index=False)
    summary = write_summary(seed, batch, gates)

    print(f"Saved {seed_path}")
    print(f"Saved {batch_path}")
    print(f"Saved {acquisition_path}")
    print(f"Saved {gates_path}")
    print(f"Saved {summary}")


if __name__ == "__main__":
    main()
