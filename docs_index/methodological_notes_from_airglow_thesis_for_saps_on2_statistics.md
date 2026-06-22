# Methodological notes from the uploaded airglow thesis for SAPS/O/N2 statistical screening

Updated: 2026-06-22

Reference document supplied by user: Gao Hong PhD thesis, *The study on airglow in middle and upper atmosphere* / `中高层大气气辉辐射研究`.

This note extracts methodological ideas that should be transferred into the SAPS/O/N2 screening project. The thesis is not about SAPS, but it is useful because it demonstrates how to turn airglow/composition observations into a defensible long-term statistical analysis with careful treatment of local time, seasonal sampling, contamination, correlations, and uncertainty.

## 1. Treat 2015-03-17 only as validation; build a long-term event sample

The thesis repeatedly uses multi-year samples rather than relying on a single example, e.g., 2000–2004 ground-based 557.7/630.0 nm observations and 2002–2007 SABER statistics. The SAPS/O/N2 project should therefore:

- retain 2015-03-17 as the smoke-test and flagship example;
- build `event_universe.csv` and `event_data_availability.csv` before claiming statistics;
- report how many storm days, DMSP passes, SuperDARN intervals, GUVI swaths, and usable conjunction windows are available;
- keep rejected/non-match windows to document selection effects.

## 2. Define valid observation windows before computing statistics

The thesis explicitly separates real nightglow from twilight/dayglow afterglow before calculating seasonal means. For SAPS/O/N2, the analogous rule is:

- GUVI O/N2 samples must carry SZA, local time, and dayglow/twilight quality flags;
- screening should distinguish dayglow-valid O/N2, twilight-contaminated O/N2, and night-side invalid/ambiguous O/N2;
- candidate tables should include `guvi_sza_median`, `guvi_local_time_range`, `guvi_dayglow_quality_flag`, and `twilight_or_sza_caveat`;
- statistics should not mix high-quality dayglow O/N2 with ambiguous twilight/night samples unless they are stratified.

## 3. Use matched pairs/conjunctions and preserve the denominator

The thesis computes correlations only for nights when both 557.7 nm and 630.0 nm observations are available. For SAPS/O/N2:

- only compute SAPS/O/N2 association statistics for windows where both SAPS-channel evidence and GUVI O/N2 samples exist;
- separately count windows with SAPS but no GUVI, GUVI O/N2 depletion but no SAPS crossing, and SuperDARN channels without DMSP/GUVI overlap;
- the statistical denominator should be event/window count, not GUVI pixel count.

## 4. Use distribution-level statistics, not only example figures

The thesis summarizes correlation-coefficient distributions and the fraction of nights in different ranges. For SAPS/O/N2, implement analogous distributions:

- candidate grade distribution: A/B/C/rejected;
- occurrence by MLT, hemisphere, season, storm phase;
- distribution of inside-minus-control O/N2 response;
- relationship between O/N2 response and DMSP drift p95/max;
- relationship between O/N2 response and SuperDARN flow speed when available;
- number and fraction of positive/negative/no-response cases.

## 5. Use inside/outside or coupled-region comparisons

The thesis uses simultaneous 557.7 nm and 630.0 nm variations to infer E-region/F-region coupling. For SAPS/O/N2, the equivalent comparison is:

- SAPS-channel GUVI O/N2 versus equatorward control;
- SAPS-channel GUVI O/N2 versus poleward control;
- SAPS-channel GUVI O/N2 versus same-MLT outside-channel control;
- optionally, GUVI O/N2 versus SuperDARN/DMSP drift strength inside the same channel.

This is stronger than simply stating that a storm-day O/N2 depletion appears near a SAPS channel.

## 6. Add uncertainty and sensitivity tests

The thesis performs explicit inversion-error and parameter-sensitivity analysis. For SAPS/O/N2 screening, Codex should add sensitivity tests for:

- DMSP SAPS drift threshold: 0.5, 1.0, 2.0, 3.0 km/s;
- SuperDARN velocity threshold: 300, 500, 1000 m/s;
- GUVI O/N2 depletion criterion: raw threshold, percentile threshold, and anomaly threshold;
- time tolerance: 1 h, 2 h, 4 h;
- MLT tolerance: 1 h, 2 h, 3 h;
- channel latitudinal padding: 0.5, 1.0, 2.0 degrees;
- baseline method: quiet-day, same-storm outside-channel, and raw fallback.

Each candidate row should retain the thresholds used so that statistical results can be reproduced and tested.

## 7. Add required columns to candidate windows

Extend `candidate_windows_all_events.csv` with:

```text
guvi_sza_median
guvi_sza_min
guvi_sza_max
guvi_local_time_min
guvi_local_time_max
guvi_dayglow_quality_flag
twilight_or_sza_caveat
valid_pair_flag
nonmatch_category
selection_denominator_group
threshold_set_id
sensitivity_run_id
inside_minus_same_mlt_outside
response_sign
response_strength_category
```

## 8. Add required statistical outputs

Codex should generate:

```text
figures/screening_outputs/stat_valid_data_availability_by_event.png
figures/screening_outputs/stat_nonmatch_categories.png
figures/screening_outputs/stat_response_sign_fraction_by_mlt.png
figures/screening_outputs/stat_inside_minus_control_distribution.png
figures/screening_outputs/stat_threshold_sensitivity_summary.png
```

and summaries:

```text
summaries/screening_outputs/selection_function_and_nonmatches.md
summaries/screening_outputs/threshold_sensitivity_summary.md
```

## 9. Manuscript implication

The statistical paper should not be framed as “we found one SAPS/O/N2 case.” A better framing is:

> We first validate the screening method on a strong 2015-03-17 case, then apply the same criteria to a multi-event dataset to quantify when and where SAPS channels are accompanied by GUVI O/N2 depletion or perturbation.

This framing directly follows the uploaded airglow-thesis logic: start from physical observables, define valid observation conditions, build a multi-year/multi-event sample, quantify distributions and correlations, and then discuss mechanisms with appropriate caveats.
