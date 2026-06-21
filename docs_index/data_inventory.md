# Data Inventory

This file records the important data products found in the original workspace and how they are treated in the curated export.

## Included in Curated Export

- Text summaries: all `*_summary.txt` files related to GUVI/DMSP/SuperDARN/SSUSI/RBSP/Swarm screening.
- Scripts: all main `make_*.py` scripts used to generate the observational figures and candidate-window tables.
- Small CSV tables:
  - `rbsp_magnetosphere_mapping_efield_saps_candidate_intervals.csv`
  - `chat_outputs_superdarn_guvi_20260618/lt12_18_overlap_aacgm/lt12_18_overlap_candidates_aacgm.csv`
- Representative figures listed in `figures/README.md`.

## Excluded or Indexed Only

- Raw TIMED/GUVI NetCDF:
  - `timed_guvi_l3-on2_2015075_Av0100r000.nc`
  - `timed_guvi_l3-on2_2015076_Av0100r000.nc`
- Raw/parsed DMSP SSIES:
  - `dmsp_f17_ssies_20150317.EDR.gz`
  - `dmsp_f18_ssies_20150317.EDR.gz`
  - `dmsp_f17_ssies_20150317_parsed.csv`
  - `dmsp_f18_ssies_20150317_parsed.csv`
- RBSP and THEMIS CDF trees:
  - `rbsp_data/`
  - `themis_data/`
- DMSP/SSUSI NetCDF files under:
  - `chat_outputs_superdarn_guvi_20260618/dmsp_ssusi_guvi_overlay/data/`
- Generated dependency/cache folders:
  - `pip/`
  - `__pycache__/`
  - `chat_outputs_superdarn_guvi_20260618/.codex_deps/`
  - Cartopy downloaded shapefiles.

These files are either large, reproducible from public data sources, or environment-specific. They should be downloaded or regenerated when needed rather than stored directly in a small GitHub work archive.

