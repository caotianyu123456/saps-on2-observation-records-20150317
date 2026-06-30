# Normalizer V3 Gate Decision Table

Generated: 2026-06-30T09:13:40+00:00

Primary input: `data_work/normalized/normalizer_status_all_events_v3.csv`.

## Overall Gate Counts

| Gate category | Rows |
| --- | ---: |
| `blocked_by_download_queue` | 12 |
| `blocked_by_missing_required_variable` | 25 |
| `blocked_by_no_dayglow_or_no_on2` | 7 |
| `blocked_by_no_quantitative_superdarn` | 101 |
| `blocked_by_unmaterialized_ssusi_boundary` | 249 |
| `science_ready` | 21 |

## Allowed Scope Counts

| Scope | Rows |
| --- | ---: |
| `blocked` | 12 |
| `science_ready` | 21 |
| `smoke_test_only` | 382 |

## By Data Group

| Gate category | Data group | Rows |
| --- | --- | ---: |
| `blocked_by_download_queue` | `dmsp_ssies` | 3 |
| `blocked_by_download_queue` | `guvi_on2` | 3 |
| `blocked_by_download_queue` | `ssusi` | 3 |
| `blocked_by_download_queue` | `superdarn` | 3 |
| `blocked_by_missing_required_variable` | `dmsp_ssies` | 25 |
| `blocked_by_no_dayglow_or_no_on2` | `guvi_on2` | 7 |
| `blocked_by_no_quantitative_superdarn` | `superdarn` | 101 |
| `blocked_by_unmaterialized_ssusi_boundary` | `ssusi` | 249 |
| `science_ready` | `indices` | 21 |

## Detector/Matching Rule

- `science_ready` scope rows may feed science logic.
- `smoke_test_only` scope rows may feed St. Patrick pipeline checks, but not final 2011-2015 statistics.
- `blocked` scope rows must remain explicit caveats or no-data rows.
