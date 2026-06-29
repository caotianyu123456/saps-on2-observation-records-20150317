# Normalizer Status V2 Summary

Generated: 2026-06-29T08:17:58+00:00

Basis: `docs_index/codex_action_plan_after_20260628_status.md` task 2.

Current science status: v2 status refines data readiness; it does not claim completed 2011-2015 SAPS/O/N2 statistics.

## Status Counts

- `download_queue_only`: 12
- `missing_required_variable`: 379
- `parsed_ok_no_dayglow_on2`: 3
- `parsed_ok_science_ready`: 21

## Generic Status Check

- `parsed_with_nonblocking_warnings`: 0 rows (0.0%)
- Acceptance target: fewer than 10% generic rows.

## Interpretation

- `parsed_ok_science_ready` currently applies to local geomagnetic index CSV rows only.
- `download_queue_only` rows are placeholders and must not be treated as local raw files.
- `missing_required_variable` is used for partial event-window coverage or missing science variables needed by a reusable normalizer.
- `unsupported_format` currently marks SuperDARN quick-look PNGs: useful context, but not quantitative vector input.
- GUVI/DMSP/SSUSI raw files remain data-present but not final science-ready until dayglow, geometry, boundary, and coordinate fields are materialized.
