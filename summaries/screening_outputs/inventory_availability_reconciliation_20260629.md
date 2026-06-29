# Inventory / Availability Reconciliation

Generated: 2026-06-29T08:15:43+00:00

Basis: `docs_index/codex_action_plan_after_20260628_status.md` task 1.

Current science status: St. Patrick smoke-test and data-layer preparation only; not completed 2011-2015 SAPS/O/N2 statistics.

## Main Finding

The apparent contradiction is explained by placeholder rows in `docs_index/data_manifest_local.csv`: validation-event non-index instrument groups have local manifest rows, but those rows have no `file_name` and `parse_status=missing`. They are download-queue placeholders, not local science-ready files.

## Reconciled Event Readiness

| Event | V1 readiness | Reconciled readiness | GUVI | DMSP | SuperDARN | SSUSI | Indices | Blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2015-03-16 `available_20150316` | `E_ON2_available_no_SAPS_data` | `E_ON2_available_no_SAPS_data` | `raw_file_present_missing_variables` | `raw_file_present_missing_variables` | `raw_file_present_missing_variables` | `raw_file_present_missing_variables` | `parsed_ok_science_ready` | SAPS detector data |
| 2015-03-17 `available_20150317` | `A_ready_for_full_SAPS_ON2_matching` | `A_ready_for_full_SAPS_ON2_matching` | `raw_file_present_not_parsed` | `raw_file_present_missing_variables` | `raw_file_present_missing_variables` | `raw_file_present_missing_variables` | `parsed_ok_science_ready` | none |
| 2015-03-18 `available_20150318` | `A_ready_for_full_SAPS_ON2_matching` | `A_ready_for_full_SAPS_ON2_matching` | `raw_file_present_missing_variables` | `raw_file_present_missing_variables` | `raw_file_present_missing_variables` | `raw_file_present_missing_variables` | `parsed_ok_science_ready` | none |
| 2014-02-19 `validation_20140219` | `F_indices_only` | `G_missing_or_unusable_with_explicit_reason` | `download_queue_only` | `download_queue_only` | `download_queue_only` | `download_queue_only` | `parsed_ok_science_ready` | GUVI O/N2; SAPS detector data |
| 2011-10-25 `validation_20111025` | `F_indices_only` | `G_missing_or_unusable_with_explicit_reason` | `download_queue_only` | `download_queue_only` | `download_queue_only` | `download_queue_only` | `parsed_ok_science_ready` | GUVI O/N2; SAPS detector data |
| 2013-06-30 `validation_20130630` | `F_indices_only` | `G_missing_or_unusable_with_explicit_reason` | `download_queue_only` | `download_queue_only` | `download_queue_only` | `download_queue_only` | `parsed_ok_science_ready` | GUVI O/N2; SAPS detector data |

## Inventory State Counts

- `download_queue_only`: 12
- `parsed_ok_science_ready`: 6
- `raw_file_present_missing_variables`: 11
- `raw_file_present_not_parsed`: 1

## Required Follow-Up

- Do not treat `download_queue_only` rows as raw files.
- Do not call validation events science-ready until GUVI O/N2 and SAPS detector data are acquired or linked and parsed.
- Use `data_samples/screening_outputs/event_data_availability_reconciled.csv` for next-step gating.
