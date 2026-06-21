# Codex Execution Plan: GUVI–DMSP–SuperDARN Screening for SAPS-Associated O/N2 Responses

Updated: 2026-06-21
Target repository: `caotianyu123456/saps-on2-observation-records-20150317`

## 0. Scientific objective

Build a reproducible screening pipeline to find events/windows where SAPS ion-drift channels and thermospheric composition observations overlap.

Primary science question:

> Do SAPS-associated subauroral ion-drift channels coincide with TIMED/GUVI O/N2 depletion or other O/N2 perturbations during geomagnetic storms?

Primary observational pair:

- SAPS channel: DMSP/SSIES horizontal ion drift, supplemented by SuperDARN convection when available.
- Composition response: TIMED/GUVI L3 O/N2, preferably expressed as an anomaly relative to a suitable background.

Secondary/optional evidence:

- SuperDARN line-of-sight or map-potential ion drift/convection to define a two-dimensional SAPS channel.
- DMSP/SSUSI FUV dayglow/O/N2-sensitive ratios, if suitable SSUSI dayglow variables are available.
- DMSP/SSUSI auroral LBHS for auroral boundary and particle-precipitation contamination context.
- RBSP mapped electric field as supporting magnetospheric context, not as a standalone SAPS proof.

The first deliverable should be a case-study-ready screening table and figures for 2015-03-17. The second deliverable should be a generalized event scanner that can be extended to multi-event statistics.

---

## 1. Strategy decision

Do not choose between case study and statistics at the start. Implement the project as:

1. A strong case study for 2015-03-17.
2. A screening framework that is immediately expandable into statistics.

The case-study manuscript should include a transparent candidate-window table, so the selected event/window does not look hand-picked.

Current best candidate from existing repository summaries:

- Southern hemisphere, AACGM 12–18 MLT, 2015-03-17, 17.25–21.25 UT, centered near 19.25 UT.
- GUVI: n about 614, median O/N2 about 0.332, min about 0.117.
- DMSP westward drift: n about 570, p95 about 3.35 km/s, max about 5.10 km/s.

Secondary candidate:

- Southern hemisphere, 12–24 MLT, roughly 21.0–02.5 UT.
- GUVI median O/N2 about 0.30–0.35, min about 0.114.
- DMSP westward p95 about 3.8–4.0 km/s, max about 4.84 km/s.

---

## 2. Core concept: define a SAPS channel, not a point conjunction

Avoid requiring GUVI and DMSP to cross the exact same geographic point at the exact same time. Instead, define a time-dependent SAPS channel in magnetic coordinates:

```text
C(t) = {hemisphere, MLAT_eq, MLAT_pole, MLT_min, MLT_max, UT_start, UT_end}
```

DMSP/SSIES provides one-dimensional crossings through the SAPS channel. SuperDARN, when available, turns this into a more credible two-dimensional channel. GUVI points are then classified as inside-channel, poleward-control, or equatorward-control samples.

Recommended magnetic coordinate system:

- Use AACGMV2 or Apex consistently for publication-quality products.
- Do not mix centered-dipole screening results with AACGM/Apex final figures unless clearly labelled.

---

## 3. Input data expected by the pipeline

### 3.1 DMSP/SSIES

Required fields after parsing:

```text
time_utc, satellite, orbit_or_rev, lat_geo, lon_geo, alt_km,
aacgm_mlat, aacgm_mlt,
horizontal_ion_drift_kms, westward_ion_drift_kms,
ion_density, electron_density, quality_flags
```

Notes:

- Existing repository convention: positive DMSP SSIES horizontal ion drift is treated as westward. Keep this convention unless raw metadata prove otherwise.
- Convert all drift speeds to km/s in summary tables.
- Store both signed drift and absolute drift.

### 3.2 TIMED/GUVI O/N2

Required fields:

```text
time_utc, orbit, lat_geo, lon_geo, sza, local_time,
aacgm_mlat, aacgm_mlt, on2, quality_flags
```

Use GUVI L3 O/N2 where possible. Preserve raw swath points. Gridded/interpolated products may be used for display, but statistics should preferably be computed from valid raw or native product samples.

### 3.3 SuperDARN

Two priority levels:

Priority A: real SuperDARN map or fit files processed with RST/pyDARN.

Priority B: quick-look convection maps for screening only.

Required outputs if SuperDARN is used quantitatively:

```text
time_utc, hemisphere, grid_or_map_id,
aacgm_mlat, aacgm_mlt,
los_velocity_or_convection_velocity_ms,
flow_direction, fit_quality, radar_count_or_support_metric
```

Use SuperDARN to:

1. Confirm a dusk-side/subauroral westward flow channel.
2. Extend DMSP point crossings into a two-dimensional channel.
3. Provide an independent ion-convection constraint, especially for post-2020 events with improved subauroral coverage.

### 3.4 DMSP/SSUSI optional products

Use SSUSI first as auroral context, then as optional O/N2-sensitive support.

Required auroral context fields:

```text
time_utc, satellite, rev, hemisphere,
mlat_grid, mlt_grid, lbhs_radiance, lbhl_radiance,
auroral_boundary_or_precipitation_mask
```

Optional O/N2-related fields, if available:

```text
OI_1356_radiance, N2_LBHS_radiance, N2_LBHL_radiance,
ON2_product_or_ratio, sza, look_angle, quality_flags
```

If no formal SSUSI O/N2 product is available, compute only a screening proxy:

```text
R_1356_LBHS = OI_1356_radiance / N2_LBHS_radiance
```

Label it as an O/N2-sensitive FUV ratio, not as official O/N2.

---

## 4. Event and window search logic

### 4.1 DMSP-first search

For each DMSP high-latitude pass:

1. Convert trajectory to AACGM/Apex MLAT and MLT.
2. Keep samples in subauroral candidate band:
   - `45 <= |MLAT| <= 70` degrees.
   - Primary MLT: 15–24 MLT.
   - Expanded MLT for GUVI overlap: 12–24 MLT.
3. Identify sustained westward drift intervals.
4. Merge adjacent intervals separated by less than 2 minutes.
5. Record candidate SAPS crossing if:
   - weak threshold: p95 westward drift >= 0.5 km/s;
   - main threshold: p95 westward drift >= 1.0 km/s;
   - strong/SAID-like threshold: peak westward drift >= 2.0 km/s;
   - very strong threshold: peak westward drift >= 3.0 km/s.
6. Estimate channel center latitude and width:
   - `MLAT_eq` and `MLAT_pole` from threshold crossing boundaries.
   - `MLAT_center = 0.5 * (MLAT_eq + MLAT_pole)`.
   - `width_deg = abs(MLAT_pole - MLAT_eq)`.

Recommended default SAPS crossing requirements:

```text
abs(MLAT) between 45 and 70 deg
MLT between 12 and 24
westward p95 >= 1.0 km/s OR westward max >= 2.0 km/s
minimum duration >= 60 s
minimum latitudinal width >= 0.5 deg
```

### 4.2 GUVI overlap search

For each DMSP SAPS crossing, search GUVI samples in the same hemisphere and similar MLT sector.

Search windows:

```text
Grade A: |Delta t| <= 1 h, |Delta MLT| <= 1 h
Grade B: |Delta t| <= 2 h, |Delta MLT| <= 2 h, plus SuperDARN or SSUSI support
Grade C: |Delta t| <= 4 h, |Delta MLT| <= 3 h, screening only
```

A GUVI sample is inside the SAPS channel if:

```text
same hemisphere
MLAT between MLAT_eq - 1 deg and MLAT_pole + 1 deg
MLT within channel MLT range +/- tolerance
valid O/N2 and quality flags pass
SZA/dayglow condition acceptable for O/N2 product
```

Define control regions:

```text
Equatorward control: 2–5 deg equatorward of SAPS channel, same MLT/time window.
Poleward control: 2–5 deg poleward of SAPS channel, same MLT/time window, excluding strong auroral contamination if possible.
Same-MLT storm control: same MLT sector outside channel.
Quiet/reference control: quiet-day or multi-day median in the same MLAT/MLT/SZA bin, if available.
```

Compute for inside and controls:

```text
n, median_ON2, p05_ON2, p25_ON2, p75_ON2, min_ON2
median_log_ON2, anomaly_log_ON2 if baseline exists
inside_minus_equatorward_control
inside_minus_poleward_control
```

### 4.3 SuperDARN-assisted search

Use this path to avoid over-reliance on DMSP one-dimensional crossings.

For each storm interval:

1. Identify subauroral westward flow channel in SuperDARN maps or fit files.
2. Define the channel in AACGM MLT/MLAT as a polygon or ribbon.
3. Check whether DMSP crosses the same channel within +/- 1–2 hours.
4. Check whether GUVI samples the channel or neighboring control regions within +/- 1–4 hours.
5. Flag the event as SuperDARN-supported.

For events after 2020, explicitly prioritize SuperDARN because expanded subauroral coverage may capture more SAPS ion drift channels.

Suggested event families for later expansion:

```text
2015-03-17 St. Patrick's Day storm: current primary event.
2018 onward: consider GOLD + DMSP + SuperDARN in addition to GUVI.
2020 onward: prioritize SuperDARN-supported SAPS channel selection.
```

### 4.4 GUVI-first search

This path is useful for reducing SAPS-selection bias in future statistics.

1. Search GUVI subauroral O/N2 low-anomaly regions:
   - `45 <= |MLAT| <= 70` degrees.
   - `12 <= MLT <= 24`.
   - O/N2 below local p20 or anomaly below -1 sigma.
2. For each GUVI depletion patch, search DMSP/SSIES SAPS crossings within +/- 1, 2, and 4 hours.
3. Add SuperDARN support when available.
4. Save all candidates, including non-matches, for selection-function diagnostics.

---

## 5. Candidate scoring

Create a score for ranking windows. The exact coefficients can be adjusted after inspecting the first results.

Suggested components:

```text
S_total = S_drift + S_on2 + S_time + S_mlt + S_lat + S_support - S_contamination
```

Definitions:

```text
S_drift = min(DMSP_westward_p95_kms / 1.0, 3.0)
S_on2 = max(0, -ON2_anomaly_zscore) if anomaly exists
       or max(0, (0.5 - median_ON2) / 0.1) as screening fallback
S_time = exp(-abs(delta_t_hours) / 2.0)
S_mlt = exp(-abs(delta_mlt_hours) / 1.5)
S_lat = exp(-distance_to_channel_center_deg / 2.0)
S_support = 0 to 3 points
  +1 for SuperDARN channel support
  +1 for SSUSI auroral-boundary context
  +1 for RBSP mapped E-field support
S_contamination = 0 to 3 points
  +1 to +3 penalty for strong auroral precipitation contamination, poor GUVI quality, high SZA problems, or inconsistent coordinates
```

Required output rank:

```text
Grade A: strong DMSP/SuperDARN SAPS, GUVI inside channel within 1 h, good O/N2 quality.
Grade B: strong SAPS, GUVI within 2 h, independent SuperDARN/SSUSI support.
Grade C: possible SAPS/O/N2 overlap within 4 h; screening only.
Rejected: poor coordinate match, poor quality, no meaningful control region, or obvious auroral contamination.
```

---

## 6. Required outputs

### 6.1 Tables

Create these files under `data_samples/screening_outputs/`:

1. `candidate_windows_20150317.csv`
2. `candidate_windows_all_events.csv` once generalized
3. `dmsp_saps_crossings_20150317.csv`
4. `guvi_channel_on2_stats_20150317.csv`
5. `superdarn_channel_support_20150317.csv` if SuperDARN data are processed
6. `ssusi_on2_or_ratio_support_20150317.csv` if SSUSI O/N2 or proxy is attempted

Minimum candidate-window columns:

```text
event_date
hemisphere
window_start_ut
window_end_ut
center_ut
source_priority
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
superdarn_support_flag
ssusi_support_flag
rbsp_support_flag
main_caveat
recommended_for_figure
```

### 6.2 Figures

Create figures under `figures/screening_outputs/`:

1. `fig_20150317_primary_aacgm_12_18_guvi_dmsp.png`
   - Polar MLT/MLAT map.
   - GUVI O/N2 points colored by O/N2 or anomaly.
   - DMSP track and westward drift arrows.
   - SAPS channel ribbon.
   - Inside/equatorward/poleward control bands.

2. `fig_20150317_primary_timeseries.png`
   - DMSP westward drift vs UT.
   - GUVI O/N2 samples in channel vs UT or along-track coordinate.
   - Mark selected candidate window.

3. `fig_20150317_superdarn_supported_channel.png`
   - SuperDARN flow/convection background if available.
   - GUVI and DMSP overlaid.
   - Label as publication-quality only if produced from proper map/fit files, not quick-look images.

4. `fig_20150317_inside_outside_on2_boxplot.png`
   - O/N2 inside channel vs equatorward/poleward controls.
   - Use raw O/N2 and, if available, anomaly.

5. Optional: `fig_20150317_ssusi_on2_ratio_support.png`
   - SSUSI O/N2 product or OI1356/LBHS proxy.
   - DMSP SSIES track/drift overlaid.

### 6.3 Summary reports

Create markdown summaries under `summaries/screening_outputs/`:

1. `screening_summary_20150317.md`
2. `primary_case_summary_20150317.md`
3. `limitations_and_quality_control.md`

Each summary must state:

- Coordinate system used.
- Time tolerance used.
- Whether GUVI points are raw/native or interpolated.
- Whether SuperDARN is quick-look or quantitatively processed.
- Whether SSUSI result is official O/N2 or only a FUV ratio proxy.
- Why the selected window is Grade A/B/C.
- What evidence supports coincidence and what does not prove causality.

---

## 7. Quality control rules

### 7.1 Coordinate consistency

- All final statistics and figures should use AACGMV2 or Apex.
- Centered-dipole results may remain in legacy screening summaries but should not be used for final quantitative claims.
- Store coordinate system metadata in every CSV and figure caption.

### 7.2 GUVI O/N2 quality

- Exclude invalid O/N2 values and bad-quality flags.
- Record SZA and local time where available.
- Prefer dayglow-valid observations.
- Avoid interpreting raw O/N2 alone; compute anomaly when possible.
- If anomaly is not yet available, explicitly call the result screening-level.

### 7.3 DMSP drift quality

- Remove obvious spikes and flagged bad samples.
- Require sustained drift intervals rather than isolated single-point maxima.
- Preserve both signed westward drift and absolute drift.
- Check whether large drift occurs in subauroral region and not inside obvious auroral precipitation core.

### 7.4 SuperDARN quality

- Quick-look maps may be used only for screening and visual context.
- Publication-level statistics should use map/fit files and reproducible processing.
- Include radar coverage/support metrics when possible.

### 7.5 SSUSI O/N2/proxy quality

- Do not call `OI1356/LBHS` an official O/N2 product unless a validated retrieval is implemented or a product variable exists.
- Mask or flag strong auroral precipitation regions.
- Use SSUSI first as supporting evidence, not as the primary O/N2 result.

---

## 8. Immediate Codex task list

### Task 1: Repository inventory

Inspect current repository directories and file names. Create or update an inventory file:

```text
docs_index/current_repository_inventory.md
```

The inventory should list available:

- GUVI files and summaries.
- DMSP SSIES parsed files and summaries.
- SuperDARN quick-look or map-related files.
- SSUSI files and summaries.
- RBSP/THEMIS/Swarm support files.
- Existing scripts that can be reused.

### Task 2: Implement a unified candidate-window table for 2015-03-17

Create a script:

```text
scripts/screen_guvi_dmsp_saps_on2_candidates.py
```

The script should:

1. Load parsed DMSP SSIES and GUVI O/N2 samples if available locally.
2. Convert/verify AACGM or Apex coordinates.
3. Find DMSP SAPS crossings.
4. Search GUVI overlap points for Grade A/B/C windows.
5. Compute inside/control O/N2 statistics.
6. Write `data_samples/screening_outputs/candidate_windows_20150317.csv`.
7. Write `summaries/screening_outputs/screening_summary_20150317.md`.

### Task 3: Reproduce the current best 2015-03-17 window

The script must reproduce or explain differences from the existing best window:

```text
hemisphere: S
MLT: 12–18
window: 17.25–21.25 UT
GUVI median O/N2: about 0.332
DMSP westward p95: about 3.35 km/s
DMSP westward max: about 5.10 km/s
```

If exact reproduction is impossible because raw large files are absent, write a clear note in the summary and use available sample tables/summaries as fixtures.

### Task 4: Add SuperDARN-assisted channel support

Create a script or module:

```text
scripts/add_superdarn_channel_support.py
```

This should:

1. Detect available SuperDARN files or quick-look references.
2. If only quick-look exists, mark support as screening-only.
3. If map/fit files exist, compute quantitative channel support.
4. Add `superdarn_support_flag`, `superdarn_time_range`, and `superdarn_caveat` to the candidate table.

### Task 5: Add optional SSUSI O/N2 or FUV-ratio support

Create a script or module:

```text
scripts/add_ssusi_on2_or_ratio_support.py
```

This should:

1. Inspect SSUSI files for formal O/N2 variables.
2. If unavailable, inspect for OI 135.6 and N2 LBHS/LBHL radiance variables.
3. Compute only a proxy ratio if a formal product is absent.
4. Flag auroral contamination using LBHS intensity or existing auroral-boundary information.
5. Write `data_samples/screening_outputs/ssusi_on2_or_ratio_support_20150317.csv`.
6. State clearly whether this is official O/N2 or a screening proxy.

### Task 6: Generate publication-planning figures

Create or update plotting scripts to generate:

```text
figures/screening_outputs/fig_20150317_primary_aacgm_12_18_guvi_dmsp.png
figures/screening_outputs/fig_20150317_primary_timeseries.png
figures/screening_outputs/fig_20150317_inside_outside_on2_boxplot.png
figures/screening_outputs/fig_20150317_superdarn_supported_channel.png
figures/screening_outputs/fig_20150317_ssusi_on2_ratio_support.png
```

Each figure should have a caption saved in a parallel `.md` file.

### Task 7: Generalize to multi-event search

After the 2015-03-17 event is reproducible, implement:

```text
scripts/batch_screen_guvi_dmsp_saps_on2_events.py
```

The batch scanner should accept a list of storm dates and output:

```text
data_samples/screening_outputs/candidate_windows_all_events.csv
summaries/screening_outputs/batch_screening_summary.md
```

Prioritize:

1. Major storms with DMSP SSIES + GUVI availability.
2. Events after 2020 with useful SuperDARN subauroral coverage.
3. Events where optional SSUSI O/N2/proxy can be attempted.

---

## 9. Acceptance criteria

The implementation is acceptable when:

1. The current best 2015-03-17 candidate can be reproduced or transparently explained from available files.
2. Every candidate window has a grade, score, and caveat.
3. GUVI statistics distinguish inside-channel and control regions.
4. DMSP SAPS crossings are identified from sustained westward drift, not isolated spikes.
5. SuperDARN support is labelled as either quantitative or screening-only.
6. SSUSI support is labelled as official O/N2 or proxy ratio.
7. The pipeline can be run again on another date with minimal code changes.
8. The final summary clearly separates observational coincidence from causal interpretation.

---

## 10. Recommended manuscript framing

Recommended title concept:

> A coordinated case study and screening framework for SAPS-associated thermospheric O/N2 depletion observed by TIMED/GUVI during the 17 March 2015 storm

Recommended claim level:

- Strong: SAPS-associated DMSP westward ion drift channels and GUVI O/N2 depletion show candidate spatial-temporal overlap in the southern day-dusk subauroral sector during 2015-03-17.
- Strong: The best overlap window can be ranked using reproducible criteria and supported by SuperDARN/SSUSI context where available.
- Moderate: The observations are consistent with SAPS-related thermospheric composition perturbations.
- Avoid as a pure observational claim: SAPS directly caused the O/N2 depletion.

Mechanism should be discussed with model support, e.g., SAPS-driven Joule/frictional heating, neutral upwelling/downwelling, and composition redistribution.
