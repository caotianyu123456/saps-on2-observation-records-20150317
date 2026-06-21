# SAPS O/N2 Observation Records for 17 March 2015

This repository is a curated working archive for the observational screening work around the question:

> Do SAPS-related ion drifts and electric-field signatures coincide with TIMED/GUVI O/N2 depletion during the 17 March 2015 storm?

The original workspace also contains manuscript drafts, large raw satellite data, Python dependency caches, and many intermediate figures. This curated export keeps the readable work products: reports, scripts, summary text, candidate-window tables, and representative figures.

## Contents

- `reports/SAPS_ON2_observation_work_report.md`: Chinese整理报告，重点记录 SAPS 调制 O/N2 的观测证据链。
- `summaries/`: 原始工作摘要文本，来自每次筛选和作图输出。
- `scripts/`: 生成 GUVI/DMSP/SuperDARN/SSUSI/RBSP/Swarm 图件与筛选表的 Python 脚本。
- `figures/`: 代表性成图，覆盖 GUVI O/N2、DMSP drift、SuperDARN、SSUSI、RBSP、Swarm/THEMIS 叠加。
- `data_samples/`: 小型候选窗口表和索引；大体积原始数据不直接上传。
- `docs_index/`: 论文版本、数据文件和未上传大文件的清单。

## Main Finding

The strongest observation-side support is in the southern hemisphere, subauroral dusk/day-dusk sector. GUVI O/N2 depletion overlaps with DMSP westward-drift/SAPS candidates in two useful windows:

- AACGM 12-18 MLT screening: 17.25-21.25 UT centered near 19.25 UT, GUVI median O/N2 about 0.332, DMSP westward p95 about 3.35 km/s, max about 5.10 km/s.
- Southern 12-24 MLT screening: around 21.0-02.5 UT, GUVI median O/N2 about 0.30-0.35, min about 0.114, DMSP westward p95 about 3.8-4.0 km/s, max about 4.84 km/s.

These are screening-level observational constraints. Final publication figures should use AACGM/Apex coordinates consistently, document the timing tolerance, and separate coincidence evidence from causal interpretation.

