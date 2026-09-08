# F16 SSUSI Normalized Proxy Method

This product remains a SSUSI radiance-ratio proxy, not official SSUSI ON2.

Input: AEB-screened F16 SSUSI SDR2-DISK proxy samples from the existing workflow.

Raw proxy: `OI 135.6 nm / N2 LBHS` after SDR2-DISK dayglow QC, SZA <= 75 deg, no SAA, exposure > 0, positive radiances, channel bad-flag screening, AACGM coordinate conversion, and AEB/auroral-contamination screening.

Background baseline: for each raw ratio sample, the preferred baseline is the 75th percentile of clean-subauroral polar samples in the same `rev + hemisphere + cross_track_index` strip. If too few samples exist, the fallback order is `rev + hemisphere`, `hemisphere + cross_track_index`, `hemisphere`, then all clean polar samples.

Normalized proxy: `raw_ratio / background_q75`. Depletion proxy: `1 - normalized_proxy`, so positive values indicate lower 135.6/LBHS relative to the clean-subauroral background.

Low normalized intervals are identified from 30-s median samples below the 20th percentile of clean polar normalized proxy values.
