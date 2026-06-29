# Seed And Batch Readiness Quicklook - 2026-06-29

This quicklook records the next execution step after the 2026-06-28/29 action-plan updates. It keeps the current work explicitly in the readiness and detector-validation stage, not in the final 2011-2015 SAPS/O/N2 statistics stage.

## Current Status

- The 2015-03-16 to 2015-03-18 St. Patrick interval remains the only smoke-test interval with local SAPS/O/N2 matching outputs.
- The thesis-inspired validation events 2014-02-19, 2011-10-25, and 2013-06-30 are still `download_queue_only` for GUVI O/N2, DMSP SSIES, SuperDARN, and SSUSI.
- The 2011-2015 Batch-1 major-storm subset has been prepared as a data-acquisition target, but no Batch-1-wide instrument normalization or science matching has been executed.

## New Machine-Readable Outputs

| File | Purpose |
| --- | --- |
| `summaries/screening_outputs/seed_and_batch_readiness_metrics_20260629.md` | Human-readable metric report for seed events and Batch-1 readiness. |
| `data_samples/screening_outputs/seed_event_readiness_metrics_20260629.csv` | Seed-event readiness counters requested by the latest execution note. |
| `data_samples/screening_outputs/batch1_major_readiness_metrics_20260629.csv` | Batch-1 major-storm data-readiness counters. |
| `data_samples/screening_outputs/seed_detector_validation_gates_20260629.csv` | Per-event DMSP, SuperDARN, O/N2, and matching gate states. |
| `docs_index/seed_event_acquisition_execution_matrix_20260629.csv` | Per-event and per-instrument acquisition matrix with expected patterns, target folders, and next actions. |

## Key Counters

| Metric | Value |
| --- | ---: |
| `N_seed_events_checked` | 6 |
| `N_seed_events_with_SAPS_channel` | 2 |
| `N_seed_events_with_GUVI_ON2` | 2 |
| `N_seed_events_with_SAPS_and_ON2_0_1h` | 1 |
| `N_seed_events_with_SAPS_and_ON2_1_3h` | 2 |
| `N_seed_events_with_SAPS_and_ON2_3_6h` | 0 |
| `N_rejected_due_to_no_SuperDARN_echo_or_quantitative_data` | 3 |
| `N_rejected_due_to_missing_DMSP` | 3 |
| `N_batch1_major_event_rows` | 129 |
| `N_batch1_storm_groups` | 22 |
| `N_batch1_science_ready` | 0 |
| `N_batch1_SAPS_ON2_matches` | 0 |

## Execution Decision

Do not start the 737-row 2011-2015 full statistical run from this state. The next scientific unlock is still to acquire or link seed-event instrument files for:

- 2014-02-19
- 2011-10-25
- 2013-06-30

After those files are present, rerun the data reconciliation, normalizer status, detector validation gates, seed SAPS/O/N2 matching, and only then promote Batch-1 major storms toward science matching.
