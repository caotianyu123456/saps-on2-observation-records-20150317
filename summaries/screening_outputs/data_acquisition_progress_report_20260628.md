# Data Acquisition Progress Report

Date: 2026-06-28

Repository target: `caotianyu123456/saps-on2-observation-records-20150317`

Execution basis:

- `docs_index/codex_master_plan_saps_channel_on2_statistical_screening.md`
- `docs_index/codex_data_acquisition_and_event_expansion_plan.md`
- Data-acquisition plan commit: `3cb2b7843c26c286bbb0fead724ed0893a71af4f`
- Master-plan commit: `818cf87acdaa77c03638aa01c6735a6e8feeb8b1`

## Status

The current science products remain a local-data smoke test for 2015-03-16 to 2015-03-18. They should not be described as 2011-2015 multi-event SAPS/O/N2 statistics.

This update implements the data-acquisition layer requested by the newest plan. The goal is to make the GitHub repository show what data exist locally, what is missing, what should be downloaded next, and why the full multi-event statistics are not ready yet.

## Work Completed

1. Synchronized the new data-acquisition plan into the local workspace.
2. Added data manifest generation scripts.
3. Added missing-data and download-queue generation scripts.
4. Added event availability classification for six seed events.
5. Added normalization status scripts under `data_work/normalized/`.
6. Updated screening summaries to state that the current result is a smoke test, not the final 2011-2015 statistics.

## Current Event Readiness

| Event date | Event ID | Current readiness | Main gap |
| --- | --- | --- | --- |
| 2015-03-16 | `available_20150316` | `E_ON2_available_no_SAPS_data` | DMSP/SuperDARN SAPS detector data |
| 2015-03-17 | `available_20150317` | `A_ready_for_full_SAPS_ON2_matching` | none in current local inventory |
| 2015-03-18 | `available_20150318` | `A_ready_for_full_SAPS_ON2_matching` | none in current local inventory |
| 2014-02-19 | `validation_20140219` | `G_missing_or_unusable` | GUVI O/N2, SAPS detector data, geomagnetic indices |
| 2011-10-25 | `validation_20111025` | `G_missing_or_unusable` | GUVI O/N2, SAPS detector data, geomagnetic indices |
| 2013-06-30 | `validation_20130630` | `G_missing_or_unusable` | GUVI O/N2, SAPS detector data, geomagnetic indices |

## Generated Data-Layer Files

| File | Rows | Purpose |
| --- | ---: | --- |
| `docs_index/data_manifest_required.csv` | 30 | Required data by event and data group |
| `docs_index/data_manifest_local.csv` | 400 | Local file inventory across the configured windows |
| `docs_index/data_manifest_missing.csv` | 28 | Structured missing-data rows |
| `docs_index/download_queue_guvi.csv` | 5 | GUVI O/N2 download queue |
| `docs_index/download_queue_dmsp.csv` | 6 | DMSP SSIES download queue |
| `docs_index/download_queue_superdarn.csv` | 6 | SuperDARN download queue |
| `docs_index/download_queue_ssusi.csv` | 6 | SSUSI download queue |
| `docs_index/download_queue_indices.csv` | 5 | geomagnetic-index download queue |
| `docs_index/download_queue_gold.csv` | 6 | future GOLD-branch queue |
| `data_samples/screening_outputs/event_universe.csv` | 6 | expanded seed event universe |
| `data_samples/screening_outputs/event_data_availability.csv` | 6 | readiness classes and blocking gaps |
| `summaries/screening_outputs/data_gap_report.md` | n/a | human-readable data-gap summary |

## New or Updated Scripts

- `scripts/data_acquisition_common.py`
- `scripts/build_event_universe.py`
- `scripts/build_required_data_manifest.py`
- `scripts/inventory_local_data.py`
- `scripts/check_missing_data.py`
- `scripts/prepare_guvi_download_queue.py`
- `scripts/prepare_dmsp_download_queue.py`
- `scripts/prepare_superdarn_download_queue.py`
- `scripts/prepare_ssusi_download_queue.py`
- `scripts/prepare_indices_download_queue.py`
- `scripts/prepare_gold_download_queue.py`
- `scripts/normalize_dmsp_ssies.py`
- `scripts/normalize_guvi_on2.py`
- `scripts/normalize_superdarn.py`
- `scripts/normalize_ssusi.py`
- `scripts/normalize_geomag_indices.py`

## Verification

The data-acquisition scripts were compiled and executed locally. The generated tables and report were checked for row counts and event-readiness classification.

## Next Required Step

Before any 2011-2015 statistical claim, the missing seed-event data must be acquired or linked locally, especially:

- TIMED/GUVI L3 O/N2 for 2014-02-19, 2011-10-25, and 2013-06-30 windows.
- DMSP SSIES/SSJ/SSUSI for the same validation windows.
- SuperDARN quantitative products or quick-look support for the validation windows.
- OMNI/SYM-H/AE/Dst/Kp indices for storm and substorm phase tagging.

After those files are available, rerun:

```text
python scripts/build_event_universe.py
python scripts/check_missing_data.py
python scripts/batch_screen_guvi_dmsp_saps_on2_events.py --events-csv data_samples/screening_outputs/event_catalog_auto_available_dates.csv
python scripts/match_saps_channels_to_on2.py
python scripts/plot_saps_on2_statistics.py
```
