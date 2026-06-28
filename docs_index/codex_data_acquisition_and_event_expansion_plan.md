# Codex Data Acquisition and Event Expansion Plan for SAPS/O/N2 Statistics

Updated: 2026-06-22
Repository: `caotianyu123456/saps-on2-observation-records-20150317`

## 0. Current status and problem

The latest local run is not only a single-day 2015-03-17 case, but it is still limited to the local St. Patrick storm data group:

```text
2015-03-16: GUVI available; no parsed DMSP SSIES, kept as data-limited/non-match.
2015-03-17: candidate windows generated; SAPS-like low-O/N2 windows found.
2015-03-18: candidate windows generated; SAPS-like low-O/N2 windows found.
```

This means the current outputs are a local-data smoke test covering 2015-03-16 to 2015-03-18. They are not yet the 2011-2015 multi-event statistics described in the master plan.

The next priority is therefore not only improving the matching algorithm. The project first needs a reproducible data-acquisition, data-classification, and event-expansion workflow.

---

## 1. Main goal of this plan

Build a reproducible data layer so the statistical SAPS/O/N2 workflow can expand from the 2015 local smoke test to:

```text
Detector validation: 2010-2014
Primary science sample: 2011-2015
Extension sample: 2010-2017
Future GOLD branch: 2018-2024
```

This plan should be executed before any claim of multi-event statistics.

---

## 2. Guiding principle: data availability first

The statistical bottleneck is O/N2 coverage near SAPS channels, not SAPS occurrence itself.

Therefore Codex should first create data-availability tables before running the full science analysis.

Required outputs:

```text
docs_index/data_manifest_required.csv
docs_index/data_manifest_local.csv
docs_index/data_manifest_missing.csv
data_samples/screening_outputs/event_universe.csv
data_samples/screening_outputs/event_data_availability.csv
```

The analysis pipeline must not silently skip missing data. Missing files must be recorded as structured rows.

---

## 3. Event tiers to acquire

### Tier A: local smoke-test group

Already partially available locally:

```text
2015-03-16
2015-03-17
2015-03-18
```

Purpose:

- verify file parsers;
- verify GUVI/DMSP matching;
- verify non-match handling;
- verify local output tables and figures.

### Tier B: thesis-inspired validation cases

Add these as soon as data can be acquired:

```text
2014-02-19
2011-10-25
2013-06-30
```

Purpose:

- validate SuperDARN SAPS channel detection;
- validate DMSP SAPS detector on known SAPS events;
- cover main phase, early recovery phase, and late recovery phase SAPS conditions;
- check whether GUVI O/N2 opportunities exist near these SAPS channels.

### Tier C: primary 2011-2015 statistical sample

Build a storm list for:

```text
2011-01-01 through 2015-12-31
```

Selection criteria:

```text
moderate_or_stronger_storm: min(SYM-H or Dst) <= -50 nT
major_storm_subset: min(SYM-H or Dst) <= -100 nT
```

For every storm, acquire or check:

```text
DMSP SSIES / SSJ / SSUSI
TIMED/GUVI O/N2
SuperDARN map/fit/grid or quick-look support
OMNI / SYM-H / AE / Dst / Kp
optional AMPERE / TEC context
```

### Tier D: 2010-2017 extension

After Tier C works, expand to:

```text
2010-01-01 through 2017-12-31
```

Purpose:

- increase event count;
- test solar-cycle dependence;
- assess whether results are robust beyond 2011-2015.

### Tier E: 2018-2024 GOLD branch

Keep this separate from the GUVI statistics:

```text
2018-01-01 through 2024-12-31
```

Purpose:

- use GOLD ON2 as a high-cadence O/N2 source;
- pair with SuperDARN and DMSP when available;
- do not mix directly with GUVI statistics because observing geometry is different.

---

## 4. Required data groups per event

For each event date, collect a minimum window:

```text
event_day_minus_1
event_day
event_day_plus_1
```

For strong storms, consider:

```text
event_day_minus_2 through event_day_plus_3
```

because O/N2 composition response can lag SAPS and storm forcing.

### 4.1 DMSP SSIES / SSJ / SSM

Purpose:

- DMSP/SSIES: ion drift and SAPS crossing detection.
- DMSP/SSJ: auroral precipitation boundary and auroral contamination mask.
- DMSP/SSM: magnetic context, optional.

Priority satellites:

```text
F16
F17
F18
F19 if available and useful
```

Required normalized output:

```text
data_work/normalized/dmsp_ssies/{YYYY}/{YYYYMMDD}/dmsp_ssies_normalized_{YYYYMMDD}.csv
```

Required fields:

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
quality_flags
source_file
```

If SSJ is available:

```text
ssj_electron_energy_flux
ssj_ion_energy_flux
auroral_boundary_flag
auroral_equatorward_boundary_mlat
```

### 4.2 TIMED/GUVI L3 O/N2

Purpose:

- main O/N2 data source for 2011-2015 and 2010-2017.

Required normalized output:

```text
data_work/normalized/guvi_on2/{YYYY}/{YYYYMMDD}/guvi_on2_normalized_{YYYYMMDD}.csv
```

Required fields:

```text
time_utc
orbit_or_scan_id
lat_geo
lon_geo
aacgm_mlat
aacgm_mlt
local_time
sza
on2
log_on2
quality_flags
native_or_interpolated
source_file
```

Quality classes:

```text
dayglow_valid
twilight_caution
night_or_ambiguous
bad_quality
```

### 4.3 SuperDARN

Purpose:

- define two-dimensional SAPS channels;
- supplement DMSP one-dimensional crossings;
- enable SuperDARN-first screening.

Preferred input:

```text
map files / fit files / grid files processed with reproducible scripts
```

Fallback input:

```text
quick-look convection maps, screening only
```

Required normalized output:

```text
data_work/normalized/superdarn/{YYYY}/{YYYYMMDD}/superdarn_normalized_{YYYYMMDD}.csv
```

Required fields:

```text
time_utc
hemisphere
radar_id_or_map_id
aacgm_mlat
aacgm_mlt
velocity_ms
flow_direction
vector_quality
radar_count
valid_echo_count
fit_quality
quicklook_or_quantitative
source_file_or_url
```

SuperDARN data status per event must be recorded as:

```text
quantitative_available
quicklook_only
insufficient_echo
not_available
not_checked
```

### 4.4 DMSP/SSUSI

Purpose priority:

1. auroral oval equatorward boundary;
2. auroral contamination mask for GUVI/GOLD O/N2;
3. optional O/N2 or O/N2-sensitive FUV ratio support.

Required normalized output:

```text
data_work/normalized/ssusi/{YYYY}/{YYYYMMDD}/ssusi_normalized_{YYYYMMDD}.csv
```

Required fields:

```text
time_utc
satellite
rev
hemisphere
mlat_grid
mlt_grid
lbhs_radiance
lbhl_radiance
auroral_boundary_flag
auroral_equatorward_boundary_mlat
source_file
```

Optional fields:

```text
OI_1356_radiance
N2_LBHS_radiance
N2_LBHL_radiance
ON2_product_or_ratio
ssusi_on2_support_type
```

SSUSI support types:

```text
auroral_boundary_only
official_or_validated_on2
OI1356_LBHS_proxy_only
not_available
```

### 4.5 Geomagnetic and solar-wind indices

Required for every event:

```text
OMNI 1-min or 5-min IMF Bz, solar wind speed, density, pressure
SYM-H
AE/AU/AL
Dst
Kp
F10.7 if needed for conductance or background models
```

Normalized output:

```text
data_work/normalized/indices/{YYYY}/{YYYYMMDD}/geomag_indices_{YYYYMMDD}.csv
```

Required fields:

```text
time_utc
symh
dst
ae
au
al
kp
imf_bz_gsm
imf_by_gsm
solar_wind_speed
solar_wind_dynamic_pressure
f107
source_file
```

### 4.6 Optional context data

Add after main data layer works:

```text
AMPERE R2 FAC
GPS TEC / TEC trough / SED context
RBSP mapped electric field
Swarm EFI/TIE if available
GOLD ON2 for 2018+
```

Do not block GUVI+DMSP+SuperDARN statistics if optional context is missing.

---

## 5. Directory structure

Use a clear separation between raw data, normalized working data, and small sample outputs.

```text
data_raw/
  dmsp/
    ssies/{YYYY}/{YYYYMMDD}/
    ssj/{YYYY}/{YYYYMMDD}/
    ssusi/{YYYY}/{YYYYMMDD}/
  guvi/on2/{YYYY}/{YYYYMMDD}/
  superdarn/{YYYY}/{YYYYMMDD}/
  indices/{YYYY}/{YYYYMMDD}/
  gold/on2/{YYYY}/{YYYYMMDD}/
  ampere/{YYYY}/{YYYYMMDD}/
  tec/{YYYY}/{YYYYMMDD}/

data_work/
  normalized/
    dmsp_ssies/{YYYY}/{YYYYMMDD}/
    guvi_on2/{YYYY}/{YYYYMMDD}/
    superdarn/{YYYY}/{YYYYMMDD}/
    ssusi/{YYYY}/{YYYYMMDD}/
    indices/{YYYY}/{YYYYMMDD}/
    gold_on2/{YYYY}/{YYYYMMDD}/

 data_samples/
  screening_outputs/
```

Do not commit large raw files unless explicitly intended. Commit small manifests, sample tables, scripts, and summaries.

---

## 6. Data manifests

### 6.1 Required manifest

Create:

```text
docs_index/data_manifest_required.csv
```

Columns:

```text
event_id
event_date
data_group
source_name
satellite_or_instrument
required_start_ut
required_end_ut
required_files_or_patterns
priority
reason
```

### 6.2 Local manifest

Create:

```text
docs_index/data_manifest_local.csv
```

Columns:

```text
event_id
event_date
data_group
source_name
local_path
file_name
file_size_mb
parse_status
normalized_output_path
last_checked_utc
```

### 6.3 Missing manifest

Create:

```text
docs_index/data_manifest_missing.csv
```

Columns:

```text
event_id
event_date
data_group
source_name
missing_reason
download_priority
manual_download_url_or_note
automated_download_possible
blocking_for_science_run
```

---

## 7. Download and availability scripts

Implement these scripts before expanding the science analysis.

### 7.1 Inventory existing data

```text
scripts/inventory_local_data.py
```

Tasks:

- scan `data_raw/`, `data_work/`, `data_samples/`, `summaries/`;
- detect available days and instruments;
- produce `data_manifest_local.csv`;
- update `event_data_availability.csv`.

### 7.2 Build required data manifest

```text
scripts/build_required_data_manifest.py
```

Inputs:

```text
event_universe.csv
configured data windows
instrument priority list
```

Output:

```text
docs_index/data_manifest_required.csv
```

### 7.3 Check missing data

```text
scripts/check_missing_data.py
```

Outputs:

```text
docs_index/data_manifest_missing.csv
summaries/screening_outputs/data_gap_report.md
```

### 7.4 Download queue builders

If fully automated download is not possible, create download queues instead of failing.

```text
scripts/prepare_guvi_download_queue.py
scripts/prepare_dmsp_download_queue.py
scripts/prepare_superdarn_download_queue.py
scripts/prepare_ssusi_download_queue.py
scripts/prepare_indices_download_queue.py
scripts/prepare_gold_download_queue.py
```

Outputs:

```text
docs_index/download_queue_guvi.csv
docs_index/download_queue_dmsp.csv
docs_index/download_queue_superdarn.csv
docs_index/download_queue_ssusi.csv
docs_index/download_queue_indices.csv
docs_index/download_queue_gold.csv
```

Queue columns:

```text
event_id
event_date
data_group
instrument
required_time_start
required_time_end
remote_source_hint
expected_file_pattern
local_target_dir
automated_download_possible
manual_step_required
priority
```

### 7.5 Normalization scripts

```text
scripts/normalize_dmsp_ssies.py
scripts/normalize_guvi_on2.py
scripts/normalize_superdarn.py
scripts/normalize_ssusi.py
scripts/normalize_geomag_indices.py
```

Each normalizer must:

- read raw files from `data_raw/`;
- write normalized CSV/Parquet to `data_work/normalized/`;
- write a parse summary;
- fail gracefully if files are missing or variables are absent;
- record missing variables in a summary table.

---

## 8. Event classification after data inventory

After inventory, classify every event/day into these categories:

```text
A_ready_for_full_SAPS_ON2_matching
B_ready_for_DMSP_GUVI_only
C_ready_for_SuperDARN_GUVI_only
D_SAPS_available_no_ON2
E_ON2_available_no_SAPS_data
F_indices_only
G_missing_or_unusable
```

Create:

```text
data_samples/screening_outputs/event_data_availability.csv
```

Minimum columns:

```text
event_id
event_date
storm_class
storm_phase_coverage
has_dmsp_ssies
has_dmsp_ssj
has_guvi_on2
has_superdarn_quantitative
has_superdarn_quicklook
has_ssusi_boundary
has_ssusi_on2_or_proxy
has_indices
has_gold_on2
ready_class
blocking_missing_data
recommended_next_action
```

---

## 9. Required event universe construction

Implement:

```text
scripts/build_event_universe.py
```

### 9.1 Seed events

Start with:

```text
2015-03-16
2015-03-17
2015-03-18
2014-02-19
2011-10-25
2013-06-30
```

### 9.2 Storm-list expansion

For 2011-2015:

- identify days with min SYM-H/Dst <= -50 nT;
- include day before and day after each storm minimum;
- tag main, early recovery, late recovery intervals.

### 9.3 SAPS-driven expansion

After DMSP/SuperDARN data are available:

- add days with DMSP westward SAPS-like crossing;
- add days with SuperDARN subauroral westward channel;
- preserve days without O/N2 as non-matches.

### 9.4 O/N2-driven expansion

After GUVI/GOLD availability is known:

- add days with strong subauroral O/N2 depletion patches;
- then search for SAPS channels near them;
- preserve O/N2-depletion-without-SAPS cases.

---

## 10. Science run readiness rules

### 10.1 Full science-ready event

An event is full science-ready if:

```text
GUVI O/N2 valid samples exist in |MLAT| 45-70, MLT 12-24
AND DMSP/SuperDARN SAPS channel can be tested
AND indices exist for storm/substorm phase tagging
```

### 10.2 Strong candidate-ready event

A strong candidate event requires:

```text
DMSP SAPS crossing OR quantitative SuperDARN SAPS channel
AND GUVI O/N2 inside/near channel within 0-1 h or 1-3 h
AND at least one control region available
```

### 10.3 Figure-ready high-quality event

A figure-ready event requires:

```text
SAPS channel Grade A/B
O/N2 quality good
control regions available
SSUSI or SSJ auroral boundary support if possible
SuperDARN quantitative support if claiming 2-D channel
```

---

## 11. Immediate Codex tasks

### Task 1: Label current run correctly

Update current summaries to state:

```text
This is a local-data smoke test for 2015-03-16 to 2015-03-18, not the planned 2011-2015 statistics.
```

### Task 2: Add manifests

Create:

```text
docs_index/data_manifest_required.csv
docs_index/data_manifest_local.csv
docs_index/data_manifest_missing.csv
```

### Task 3: Build data availability table

Create or update:

```text
data_samples/screening_outputs/event_data_availability.csv
```

It must include at least:

```text
2015-03-16
2015-03-17
2015-03-18
2014-02-19
2011-10-25
2013-06-30
```

### Task 4: Build download queues

Create download queue files for GUVI, DMSP, SuperDARN, SSUSI, and indices.

### Task 5: Add missing-data report

Create:

```text
summaries/screening_outputs/data_gap_report.md
```

It must state exactly which data are missing before 2011-2015 statistics can be run.

### Task 6: Only then rerun science matching

After data are acquired or normalized, rerun:

```text
scripts/batch_screen_guvi_dmsp_saps_on2_events.py
scripts/match_saps_channels_to_on2.py
scripts/plot_saps_on2_statistics.py
```

---

## 12. Acceptance criteria for the data-acquisition phase

The data-acquisition phase is complete when:

1. The repository contains a required/local/missing data manifest.
2. The current 2015-only run is explicitly labeled as a smoke test.
3. `event_data_availability.csv` lists at least the local 2015 dates and the three thesis-inspired SAPS events.
4. Missing files are not silent; they are listed in `data_manifest_missing.csv`.
5. Download queue CSVs exist for every required data group.
6. Normalizers produce standardized outputs under `data_work/normalized/`.
7. The pipeline can distinguish data-limited non-matches from scientific non-matches.
8. No multi-year statistical claim is made until at least the 2011-2015 event set has been inventoried and partly processed.

---

## 13. Notes for interpretation

The current 2015-03-16 to 2015-03-18 outputs are useful and should be preserved, but they should be interpreted as:

```text
local-data validation / St. Patrick storm mini-sample
```

not as:

```text
2011-2015 SAPS/O/N2 statistics
```

The next manuscript or progress report should explicitly separate:

1. local smoke-test results;
2. data-acquisition status;
3. multi-event candidate results;
4. final statistical interpretation.
