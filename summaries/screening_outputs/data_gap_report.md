# Data Gap Report

This report implements `docs_index/codex_data_acquisition_and_event_expansion_plan.md` from commit `3cb2b7843c26c286bbb0fead724ed0893a71af4f`.

Current science status: local-data smoke test for 2015-03-16 to 2015-03-18 only; not the planned 2011-2015 statistics.

## Event Readiness

- 2015-03-16 `available_20150316`: E_ON2_available_no_SAPS_data; missing: SAPS detector data; next: acquire DMSP/SuperDARN SAPS data
- 2015-03-17 `available_20150317`: A_ready_for_full_SAPS_ON2_matching; missing: none; next: run full SAPS/O/N2 matching after normalization
- 2015-03-18 `available_20150318`: A_ready_for_full_SAPS_ON2_matching; missing: none; next: run full SAPS/O/N2 matching after normalization
- 2014-02-19 `validation_20140219`: F_indices_only; missing: GUVI O/N2; SAPS detector data; next: acquire instrument data
- 2011-10-25 `validation_20111025`: F_indices_only; missing: GUVI O/N2; SAPS detector data; next: acquire instrument data
- 2013-06-30 `validation_20130630`: F_indices_only; missing: GUVI O/N2; SAPS detector data; next: acquire instrument data

## Missing Data Counts

- 2011-10-25 dmsp_ssies: 1
- 2011-10-25 guvi_on2: 1
- 2011-10-25 ssusi: 1
- 2011-10-25 superdarn: 1
- 2013-06-30 dmsp_ssies: 1
- 2013-06-30 guvi_on2: 1
- 2013-06-30 ssusi: 1
- 2013-06-30 superdarn: 1
- 2014-02-19 dmsp_ssies: 1
- 2014-02-19 guvi_on2: 1
- 2014-02-19 ssusi: 1
- 2014-02-19 superdarn: 1
- 2015-03-16 dmsp_ssies: 1
- 2015-03-16 guvi_on2: 1
- 2015-03-16 ssusi: 1
- 2015-03-16 superdarn: 1
- 2015-03-17 dmsp_ssies: 1
- 2015-03-17 ssusi: 1
- 2015-03-17 superdarn: 1
- 2015-03-18 dmsp_ssies: 1
- 2015-03-18 guvi_on2: 1
- 2015-03-18 ssusi: 1
- 2015-03-18 superdarn: 1

## Blocking Items Before 2011-2015 Statistics

- The 2011-2015 Dst storm-index universe now exists, but instrument data have not been downloaded and normalized for the 737 event rows.
- Acquire GUVI O/N2, DMSP SSIES/SSJ/SSUSI, and SuperDARN quantitative or quick-look support for the seed validation events.
- Normalize raw files into `data_work/normalized/` before claiming multi-event statistics.
