# 2015-03-17 南北半球 O/N2-SAPS 观测机会整理

## 筛选口径

- 事件目录口径：`2015_st_patrick`，2015-03-16 00:00 到 2015-03-19 00:00 UTC；重点日为 2015-03-17 UTC。
- O/N2 source-first：先看 GUVI O/N2 在 `|AACGM MLAT|=45-80 deg, MLT=12-18 h` 的有效机会，再匹配 DMSP SAPS-like drift。
- 匹配阈值：`|dt| <= 3 h`，`|dMLAT| <= 3 deg`，`|dMLT| <= 0.5 h`，且同段 DMSP matched samples `N >= 10`。
- SAPS/O/N2 响应筛选：`|Vi| p95 >= 0.5 km/s`，并且 GUVI O/N2 median `<= 0.20` 或 p05 `<= 0.15`。
- SuperDARN 这里只作为 quick-look 支持：候选窗中心前后 1 h 内有南半球 convection map。

## 南北半球结论

| Hemisphere | GUVI points | DMSP segments | strict matches | candidate windows | SuperDARN | SAPS-low O/N2 | median O/N2 | max \|Vi\|p95 | main note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N | 0 | 129 | 0 | 0 | 0 | 0 |  |  | No GUVI O/N2 opportunity in same hemisphere, 12-18 MLT, within +/-3 h |
| S | 3532 | 144 | 29 | 29 | 29 | 14 | 0.189 | 2.52 | Southern-only GUVI O/N2 opportunity; controls are same-event screening controls |

核心结论：按这个 opportunity-first 口径，2015-03-17 事件期的可用 O/N2-SAPS 匹配是南半球主导。北半球不是 DMSP 没有穿越，而是在当前 GUVI dayglow O/N2 条件下，同半球、12-18 MLT、前后 3 h 内没有可用 O/N2 点，因此不能形成严格匹配样本。

## 按日期拆分的候选窗

| Date | Hemisphere | candidate windows | SAPS-low O/N2 | median O/N2 | max \|Vi\|p95 |
| --- | --- | --- | --- | --- | --- |
| 2015-03-17 | N | 0 | 0 |  |  |
| 2015-03-17 | S | 16 | 7 | 0.220 | 2.52 |
| 2015-03-18 | S | 13 | 7 | 0.188 | 1.23 |

## 2015-03-17 当天候选明细

| UT | Hemi | DMSP | GUVI UT | dt h | DMSP MLT | DMSP MLAT | O/N2 med | O/N2 p05 | \|Vi\|p95 | class |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00:06 | S | F18 | 01:30-01:34 | 1.43 | 12.2-18.0 | -76.5 to -76.1 | 0.396 | 0.375 | 0.26 | screen |
| 00:11 | S | F16 | 22:18-01:29 | 1.83 | 12.3-17.8 | -67.6 to -67.4 | 0.499 | 0.436 | 0.36 | screen |
| 12:54 | S | F15 | 14:32-14:32 | 1.70 | 12.0-14.4 | -78.0 to -45.0 | 0.184 | 0.184 | 2.20 | yes |
| 14:35 | S | F15 | 14:32-16:09 | 1.61 | 12.5-14.4 | -80.0 to -45.0 | 0.161 | 0.131 | 1.97 | yes |
| 15:41 | S | F16 | 17:46-17:46 | 2.12 | 13.6-16.2 | -80.0 to -45.0 | 0.168 | 0.168 | 0.47 | screen |
| 16:15 | S | F15 | 17:44-17:46 | 1.53 | 14.5-14.5 | -80.0 to -45.0 | 0.215 | 0.119 | 2.45 | yes |
| 17:21 | S | F16 | 19:22-19:23 | 2.05 | 15.4-16.1 | -80.0 to -45.0 | 0.276 | 0.227 | 0.28 | screen |
| 17:55 | S | F15 | 19:20-19:23 | 1.46 | 14.8-17.2 | -80.0 to -45.0 | 0.258 | 0.200 | 0.74 | screen |
| 19:02 | S | F16 | 20:59-21:00 | 1.98 | 16.3-17.8 | -80.0 to -45.0 | 0.250 | 0.149 | 1.15 | yes |
| 19:36 | S | F15 | 20:58-22:34 | 1.40 | 15.5-18.0 | -73.2 to -45.0 | 0.227 | 0.140 | 0.82 | yes |
| 20:44 | S | F16 | 22:36-22:36 | 1.92 | 16.9-18.0 | -66.6 to -45.0 | 0.130 | 0.130 | 2.16 | yes |
| 21:05 | S | F15 | 19:22-22:36 | 1.40 | 12.1-17.7 | -65.2 to -64.6 | 0.306 | 0.157 | 0.37 | screen |
| 21:19 | S | F15 | 21:00-22:36 | 1.33 | 16.1-18.0 | -66.2 to -45.0 | 0.154 | 0.122 | 2.52 | yes |
| 23:01 | S | F19 | 01:43-01:47 | 2.74 | 12.2-17.9 | -78.2 to -78.1 | 0.147 | 0.125 | 0.42 | screen |
| 23:53 | S | F18 | 01:43-01:47 | 1.87 | 12.2-18.0 | -78.0 to -77.7 | 0.158 | 0.130 | 0.39 | screen |
| 23:58 | S | F16 | 22:30-01:42 | 1.43 | 12.1-18.0 | -68.3 to -68.1 | 0.225 | 0.158 | 0.41 | screen |

## 北半球 near-miss 诊断

| Hemisphere | reason | segment count |
| --- | --- | --- |
| N | No GUVI points in same hemisphere/12-18 MLT within +/-3 h | 129 |

南半球没有通过的 DMSP 段主要是几何/样本数限制，而不是完全无 GUVI：

| Hemisphere | reason | segment count |
| --- | --- | --- |
| S | Would pass strict criteria | 29 |
| S | No GUVI points in same hemisphere/12-18 MLT within +/-3 h | 27 |
| S | MLT overlaps, magnetic latitude does not | 24 |
| S | Some strict overlap, but fewer than 10 DMSP samples | 22 |
| S | No same-region spatial overlap within +/-3 h | 16 |
| S | Near miss: only appears after relaxed spatial tolerance | 15 |
| S | Magnetic latitude overlaps, MLT does not | 11 |

## SSUSI 状态

本地 SSUSI 文件清单共有 98 个条目，其中 98 个被标记为 `auroral_context_only`。因此这里没有把 SSUSI 当作正式 O/N2 source，只把它留作极光背景/污染检查的后续分支。

## 输出图

- `figures\screening_outputs\event_20150317_hemisphere_timeline.png`
- `figures\screening_outputs\event_20150317_hemisphere_counts.png`
- `figures\screening_outputs\event_20150317_diagnostic_reasons.png`
- `figures\screening_outputs\event_20150317_on2_vs_drift.png`

## 输出表

- `data_samples\screening_outputs\event_20150317_hemisphere_observation_summary.csv`
- `data_samples\screening_outputs\event_20150317_candidate_windows_by_hemisphere.csv`
- `data_samples\screening_outputs\event_20150317_diagnostic_reasons_by_hemisphere.csv`
