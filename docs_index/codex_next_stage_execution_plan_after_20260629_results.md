# Codex Next-Stage Execution Plan After 2026-06-29 Results

Updated: 2026-06-30
Repository: `caotianyu123456/saps-on2-observation-records-20150317`

## 0. Current verified state

The latest GitHub progress shows a correct data-readiness/smoke-test stage, not completed 2011-2015 statistics.

Current state:

```text
2015-03-16 to 2015-03-18 St. Patrick storm smoke test
not yet 2011-2015 multi-event SAPS/O/N2 statistics
```

Latest completed items:

```text
inventory vs availability reconciliation completed
normalizer_status_all_events_v2.csv generated, 415 rows
generic parsed_with_nonblocking_warnings = 0
seed-event download queues generated
indices normalized for all six seed events
SuperDARN validation events retained as rejected/no-data rows
seed SAPS/O/N2 tables retain no-data validation rows
Batch-1 major/super storm subset generated: 129 event rows, 22 storm groups
```

Main remaining blockers:

```text
2014-02-19, 2011-10-25, 2013-06-30 still have GUVI/DMSP/SuperDARN/SSUSI = download_queue_only
St. Patrick GUVI/DMSP/SSUSI raw/support files still need science-ready normalized variables
SuperDARN quantitative map/fit/grid products are not yet available for detector validation
Batch-1 queues exist, but instrument data are not acquired/normalized
```

---

## 1. Immediate stop rule

Do not claim:

```text
completed 2011-2015 multi-event SAPS/O/N2 statistics
validated SuperDARN SAPS detector for the thesis-inspired events
final seed-event O/N2 response statistics for validation events
```

until science-ready seed tables and Batch-1 instrument data exist.

---

## 2. Next-stage objective

Move from:

```text
data-readiness smoke test + Batch-1 preparation
```

to:

```text
science-ready seed-event data + validated SAPS detectors + seed-event SAPS/O/N2 matching + Batch-1 acquisition triage
```

---

## 3. Task A — materialize seed-event download instructions

Target events:

```text
2014-02-19
2011-10-25
2013-06-30
```

Priority windows:

```text
0300-0700 UT for SAPS detector validation
event_day_minus_1 to event_day_plus_1 for O/N2 response checks
```

Create:

```text
scripts/materialize_seed_download_instructions.py
scripts/link_local_raw_files_from_manifest.py
docs_index/seed_event_download_instructions.md
docs_index/seed_event_manual_download_checklist.csv
docs_index/seed_event_remote_availability.csv
docs_index/data_manifest_seed_events_required.csv
docs_index/data_manifest_seed_events_linked.csv
docs_index/data_manifest_seed_events_missing.csv
summaries/screening_outputs/seed_event_download_blockers.md
```

Every missing group must be labelled as one of:

```text
automated_download_possible
manual_download_required
authentication_required
remote_data_not_found
local_link_needed
```

---

## 4. Task B — make St. Patrick normalizers science-ready

Target events:

```text
2015-03-17
2015-03-18
```

Update:

```text
scripts/normalize_guvi_on2.py
scripts/normalize_dmsp_ssies.py
scripts/normalize_ssusi.py
scripts/normalize_superdarn.py
scripts/build_normalizer_status_all_events.py
```

Required normalized outputs:

```text
data_work/normalized/guvi_on2/2015/20150317/guvi_on2_normalized_20150317.csv
data_work/normalized/guvi_on2/2015/20150318/guvi_on2_normalized_20150318.csv
data_work/normalized/dmsp_ssies/2015/20150317/dmsp_ssies_normalized_20150317.csv
data_work/normalized/dmsp_ssies/2015/20150318/dmsp_ssies_normalized_20150318.csv
data_work/normalized/ssusi/2015/20150317/ssusi_normalized_20150317.csv
data_work/normalized/ssusi/2015/20150318/ssusi_normalized_20150318.csv
data_work/normalized/normalizer_status_all_events_v3.csv
summaries/screening_outputs/st_patrick_normalizer_v3_summary.md
```

Minimum science-ready fields:

```text
GUVI: time, lat/lon, AACGM MLAT/MLT, SZA, LT, O/N2, log(O/N2), quality/dayglow flag
DMSP: time, lat/lon, AACGM MLAT/MLT, westward drift, density, quality flag, sign convention
SSUSI: auroral boundary or contamination-mask status if variables exist
SuperDARN: quantitative / quicklook_only / insufficient_echo / not_available status
```

---

## 5. Task C — rerun seed SAPS detector validation

Run only after Task B or after new seed raw files are linked.

Run:

```text
scripts/detect_dmsp_saps_crossings.py
scripts/screen_superdarn_saps_channels.py
scripts/build_saps_channel_objects.py
scripts/score_saps_channel_confidence.py
```

Create:

```text
data_samples/screening_outputs/dmsp_saps_crossings_seed_events_v2.csv
data_samples/screening_outputs/superdarn_saps_channels_seed_events_v2.csv
data_samples/screening_outputs/saps_channel_objects_seed_events_v2.csv
summaries/screening_outputs/dmsp_detector_validation_seed_events_v2.md
summaries/screening_outputs/superdarn_detector_validation_seed_events_v2.md
summaries/screening_outputs/saps_channel_object_seed_events_v2_summary.md
```

Detector rules:

```text
DMSP SAPS: sustained westward interval, >=500 m/s baseline threshold, peak/inflection, geometry quality, boundary relation, morphology class
SuperDARN SAPS: quantitative map/fit/grid for velocity claims, echo/coverage gate, connected westward channel, vector quality, duration, MLT extent, T-Slope if coverage allows
```

---

## 6. Task D — rebuild seed O/N2 opportunity and matching with science-ready inputs

Run:

```text
scripts/build_on2_opportunity_database.py
scripts/build_on2_patches.py
scripts/match_saps_channels_to_on2.py
scripts/build_dmsp_crossing_relative_on2_profiles.py
```

Create:

```text
data_samples/screening_outputs/on2_opportunity_seed_events_science_ready.csv
data_samples/screening_outputs/guvi_on2_patches_seed_events_science_ready.csv
data_samples/screening_outputs/saps_on2_match_candidates_seed_events_science_ready.csv
data_samples/screening_outputs/dmsp_crossing_relative_on2_profiles_seed_events_science_ready.csv
data_samples/screening_outputs/nonmatch_selection_function_seed_events_science_ready.csv
summaries/screening_outputs/seed_event_science_ready_summary.md
```

Use lag bins:

```text
0-1 h: near-simultaneous
1-3 h: primary short-lag window
3-6 h: delayed/sensitivity
6-12 h: storm context only
```

Use region classes:

```text
inside_channel
near_channel
equatorward_control
poleward_control
same_MLT_outside_channel
```

---

## 7. Task E — rank Batch-1 major storm groups before downloading everything

Batch-1 currently has:

```text
129 event rows
22 storm groups
selection: min(Dst) <= -100 nT
```

Do not download/process all 129 rows first. Rank storm groups and choose a pilot top-5.

Create:

```text
scripts/rank_batch1_major_storms_for_download.py
data_samples/screening_outputs/batch1_major_storm_group_priority.csv
docs_index/download_queue_batch1_priority_top5_guvi.csv
docs_index/download_queue_batch1_priority_top5_dmsp.csv
docs_index/download_queue_batch1_priority_top5_superdarn.csv
docs_index/download_queue_batch1_priority_top5_ssusi.csv
summaries/screening_outputs/batch1_major_storm_download_priority.md
```

Ranking factors:

```text
min(Dst)
season
storm phase coverage
known thesis event inclusion
existing local data availability
expected GUVI day-dusk subauroral O/N2 opportunity
expected DMSP F16/F17/F18 coverage
expected SuperDARN MLT coverage
SSUSI boundary support likelihood
```

Always include if present:

```text
2011-10-25 storm group
2015-03-17 St. Patrick storm group
```

---

## 8. Task F — prepare Batch-1 readiness v2, but do not run final statistics yet

Create:

```text
data_samples/screening_outputs/batch1_major_storm_data_availability_v2.csv
data_work/normalized/normalizer_status_batch1_major_v1.csv
summaries/screening_outputs/batch1_major_storm_data_readiness_v2.md
```

Readiness classes:

```text
A_ready_for_full_SAPS_ON2_matching
B_ready_for_DMSP_GUVI_only
C_ready_for_SuperDARN_GUVI_only
D_SAPS_available_no_ON2
E_ON2_available_no_SAPS_data
F_indices_only
G_missing_or_unusable_with_explicit_reason
```

Only after Batch-1 data are acquired and normalized should Codex run:

```text
scripts/batch_screen_guvi_dmsp_saps_on2_events.py
scripts/match_saps_channels_to_on2.py
```

---

## 9. Required progress reports

Create or update:

```text
summaries/screening_outputs/progress_after_science_ready_seed_normalization.md
summaries/screening_outputs/seed_event_detector_validation_v2_summary.md
summaries/screening_outputs/seed_event_science_ready_summary.md
summaries/screening_outputs/batch1_major_storm_download_priority.md
summaries/screening_outputs/batch1_major_storm_data_readiness_v2.md
```

Each report must state:

```text
what was run
which inputs were present
which data are missing
which scripts/versions were used
which events are science-ready
which events are data-limited
what cannot yet be claimed
```

---

## 10. Exact Codex execution order

```text
1. materialize_seed_download_instructions
2. link_local_raw_files_from_manifest
3. update GUVI/DMSP/SSUSI/SuperDARN normalizers for St. Patrick science-ready fields
4. build normalizer_status_all_events_v3
5. rerun DMSP detector validation on 2015-03-17/18
6. acquire/link 2014-02-19, 2011-10-25, 2013-06-30 instrument data if possible
7. rerun seed SuperDARN/DMSP detector validation
8. build seed SAPS channel objects v2
9. build seed O/N2 opportunity and matching science-ready tables
10. rank Batch-1 major storm groups and prepare top-5 acquisition queues
11. build Batch-1 readiness v2
```

---

## 11. Acceptance criteria for this stage

This stage is complete only when:

```text
seed download instructions and blockers exist
normalizer_status_all_events_v3.csv exists
St. Patrick GUVI/DMSP normalizers produce science-ready rows or explicit nonfatal caveats
dmsp_saps_crossings_seed_events_v2.csv exists
superdarn_saps_channels_seed_events_v2.csv exists and separates quantitative/no-data/quicklook
saps_channel_objects_seed_events_v2.csv exists
on2_opportunity_seed_events_science_ready.csv exists
saps_on2_match_candidates_seed_events_science_ready.csv exists
nonmatch_selection_function_seed_events_science_ready.csv exists
Batch-1 top-5 storm-group download priority files exist
no summary claims completed 2011-2015 statistics
```

Expected final status after this stage:

```text
Seed-event science-ready SAPS/O/N2 screening validated for local St. Patrick data;
validation-event data acquisition paths defined;
Batch-1 major-storm acquisition priority established;
2011-2015 statistics still pending broader instrument-data acquisition.
```
