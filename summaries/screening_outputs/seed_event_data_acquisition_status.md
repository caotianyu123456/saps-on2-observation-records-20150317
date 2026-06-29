# Seed Event Data Acquisition Status

Generated: 2026-06-29T08:21:58+00:00

Basis: `docs_index/codex_action_plan_after_20260628_status.md` task 3.

The three thesis-inspired validation events still do not have local science-ready GUVI/DMSP/SuperDARN/SSUSI instrument data. Their non-index rows are download queues/placeholders, not raw files.

## Validation Event Readiness

| Event | Reconciled readiness | GUVI | DMSP | SuperDARN | SSUSI | Indices |
| --- | --- | --- | --- | --- | --- | --- |
| 2014-02-19 `validation_20140219` | `G_missing_or_unusable_with_explicit_reason` | `download_queue_only` | `download_queue_only` | `download_queue_only` | `download_queue_only` | `parsed_ok_science_ready` |
| 2011-10-25 `validation_20111025` | `G_missing_or_unusable_with_explicit_reason` | `download_queue_only` | `download_queue_only` | `download_queue_only` | `download_queue_only` | `parsed_ok_science_ready` |
| 2013-06-30 `validation_20130630` | `G_missing_or_unusable_with_explicit_reason` | `download_queue_only` | `download_queue_only` | `download_queue_only` | `download_queue_only` | `parsed_ok_science_ready` |

## Queue Files

- `docs_index/download_queue_seed_events_guvi.csv`
- `docs_index/download_queue_seed_events_dmsp.csv`
- `docs_index/download_queue_seed_events_superdarn.csv`
- `docs_index/download_queue_seed_events_ssusi.csv`
- `docs_index/download_queue_seed_events_indices.csv`

## Next Required Data Action

- Acquire or link GUVI L3 O/N2 for event_day_minus_1 through event_day_plus_1.
- Acquire or link DMSP SSIES/SSJ and SSUSI for the 0300-0700 UT priority windows plus context.
- Acquire quantitative SuperDARN map/fit/grid files for detector validation; quick-look images alone are not enough for T-Slope/vector-quality validation.
- Rerun reconciliation and normalizer status after any new files are linked.
