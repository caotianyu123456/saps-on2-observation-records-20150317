# Normalizer Status V3 Summary

Generated: 2026-06-30T08:05:50+00:00

V3 adds science-ready gates required by `docs_index/codex_next_stage_execution_plan_after_20260629_results.md`.

## Status Counts

- `download_queue_only_blocking`: 12
- `parsed_ok_science_ready`: 21
- `raw_or_screening_dmsp_not_science_ready`: 25
- `raw_or_screening_guvi_not_science_ready`: 7
- `ssusi_boundary_support_not_materialized`: 249
- `superdarn_quicklook_or_missing_quantitative_data`: 101

## St. Patrick Caveat

The 2015-03-17/18 smoke-test rows are preserved, but GUVI/DMSP/SuperDARN/SSUSI rows are not promoted to science-ready until dayglow, AACGM/MLT, detector geometry, boundary, and quantitative SuperDARN fields are materialized.
