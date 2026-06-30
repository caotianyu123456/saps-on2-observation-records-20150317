# St. Patrick Science-Ready Normalizer Summary

Generated: 2026-06-30T09:13:40+00:00

The St. Patrick rows are checked against the V3 normalizer gate. Current GUVI/DMSP/SuperDARN/SSUSI rows remain smoke-test/caveated until required science-ready fields are materialized.

## Status Counts

- `explicit_caveat_smoke_test_only`: 299
- `science_ready`: 8

## Required For Promotion

- GUVI: time, geo lat/lon, AACGM MLAT/MLT, LT, SZA, O/N2, log(O/N2), dayglow quality flag.
- DMSP: time, satellite, geo lat/lon, AACGM MLAT/MLT, westward drift, density, quality, sign convention.
- SSUSI: auroral boundary or contamination-mask status.
- SuperDARN: quantitative map/fit/grid or explicit quicklook/insufficient/not_available state.
