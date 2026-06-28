# Codex Master Plan: SAPS Channel + O/N2 Statistical Screening

Updated: 2026-06-22
Repository: `caotianyu123456/saps-on2-observation-records-20150317`

## 0. Purpose

This is the master execution plan for Codex.

The goal is not only to reproduce the 2015-03-17 case. The real goal is to build a reproducible pipeline that can:

1. identify reliable SAPS channels from DMSP/SSIES and SuperDARN;
2. build an O/N2 opportunity database from GUVI and other available O/N2 sources;
3. match SAPS channels to O/N2 observations in the same or nearby magnetic coordinates;
4. compare O/N2 inside/near SAPS channels with control regions;
5. first produce a controlled multi-event study, and later expand to broader statistics.

The 2015-03-17 St. Patrick's Day storm remains a validation and flagship example. It must not be hard-coded as the only target.

The SAPS screening rules should follow the logic of Zhang Qiang's 2021 PhD thesis on SAPS evolution and SAPS-associated ion upflow: DMSP detects crossings, SuperDARN defines larger-scale channels, SSUSI constrains auroral boundaries, and storm/substorm phase must be tagged.

---

## 1. Overall research design

### 1.1 Four-level sample structure

Use four sample levels to avoid the false choice between several hand-picked cases and uncontrolled full-database statistics.

#### Level 0: Storm/substorm event universe

All candidate storm and substorm intervals.

Purpose:

- document the denominator;
- measure data availability;
- preserve non-matches and rejected intervals;
- avoid hand-picked event selection.

Output:

```text
data_samples/screening_outputs/event_universe.csv
data_samples/screening_outputs/event_data_availability.csv
```

#### Level 1: SAPS channel candidate library

All DMSP/SuperDARN-detected SAPS channels, regardless of whether O/N2 is available.

Output:

```text
data_samples/screening_outputs/dmsp_saps_crossings_all_events.csv
data_samples/screening_outputs/superdarn_saps_channels_all_events.csv
data_samples/screening_outputs/saps_channel_objects_all_events.csv
```

#### Level 2: SAPS/O/N2 match candidate library

SAPS channels with O/N2 coverage inside or near the channel within the lag windows.

Output:

```text
data_samples/screening_outputs/on2_opportunity_all_sources.csv
data_samples/screening_outputs/saps_on2_match_candidates_all_events.csv
```

#### Level 3: High-quality physical cases

Multi-instrument, high-confidence cases for publication figures and mechanism discussion.

Initial high-quality cases should include, if data permit:

```text
2014-02-19: winter, storm main phase, strong SAPS, SuperDARN case in Zhang thesis.
2011-10-25: autumn/equinox-adjacent, early recovery phase, SuperDARN case in Zhang thesis.
2013-06-30: summer, late recovery phase, weak/broken SAPS, SuperDARN case in Zhang thesis.
2015-03-17: equinox, strong storm, existing GUVI+DMSP O/N2 validation case.
```

---

## 2. Recommended year ranges

### 2.1 Detector validation period

```text
2010-2014
```

Reason:

- Zhang thesis used DMSP F16/F17/F18 2010-2014 to identify SAPS and SAPS-associated ion upflow.
- Use this range to validate the DMSP SAPS detector.

### 2.2 Primary GUVI+DMSP+SuperDARN science period

```text
2011-2015
```

Reason:

- Since 2011, the North American midlatitude SuperDARN chain is more complete.
- Includes the three Zhang thesis SuperDARN SAPS evolution cases and the 2015-03-17 strong GUVI/DMSP validation case.
- Covers multiple seasons and storm phases.

### 2.3 Extension period

```text
2010-2017
```

Reason:

- Increases sample size after the primary workflow is stable.
- Enables comparison between higher solar activity and declining solar activity years.

### 2.4 GOLD/SuperDARN future branch

```text
2018-2024
```

Reason:

- GOLD O/N2 has very different observing geometry from GUVI.
- Treat this as a separate branch, not mixed directly into the GUVI statistics.

---

## 3. Outer event selection: storm and substorm universe

Build `event_universe.csv` first.

### 3.1 Storm selection

Use SYM-H or Dst as the main storm index.

Recommended bins:

```text
minor_storm:       -50 nT < min(SYM-H/Dst) <= -30 nT
moderate_storm:   -100 nT < min(SYM-H/Dst) <= -50 nT
major_storm:      -200 nT < min(SYM-H/Dst) <= -100 nT
super_storm:      min(SYM-H/Dst) <= -200 nT
```

Primary sample:

```text
moderate_storm or stronger: min(SYM-H/Dst) <= -50 nT
strong-storm subset: min(SYM-H/Dst) <= -100 nT
```

### 3.2 Storm phase tags

Each SAPS/O/N2 candidate must carry storm phase labels:

```text
initial_phase
main_phase
early_recovery
late_recovery
quiet_or_nonstorm
```

Suggested automatic definition:

```text
main_phase: interval from storm onset to time of minimum SYM-H/Dst
early_recovery: first 0-12 h after minimum SYM-H/Dst
late_recovery: 12-72 h after minimum SYM-H/Dst, or until recovery to -30 nT
```

### 3.3 Substorm tags

AE/AL should be used as an inner modulation variable, not the outermost event definition.

Recommended AE bins:

```text
quiet_or_weak: 0-250 nT
small_substorm: 250-500 nT
moderate_substorm: 500-1000 nT
large_substorm: >1000 nT
```

Each candidate window should include:

```text
ae_max_in_window
al_min_in_window
ae_bin
substorm_phase_if_available
```

---

## 4. SAPS channel detection overview

Do not define SAPS using a single velocity threshold. A valid SAPS channel must satisfy a combination of:

```text
velocity condition
subauroral location condition
auroral-boundary condition
morphology/continuity condition
context/support condition
quality-control condition
```

The pipeline should produce a `SAPS_channel_object`, not just an `is_saps=True/False` flag.

### 4.1 Unified SAPS channel object

Every channel object should include:

```text
channel_id
event_id
event_date
hemisphere
source_pathway              # DMSP_only / SuperDARN_only / joint_DMSP_SuperDARN
time_start_ut
time_end_ut
time_center_ut
storm_phase
substorm_phase_or_ae_bin
mlt_min
mlt_max
mlt_center
mlat_eq
mlat_pole
mlat_center
channel_width_deg
velocity_median
velocity_p95
velocity_max
velocity_units
saps_morphology_class
saps_confidence_score
saps_grade                  # A/B/C/rejected
auroral_boundary_source
peak_relative_to_auroral_boundary
superdarn_vector_quality
dmsp_geometry_quality
main_caveat
```

---

## 5. DMSP-first SAPS channel detector

Implement:

```text
scripts/detect_dmsp_saps_crossings.py
```

### 5.1 Input data

DMSP normalized fields:

```text
time_utc
satellite
orbit_or_rev
lat_geo
lon_geo
aacgm_mlat
aacgm_mlt
horizontal_ion_drift_kms
westward_ion_drift_kms
ion_density
electron_density
ssj_electron_energy_flux, if available
ssj_ion_energy_flux, if available
quality_flags
```

### 5.2 Spatial prefilter

```text
45 <= |AACGM_MLAT| <= 70 deg
12 <= AACGM_MLT <= 24 for O/N2-oriented search
15 <= AACGM_MLT <= 24 for classical SAPS core search
```

### 5.3 DMSP geometry filter

Only use DMSP cross-track/y-axis drift as SAPS drift if the orbit geometry is suitable.

Required field:

```text
dmsp_track_auroral_boundary_angle_deg
```

Quality grades:

```text
A: angle <= 30 deg
B: 30 < angle <= 45 deg
C/reject: angle > 45 deg, unless only used as weak candidate
```

### 5.4 Velocity thresholds

Use multiple thresholds and keep threshold metadata.

```text
wide_detection_threshold:
  premidnight peak >= 250 m/s
  postmidnight peak >= 100 m/s

baseline_SAPS_threshold:
  westward peak >= 500 m/s
  or westward p95 >= 500 m/s

strong_SAPS:
  westward peak >= 1000 m/s

SAID_like_or_very_strong:
  westward peak >= 2000 m/s and narrow channel

extreme:
  westward peak >= 3000 m/s
```

Primary statistical sample should use `baseline_SAPS_threshold` and above. The wide threshold is for sensitivity and candidate discovery only.

### 5.5 Sustained interval requirement

Do not identify SAPS from a single-point spike.

```text
minimum_duration_s >= 60
minimum_width_deg >= 0.5
merge_gaps_s <= 30-60
smoothing_window_s = 8-20, depending on native cadence
```

The script should compute:

```text
time_start
time_end
time_peak
mlat_start
mlat_end
mlat_peak
width_deg
westward_peak_kms
westward_p95_kms
westward_median_kms
```

### 5.6 Velocity profile morphology

A valid DMSP SAPS crossing should have a clear peak or inflection.

Required fields:

```text
has_velocity_peak_or_inflection
number_of_westward_peaks
peak_prominence
peak_width_deg
```

### 5.7 Auroral boundary condition

The westward velocity peak should be at or equatorward of the auroral oval equatorward boundary.

Boundary sources, priority order:

```text
1. DMSP/SSJ precipitation boundary
2. DMSP/SSUSI LBHS auroral boundary
3. empirical auroral boundary model
4. SuperDARN convection reversal / return-flow boundary
5. manual case-study boundary, only for validation figures
```

Unified condition:

```text
abs(mlat_peak) <= abs(auroral_equatorward_boundary_mlat) + tolerance
```

Recommended tolerance:

```text
0.5-1.0 deg
```

### 5.8 DMSP morphology classification

Classify SAPS morphology instead of mixing all types.

```text
class_1_regular_saps:
  one westward peak equatorward of auroral oval; primary statistical sample

class_2_boundary_merged:
  one peak near auroral equatorward boundary, possibly merged with sunward return flow; usable with caution

class_3_double_peak_dsaps_dsaid:
  two westward peaks outside auroral boundary; keep separate

class_4_asaps_asaid:
  strong eastward subauroral flow; exclude from main SAPS/O/N2 sample unless separate study

uncertain:
  no clear peak, noisy, or boundary missing
```

Main sample:

```text
class_1_regular_saps
class_2_boundary_merged if confidence is high
```

### 5.9 Output

```text
data_samples/screening_outputs/dmsp_saps_crossings_all_events.csv
```

Minimum columns:

```text
crossing_id
event_id
event_date
satellite
orbit_or_rev
hemisphere
time_start_ut
time_end_ut
time_peak_ut
aacgm_mlat_peak
aacgm_mlt_peak
mlat_eq
mlat_pole
channel_width_deg
westward_peak_kms
westward_p95_kms
westward_median_kms
saps_threshold_tier
has_velocity_peak_or_inflection
number_of_westward_peaks
dmsp_track_auroral_boundary_angle_deg
dmsp_geometry_quality
auroral_boundary_source
auroral_equatorward_boundary_mlat
peak_relative_to_boundary_deg
saps_morphology_class
saps_confidence_score
saps_grade
rejection_reason
```

---

## 6. SuperDARN-first SAPS channel detector

Implement:

```text
scripts/screen_superdarn_saps_channels.py
```

### 6.1 Coverage gate

Before detecting SAPS, determine whether SuperDARN coverage is sufficient.

Required fields:

```text
superdarn_available
radar_count
valid_echo_count
time_coverage_min
mlt_coverage_h
mlat_coverage_deg
has_sufficient_echo
```

Suggested minimum:

```text
weak_candidate: radar_count >= 1, time_coverage >= 20 min, MLT coverage >= 1 h
vector_quality_candidate: radar_count >= 2 or merged-vector availability
high_quality_case: duration >= 60 min, MLT extent >= 2 h
```

### 6.2 Data and time binning

Use quantitative map/fit/grid files whenever possible. Quick-look images are screening only.

Recommended bins:

```text
time_bin = 4 min
MLT_bin = 0.25-0.5 h
MLAT_bin = 0.5-1.0 deg
```

### 6.3 Velocity quality classification

```text
V_quality_A:
  multi-radar vector fit

V_quality_B:
  single-radar LOS projected using nearby merged-vector direction

V_quality_C:
  LOS-only or quick-look qualitative support
```

Only A/B should be used for quantitative velocity statistics. C can support candidate context only.

### 6.4 Spatial and velocity conditions

```text
45 <= |AACGM_MLAT| <= 70 deg
12 <= MLT <= 24 for O/N2-oriented search
15 <= MLT <= 24 for classical SAPS core search
westward component dominates
```

Velocity tiers:

```text
weak: 100-300 m/s
baseline: 300-500 m/s
strong: 500-1000 m/s
very_strong: >1000 m/s
```

Primary quantitative SAPS channel threshold:

```text
westward velocity >= 500 m/s, or p95 >= 500 m/s in connected channel
```

The 100 m/s threshold may be kept for broad velocity-vector statistics and sensitivity, not for main channel identification.

### 6.5 Auroral boundary and SAPS latitude band

Use SSUSI/SSJ/empirical auroral boundary to restrict SAPS to the equatorward side of the auroral oval.

Recommended SuperDARN condition:

```text
0 <= abs(boundary_mlat) - abs(channel_mlat) <= 10 deg
```

Sensitivity tests:

```text
5 deg, 8 deg, 10 deg, 12 deg
```

### 6.6 Connected-component channel definition

A SuperDARN SAPS channel should be a connected westward flow structure, not isolated bins.

Suggested conditions:

```text
minimum_duration_min >= 20-30
minimum_mlt_extent_h >= 1.0
minimum_connected_bins >= 3-5
maximum_gap_time_min <= 8-12
dominant_flow_direction = westward
```

For high-quality evolution cases:

```text
duration_min >= 60
mlt_extent_h >= 2-3
```

### 6.7 T-Slope and longitudinal extent

For each SuperDARN channel, compute SAPS velocity as a function of MLT and fit a linear slope.

Fields:

```text
saps_t_slope
saps_t_slope_r_value
saps_longitudinal_extent_mlt
saps_dusk_to_midnight_expansion_flag
```

Interpretation:

```text
negative slope expected for classical dusk-to-midnight SAPS speed structure;
more negative slope = stronger MLT transport in the Zhang-thesis convention;
positive or chaotic slope = broken/late-recovery/nonclassical SAPS candidate.
```

### 6.8 Output

```text
data_samples/screening_outputs/superdarn_saps_channels_all_events.csv
```

Minimum columns:

```text
superdarn_channel_id
event_id
event_date
hemisphere
time_start_ut
time_end_ut
time_center_ut
mlt_min
mlt_max
mlat_eq
mlat_pole
mlat_center
velocity_median_ms
velocity_p95_ms
velocity_max_ms
velocity_threshold_tier
vector_quality
radar_count
valid_echo_count
duration_min
mlt_extent_h
auroral_boundary_source
boundary_relative_position
saps_t_slope
saps_t_slope_r_value
saps_morphology_class
saps_confidence_score
saps_grade
main_caveat
```

---

## 7. Joint DMSP + SuperDARN SAPS channel builder

Implement:

```text
scripts/build_saps_channel_objects.py
```

### 7.1 Merge criteria

Match DMSP crossings with SuperDARN channels if:

```text
same event_date
same hemisphere
abs(delta_time) <= 1 h for strong match; <= 2 h for weak match
abs(delta_MLT) <= 1 h
abs(delta_MLAT) <= 2 deg
DMSP peak lies inside or near SuperDARN channel ribbon
```

### 7.2 Channel source grades

```text
DMSP_only:
  one-dimensional crossing; can be Grade A only if DMSP morphology and auroral-boundary support are excellent.

SuperDARN_only:
  two-dimensional flow channel; can be Grade A only if vector quality and boundary support are good.

joint_DMSP_SuperDARN:
  preferred high-confidence source for O/N2 statistics.
```

### 7.3 Output

```text
data_samples/screening_outputs/saps_channel_objects_all_events.csv
```

---

## 8. O/N2 opportunity database

Implement:

```text
scripts/build_on2_opportunity_database.py
```

The O/N2 opportunity database is essential because O/N2 coverage is the limiting factor, not SAPS occurrence.

### 8.1 O/N2 sources

Primary:

```text
TIMED/GUVI L3 O/N2
```

Secondary / branch:

```text
GOLD ON2, 2018 onward, separate branch
DMSP/SSUSI formal O/N2 if available
DMSP/SSUSI OI1356/LBHS proxy, screening only
```

### 8.2 GUVI/GOLD/SSUSI normalized fields

```text
on2_source                 # GUVI / GOLD / SSUSI_ON2 / SSUSI_proxy
event_date
time_utc
orbit_or_scan_id
hemisphere
lat_geo
lon_geo
aacgm_mlat
aacgm_mlt
local_time
sza
on2
log_on2
on2_quality_flag
native_or_interpolated
dayglow_quality_flag
twilight_or_sza_caveat
```

### 8.3 Spatial prefilter

```text
45 <= |AACGM_MLAT| <= 70 deg
12 <= MLT <= 24
```

Sub-bins:

```text
12-15 MLT
15-18 MLT
18-21 MLT
21-24 MLT
```

### 8.4 Dayglow/SZA quality

For every O/N2 point, save:

```text
sza
local_time
dayglow_valid
twilight_flag
night_or_ambiguous_flag
```

Do not mix high-quality dayglow O/N2 with twilight/night ambiguous samples unless stratified.

### 8.5 O/N2 patches/windows

Cluster O/N2 samples into patches/windows by source, hemisphere, MLAT, MLT, and time.

Output:

```text
data_samples/screening_outputs/on2_opportunity_all_sources.csv
data_samples/screening_outputs/guvi_on2_patches_all_events.csv
```

Minimum patch columns:

```text
on2_patch_id
on2_source
event_id
event_date
hemisphere
time_start_ut
time_end_ut
time_center_ut
mlt_min
mlt_max
mlat_min
mlat_max
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

---

## 9. Matching SAPS channels with O/N2 observations

Implement:

```text
scripts/match_saps_channels_to_on2.py
```

### 9.1 Time-lag bins

Use lag from SAPS to O/N2:

```text
delta_t_hours = t_ON2 - t_SAPS_channel_center
```

Recommended bins:

```text
near_simultaneous: 0-1 h
short_lag_response: 1-3 h     # primary delayed neutral/composition response window
delayed_response: 3-6 h       # sensitivity / cautious interpretation
storm_context: 6-12 h         # background only, not strong causal evidence
```

Primary analysis:

```text
0-1 h and 1-3 h
```

### 9.2 Spatial matching classes

For each O/N2 point/patch relative to each SAPS channel:

```text
inside_channel:
  inside channel ribbon, with optional +/- 0.5-1 deg padding

near_channel:
  within +/- 2 deg MLAT or +/- 1 h MLT of channel boundary

equatorward_control:
  2-5 deg equatorward of channel, same MLT/time window

poleward_control:
  2-5 deg poleward of channel, same MLT/time window, excluding auroral contamination

same_MLT_outside_channel:
  same MLT sector outside inside/near regions
```

### 9.3 DMSP-crossing-relative O/N2 profile

For DMSP crossings, build a relative profile:

```text
relative_coordinate = signed distance to SAPS peak or channel center
```

Bins:

```text
equatorward_pre
inside_channel
poleward_post
near_equatorward
near_poleward
```

Important flags:

```text
track_direction
time_order_before_after
spatial_side_equatorward_poleward
```

Do not confuse time-before/after with spatial equatorward/poleward.

Output:

```text
data_samples/screening_outputs/dmsp_crossing_relative_on2_profiles_all_events.csv
```

### 9.4 O/N2 response metrics

Compute for each match:

```text
ON2_inside_median
ON2_near_channel_median
ON2_equatorward_control_median
ON2_poleward_control_median
ON2_same_MLT_outside_median
log_ON2_inside_median
log_ON2_control_median
delta_ON2_inside_minus_equatorward
delta_ON2_inside_minus_poleward
delta_ON2_inside_minus_same_MLT
delta_log_ON2_inside_minus_control
response_sign                   # depletion / enhancement / no_response
response_strength_category       # weak / moderate / strong
```

Baseline priority:

```text
Priority 1: quiet-day or multi-day baseline matched by MLAT/MLT/SZA/source
Priority 2: same-storm same-MLT outside-channel control
Priority 3: same-event equatorward/poleward control
Priority 4: raw O/N2 only, screening-level
```

---

## 10. Candidate grading

### Grade A

High-confidence SAPS/O/N2 match:

```text
SAPS channel Grade A or strong Grade B
O/N2 samples inside/near channel within 0-1 h or 1-3 h
same hemisphere and matched MLT/MLAT
valid O/N2 dayglow quality
inside/control regions available
DMSP+SuperDARN joint support, or one source very strong plus boundary support
```

### Grade B

Usable statistical candidate:

```text
SAPS channel credible but one support component missing
O/N2 within 1-3 h or 3-6 h
inside or near-channel O/N2 available
control available but imperfect
SuperDARN or DMSP support present
```

### Grade C

Screening candidate only:

```text
wide time lag
weak/uncertain SAPS morphology
boundary missing or SuperDARN sparse
O/N2 quality acceptable but not ideal
```

### Rejected

```text
single-point drift spike
inside auroral oval rather than subauroral
polar cap convection
ASAPS/eastward flow mixed into westward SAPS sample
DMSP geometry angle >45 deg without correction
no sustained interval
no meaningful O/N2 control region
poor O/N2 quality or strong auroral contamination
```

---

## 11. Required output tables

### 11.1 Event and data availability

```text
data_samples/screening_outputs/event_universe.csv
data_samples/screening_outputs/event_data_availability.csv
```

### 11.2 SAPS channels

```text
data_samples/screening_outputs/dmsp_saps_crossings_all_events.csv
data_samples/screening_outputs/superdarn_saps_channels_all_events.csv
data_samples/screening_outputs/saps_channel_objects_all_events.csv
```

### 11.3 O/N2 opportunity and patches

```text
data_samples/screening_outputs/on2_opportunity_all_sources.csv
data_samples/screening_outputs/guvi_on2_patches_all_events.csv
data_samples/screening_outputs/gold_on2_patches_all_events.csv
data_samples/screening_outputs/ssusi_on2_or_ratio_support_all_events.csv
```

### 11.4 SAPS/O/N2 matches

```text
data_samples/screening_outputs/saps_on2_match_candidates_all_events.csv
data_samples/screening_outputs/dmsp_crossing_relative_on2_profiles_all_events.csv
```

### 11.5 Non-matches and selection function

```text
data_samples/screening_outputs/nonmatch_selection_function_all_events.csv
```

Required non-match categories:

```text
storm_no_saps_detected
saps_no_on2_coverage
on2_depletion_no_saps_match
superdarn_channel_no_dmsp_crossing
superdarn_channel_no_on2_coverage
dmsp_saps_no_superdarn_support
poor_on2_quality
poor_saps_quality
rejected_auroral_contamination
```

---

## 12. Required figures

### 12.1 Validation and physical-case figures

```text
figures/screening_outputs/fig_20150317_primary_aacgm_12_18_guvi_dmsp.png
figures/screening_outputs/fig_20150317_dmsp_relative_on2_profile.png
figures/screening_outputs/fig_20140219_superdarn_saps_on2_opportunity.png
figures/screening_outputs/fig_20111025_superdarn_saps_on2_opportunity.png
figures/screening_outputs/fig_20130630_superdarn_saps_on2_opportunity.png
```

### 12.2 Statistical figures

```text
figures/screening_outputs/stat_saps_channel_occurrence_by_mlt.png
figures/screening_outputs/stat_saps_on2_match_occurrence_by_mlt.png
figures/screening_outputs/stat_on2_response_by_lag_bin.png
figures/screening_outputs/stat_on2_response_vs_dmsp_drift.png
figures/screening_outputs/stat_on2_response_vs_superdarn_velocity.png
figures/screening_outputs/stat_on2_response_vs_t_slope.png
figures/screening_outputs/stat_response_sign_by_storm_phase.png
figures/screening_outputs/stat_selection_function_nonmatches.png
figures/screening_outputs/stat_data_availability_by_year.png
```

Each figure must have a parallel `.md` caption with:

```text
data sources
coordinate system
time window
lag bin
SAPS channel source
O/N2 source
quality caveat
```

---

## 13. Scripts to implement

### 13.1 Inventory and event universe

```text
scripts/inventory_repository_data.py
scripts/build_event_universe.py
scripts/tag_storm_and_substorm_phase.py
```

### 13.2 SAPS detection

```text
scripts/detect_dmsp_saps_crossings.py
scripts/screen_superdarn_saps_channels.py
scripts/build_saps_channel_objects.py
scripts/score_saps_channel_confidence.py
```

### 13.3 O/N2 opportunity and matching

```text
scripts/build_on2_opportunity_database.py
scripts/build_on2_patches.py
scripts/match_saps_channels_to_on2.py
scripts/build_dmsp_crossing_relative_on2_profiles.py
```

### 13.4 Optional support

```text
scripts/inspect_ssusi_on2_variables.py
scripts/add_ssusi_boundary_and_on2_support.py
scripts/add_ampere_r2_fac_support.py
scripts/add_tec_trough_support.py
```

### 13.5 Plotting and summaries

```text
scripts/plot_saps_on2_validation_cases.py
scripts/plot_saps_on2_statistics.py
scripts/summarize_selection_function.py
scripts/summarize_threshold_sensitivity.py
```

---

## 14. Threshold sensitivity tests

Every threshold set should have an ID.

Required sensitivity dimensions:

```text
DMSP velocity threshold: 250/100 m/s, 500 m/s, 1000 m/s, 2000 m/s
SuperDARN velocity threshold: 100, 300, 500, 1000 m/s
DMSP duration threshold: 30, 60, 120 s
SuperDARN duration threshold: 20, 30, 60 min
O/N2 lag bin: 0-1, 1-3, 3-6 h
MLAT padding: 0.5, 1.0, 2.0 deg
MLT tolerance: 0.5, 1.0, 2.0 h
Auroral-boundary latitude band: 5, 8, 10, 12 deg equatorward
O/N2 response criterion: raw ON2, log ON2, inside-control difference, quiet-baseline anomaly
```

Output:

```text
data_samples/screening_outputs/threshold_sensitivity_results.csv
summaries/screening_outputs/threshold_sensitivity_summary.md
```

---

## 15. Codex execution order

### Phase 1: Repository inventory

Create:

```text
docs_index/current_repository_inventory.md
data_samples/screening_outputs/event_data_availability.csv
```

### Phase 2: SAPS detector validation

Implement DMSP detector and validate on 2010-2014 / thesis-like cases.

Required:

```text
dmsp_saps_crossings_all_events.csv
summary of detector threshold counts
comparison against known 2014-02-19 DMSP F18 example if data exist
```

### Phase 3: SuperDARN detector validation

Implement SuperDARN detector and validate on:

```text
2014-02-19
2011-10-25
2013-06-30
```

Required:

```text
superdarn_saps_channels_all_events.csv
saps_t_slope for validation events
coverage and echo sufficiency report
```

### Phase 4: O/N2 opportunity database

Implement GUVI O/N2 availability scan first.

Required:

```text
on2_opportunity_all_sources.csv
guvi_on2_patches_all_events.csv
```

Then add optional GOLD and SSUSI branches.

### Phase 5: Match SAPS channels to O/N2

Create:

```text
saps_on2_match_candidates_all_events.csv
dmsp_crossing_relative_on2_profiles_all_events.csv
nonmatch_selection_function_all_events.csv
```

### Phase 6: Validation cases and first statistics

Produce 2015-03-17 validation figures and the three thesis-inspired SuperDARN event opportunity checks.

Then produce first statistics for 2011-2015.

---

## 16. Acceptance criteria

The Codex implementation is acceptable when:

1. The code produces event-level, SAPS-channel-level, O/N2-opportunity-level, and SAPS/O/N2-match-level tables.
2. SAPS channels are not identified by a single threshold alone; boundary, geometry, morphology, duration, and continuity are included.
3. DMSP SAPS crossings include geometry quality and morphology class.
4. SuperDARN channels include echo availability, vector quality, duration, MLT extent, and T-Slope.
5. O/N2 statistics include inside, near, equatorward-control, poleward-control, and same-MLT outside-channel regions.
6. O/N2 matches are stratified by lag bins: 0-1 h, 1-3 h, 3-6 h.
7. The output includes non-matches and rejected windows.
8. The first science run covers 2011-2015 and includes the 2015-03-17 validation case.
9. The 2018+ GOLD branch is kept separate from the GUVI statistics.
10. Summary reports clearly separate observational coincidence, statistical association, and causal interpretation.

---

## 17. Manuscript framing

Recommended first-paper framing:

> A controlled multi-event screening of SAPS-associated thermospheric O/N2 responses using DMSP ion drifts, SuperDARN convection channels, and TIMED/GUVI O/N2.

Recommended claim level:

- Strong: The pipeline identifies SAPS channels with quantified confidence from DMSP and SuperDARN.
- Strong: The pipeline quantifies when SAPS channels have valid O/N2 observations inside/near them.
- Moderate: O/N2 depletion/enhancement can be statistically stratified by SAPS strength, lag, MLT, season, and storm phase.
- Avoid without model support: every O/N2 depletion near a SAPS channel is directly caused by SAPS.
