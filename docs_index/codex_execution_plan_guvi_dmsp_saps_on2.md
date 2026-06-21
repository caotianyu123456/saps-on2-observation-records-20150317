# Codex Execution Plan: Statistical GUVI–DMSP–SuperDARN Screening for SAPS-Associated O/N2 Responses

Updated: 2026-06-21
Target repository: `caotianyu123456/saps-on2-observation-records-20150317`

## 0. Corrected project objective

This project is not only a 2015-03-17 case study. The real goal is to build a statistical or multi-case screening framework for finding events/windows where SAPS ion-drift channels overlap thermospheric O/N2 observations.

The 2015-03-17 St. Patrick's Day storm should remain as the first validation case and publication-quality example, but the code and tables must be designed from the beginning for batch screening across many storm events and many satellite conjunction windows.

Primary statistical science question:

> Across many geomagnetic storms, how often do SAPS-associated subauroral ion-drift channels coincide with TIMED/GUVI O/N2 depletion or O/N2 perturbations, and how does the O/N2 response depend on SAPS drift speed/channel strength, MLT, hemisphere, storm phase, and SuperDARN channel support?

Primary observational pair:

- SAPS channel: DMSP/SSIES horizontal ion drift, supplemented by SuperDARN convection/ion drift whenever available.
- Composition response: TIMED/GUVI L3 O/N2, preferably expressed as an anomaly or inside/outside-channel contrast.

Secondary/optional evidence:

- SuperDARN line-of-sight or map-potential ion drift/convection to define a two-dimensional SAPS channel. This is especially important for post-2020 events if subauroral flow coverage is better.
- DMSP/SSUSI FUV dayglow/O/N2-sensitive ratios or formal SSUSI-derived O/N2 if suitable product variables are available.
- DMSP/SSUSI auroral LBHS for auroral boundary and auroral-contamination context.
- RBSP/THEMIS/Swarm or other magnetospheric/ionospheric context only as supporting evidence, not as the primary SAPS definition.

---

## 1. Strategy: statistical-first, case-validated

Implement the project in three layers:

### Layer A: 2015-03-17 smoke test and strong case

Use the known 2015-03-17 windows to validate parsing, coordinate conversion, DMSP/GUVI matching, scoring, and figures. This case should not hard-code the whole workflow; it is a unit test and a flagship example.

Known best validation window from existing summaries:

- Southern hemisphere, AACGM 12–18 MLT, 2015-03-17, 17.25–21.25 UT, centered near 19.25 UT.
- GUVI: n about 614, median O/N2 about 0.332, min about 0.117.
- DMSP westward drift: n about 570, p95 about 3.35 km/s, max about 5.10 km/s.

Secondary validation window:

- Southern hemisphere, 12–24 MLT, roughly 21.0–02.5 UT.
- GUVI median O/N2 about 0.30–0.35, min about 0.114.
- DMSP westward p95 about 3.8–4.0 km/s, max about 4.84 km/s.

### Layer B: batch GUVI–DMSP statistical scan

After the 2015 validation passes, run the same algorithm on a broad event list. The unit of analysis should be an event/window, not a pixel. GUVI pixels are spatially correlated and affected by orbital selection; the statistical table should aggregate by candidate SAPS/O/N2 window.

### Layer C: SuperDARN-assisted and SSUSI-assisted expansion

Add SuperDARN-supported channel identification and optional SSUSI O/N2/proxy support. SuperDARN should not be treated as a minor add-on: it is the main way to overcome the one-dimensional nature of DMSP crossings and the different GUVI/DMSP viewing geometries.

---

## 2. Core concept: screen channel conjunctions, not point conjunctions

Do not require GUVI and DMSP to cross the exact same geographic point at the exact same time. Instead, define a time-dependent SAPS channel in magnetic coordinates:

```text
C(t) = {event_id, hemisphere, MLAT_eq, MLAT_pole, MLT_min, MLT_max, UT_start, UT_end, source}
```

DMSP/SSIES provides one-dimensional crossings through the SAPS channel. SuperDARN, when available, converts this into a more credible two-dimensional ion-drift/convection channel. GUVI points are then classified as:

```text
inside_channel
poleward_control
equatorward_control
same_MLT_outside_channel
quiet_or_reference_background, if available
```

Recommended coordinate system:

- Use AACGMV2 or Apex consistently for publication-quality statistics and figures.
- Do not mix centered-dipole screening products with AACGM/Apex final claims unless explicitly labelled.

---

## 3. Statistical event universe

Codex should create an event-list builder rather than manually coding one storm.

### 3.1 Event families to include

Create a configurable event list from one or more of the following sources:

1. Major storms by SYM-H/Dst threshold.
2. Moderate storms with strong SAPS probability.
3. Days with DMSP/SSIES high-latitude passes and GUVI O/N2 availability.
4. Days with SuperDARN subauroral convection coverage.
5. Post-2020 events prioritized for SuperDARN-assisted screening.
6. Optional: events where DMSP/SSUSI dayglow data are available for O/N2/proxy checks.

Suggested thresholds for event-list construction:

```text
Major storm list: min(SYM-H or Dst) <= -100 nT
Moderate storm list: min(SYM-H or Dst) <= -50 nT and AE/Kp elevated
SAPS-focused list: DMSP/SuperDARN shows subauroral westward drift/flow >= 0.5 km/s
GUVI-available list: valid GUVI O/N2 samples in |MLAT| 45–70 and MLT 12–24
```

The screening should not only keep positive matches. It must also save non-matches to quantify the selection function:

```text
storm_has_DMSP_SAPS_but_no_GUVI_overlap
storm_has_GUVI_ON2_depletion_but_no_DMSP_SAPS_crossing
storm_has_SuperDARN_channel_but_no_GUVI_overlap
storm_has_no_valid_quality_data
```

### 3.2 Recommended batch periods

Use the available local data first. Then design the code to expand to:

```text
GUVI era with DMSP SSIES overlap: event-date dependent
DMSP F16/F17/F18 era: especially useful for same-platform SSIES + SSUSI context
Post-2020 subset: prioritize SuperDARN-assisted channel detection
2018 onward optional: consider GOLD + DMSP + SuperDARN as a future branch, but do not mix GOLD with GUVI statistics unless separated
```

Do not hard-code a final year range until the repository inventory confirms what data are locally present or downloadable.

---

## 4. Input data required by the pipeline

### 4.1 DMSP/SSIES

Required normalized fields:

```text
event_date, time_utc, satellite, orbit_or_rev,
lat_geo, lon_geo, alt_km,
aacgm_mlat, aacgm_mlt,
horizontal_ion_drift_kms,
westward_ion_drift_kms,
ion_density, electron_density,
quality_flags
```

Notes:

- Existing repository convention: positive DMSP SSIES horizontal ion drift is treated as westward. Preserve this convention unless raw metadata prove otherwise.
- Convert all drift speeds to km/s.
- Save both signed westward drift and absolute drift.
- Require sustained intervals; do not define SAPS from single-point spikes.

### 4.2 TIMED/GUVI O/N2

Required normalized fields:

```text
event_date, time_utc, orbit,
lat_geo, lon_geo, sza, local_time,
aacgm_mlat, aacgm_mlt,
on2, on2_log, quality_flags,
native_or_interpolated
```

Rules:

- Prefer native/raw valid GUVI samples for statistics.
- Gridded/interpolated GUVI products may be used for display only unless clearly justified.
- Save SZA/local-time metadata whenever available.
- Compute O/N2 anomaly when possible.

### 4.3 SuperDARN

Two priority levels:

```text
Priority A: SuperDARN map/fit/grid files processed reproducibly with RST/pyDARN.
Priority B: quick-look convection maps for screening and figure planning only.
```

Required normalized fields if quantitative SuperDARN is used:

```text
event_date, time_utc, hemisphere,
aacgm_mlat, aacgm_mlt,
velocity_ms, flow_direction,
radar_id_or_map_id,
fit_quality, support_metric,
quicklook_or_quantitative
```

SuperDARN use cases:

1. Find subauroral westward flow channels independently of DMSP.
2. Extend DMSP one-dimensional crossings into two-dimensional SAPS channel polygons/ribbons.
3. Provide post-2020 event coverage where DMSP and GUVI do not exactly co-locate.
4. Separate Grade B/C events into stronger SuperDARN-supported subsets.

### 4.4 DMSP/SSUSI optional products

Use SSUSI first for auroral context, then optionally for O/N2-sensitive support.

Required auroral context fields:

```text
event_date, time_utc, satellite, rev, hemisphere,
mlat_grid, mlt_grid,
lbhs_radiance, lbhl_radiance,
auroral_boundary_or_precipitation_mask
```

Optional O/N2-related fields if available:

```text
OI_1356_radiance, N2_LBHS_radiance, N2_LBHL_radiance,
ON2_product_or_ratio, sza, look_angle, quality_flags
```

If no formal SSUSI O/N2 product exists, compute only a screening proxy:

```text
R_1356_LBHS = OI_1356_radiance / N2_LBHS_radiance
```

Label it as an O/N2-sensitive FUV ratio, not official O/N2.

---

## 5. Screening algorithms

### 5.1 DMSP-first SAPS channel search

For each DMSP high-latitude pass:

1. Convert to AACGM/Apex MLAT/MLT.
2. Keep subauroral candidates:

```text
45 <= |MLAT| <= 70 deg
Primary SAPS MLT: 15–24
Expanded GUVI-overlap MLT: 12–24
```

3. Identify sustained westward drift intervals.
4. Merge adjacent intervals separated by less than 2 minutes.
5. Record a SAPS crossing if:

```text
weak threshold: p95 westward drift >= 0.5 km/s
main threshold: p95 westward drift >= 1.0 km/s
strong/SAID-like threshold: peak westward drift >= 2.0 km/s
very strong threshold: peak westward drift >= 3.0 km/s
minimum duration >= 60 s
minimum latitudinal width >= 0.5 deg
```

6. Estimate channel boundaries:

```text
MLAT_eq, MLAT_pole, MLAT_center, width_deg
MLT_min, MLT_max or crossing_MLT_center
UT_start, UT_end, UT_center
```

### 5.2 SuperDARN-first SAPS channel search

For each event interval:

1. Load available SuperDARN map/fit/grid data if present.
2. Search for subauroral westward flow channels in:

```text
45 <= |MLAT| <= 70 deg
12 <= MLT <= 24, with focus on 15–24
velocity threshold: >= 300, 500, and 1000 m/s tiers
```

3. Define channel polygons/ribbons in AACGM coordinates.
4. Search for DMSP crossings through or near the SuperDARN channel within +/- 1–2 h.
5. Search for GUVI O/N2 samples inside the SuperDARN channel within +/- 1–4 h.
6. Save SuperDARN-only candidates even if DMSP did not cross, but grade them separately.

This algorithm is important for post-2020 expansion and for cases where DMSP does not happen to cross the strongest SAPS channel.

### 5.3 GUVI-first O/N2 depletion search

Use this to reduce SAPS-selection bias.

For every GUVI O/N2 day/orbit:

1. Search subauroral GUVI samples:

```text
45 <= |MLAT| <= 70 deg
12 <= MLT <= 24
valid O/N2 and quality flags
```

2. Identify low-O/N2 patches using one or more criteria:

```text
raw O/N2 below local percentile threshold, e.g., p20
log(O/N2) anomaly below -1 sigma, if baseline exists
inside-day sector median lower than controls
```

3. For each GUVI depletion patch, search DMSP SAPS crossings within +/- 1, 2, and 4 h.
4. Add SuperDARN support if a channel is present.
5. Keep both matches and non-matches.

### 5.4 Combined candidate grading

Use Grades A/B/C for statistical stratification:

```text
Grade A:
  Strong DMSP or SuperDARN SAPS channel.
  GUVI inside-channel O/N2 samples within <= 1 h.
  Good GUVI quality and usable control regions.

Grade B:
  Strong SAPS channel.
  GUVI inside-channel samples within <= 2 h.
  Independent SuperDARN or SSUSI auroral-boundary support.

Grade C:
  Possible SAPS/O/N2 overlap within <= 4 h.
  Useful for screening/statistical occurrence but not a strong causal case.

Rejected:
  Poor quality, no meaningful control, bad coordinate match, obvious auroral contamination, or no valid overlap.
```

---

## 6. O/N2 statistics and controls

Do not rely only on raw GUVI O/N2 values. For every candidate window compute:

```text
inside_channel_ON2
poleward_control_ON2
equatorward_control_ON2
same_MLT_outside_channel_ON2
quiet_or_reference_ON2, if possible
```

For each region compute:

```text
n
median_ON2
p05_ON2
p25_ON2
p75_ON2
min_ON2
median_log_ON2
anomaly_log_ON2 if baseline exists
inside_minus_equatorward
inside_minus_poleward
inside_minus_same_MLT_outside
```

Baseline hierarchy:

1. Best: quiet-day or multi-day median matched in MLAT/MLT/SZA/local time.
2. Good: same storm, same MLT, outside SAPS channel.
3. Screening fallback: raw ON2 and inside/outside contrast only.

Save the baseline method in every row.

---

## 7. Candidate scoring

Create a score for ranking windows. Use this score for selection, but preserve all raw components for later sensitivity tests.

```text
S_total = S_drift + S_on2 + S_time + S_mlt + S_lat + S_support - S_contamination
```

Suggested definitions:

```text
S_drift = min(DMSP_westward_p95_kms / 1.0, 3.0)
S_on2 = max(0, -ON2_anomaly_zscore) if anomaly exists
       or max(0, (0.5 - median_ON2_inside) / 0.1) as screening fallback
S_time = exp(-abs(delta_t_hours) / 2.0)
S_mlt = exp(-abs(delta_mlt_hours) / 1.5)
S_lat = exp(-distance_to_channel_center_deg / 2.0)
S_support = 0 to 4 points
  +1 for quantitative SuperDARN channel support
  +0.5 for quick-look SuperDARN support
  +1 for SSUSI auroral-boundary context
  +1 for SSUSI O/N2 or O/N2-sensitive ratio support
  +0.5 for RBSP/magnetospheric E-field support
S_contamination = 0 to 3 points
  penalty for auroral contamination, poor GUVI quality, bad SZA, or inconsistent coordinates
```

---

## 8. Required outputs

### 8.1 Repository inventory

Create or update:

```text
docs_index/current_repository_inventory.md
```

It should list available GUVI, DMSP SSIES, SuperDARN, SSUSI, RBSP, THEMIS, Swarm, scripts, figures, and sample tables.

### 8.2 Batch event table

Create:

```text
data_samples/screening_outputs/event_universe.csv
data_samples/screening_outputs/event_data_availability.csv
```

Minimum columns for `event_universe.csv`:

```text
event_id
event_date
storm_start_ut
storm_end_ut
min_symh_or_dst
time_min_symh_or_dst
max_ae_or_kp
storm_phase_tags
has_guvi
has_dmsp_ssies
has_superdarn
has_ssusi
has_gold_future_branch
priority_level
notes
```

Minimum columns for `event_data_availability.csv`:

```text
event_id
event_date
guvi_valid_sample_count_subauroral_12_24
dmsp_pass_count_subauroral_12_24
dmsp_saps_crossing_count
superdarn_channel_candidate_count
ssusi_file_count
ssusi_on2_or_proxy_possible
missing_data_reason
```

### 8.3 Candidate-window tables

Create:

```text
data_samples/screening_outputs/candidate_windows_20150317.csv
data_samples/screening_outputs/candidate_windows_all_events.csv
data_samples/screening_outputs/dmsp_saps_crossings_all_events.csv
data_samples/screening_outputs/guvi_on2_patches_all_events.csv
data_samples/screening_outputs/superdarn_channels_all_events.csv
data_samples/screening_outputs/ssusi_on2_or_ratio_support_all_events.csv
```

Minimum candidate-window columns:

```text
event_id
event_date
hemisphere
window_start_ut
window_end_ut
center_ut
source_pathway
candidate_grade
score_total
score_drift
score_on2
score_time
score_mlt
score_lat
score_support
score_contamination
coordinate_system
mlt_min
mlt_max
mlat_eq
mlat_pole
mlat_center
channel_width_deg
dmsp_satellites
dmsp_orbits_or_revs
dmsp_n
dmsp_westward_median_kms
dmsp_westward_p95_kms
dmsp_westward_max_kms
superdarn_support_flag
superdarn_support_type
superdarn_velocity_p95_ms
superdarn_velocity_max_ms
guvi_n_inside
guvi_on2_median_inside
guvi_on2_p05_inside
guvi_on2_min_inside
guvi_on2_anomaly_inside
guvi_n_equatorward_control
guvi_on2_median_equatorward_control
guvi_n_poleward_control
guvi_on2_median_poleward_control
inside_minus_equatorward
inside_minus_poleward
baseline_method
ssusi_support_flag
ssusi_support_type
rbsp_support_flag
main_caveat
recommended_for_case_study
recommended_for_statistics
```

### 8.4 Figures

For 2015 validation:

```text
figures/screening_outputs/fig_20150317_primary_aacgm_12_18_guvi_dmsp.png
figures/screening_outputs/fig_20150317_primary_timeseries.png
figures/screening_outputs/fig_20150317_inside_outside_on2_boxplot.png
figures/screening_outputs/fig_20150317_superdarn_supported_channel.png
figures/screening_outputs/fig_20150317_ssusi_on2_ratio_support.png
```

For statistics:

```text
figures/screening_outputs/stat_occurrence_by_mlt.png
figures/screening_outputs/stat_occurrence_by_hemisphere.png
figures/screening_outputs/stat_on2_response_vs_dmsp_drift.png
figures/screening_outputs/stat_on2_response_vs_superdarn_velocity.png
figures/screening_outputs/stat_grade_distribution.png
figures/screening_outputs/stat_selection_function_data_availability.png
```

Each figure must have a parallel `.md` caption file explaining data source, coordinate system, time tolerance, and caveat.

### 8.5 Summary reports

Create:

```text
summaries/screening_outputs/screening_summary_20150317.md
summaries/screening_outputs/batch_screening_summary_all_events.md
summaries/screening_outputs/statistical_findings_preliminary.md
summaries/screening_outputs/limitations_and_selection_function.md
```

---

## 9. Scripts to implement

### 9.1 Inventory and event selection

```text
scripts/build_event_universe.py
scripts/inventory_repository_data.py
```

`build_event_universe.py` should construct or update `event_universe.csv` from locally available files and configurable storm-date lists.

### 9.2 Core screening

```text
scripts/screen_guvi_dmsp_saps_on2_candidates.py
scripts/batch_screen_guvi_dmsp_saps_on2_events.py
```

`screen_guvi_dmsp_saps_on2_candidates.py` should run a single-event screen.

`batch_screen_guvi_dmsp_saps_on2_events.py` should loop over all events and write `candidate_windows_all_events.csv`.

### 9.3 SuperDARN support

```text
scripts/add_superdarn_channel_support.py
scripts/screen_superdarn_saps_channels.py
```

The code must distinguish:

```text
quantitative_from_map_or_fit_files
screening_only_from_quicklook
not_available
```

### 9.4 SSUSI support

```text
scripts/add_ssusi_on2_or_ratio_support.py
scripts/inspect_ssusi_on2_variables.py
```

The code must distinguish:

```text
official_or_validated_ON2_product
OI1356_LBHS_proxy_only
auroral_context_only
not_available
```

### 9.5 Plotting/statistics

```text
scripts/plot_primary_case_20150317.py
scripts/plot_batch_statistics.py
scripts/summarize_selection_function.py
```

---

## 10. Immediate Codex task list

### Task 1: Convert the project to statistical-first structure

Update directory outputs so that single-event and all-event outputs are both supported.

### Task 2: Build repository inventory and event availability table

Create:

```text
docs_index/current_repository_inventory.md
data_samples/screening_outputs/event_data_availability.csv
```

### Task 3: Validate with 2015-03-17

Reproduce or explain differences from the known best 2015-03-17 AACGM 12–18 MLT window.

### Task 4: Implement batch GUVI–DMSP scan

Run the same logic across all available event dates, not only 2015-03-17.

### Task 5: Add SuperDARN-first and SuperDARN-assisted modes

Use SuperDARN to define or support SAPS channels, especially for post-2020 events.

### Task 6: Add optional SSUSI O/N2/proxy mode

Attempt SSUSI only after the main GUVI–DMSP statistical table works.

### Task 7: Generate preliminary statistical figures

At minimum:

```text
occurrence by MLT
occurrence by hemisphere
O/N2 response vs DMSP drift
O/N2 response vs SuperDARN velocity, if available
Grade A/B/C distribution
selection-function/data-availability summary
```

---

## 11. Acceptance criteria

The implementation is acceptable when:

1. The 2015-03-17 candidate is reproduced or transparently explained.
2. The code produces an `event_universe.csv` and `event_data_availability.csv`.
3. The code produces `candidate_windows_all_events.csv`, not only the 2015 table.
4. Candidate windows include grade, score, caveat, source pathway, and data-availability flags.
5. GUVI statistics distinguish inside-channel and control regions.
6. DMSP SAPS crossings are identified from sustained westward drift intervals, not isolated spikes.
7. SuperDARN support is labelled as quantitative, quick-look screening, or unavailable.
8. SSUSI support is labelled as official O/N2, proxy ratio, auroral context only, or unavailable.
9. The batch statistics explicitly report non-matches and data-availability limits.
10. Final summaries clearly separate observational coincidence, statistical association, and causal interpretation.

---

## 12. Recommended manuscript framing

Primary manuscript concept:

> Statistical screening of SAPS-associated thermospheric O/N2 responses using DMSP ion drifts, TIMED/GUVI O/N2, and SuperDARN convection channels

Role of 2015-03-17:

- A validation/flagship case.
- A detailed example showing how the automated screening identifies a strong SAPS/O/N2 overlap.
- Not the sole objective of the project.

Claim hierarchy:

- Strong: A reproducible multi-event screening framework identifies SAPS/O/N2 conjunction candidates and quantifies the selection function.
- Strong: DMSP/SuperDARN-defined SAPS channels can be compared with GUVI O/N2 inside/outside-channel statistics.
- Moderate: O/N2 depletion or perturbation occurrence can be stratified by SAPS drift speed, MLT, hemisphere, storm phase, and SuperDARN support.
- Avoid without model support: SAPS directly caused every observed O/N2 depletion.

Future branch:

- Add GOLD for 2018 onward as a separate analysis branch.
- Add SSUSI-derived O/N2 or O/N2-sensitive proxy as an independent DMSP-platform check when feasible.
