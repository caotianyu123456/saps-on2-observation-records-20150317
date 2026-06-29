# Seed And Batch Readiness Metrics

Generated: 2026-06-29T10:35:38+00:00

Basis: latest GitHub action plan and 2026-06-29 quicklook. This report records measurable next-stage readiness without claiming completed 2011-2015 statistics.

## Seed Metrics

| Metric | Value | Interpretation |
| --- | ---: | --- |
| `N_seed_events_checked` | 6 | All seed events in reconciled availability table. |
| `N_seed_events_with_SAPS_channel` | 2 | Events with non-rejected seed SAPS channel object rows; currently smoke-test only. |
| `N_seed_events_with_GUVI_ON2` | 2 | Events with n_on2_valid > 0 in seed O/N2 opportunity table. |
| `N_seed_events_with_SAPS_and_ON2_0_1h` | 1 | Events with recommended 0-1 h SAPS/O/N2 matches. |
| `N_seed_events_with_SAPS_and_ON2_1_3h` | 2 | Events with recommended 1-3 h SAPS/O/N2 matches. |
| `N_seed_events_with_SAPS_and_ON2_3_6h` | 0 | Events with recommended 3-6 h SAPS/O/N2 matches. |
| `N_seed_events_with_SAPS_no_ON2` | 0 | No validation SAPS channel is currently confirmed without O/N2; validation events are instrument-missing. |
| `N_ON2_opportunity_no_SAPS` | 1 | Events with O/N2 available but SAPS detector data unavailable. |
| `N_rejected_due_to_no_SuperDARN_echo_or_quantitative_data` | 3 | Rejected/no-data SuperDARN validation rows. |
| `N_rejected_due_to_missing_DMSP` | 3 | Seed events whose DMSP state is download_queue_only. |

## Batch-1 Metrics

| Metric | Value | Interpretation |
| --- | ---: | --- |
| `N_batch1_major_event_rows` | 129 | Batch-1 rows selected by min(Dst) <= -100 nT. |
| `N_batch1_storm_groups` | 22 | Unique storm groups in Batch-1. |
| `N_batch1_with_GUVI` | 0 | No Batch-1-wide GUVI instrument acquisition has been verified yet; queues exist. |
| `N_batch1_with_DMSP` | 0 | No Batch-1-wide DMSP instrument acquisition has been verified yet; queues exist. |
| `N_batch1_with_SuperDARN` | 0 | No Batch-1-wide quantitative SuperDARN acquisition has been verified yet; queues exist. |
| `N_batch1_science_ready` | 0 | Batch-1 science matching is blocked until instrument data are acquired and normalized. |
| `N_batch1_SAPS_ON2_matches` | 0 | No Batch-1 SAPS/O/N2 matching run has been executed. |
| `N_batch1_GUVI_queue_rows` | 129 | Batch-1 GUVI download queue rows. |
| `N_batch1_DMSP_queue_rows` | 129 | Batch-1 DMSP download queue rows. |
| `N_batch1_SuperDARN_queue_rows` | 129 | Batch-1 SuperDARN download queue rows. |
| `N_batch1_SSUSI_queue_rows` | 129 | Batch-1 SSUSI download queue rows. |
| `N_batch1_indices_queue_rows` | 129 | Batch-1 indices queue/status rows. |
| `N_seed_smoke_test_matches_available_for_reference` | 26 | Existing 2015 smoke-test recommended match rows, not Batch-1 statistics. |

## Detector Gates

| Event | DMSP | SuperDARN | O/N2 | Matching |
| --- | --- | --- | --- | --- |
| 2015-03-16 `available_20150316` | `partial_or_missing_required_variables` | `partial_or_missing_required_variables` | `partial_or_missing_required_variables` | `on2_nonmatch_only_until_saps_data` |
| 2015-03-17 `available_20150317` | `partial_or_missing_required_variables` | `partial_or_missing_required_variables` | `raw_present_normalizer_pending` | `smoke_test_matching_available_not_final` |
| 2015-03-18 `available_20150318` | `partial_or_missing_required_variables` | `partial_or_missing_required_variables` | `partial_or_missing_required_variables` | `smoke_test_matching_available_not_final` |
| 2014-02-19 `validation_20140219` | `blocked_download_queue_only` | `blocked_download_queue_only` | `blocked_download_queue_only` | `blocked_missing_instrument_data` |
| 2011-10-25 `validation_20111025` | `blocked_download_queue_only` | `blocked_download_queue_only` | `blocked_download_queue_only` | `blocked_missing_instrument_data` |
| 2013-06-30 `validation_20130630` | `blocked_download_queue_only` | `blocked_download_queue_only` | `blocked_download_queue_only` | `blocked_missing_instrument_data` |

## Next Action

The next real unlock remains data acquisition/linking for 2014-02-19, 2011-10-25, and 2013-06-30. Until those instrument files exist locally and parse successfully, detector validation rows must remain explicit blocked/rejected rows.
