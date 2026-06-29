# Action Plan Web Quicklook

Date: 2026-06-29

Basis:

- `docs_index/codex_action_plan_after_20260628_status.md`
- plan commit: `8bddb139b44b923c56e827ebc2c66f3f197a2d89`

## Current Status

The project is still at:

```text
2015-03-16 to 2015-03-18 St. Patrick storm smoke test
not yet 2011-2015 multi-event SAPS/O/N2 statistics
```

This update executes the next action-plan layer without claiming final statistics.

## What Changed

| Task | Status | Main output |
| --- | --- | --- |
| 1. Reconcile inventory vs availability | completed | `data_samples/screening_outputs/event_data_availability_reconciled.csv` |
| 2. Refine normalizer status schema | completed | `data_work/normalized/normalizer_status_all_events_v2.csv` |
| 3. Seed-event data acquisition queues | completed | `docs_index/download_queue_seed_events_*.csv` |
| 4. Normalize seed-event instruments | partial | geomagnetic indices normalized; other instruments blocked by missing raw files |
| 5. SuperDARN detector validation | blocked explicitly | no quantitative SuperDARN map/fit/grid data for validation events |
| 6. DMSP detector validation | smoke-test partial | 2015-03-17/18 candidates retained; 2014-02-19 blocked pending DMSP data |
| 7. Seed SAPS channel objects | completed as smoke-test + no-data rows | validation events retained as rejected/no-data rows |
| 8. Seed O/N2 opportunity database | completed as smoke-test + no-data rows | validation events retained as O/N2 download-queue-only |
| 9. Seed SAPS/O/N2 matching | completed as smoke-test + no-data rows | validation events retained in nonmatch selection function |
| 10. Batch-1 major-storm preparation | completed | `data_samples/screening_outputs/event_universe_2011_2015_batch1_major.csv` |

## Key Numbers

| Artifact | Rows |
| --- | ---: |
| Reconciled seed availability | 6 |
| Normalizer v2 status | 415 |
| Seed SuperDARN validation table | 3 |
| Seed DMSP crossing table | 27 |
| Seed SAPS channel objects | 29 |
| Seed O/N2 opportunities | 29 |
| Seed SAPS/O/N2 match candidates | 29 |
| Seed nonmatch selection rows | 23 |
| Batch-1 major-storm event rows | 129 |

## Main Finding

The earlier apparent contradiction is resolved:

```text
validation events had local manifest rows,
but non-index rows were missing placeholders / download-queue rows,
not local science-ready raw files.
```

The three validation events now remain explicitly data-limited:

| Event | Reconciled state |
| --- | --- |
| 2014-02-19 | `G_missing_or_unusable_with_explicit_reason` |
| 2011-10-25 | `G_missing_or_unusable_with_explicit_reason` |
| 2013-06-30 | `G_missing_or_unusable_with_explicit_reason` |

## Web Entry Files

- `summaries/screening_outputs/next_phase_progress_after_20260628.md`
- `summaries/screening_outputs/inventory_availability_reconciliation_20260629.md`
- `summaries/screening_outputs/normalizer_status_v2_summary.md`
- `summaries/screening_outputs/seed_event_data_acquisition_status.md`
- `summaries/screening_outputs/batch1_major_storm_data_readiness.md`
- `docs_index/action_plan_output_manifest_20260629.csv`

## Cannot Yet Claim

- Completed 2011-2015 multi-event SAPS/O/N2 statistics.
- Quantitative SuperDARN SAPS detector validation for the three thesis-inspired events.
- Final seed-event O/N2 response statistics for validation events.
- Full 737-row 2011-2015 statistical run.
