# Codex Next Work Plan After Upload Recovery

Updated: 2026-06-30
Repository: `caotianyu123456/saps-on2-observation-records-20150317`

## 0. Current state from latest uploaded progress

The GitHub write channel has recovered enough to upload the next-stage quicklook, manifests, priority ranking, upload pending note, and normalizer V3 summary.

The project state is still:

```text
local seed-event data-readiness and St. Patrick smoke-test stage
not completed 2011-2015 multi-event SAPS/O/N2 statistics
```

Latest quicklook states that the current package keeps the project in:

```text
data acquisition
normalizer hardening
detector-gate
Batch-1 acquisition-pilot mode
```

It also says explicitly that final 2011-2015 statistics should not be run from the present state because seed validation events still need instrument files and Batch-1 is only prioritized for top-5 acquisition.

Key latest counts:

```text
seed missing/blocking rows: 12
Batch-1 readiness rows: 129
ranked Batch-1 storm groups: 22
```

Normalizer V3 summary currently reports:

```text
download_queue_only_blocking: 12
parsed_ok_science_ready: 21
raw_or_screening_dmsp_not_science_ready: 25
raw_or_screening_guvi_not_science_ready: 7
ssusi_boundary_support_not_materialized: 249
superdarn_quicklook_or_missing_quantitative_data: 101
```

The St. Patrick rows are preserved as smoke-test rows, but GUVI/DMSP/SuperDARN/SSUSI are not promoted to science-ready until dayglow, AACGM/MLT, detector geometry, boundary, and quantitative SuperDARN fields are materialized.

---

## 1. Immediate correction after upload recovery

### 1.1 Update upload verification status

The uploaded verification manifest still contains rows whose status is:

```text
github_upload_status = pending_verification
github_visible = False
```

This should be refreshed after the successful upload recovery.

Create or update:

```text
scripts/verify_github_upload_recovery.py
summaries/screening_outputs/github_upload_recovery_verification_20260630.md
docs_index/next_stage_after_20260629_upload_verification_manifest_v2.csv
```

The v2 manifest should classify each artifact as:

```text
remote_visible
manifest_only_local_large_artifact
summary_uploaded_full_data_local
upload_failed
not_attempted
```

Special rule:

```text
normalizer_status_all_events_v3.csv may remain manifest-only / local-large-artifact if SHA256, row count, and summary are uploaded.
```

Acceptance criteria:

```text
all small text files have remote_visible status;
large local artifacts are intentionally marked manifest_only;
no row remains pending_verification unless the connector fails again.
```

---

## 2. Use Normalizer V3 as the new data gate

From now on, Codex should use:

```text
data_work/normalized/normalizer_status_all_events_v3.csv
```

as the primary local gatekeeper for science readiness.

If the full CSV is not uploaded to GitHub, Codex should use the local file plus the uploaded SHA/row manifest and summary.

Required next summary:

```text
summaries/screening_outputs/normalizer_v3_gate_decision_table.md
```

This summary should group rows by:

```text
science_ready
blocked_by_download_queue
blocked_by_missing_required_variable
blocked_by_no_dayglow_or_no_on2
blocked_by_no_quantitative_superdarn
blocked_by_unmaterialized_ssusi_boundary
smoke_test_only
```

Do not run detector or matching on rows outside `science_ready` or explicitly allowed `smoke_test_only` rows.

---

## 3. Resolve the 12 seed-event instrument blockers

The most important next science action is still to resolve the 12 blocking rows for:

```text
2014-02-19
2011-10-25
2013-06-30
```

These events remain essential validation targets for SAPS channel detection.

### 3.1 Required data groups

For each validation event, resolve or explicitly mark:

```text
GUVI L3 O/N2
DMSP SSIES / SSJ
SuperDARN map/fit/grid or verified quick-look-only status
DMSP/SSUSI auroral boundary support
```

### 3.2 Required output

Create:

```text
summaries/screening_outputs/validation_event_instrument_blocker_resolution.md
docs_index/validation_event_data_resolution_table.csv
```

Each blocker must have one status:

```text
downloaded_and_linked
manual_download_required
authentication_required
remote_data_not_found
local_path_missing
raw_present_parse_failed
not_needed_for_current_gate
```

### 3.3 Important rule

If a validation event still lacks instrument files, preserve it as a no-data/nonmatch row. Do not drop it and do not pretend it is a detector failure.

---

## 4. Science-ready St. Patrick normalizer work

The 2015-03-17/18 St. Patrick rows should be promoted from smoke-test to science-ready only after normalized fields exist.

### 4.1 Required science-ready GUVI fields

```text
time_utc
lat_geo
lon_geo
aacgm_mlat
aacgm_mlt
local_time
sza
on2
log_on2
quality_flags
dayglow_quality_flag
source_file
```

### 4.2 Required science-ready DMSP fields

```text
time_utc
satellite
lat_geo
lon_geo
aacgm_mlat
aacgm_mlt
horizontal_ion_drift_kms
westward_ion_drift_kms
ion_density
electron_density
quality_flags
sign_convention_note
source_file
```

### 4.3 Required SSUSI and SuperDARN status

SSUSI:

```text
auroral_boundary_available
auroral_contamination_mask_available
boundary_source
```

SuperDARN:

```text
quantitative_map_fit_grid
quicklook_only
insufficient_echo
not_available
```

Quick-look must not be treated as quantitative velocity.

### 4.4 Required outputs

```text
data_samples/screening_outputs/st_patrick_science_ready_normalizer_rows.csv
summaries/screening_outputs/st_patrick_science_ready_normalizer_summary.md
```

---

## 5. Rerun seed-event detector gate after V3 normalizer decisions

After Sections 2-4, rerun seed detector outputs only on science-ready or explicitly smoke-test-allowed rows.

Required outputs:

```text
data_samples/screening_outputs/dmsp_saps_crossings_seed_events_v3.csv
data_samples/screening_outputs/superdarn_saps_channels_seed_events_v3.csv
data_samples/screening_outputs/saps_channel_objects_seed_events_v3.csv
summaries/screening_outputs/seed_detector_gate_v3_summary.md
```

Detector rules remain:

```text
DMSP: sustained westward interval, >=500 m/s baseline threshold, geometry quality, boundary relation, morphology class.
SuperDARN: quantitative map/fit/grid required for velocity/T-Slope claims; quick-look gives context only.
```

Validation-event no-data rows should remain explicit if data are absent.

---

## 6. Rerun science-ready O/N2 opportunity and matching

Once seed channel objects V3 exist, run:

```text
scripts/build_on2_opportunity_database.py
scripts/build_on2_patches.py
scripts/match_saps_channels_to_on2.py
scripts/build_dmsp_crossing_relative_on2_profiles.py
```

Required outputs:

```text
data_samples/screening_outputs/on2_opportunity_seed_events_v2_science_ready.csv
data_samples/screening_outputs/guvi_on2_patches_seed_events_v2_science_ready.csv
data_samples/screening_outputs/saps_on2_match_candidates_seed_events_v2_science_ready.csv
data_samples/screening_outputs/dmsp_crossing_relative_on2_profiles_seed_events_v2_science_ready.csv
data_samples/screening_outputs/nonmatch_selection_function_seed_events_v2_science_ready.csv
summaries/screening_outputs/seed_event_science_ready_matching_v2_summary.md
```

Use lag bins:

```text
0-1 h
1-3 h
3-6 h
6-12 h context only
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

## 7. Batch-1 top-5 acquisition pilot

The Batch-1 major/super storm subset has 129 event rows and 22 storm groups. Do not process all rows first.

Use:

```text
docs_index/batch1_major_storm_group_priority.csv
```

as the storm-group ranking input.

### 7.1 Top-5 selection rule

Top-5 must include, if present:

```text
storm_153_2015031722
storm_025_2011102501
```

The remaining top-5 groups should be selected by:

```text
min(Dst)
seasonal coverage
expected GUVI day-dusk O/N2 opportunity
expected DMSP F16/F17/F18 coverage
expected SuperDARN MLT coverage
SSUSI boundary likelihood
existing local data availability
```

### 7.2 Required outputs

```text
docs_index/download_queue_batch1_top5_guvi.csv
docs_index/download_queue_batch1_top5_dmsp.csv
docs_index/download_queue_batch1_top5_superdarn.csv
docs_index/download_queue_batch1_top5_ssusi.csv
docs_index/download_queue_batch1_top5_indices.csv
summaries/screening_outputs/batch1_top5_acquisition_status.md
```

### 7.3 Do not run final Batch-1 statistics yet

Only run Batch-1 matching after at least one top-5 storm group has:

```text
science-ready GUVI O/N2
science-ready DMSP or quantitative SuperDARN SAPS detector data
science-ready indices
at least one inside/near/control O/N2 opportunity
```

---

## 8. Required progress reports after this stage

Create or update:

```text
summaries/screening_outputs/github_upload_recovery_verification_20260630.md
summaries/screening_outputs/normalizer_v3_gate_decision_table.md
summaries/screening_outputs/validation_event_instrument_blocker_resolution.md
summaries/screening_outputs/st_patrick_science_ready_normalizer_summary.md
summaries/screening_outputs/seed_detector_gate_v3_summary.md
summaries/screening_outputs/seed_event_science_ready_matching_v2_summary.md
summaries/screening_outputs/batch1_top5_acquisition_status.md
summaries/screening_outputs/next_stage_execution_after_upload_recovery_summary.md
```

Each summary must say:

```text
what was run
what data were present
what data remain blocked
what rows are science-ready
what rows are smoke-test only
what cannot yet be claimed
```

---

## 9. Final acceptance criteria

This next stage is complete only when:

```text
upload verification manifest v2 exists and resolves pending statuses
normalizer V3 gate decision table exists
validation-event blocker resolution exists
St. Patrick science-ready normalized rows exist or explicit caveats exist
seed detector v3 outputs exist
seed O/N2 matching v2 science-ready outputs exist
Batch-1 top-5 acquisition status exists
no summary claims completed 2011-2015 statistics
```

Correct final wording after this stage:

```text
Upload recovery is complete; seed-event data gates are explicit; St. Patrick smoke-test rows have been upgraded or caveated through science-ready normalizer checks; validation-event data blockers are resolved or documented; Batch-1 top-5 acquisition pilot is prepared. Full 2011-2015 SAPS/O/N2 statistics remain pending instrument-data acquisition and normalization.
```
