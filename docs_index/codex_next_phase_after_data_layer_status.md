# Codex Next-Phase Plan After Data-Layer Status Update

Updated: 2026-06-22
Repository: `caotianyu123456/saps-on2-observation-records-20150317`

## 0. Current verified status

The latest local execution correctly stopped at the data layer instead of claiming a false multi-event statistical result.

Current local data universe:

```text
2015-03-16
2015-03-17
2015-03-18
2014-02-19
2011-10-25
2013-06-30
```

Current data-layer outputs reported by the local run:

```text
docs_index/data_manifest_required.csv   # 30 rows
docs_index/data_manifest_local.csv      # 400 rows
docs_index/data_manifest_missing.csv    # 28 rows
data_samples/screening_outputs/event_data_availability.csv
summaries/screening_outputs/data_gap_report.md
docs_index/download_queue_guvi.csv
docs_index/download_queue_dmsp.csv
docs_index/download_queue_superdarn.csv
docs_index/download_queue_ssusi.csv
docs_index/download_queue_indices.csv
docs_index/download_queue_gold.csv
data_work/normalized/
docs_index/current_repository_inventory.md
```

Current event readiness classes:

```text
2015-03-16: E_ON2_available_no_SAPS_data
2015-03-17: A_ready_for_full_SAPS_ON2_matching
2015-03-18: A_ready_for_full_SAPS_ON2_matching
2014-02-19: G_missing_or_unusable
2011-10-25: G_missing_or_unusable
2013-06-30: G_missing_or_unusable
```

Interpretation:

- The current science output is a St. Patrick storm local-data smoke test covering 2015-03-16 to 2015-03-18.
- The current output is not yet the planned 2011-2015 multi-event SAPS/O/N2 statistics.
- The next work must focus on data acquisition, event expansion, and normalizer validation before science-level statistics.

---

## 1. Immediate planning correction

Codex should not continue improving only the 2015 matching results. The correct next objective is:

> Convert the existing smoke-test data layer into a multi-event-ready data system, then run controlled SAPS/O/N2 statistics only after the required data for the seed events and 2011-2015 storm universe are present.

This requires three parallel tracks:

```text
Track A: fill missing data for the three thesis-inspired SAPS events.
Track B: construct the 2011-2015 storm/SAPS/O/N2 event universe.
Track C: harden parsers, normalizers, and quality-control outputs so failed downloads or missing variables do not silently disappear.
```

---

## 2. Track A: complete the three thesis-inspired SAPS events

These events are essential because they validate the SAPS channel detector against known SuperDARN/DMSP SAPS evolution cases:

```text
2014-02-19: storm main phase; strong SAPS; DMSP F18 example around 0507-0521 UT; SuperDARN evolution around 0400-0530 UT.
2011-10-25: early recovery phase; SuperDARN SAPS evolution around 0400-0600 UT.
2013-06-30: late recovery phase; weak/broken SAPS; SuperDARN evolution around 0400-0600 UT.
```

### 2.1 Required data for each thesis event

For each event, acquire at minimum:

```text
TIMED/GUVI L3 O/N2: event_day_minus_1 to event_day_plus_1
DMSP SSIES: F16/F17/F18, event_day_minus_1 to event_day_plus_1
DMSP SSJ: same satellites/days if available, for precipitation boundary
DMSP SSUSI: same satellites/days if available, for auroral boundary and contamination mask
SuperDARN: preferably map/fit/grid files for 0300-0700 UT on event day, plus broader day context
OMNI/SYM-H/AE/Dst/Kp: event_day_minus_1 to event_day_plus_1
```

For 2014-02-19, prioritize the window:

```text
2014-02-19 0300-0700 UT
```

For 2011-10-25, prioritize:

```text
2011-10-25 0300-0700 UT
```

For 2013-06-30, prioritize:

```text
2013-06-30 0300-0700 UT
```

### 2.2 Expected outputs after download/normalization

For each event, Codex should create:

```text
data_work/normalized/guvi_on2/{YYYY}/{YYYYMMDD}/guvi_on2_normalized_{YYYYMMDD}.csv
data_work/normalized/dmsp_ssies/{YYYY}/{YYYYMMDD}/dmsp_ssies_normalized_{YYYYMMDD}.csv
data_work/normalized/superdarn/{YYYY}/{YYYYMMDD}/superdarn_normalized_{YYYYMMDD}.csv
data_work/normalized/ssusi/{YYYY}/{YYYYMMDD}/ssusi_normalized_{YYYYMMDD}.csv
data_work/normalized/indices/{YYYY}/{YYYYMMDD}/geomag_indices_{YYYYMMDD}.csv
```

and update:

```text
data_samples/screening_outputs/event_data_availability.csv
docs_index/data_manifest_local.csv
docs_index/data_manifest_missing.csv
summaries/screening_outputs/data_gap_report.md
```

### 2.3 Success criteria for Track A

The three thesis-inspired events should move from:

```text
G_missing_or_unusable
```

to one of:

```text
A_ready_for_full_SAPS_ON2_matching
B_ready_for_DMSP_GUVI_only
C_ready_for_SuperDARN_GUVI_only
D_SAPS_available_no_ON2
E_ON2_available_no_SAPS_data
```

If an event remains missing, the missing reason must be explicit:

```text
remote_data_not_found
manual_download_required
authentication_required
raw_file_present_parse_failed
raw_file_present_missing_variables
coverage_insufficient
```

---

## 3. Track B: build the 2011-2015 event universe

The first true science run should cover:

```text
2011-01-01 to 2015-12-31
```

This should be done in two stages.

### 3.1 Stage B1: storm-index event universe

Build a storm-day list from geomagnetic indices.

Selection criteria:

```text
primary: min(SYM-H or Dst) <= -50 nT
major subset: min(SYM-H or Dst) <= -100 nT
super-storm subset: min(SYM-H or Dst) <= -200 nT
```

For every storm minimum, include:

```text
storm_day_minus_1
storm_day
storm_day_plus_1
```

For strong storms, include:

```text
storm_day_minus_2 through storm_day_plus_3
```

Output:

```text
data_samples/screening_outputs/event_universe_2011_2015.csv
```

Minimum columns:

```text
event_id
event_date
storm_group_id
storm_min_time_ut
min_symh_or_dst
storm_class
include_reason
phase_window
priority_level
```

### 3.2 Stage B2: observation-opportunity event universe

Add days that may not pass the storm threshold but contain useful SAPS/O/N2 opportunities:

```text
DMSP westward drift candidate day
SuperDARN subauroral westward channel day
GUVI subauroral O/N2 opportunity day
SSUSI boundary-support day
```

These should be marked as `opportunity_added` so they can be separated from storm-index-selected events.

Output:

```text
data_samples/screening_outputs/event_universe_expanded_2011_2015.csv
```

### 3.3 Download manifest for 2011-2015

Generate required manifests from the expanded event universe:

```text
docs_index/data_manifest_required_2011_2015.csv
docs_index/download_queue_guvi_2011_2015.csv
docs_index/download_queue_dmsp_2011_2015.csv
docs_index/download_queue_superdarn_2011_2015.csv
docs_index/download_queue_ssusi_2011_2015.csv
docs_index/download_queue_indices_2011_2015.csv
```

---

## 4. Track C: harden normalizers and data-quality states

Every normalizer must write both normalized data and a status row.

### 4.1 Normalizer status table

Create:

```text
data_work/normalized/normalizer_status_all_events.csv
```

Columns:

```text
event_id
event_date
data_group
source_file
parse_status
normalized_output_path
n_records
n_valid_subauroral_records
missing_required_variables
coordinate_conversion_status
quality_flag_summary
failure_reason
last_run_utc
```

### 4.2 Required parse statuses

```text
parsed_ok
parsed_with_warnings
file_missing
unsupported_format
missing_required_variable
coordinate_conversion_failed
quality_rejected
empty_after_filtering
```

### 4.3 No silent failures

If a file is present but unusable, the event should not be labelled simply as missing. It should say why:

```text
present_but_parse_failed
present_but_quality_rejected
present_but_no_subauroral_coverage
present_but_no_dayglow_valid_on2
```

---

## 5. Science rerun sequence after data fill

Only after Tracks A-C have updated availability should Codex rerun the science matching.

### 5.1 Rerun seed events first

Run the full pipeline for:

```text
2015-03-16 to 2015-03-18
2014-02-19
2011-10-25
2013-06-30
```

Outputs:

```text
data_samples/screening_outputs/saps_channel_objects_seed_events.csv
data_samples/screening_outputs/on2_opportunity_seed_events.csv
data_samples/screening_outputs/saps_on2_match_candidates_seed_events.csv
data_samples/screening_outputs/nonmatch_selection_function_seed_events.csv
summaries/screening_outputs/seed_event_screening_summary.md
```

### 5.2 Then run 2011-2015 primary sample

Run:

```text
scripts/batch_screen_guvi_dmsp_saps_on2_events.py --event-list data_samples/screening_outputs/event_universe_expanded_2011_2015.csv
```

Outputs:

```text
data_samples/screening_outputs/saps_channel_objects_2011_2015.csv
data_samples/screening_outputs/on2_opportunity_2011_2015.csv
data_samples/screening_outputs/saps_on2_match_candidates_2011_2015.csv
data_samples/screening_outputs/nonmatch_selection_function_2011_2015.csv
summaries/screening_outputs/batch_screening_summary_2011_2015.md
```

---

## 6. Required statistical summaries after 2011-2015 data exist

Do not produce these until the 2011-2015 availability is real.

### 6.1 Denominator summary

```text
N_storm_days_checked
N_days_with_GUVI_ON2
N_days_with_DMSP_SSIES
N_days_with_SuperDARN_quantitative
N_days_with_SSUSI_boundary
N_days_ready_for_full_matching
N_days_rejected_by_quality
```

### 6.2 SAPS-channel summary

```text
N_DMSP_SAPS_crossings
N_SuperDARN_SAPS_channels
N_joint_DMSP_SuperDARN_channels
SAPS_grade_distribution
SAPS_morphology_distribution
SAPS_MLT_distribution
SAPS_storm_phase_distribution
```

### 6.3 O/N2 opportunity summary

```text
N_GUVI_ON2_patches
N_dayglow_valid_patches
N_twilight_caution_patches
N_subauroral_12_24_MLT_patches
N_inside_or_near_SAPS_channel_patches
```

### 6.4 SAPS/O/N2 response summary

```text
N_matches_0_1h
N_matches_1_3h
N_matches_3_6h
inside_minus_control_distribution
response_sign_distribution
response_by_storm_phase
response_by_MLT_sector
response_vs_DMSP_drift
response_vs_SuperDARN_velocity
```

---

## 7. Updated priority order for Codex

### Priority 1: Data status integrity

- keep current St. Patrick smoke-test outputs;
- make all missing data explicit;
- ensure manifests and normalizer status tables are complete.

### Priority 2: Three thesis-inspired events

- download/normalize 2014-02-19, 2011-10-25, and 2013-06-30;
- use them to validate SuperDARN channel detection and T-Slope;
- check GUVI O/N2 opportunity near their SAPS channels.

### Priority 3: 2011-2015 storm universe

- build event universe from SYM-H/Dst;
- generate data queues;
- download/normalize available data;
- rerun SAPS/O/N2 matching.

### Priority 4: 2010-2017 extension

- only after 2011-2015 works.

### Priority 5: 2018-2024 GOLD branch

- keep separate from GUVI statistics.

---

## 8. Acceptance criteria for the next phase

The next phase is complete when:

1. `data_manifest_required.csv`, `data_manifest_local.csv`, and `data_manifest_missing.csv` are updated after attempted downloads.
2. The three thesis-inspired events no longer have unexplained `G_missing_or_unusable` status.
3. `normalizer_status_all_events.csv` exists and records parse status for every data group.
4. `event_universe_2011_2015.csv` and `event_universe_expanded_2011_2015.csv` exist.
5. Download queues for 2011-2015 exist.
6. A seed-event science rerun has been performed after data acquisition.
7. If 2011-2015 statistics are not yet possible, `data_gap_report.md` states exactly why.
8. No output summary describes the current project as completed multi-event statistics until the 2011-2015 data universe has actually been processed.

---

## 9. Notes for manuscript/progress reporting

Current wording should be:

> We have completed the data-layer inventory and smoke-test run for the locally available St. Patrick storm data group. The current available science outputs cover 2015-03-16 to 2015-03-18. The thesis-inspired SAPS events and the planned 2011-2015 multi-event sample remain data-acquisition targets.

Do not write:

> We have completed 2011-2015 SAPS/O/N2 statistics.

Until the data fill is complete, the correct project state is:

```text
data-layer complete for local smoke test;
seed-event expansion prepared;
multi-event statistics pending data acquisition and normalization.
```
