# Next-Phase Execution Status

Date: 2026-06-28

Execution basis:

- `docs_index/codex_next_phase_after_data_layer_status.md`
- commit `da956dc7dffbeb670efcf30a872e7d5aa15ad44d`

## Current Scientific Status

The current science products remain a St. Patrick storm smoke test for 2015-03-16 to 2015-03-18.

They are not yet 2011-2015 multi-event SAPS/O/N2 statistics.

## Track A: Thesis-Inspired Events

The official NASA CDAWeb OMNI2 hourly Dst/Kp/AE index data were acquired for 2011-2015 and cached locally under:

```text
data_raw/indices/global/omni2_h0_mrg1hr_20110101_20151231.csv
```

After rebuilding the seed-event manifests, the three thesis-inspired events moved from `G_missing_or_unusable` to `F_indices_only`:

| Event date | Event ID | Updated readiness | Remaining blocking gap |
| --- | --- | --- | --- |
| 2014-02-19 | `validation_20140219` | `F_indices_only` | GUVI O/N2 and SAPS detector data |
| 2011-10-25 | `validation_20111025` | `F_indices_only` | GUVI O/N2 and SAPS detector data |
| 2013-06-30 | `validation_20130630` | `F_indices_only` | GUVI O/N2 and SAPS detector data |

Seed-event manifest counts after this update:

| File | Rows |
| --- | ---: |
| `docs_index/data_manifest_required.csv` | 30 |
| `docs_index/data_manifest_local.csv` | 415 |
| `docs_index/data_manifest_missing.csv` | 23 |
| `data_samples/screening_outputs/event_data_availability.csv` | 6 |

The full local manifest contains machine-specific paths and should remain local. The public aggregate summary is:

```text
docs_index/data_manifest_local_public_summary.csv
```

## Track B: 2011-2015 Event Universe

The 2011-2015 storm-index universe was generated from official NASA CDAWeb OMNI2 hourly Dst data using:

```text
scripts/build_2011_2015_event_universe.py
```

Generated outputs:

| File | Rows |
| --- | ---: |
| `data_samples/screening_outputs/event_universe_2011_2015.csv` | 737 |
| `data_samples/screening_outputs/event_universe_expanded_2011_2015.csv` | 737 |
| `docs_index/data_manifest_required_2011_2015.csv` | 3685 |
| `docs_index/download_queue_guvi_2011_2015.csv` | 737 |
| `docs_index/download_queue_dmsp_2011_2015.csv` | 737 |
| `docs_index/download_queue_superdarn_2011_2015.csv` | 737 |
| `docs_index/download_queue_ssusi_2011_2015.csv` | 737 |
| `docs_index/download_queue_indices_2011_2015.csv` | 737 |

Selection rules implemented:

```text
primary: min(Dst) <= -50 nT
major subset: min(Dst) <= -100 nT
super-storm subset: min(Dst) <= -200 nT
```

For `major` and `super_storm` events, the universe includes storm_day_minus_2 through storm_day_plus_3. For moderate storms, it includes storm_day_minus_1 through storm_day_plus_1.

## Track C: Normalizer Status

The all-event normalizer status table now exists:

```text
data_work/normalized/normalizer_status_all_events.csv
```

Rows: 415

Current status counts:

| parse_status | Rows |
| --- | ---: |
| `parsed_with_warnings` | 403 |
| `file_missing` | 12 |

The current `parsed_with_warnings` status means raw/support files are present but the full reusable normalizer and science-quality filtering still need to be completed before final statistics.

## What Still Blocks Science Statistics

The next phase is not complete yet because:

- GUVI O/N2 is still missing for 2014-02-19, 2011-10-25, and 2013-06-30.
- DMSP SSIES/SSJ and SuperDARN quantitative products are still missing for those thesis-inspired validation events.
- The 2011-2015 event universe has been generated, but instrument data have not been downloaded and normalized for the 737 event rows.
- Seed-event science matching should not be rerun as a final validation until the missing Track A instrument data are present.

## Next Action

Use the generated 2011-2015 download queues to acquire or link:

```text
TIMED/GUVI L3 O/N2
DMSP SSIES/SSJ
SuperDARN map/fit/grid or verified quick-look support
DMSP SSUSI boundary support
```

Then rerun:

```text
python scripts/build_event_universe.py
python scripts/check_missing_data.py
python scripts/build_normalizer_status_all_events.py
python scripts/batch_screen_guvi_dmsp_saps_on2_events.py --event-list data_samples/screening_outputs/event_universe_expanded_2011_2015.csv
```
