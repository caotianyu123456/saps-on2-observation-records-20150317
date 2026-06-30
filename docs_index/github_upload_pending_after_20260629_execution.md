# GitHub Upload Pending After 2026-06-29 Execution

Generated locally during the 2026-06-30 next-stage execution pass.

The next-stage execution package was generated locally, but GitHub upload did not complete because the GitHub connector returned a transport error while attempting to create `docs_index/next_stage_after_20260629_web_quicklook.md`.

Observed connector error:

```text
Transport send error ... HTTP request failed ... error sending request for url (https://chatgpt.com/backend-api/ps/mcp)
```

Local fallback checks:

- `git`: not available in PATH
- `gh`: not available in PATH
- `GITHUB_TOKEN`: not present
- `GH_TOKEN`: not present

Upload these files when the GitHub connector is available again:

- `docs_index/next_stage_after_20260629_web_quicklook.md`
- `docs_index/next_stage_after_20260629_output_manifest.csv`
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
- `scripts/materialize_seed_download_instructions.py`
- `scripts/link_local_raw_files_from_manifest.py`
- `scripts/rank_batch1_major_storms_for_download.py`
- `scripts/materialize_next_stage_after_20260629.py`

Current scientific status remains unchanged by the upload failure: this is a data acquisition and science-ready gate package, not a completed 2011-2015 SAPS/O/N2 statistical run.
