# Next-Phase Web Quicklook

Date: 2026-06-28

Basis:

- `docs_index/codex_next_phase_after_data_layer_status.md`
- plan commit: `da956dc7dffbeb670efcf30a872e7d5aa15ad44d`

## Status

The repository is still at:

```text
2015-03-16 to 2015-03-18 St. Patrick storm smoke test
not yet 2011-2015 multi-event statistics
```

This update executed the data-layer next phase:

| Track | Result |
| --- | --- |
| A | 2011-2015 OMNI2 Dst/Kp/AE indices acquired; 2014-02-19, 2011-10-25, and 2013-06-30 now classify as `F_indices_only` |
| B | 2011-2015 Dst storm event universe and instrument download queues generated locally |
| C | All-event normalizer status table generated locally |

## Key Outputs

| Output | Rows | GitHub visibility |
| --- | ---: | --- |
| `summaries/screening_outputs/next_phase_execution_status_20260628.md` | n/a | uploaded |
| `docs_index/next_phase_output_manifest_20260628.csv` | 9 | uploaded; includes SHA256 for large local artifacts |
| `scripts/build_2011_2015_event_universe.py` | n/a | uploaded |
| `scripts/build_normalizer_status_all_events.py` | n/a | uploaded |
| `data_samples/screening_outputs/event_universe_2011_2015.csv` | 737 | local large artifact; regenerate from script |
| `data_samples/screening_outputs/event_universe_expanded_2011_2015.csv` | 737 | local large artifact; regenerate from script |
| `docs_index/data_manifest_required_2011_2015.csv` | 3685 | local large artifact; regenerate from script |
| `data_work/normalized/normalizer_status_all_events.csv` | 415 | local large artifact; regenerate from script |

## Seed Event Availability

| Event date | Event ID | Current readiness | Blocking gap |
| --- | --- | --- | --- |
| 2015-03-16 | `available_20150316` | `E_ON2_available_no_SAPS_data` | SAPS detector data |
| 2015-03-17 | `available_20150317` | `A_ready_for_full_SAPS_ON2_matching` | none after normalization |
| 2015-03-18 | `available_20150318` | `A_ready_for_full_SAPS_ON2_matching` | none after normalization |
| 2014-02-19 | `validation_20140219` | `F_indices_only` | GUVI O/N2; SAPS detector data |
| 2011-10-25 | `validation_20111025` | `F_indices_only` | GUVI O/N2; SAPS detector data |
| 2013-06-30 | `validation_20130630` | `F_indices_only` | GUVI O/N2; SAPS detector data |

## Event Universe Sample

First generated rows:

| event_id | event_date | min_dst_nt | storm_class | priority |
| --- | --- | ---: | --- | --- |
| `storm_001_2011020421_20110203` | 2011-02-03 | -63 | `moderate_storm` | `primary` |
| `storm_001_2011020421_20110204` | 2011-02-04 | -63 | `moderate_storm` | `primary` |
| `storm_001_2011020421_20110205` | 2011-02-05 | -63 | `moderate_storm` | `primary` |
| `storm_002_2011020508_20110204` | 2011-02-04 | -54 | `moderate_storm` | `primary` |
| `storm_002_2011020508_20110205` | 2011-02-05 | -54 | `moderate_storm` | `primary` |
| `storm_002_2011020508_20110206` | 2011-02-06 | -54 | `moderate_storm` | `primary` |
| `storm_003_2011030114_20110228` | 2011-02-28 | -88 | `moderate_storm` | `primary` |
| `storm_003_2011030114_20110301` | 2011-03-01 | -88 | `moderate_storm` | `primary` |
| `storm_003_2011030114_20110302` | 2011-03-02 | -88 | `moderate_storm` | `primary` |
| `storm_014_2011080603_20110804` | 2011-08-04 | -115 | `major_storm` | `major_subset` |

## Reproduction Commands

```bash
python scripts/build_2011_2015_event_universe.py
python scripts/build_event_universe.py
python scripts/check_missing_data.py
python scripts/build_normalizer_status_all_events.py
```

The next scientific step is not final statistics yet. It is data acquisition for GUVI, DMSP, SuperDARN, and SSUSI using the generated 2011-2015 download queues.
