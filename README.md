# SAPS–O/N2 Observation Records

This repository is a curated record of the observational work testing whether SAPS-related subauroral ion drifts are associated with thermospheric composition disturbances during the March 2015 St. Patrick storm, and of the workflow prepared for a broader 2011–2015 study.

## New execution branch — SSUSI / SuperDARN / GOLD (2026-09-10)

**Codex should start here:** [Execution handoff and phased task list](docs_index/CODEX_START_HERE_SSUSI_SUPERDARN_GOLD_20260910.md).

Supporting specifications:

- [Scientific execution plan V2](docs_index/SSUSI_SuperDARN_GOLD_ON2_execution_plan_v2_20260910.md)
- [Parameter and rule template V2](docs_index/SSUSI_SuperDARN_GOLD_ON2_protocol_v2_20260910.yaml)

The new observational design uses SSUSI to constrain the local auroral boundary, quantitative SuperDARN observations to identify and track equatorward westward-flow channels, and official GOLD column O/N2 to measure spatial contrasts and temporal changes. DMSP SSJ/SSIES is an independent-validation pathway, not a required in-situ crossing for every event.

The candidate archive is 2019–2024 with 2025 reserved for a separate validation branch. The initial task is **P0–P2 only: audit actual code/data and methods, establish joint coverage, implement and test the required modules, and run a small real-data pilot**. Do not launch full-period confirmatory statistics or model simulations before the scientific gates and independent review are complete.

These documents are **proposed specifications, not implemented software or new scientific results**. The historical 2015 evidence and June/July gate snapshots below are unchanged. Raw data, authentication details, and machine-specific paths must remain outside the public repository.

## Current status — 2026-09-08

The strongest current result is an event-level Southern Hemisphere association within one storm:

- the 0.5 h DMSP–GUVI screen contains 9 candidate windows;
- 5 windows meet the plotting-level condition of strong horizontal drift and low GUVI O/N2;
- their median DMSP–GUVI offsets are 2.5–25.9 min, GUVI O/N2 medians are 0.137–0.184, and DMSP `|Vi|` p95 values are 0.59–1.29 km/s;
- the separate 2015-03-17 08:59 UT F16 flagship case has a nearby AEB-filtered SSUSI radiance-ratio proxy point only 17 s later, with normalized `135.6/LBHS = 0.828` (about 17.2% below its same-revolution, same-hemisphere, cross-track q75 background).

These are **SAPS-like candidate associations**, not five confirmed or independent SAPS events. They come from one storm, are Southern Hemisphere only, and have not yet passed the full direction, orbit-geometry, persistence, morphology, auroral-boundary, control-sample, and quantitative-SuperDARN gates. The SSUSI value is a relative O/N2-sensitive radiance-ratio proxy, not an official column O/N2 retrieval.

## Read this first

- [Codex execution entry for the new SSUSI–SuperDARN–GOLD pilot](docs_index/CODEX_START_HERE_SSUSI_SUPERDARN_GOLD_20260910.md)
- [Current project progress and evidence status](reports/SAPS_ON2_CURRENT_PROGRESS_20260908.md)
- [Evidence snapshot manifest](docs_index/progress_snapshot_manifest_20260908.csv)
- [SSUSI proxy usability report](summaries/ssusi_on2_proxy_usability_report_20150317_f16.md)
- [Normalizer V3 gate decision](summaries/screening_outputs/normalizer_v3_gate_decision_table.md)
- [Validation-event instrument blockers](summaries/screening_outputs/validation_event_instrument_blocker_resolution.md)

## Evidence boundary

The current repository supports this statement:

> During the 2015 St. Patrick storm, Southern Hemisphere observations show repeated close space-time associations between strong horizontal ion drift and relatively low GUVI O/N2; one separate F16 crossing also has a near-simultaneous, AEB-filtered SSUSI relative O/N2-sensitive proxy decrease.

It does **not** yet establish that SAPS caused the O/N2 decrease, a multi-storm statistical relationship, a hemispheric climatology, or a chemical/optical mechanism. The intended evidence chain is:

> observation constraint → modeled composition response → chemistry → optical consequence

This repository currently reaches only the observation-constraint layer.

## Repository contents

- `reports/`: current and historical work reports.
- `data_samples/progress_snapshot_20260908/`: public-safe small tables supporting the current report.
- `figures/progress_snapshot_20260908/`: representative tight DMSP–GUVI pages and the flagship SSUSI proxy figure.
- `summaries/`: generated summaries and gate decisions.
- `scripts/`: screening and plotting scripts from the curated export.
- `docs_index/`: plans, data-readiness records, manifests, and acquisition queues.

Large raw satellite files, caches, repeated intermediate figures, and unpublished manuscript files are intentionally excluded. Newly added snapshot files contain no local drive paths.

## Historical note

The earlier [June 2026 observation work report](reports/SAPS_ON2_observation_work_report.md) is retained as a historical record of the broad-window exploratory stage. Its 2–4 h window metrics must not be mixed with the later 0.5 h tight-window results or treated as the current scientific conclusion.
