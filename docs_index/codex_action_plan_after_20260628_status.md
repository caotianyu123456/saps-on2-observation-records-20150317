# Codex Action Plan After 2026-06-28 Repository Status Review

Updated: 2026-06-29
Repository: `caotianyu123456/saps-on2-observation-records-20150317`

## 0. Executive status

The newest repository materials show that the project has correctly moved from a single-case mindset to a data-layer preparation stage, but it is still not a completed multi-event SAPS/O/N2 statistical study.

Current verified state:

```text
Science products: 2015-03-16 to 2015-03-18 St. Patrick storm smoke test
Not yet: 2011-2015 multi-event SAPS/O/N2 statistics
```

Latest repository summary indicates:

```text
2011-2015 OMNI2 Dst/Kp/AE indices acquired.
2011-2015 Dst storm event universe generated: 737 event rows.
2011-2015 required manifest generated: 3685 rows.
Download queues generated locally for GUVI, DMSP, SuperDARN, SSUSI, and indices.
All-event normalizer status generated: 415 rows.
Current normalizer status: 403 parsed_with_warnings, 12 file_missing.
```

Seed-event readiness currently is:

```text
2015-03-16: E_ON2_available_no_SAPS_data
2015-03-17: A_ready_for_full_SAPS_ON2_matching
2015-03-18: A_ready_for_full_SAPS_ON2_matching
2014-02-19: F_indices_only
2011-10-25: F_indices_only
2013-06-30: F_indices_only
```

Therefore the next work is not to claim final statistics. The next work is to turn the data-layer outputs into a reliable seed-event detector validation and then a staged 2011-2015 Batch-1 science run.

---

## 1. Immediate stop rule

Codex must not describe any current result as:

```text
2011-2015 SAPS/O/N2 statistics
multi-year O/N2 response statistics
completed SAPS/O/N2 statistical study
```

until all of the following exist:

```text
data_samples/screening_outputs/saps_channel_objects_2011_2015.csv
data_samples/screening_outputs/on2_opportunity_2011_2015.csv
data_samples/screening_outputs/saps_on2_match_candidates_2011_2015.csv
data_samples/screening_outputs/nonmatch_selection_function_2011_2015.csv
summaries/screening_outputs/batch_screening_summary_2011_2015.md
```

Current correct wording:

```text
Data-layer and St. Patrick smoke-test stage completed; 2011-2015 event universe and download queues prepared; multi-event science matching pending instrument-data acquisition and normalization.
```

---

## 2. Scientific basis to preserve

Use the Zhang Qiang 2021 SAPS thesis as the SAPS-channel detector reference.

Key methodological rules to preserve in code:

```text
DMSP F16/F17/F18 can identify SAPS crossings.
Use DMSP cross-track/y-axis drift as SAPS speed only when DMSP track geometry relative to auroral oval is suitable.
A 500 m/s minimum westward-speed threshold is the conservative SAPS threshold.
SAPS speed profile should have a peak or inflection.
SAPS peak should be located at or equatorward of the auroral oval equatorward boundary.
Classify SAPS morphology; keep regular SAPS separate from double-peak and abnormal eastward cases.
SuperDARN midlatitude radar chain validates large-scale SAPS channels and event evolution.
SSUSI should primarily support auroral boundary and contamination masking.
Storm phase must be tagged because main phase, early recovery, and late recovery SAPS behave differently.
```

---

## 3. Next-phase objective

Move the project from:

```text
2015 smoke test + 2011-2015 event universe prepared
```

to:

```text
seed-event SAPS detector validated + O/N2 opportunity checked + Batch-1 2011-2015 major-storm data acquisition prepared
```

The next phase has ten tasks.

---

## 4. Task 1 — reconcile local inventory and event availability

### Problem

The latest public summary lists local inventory rows for validation-event data groups, while `event_data_availability.csv` still marks 2014-02-19, 2011-10-25, and 2013-06-30 as `F_indices_only`. This likely means some rows are placeholders, queue entries, or unparsed local artifacts rather than science-ready files.

### Action

Create:

```text
scripts/reconcile_inventory_vs_availability.py
summaries/screening_outputs/inventory_availability_reconciliation_20260629.md
```

### Required checks

For every seed event and data group, classify the state as one of:

```text
not_required
file_missing
download_queue_only
raw_file_present_not_parsed
raw_file_present_parse_failed
raw_file_present_missing_variables
parsed_ok_no_subauroral_coverage
parsed_ok_no_dayglow_on2
parsed_ok_science_ready
```

### Required outputs

```text
data_samples/screening_outputs/event_data_availability_reconciled.csv
docs_index/data_manifest_local_reconciled.csv
summaries/screening_outputs/inventory_availability_reconciliation_20260629.md
```

### Acceptance criteria

- No seed-event data group remains ambiguous.
- The three validation events must not be called `F_indices_only` if raw files truly exist and parse successfully.
- If raw files exist but are unusable, the failure reason must be explicit.

---

## 5. Task 2 — refine normalizer status schema

### Problem

The current `normalizer_status_all_events.csv` has 403 `parsed_with_warnings` rows and 12 `file_missing` rows. `parsed_with_warnings` is too broad for science decisions.

### Action

Update:

```text
scripts/build_normalizer_status_all_events.py
```

Create:

```text
data_work/normalized/normalizer_status_all_events_v2.csv
summaries/screening_outputs/normalizer_status_v2_summary.md
```

### Required parse statuses

```text
parsed_ok_science_ready
parsed_ok_no_subauroral_coverage
parsed_ok_no_dayglow_on2
parsed_ok_missing_optional_variables
parsed_with_nonblocking_warnings
file_missing
download_queue_only
unsupported_format
missing_required_variable
coordinate_conversion_failed
quality_rejected
empty_after_filtering
```

### Required columns

```text
event_id
event_date
data_group
source_file_or_queue
local_path_or_placeholder
parse_status_v1
parse_status_v2
normalized_output_path
n_records
n_valid_records
n_valid_subauroral_records
n_valid_dayglow_on2_records
missing_required_variables
missing_optional_variables
coordinate_system
coordinate_conversion_status
quality_flag_summary
failure_reason
last_run_utc
```

### Acceptance criteria

- Fewer than 10% of rows may remain in generic `parsed_with_nonblocking_warnings`.
- Every non-science-ready row has an actionable `failure_reason`.

---

## 6. Task 3 — acquire or link seed-event instrument data

### Target seed events

```text
2014-02-19
2011-10-25
2013-06-30
```

These are the thesis-inspired SAPS evolution validation events.

### Priority windows

```text
2014-02-19 0300-0700 UT
2011-10-25 0300-0700 UT
2013-06-30 0300-0700 UT
```

For O/N2 response, also keep:

```text
event_day_minus_1 to event_day_plus_1
```

### Required data groups

```text
GUVI L3 O/N2
DMSP SSIES F16/F17/F18
DMSP SSJ, if available
DMSP SSUSI auroral data
SuperDARN map/fit/grid if possible; quick-look only as fallback
OMNI/SYM-H/AE/Dst/Kp indices
```

### Create or update queue files

```text
docs_index/download_queue_seed_events_guvi.csv
docs_index/download_queue_seed_events_dmsp.csv
docs_index/download_queue_seed_events_superdarn.csv
docs_index/download_queue_seed_events_ssusi.csv
docs_index/download_queue_seed_events_indices.csv
```

### Create status report

```text
summaries/screening_outputs/seed_event_data_acquisition_status.md
```

### Acceptance criteria

Each of the three validation events should move from `F_indices_only` to one of:

```text
A_ready_for_full_SAPS_ON2_matching
B_ready_for_DMSP_GUVI_only
C_ready_for_SuperDARN_GUVI_only
D_SAPS_available_no_ON2
E_ON2_available_no_SAPS_data
G_missing_or_unusable_with_explicit_reason
```

---

## 7. Task 4 — normalize seed-event instruments

### Action

Run or implement:

```text
scripts/normalize_guvi_on2.py
scripts/normalize_dmsp_ssies.py
scripts/normalize_superdarn.py
scripts/normalize_ssusi.py
scripts/normalize_geomag_indices.py
```

### Required normalized seed outputs

```text
data_work/normalized/guvi_on2/{YYYY}/{YYYYMMDD}/guvi_on2_normalized_{YYYYMMDD}.csv
data_work/normalized/dmsp_ssies/{YYYY}/{YYYYMMDD}/dmsp_ssies_normalized_{YYYYMMDD}.csv
data_work/normalized/superdarn/{YYYY}/{YYYYMMDD}/superdarn_normalized_{YYYYMMDD}.csv
data_work/normalized/ssusi/{YYYY}/{YYYYMMDD}/ssusi_normalized_{YYYYMMDD}.csv
data_work/normalized/indices/{YYYY}/{YYYYMMDD}/geomag_indices_{YYYYMMDD}.csv
```

### Normalization requirements

- All files must include `source_file` or `source_url_or_queue`.
- All geolocated observations must include AACGM/Apex MLAT and MLT if conversion is possible.
- GUVI must include SZA/local-time/dayglow quality flags.
- SuperDARN must include `quantitative`, `quicklook_only`, or `insufficient_echo` status.
- SSUSI must include auroral-boundary support status.

---

## 8. Task 5 — validate SuperDARN SAPS detector on seed events

### Action

Run or implement:

```text
scripts/screen_superdarn_saps_channels.py
```

### Seed validation events

```text
2014-02-19
2011-10-25
2013-06-30
```

### Required outputs

```text
data_samples/screening_outputs/superdarn_saps_channels_seed_events.csv
summaries/screening_outputs/superdarn_detector_validation_seed_events.md
figures/screening_outputs/fig_20140219_superdarn_saps_channel_validation.png
figures/screening_outputs/fig_20111025_superdarn_saps_channel_validation.png
figures/screening_outputs/fig_20130630_superdarn_saps_channel_validation.png
```

### Required channel fields

```text
event_date
hemisphere
time_start_ut
time_end_ut
mlt_min
mlt_max
mlat_center
mlat_width
velocity_median_ms
velocity_p95_ms
velocity_max_ms
radar_count
valid_echo_count
vector_quality
auroral_boundary_support
duration_min
mlt_extent_h
saps_t_slope
saps_t_slope_r_value
confidence_grade
failure_or_caveat
```

### Acceptance criteria

- 2014-02-19 should show a main-phase SAPS channel near the thesis interval if data are available.
- 2011-10-25 should show early-recovery SAPS evolution or explicitly fail because of missing/insufficient radar data.
- 2013-06-30 should either show weak/broken late-recovery SAPS or explicitly fail because of missing/insufficient radar data.
- T-Slope must be computed when MLT coverage is sufficient.

---

## 9. Task 6 — validate DMSP SAPS detector on seed events

### Action

Run or implement:

```text
scripts/detect_dmsp_saps_crossings.py
```

### Initial validation events

```text
2015-03-17
2015-03-18
2014-02-19, after data are acquired
```

### Required outputs

```text
data_samples/screening_outputs/dmsp_saps_crossings_seed_events.csv
summaries/screening_outputs/dmsp_detector_validation_seed_events.md
```

### Required fields

```text
event_date
satellite
orbit_or_rev
time_start_ut
time_end_ut
time_peak_ut
hemisphere
aacgm_mlat_peak
aacgm_mlt_peak
westward_peak_kms
westward_p95_kms
duration_s
width_deg
has_velocity_peak_or_inflection
auroral_boundary_source
auroral_equatorward_boundary_mlat
peak_relative_to_boundary_deg
dmsp_track_auroral_boundary_angle_deg
dmsp_geometry_quality
saps_morphology_class
confidence_grade
rejection_reason
```

### Acceptance criteria

- DMSP detector must not use a single-point maximum.
- Sustained interval, boundary position, geometry, and morphology must be included.
- Class-1 regular SAPS should be separated from DSAID/ASAPS/uncertain cases.

---

## 10. Task 7 — build seed-event SAPS channel objects

### Action

Run or implement:

```text
scripts/build_saps_channel_objects.py
scripts/score_saps_channel_confidence.py
```

### Required output

```text
data_samples/screening_outputs/saps_channel_objects_seed_events.csv
```

### Source pathways

```text
DMSP_only
SuperDARN_only
joint_DMSP_SuperDARN
```

### Acceptance criteria

- Every SAPS channel has a grade A/B/C/rejected.
- Every channel has a `source_pathway` and `main_caveat`.
- Joint DMSP/SuperDARN channels should be prioritized for O/N2 response interpretation.

---

## 11. Task 8 — build seed-event O/N2 opportunity database

### Action

Run or implement:

```text
scripts/build_on2_opportunity_database.py
scripts/build_on2_patches.py
```

### Required output

```text
data_samples/screening_outputs/on2_opportunity_seed_events.csv
data_samples/screening_outputs/guvi_on2_patches_seed_events.csv
```

### Required O/N2 source fields

```text
on2_source
event_date
time_start_ut
time_end_ut
time_center_ut
hemisphere
aacgm_mlat_min
aacgm_mlat_max
aacgm_mlt_min
aacgm_mlt_max
n_on2_valid
on2_median
on2_p05
on2_min
log_on2_median
sza_median
local_time_min
local_time_max
dayglow_quality_flag
quality_caveat
```

### Acceptance criteria

- GUVI O/N2 must not be treated as valid if dayglow/SZA quality is poor unless labelled.
- O/N2 opportunity can exist even if no SAPS exists; preserve these as nonmatches.

---

## 12. Task 9 — match seed SAPS channels to O/N2

### Action

Run or implement:

```text
scripts/match_saps_channels_to_on2.py
scripts/build_dmsp_crossing_relative_on2_profiles.py
```

### Required outputs

```text
data_samples/screening_outputs/saps_on2_match_candidates_seed_events.csv
data_samples/screening_outputs/dmsp_crossing_relative_on2_profiles_seed_events.csv
data_samples/screening_outputs/nonmatch_selection_function_seed_events.csv
summaries/screening_outputs/seed_event_screening_summary.md
```

### Lag bins

```text
0-1 h: near-simultaneous
1-3 h: primary short-lag neutral/composition response window
3-6 h: delayed response / sensitivity
6-12 h: storm context only
```

### Region classes

```text
inside_channel
near_channel
equatorward_control
poleward_control
same_MLT_outside_channel
```

### Required O/N2 response metrics

```text
ON2_inside_median
ON2_near_channel_median
ON2_equatorward_control_median
ON2_poleward_control_median
ON2_same_MLT_outside_median
delta_ON2_inside_minus_equatorward
delta_ON2_inside_minus_poleward
delta_ON2_inside_minus_same_MLT
delta_log_ON2_inside_minus_control
response_sign
response_strength_category
```

### Acceptance criteria

- 2015-03-17 and 2015-03-18 should remain the first full matching smoke test.
- Validation events with SAPS but no O/N2 must be preserved as `SAPS_available_no_ON2`, not discarded.
- O/N2 depletion without SAPS must also be preserved.

---

## 13. Task 10 — prepare 2011-2015 Batch-1 major-storm run

Do not immediately run all 737 event rows. Start with the high-yield subset.

### Batch-1 selection

```text
major_or_super_storm: min(Dst) <= -100 nT
include storm_day_minus_2 through storm_day_plus_3
priority: events with GUVI day-dusk subauroral O/N2 opportunity or DMSP/SuperDARN availability
```

### Required outputs before science matching

```text
data_samples/screening_outputs/event_universe_2011_2015_batch1_major.csv
docs_index/download_queue_guvi_2011_2015_batch1_major.csv
docs_index/download_queue_dmsp_2011_2015_batch1_major.csv
docs_index/download_queue_superdarn_2011_2015_batch1_major.csv
docs_index/download_queue_ssusi_2011_2015_batch1_major.csv
docs_index/download_queue_indices_2011_2015_batch1_major.csv
summaries/screening_outputs/batch1_major_storm_data_readiness.md
```

### Run only after data readiness

```bash
python scripts/batch_screen_guvi_dmsp_saps_on2_events.py --event-list data_samples/screening_outputs/event_universe_2011_2015_batch1_major.csv
python scripts/match_saps_channels_to_on2.py --event-list data_samples/screening_outputs/event_universe_2011_2015_batch1_major.csv
```

### Batch-1 outputs

```text
data_samples/screening_outputs/saps_channel_objects_2011_2015_batch1_major.csv
data_samples/screening_outputs/on2_opportunity_2011_2015_batch1_major.csv
data_samples/screening_outputs/saps_on2_match_candidates_2011_2015_batch1_major.csv
data_samples/screening_outputs/nonmatch_selection_function_2011_2015_batch1_major.csv
summaries/screening_outputs/batch1_major_storm_screening_summary.md
```

---

## 14. Required progress summaries after this phase

Create or update:

```text
summaries/screening_outputs/next_phase_progress_after_20260628.md
summaries/screening_outputs/seed_event_detector_validation_summary.md
summaries/screening_outputs/seed_event_on2_opportunity_summary.md
summaries/screening_outputs/batch1_major_storm_data_readiness.md
```

Each summary must state:

```text
what was run
which input data were present
which data were missing
which detector/matcher version was used
which events are science-ready
which events are data-limited
what cannot yet be claimed
```

---

## 15. Final acceptance criteria for this next phase

The next phase is complete only when:

1. Inventory-vs-availability ambiguity is resolved.
2. `normalizer_status_all_events_v2.csv` exists and uses detailed statuses.
3. Three thesis-inspired events are no longer ambiguous `F_indices_only` rows.
4. SuperDARN detector has been tested on 2014-02-19, 2011-10-25, and 2013-06-30, or missing-data reasons are explicit.
5. DMSP detector has been tested on 2015-03-17/18 and 2014-02-19 if data are available.
6. `saps_channel_objects_seed_events.csv` exists.
7. `on2_opportunity_seed_events.csv` exists.
8. `saps_on2_match_candidates_seed_events.csv` exists.
9. `nonmatch_selection_function_seed_events.csv` exists.
10. Batch-1 major-storm event list and download queues exist.
11. No report claims completed 2011-2015 statistics until actual 2011-2015 matching outputs exist.

---

## 16. Recommended Codex execution order

Run tasks in this order:

```text
1. reconcile_inventory_vs_availability
2. refine_normalizer_status_schema
3. acquire_or_link_seed_event_instrument_data
4. normalize_seed_event_instruments
5. validate_superdarn_detector_on_seed_events
6. validate_dmsp_detector_on_seed_events
7. build_seed_saps_channel_objects
8. build_seed_on2_opportunity_database
9. match_seed_saps_channels_to_on2
10. prepare_2011_2015_batch1_major_storm_run
```

Do not skip directly from Task 2 to 2011-2015 statistics.
