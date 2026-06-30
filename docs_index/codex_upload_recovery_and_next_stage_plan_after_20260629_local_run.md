# Codex Upload Recovery And Next-Stage Plan After 2026-06-29 Local Run

This file records the recovery plan after the 2026-06-30 local next-stage execution pass. The local execution completed, but GitHub write-back was blocked by an unstable or unavailable write channel.

## Current State

```text
local seed-event data-readiness execution completed
upload recovery pending
not completed 2011-2015 multi-event SAPS/O/N2 statistics
```

The current local run generated the next-stage data-readiness package after the 2026-06-29 readiness results. It does not claim completed multi-event science statistics.

## Task 1: Recover GitHub Upload

Upload the following priority files first:

- `docs_index/next_stage_after_20260629_web_quicklook.md`
- `docs_index/next_stage_after_20260629_output_manifest.csv`
- `data_work/normalized/normalizer_status_all_events_v3.csv`
- `docs_index/batch1_major_storm_group_priority.csv`
- `docs_index/github_upload_pending_after_20260629_execution.md`

Then upload the full next-stage package listed in:

- `docs_index/next_stage_after_20260629_upload_verification_manifest.csv`

For each uploaded file, verify:

- GitHub visibility on the default branch
- byte size
- row count for CSV files
- SHA256 match against the local manifest

## Task 2: Use Normalizer V3 As Gatekeeper

Use:

```text
data_work/normalized/normalizer_status_all_events_v3.csv
```

as the next data gatekeeper. A row can feed detector validation or SAPS/O/N2 matching only when its v3 gate permits it. `download_queue_only`, quick-look-only SuperDARN, and screening-level GUVI/DMSP rows must not be promoted to final science statistics.

## Task 3: Resolve Seed Validation Instrument Blockers

Resolve the 12 instrument blocking rows for:

```text
2014-02-19
2011-10-25
2013-06-30
```

Required instrument groups:

- GUVI O/N2
- DMSP SSIES/SSJ
- quantitative SuperDARN map/fit/grid
- SSUSI boundary support

After acquisition or linking, rerun:

```text
python scripts/reconcile_inventory_vs_availability.py
python scripts/build_normalizer_status_all_events.py
python scripts/materialize_next_stage_after_20260629.py
```

## Task 4: Rerun Seed Detector Only On Science-Ready Rows

Use the v2/v3 gate products:

- `data_samples/screening_outputs/dmsp_saps_crossings_seed_events_v2.csv`
- `data_samples/screening_outputs/superdarn_saps_channels_seed_events_v2.csv`
- `data_samples/screening_outputs/saps_channel_objects_seed_events_v2.csv`

Keep explicit no-data / nonmatch rows for:

```text
2014-02-19
2011-10-25
2013-06-30
```

until the required instrument data exist locally and parse successfully.

## Task 5: Execute Batch-1 Top-5 Acquisition Pilot

Use:

```text
docs_index/batch1_major_storm_group_priority.csv
```

and the top-5 download queues:

- `docs_index/download_queue_batch1_priority_top5_guvi.csv`
- `docs_index/download_queue_batch1_priority_top5_dmsp.csv`
- `docs_index/download_queue_batch1_priority_top5_superdarn.csv`
- `docs_index/download_queue_batch1_priority_top5_ssusi.csv`

The top-5 priority list must include:

```text
storm_153_2015031722
storm_025_2011102501
```

Do not expand to the 129-row Batch-1 full run until top-5 acquisition, normalization, and gate checks have passed.

## Stop Rule

All reports and summaries must continue to state:

```text
Do not claim completed 2011-2015 multi-event SAPS/O/N2 statistics.
```

The correct status is data-readiness and acquisition-pilot execution, not final science statistics.

## Issue Comment To Add After Upload Recovery

```text
Added upload-recovery and next-stage plan after 2026-06-29 local run:
docs_index/codex_upload_recovery_and_next_stage_plan_after_20260629_local_run.md
```

## Note On Source PDFs

Some previously uploaded PDF materials have expired in the current session. If exact thesis passages or page numbers are needed again, the corresponding PDF should be uploaded again before quoting or citing those details.
