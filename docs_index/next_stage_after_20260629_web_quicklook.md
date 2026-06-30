# Next Stage After 2026-06-29 Results Quicklook

Generated: 2026-06-30T08:05:51+00:00

This package executes the next-stage plan after the 2026-06-29 readiness results. It keeps the project in data acquisition, normalizer hardening, detector-gate, and Batch-1 acquisition-pilot mode.

## Current Decision

Do not run final 2011-2015 statistics from the present state. The seed validation events still need instrument files, and Batch-1 is only prioritized for top-5 acquisition.

## Key Counts

- Seed missing/blocking rows: 12
- Batch-1 readiness rows: 129
- Ranked Batch-1 storm groups: 22

## Main Outputs

- `docs_index/seed_event_download_instructions.md`
- `docs_index/seed_event_manual_download_checklist.csv`
- `docs_index/seed_event_remote_availability.csv`
- `docs_index/data_manifest_seed_events_required.csv`
- `docs_index/data_manifest_seed_events_linked.csv`
- `docs_index/data_manifest_seed_events_missing.csv`
- `summaries/screening_outputs/seed_event_download_blockers.md`
- `docs_index/batch1_major_storm_group_priority.csv`
- `docs_index/download_queue_batch1_priority_top5_guvi.csv`
- `docs_index/download_queue_batch1_priority_top5_dmsp.csv`
- `docs_index/download_queue_batch1_priority_top5_superdarn.csv`
- `docs_index/download_queue_batch1_priority_top5_ssusi.csv`
- `summaries/screening_outputs/batch1_major_storm_download_priority.md`
- `data_work/normalized/normalizer_status_all_events_v3.csv`
- `data_samples/screening_outputs/st_patrick_normalizer_science_ready_caveats.csv`
- `summaries/screening_outputs/normalizer_status_v3_summary.md`
- `data_samples/screening_outputs/dmsp_saps_crossings_seed_events_v2.csv`
- `data_samples/screening_outputs/superdarn_saps_channels_seed_events_v2.csv`
- `data_samples/screening_outputs/saps_channel_objects_seed_events_v2.csv`
- `summaries/screening_outputs/seed_detector_v2_gate_summary.md`
- `data_samples/screening_outputs/on2_opportunity_seed_events_science_ready.csv`
- `data_samples/screening_outputs/guvi_on2_patches_seed_events_science_ready.csv`
- `data_samples/screening_outputs/saps_on2_match_candidates_seed_events_science_ready.csv`
- `data_samples/screening_outputs/dmsp_crossing_relative_on2_profiles_seed_events_science_ready.csv`
- `data_samples/screening_outputs/nonmatch_selection_function_seed_events_science_ready.csv`
- `summaries/screening_outputs/seed_event_science_ready_summary.md`
- `data_samples/screening_outputs/batch1_major_storm_data_availability_v2.csv`
- `data_work/normalized/normalizer_status_batch1_major_v1.csv`
- `summaries/screening_outputs/batch1_major_storm_data_readiness_v2.md`
- `docs_index/next_stage_after_20260629_output_manifest.csv`

## Next Unlock

Acquire or link GUVI, DMSP, quantitative SuperDARN, and SSUSI data for 2014-02-19, 2011-10-25, and 2013-06-30; then rerun this package and promote only passing rows to detector validation.
