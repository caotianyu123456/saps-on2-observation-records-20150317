# Reproduction Notes

The scripts were produced during an exploratory analysis session and expect the original raw data filenames used in the workspace.

## Python Dependencies

Install the approximate package set from `requirements.txt`.

On Windows, `aacgmv2` may require Microsoft C++ Build Tools. Early centered-dipole figures were created before AACGMV2 was available; the later `lt12_18_overlap_aacgm` branch used `aacgmv2 2.7.1` and should be treated as the preferred coordinate workflow.

## Expected Raw Data

The scripts refer to these local data products:

- TIMED/GUVI L3 O/N2 NetCDF files for 2015 day 075/076.
- DMSP F17/F18 SSIES EDR files and parsed CSVs.
- DMSP/SSUSI EDR-Aurora NetCDF files for selected F16/F17/F18 passes.
- SuperDARN quick-look convection map PNGs.
- RBSP EFW and MagEphem CDF files.
- THEMIS MOM and state CDF files.
- Swarm MAG orbit-track CSVs.

Large raw data are indexed in `docs_index/data_inventory.md` but excluded from the curated GitHub export.

## Script Layout

Scripts are grouped by source:

- `scripts/root/`: root-level GUVI/DMSP/RBSP/THEMIS/Swarm scripts.
- `scripts/superdarn_guvi/`: SuperDARN/GUVI/DMSP context scripts.
- `scripts/dmsp_ssusi_guvi_overlay/`: SSUSI + GUVI + DMSP drift overlay scripts.
- `scripts/lt12_18_overlap_aacgm/`: AACGM 12-18 MLT overlap screening scripts.

Some scripts import helper functions from root-level scripts. When running from this curated layout, either run from the original workspace root or add `scripts/root` to `PYTHONPATH`.

