# 研究交接的小型证据表

这些表支持[2026年10月15日研究交接](../../reports/SAPS_ON2_RESEARCH_HANDOFF_20261015.md)，均为已有分析的派生汇总，不是原始卫星数据或独立事件目录。行数不代表独立统计样本量。

| 文件 | 来源和筛选 | 含义 |
|---|---|---|
| `hkw_reference_radar_audit.csv` | 10月14日`three_case_design/reference_radar_audit.csv`原样复制 | 8行事件/前期参照/台站分组，旧近门口径；不能当精确格点相交 |
| `hkw_on2_standard_comparisons.csv` | 10月15日`hkw_locality_20261015/band_sensitivity.csv`选`standard`及三个固定纬段，保留原列和值 | 4参考×3纬段，共12行；主表极侧为63–67°，不是62–66° |
| `hkw_context_residual_standard.csv` | 同专项`context_residual_sensitivity.csv`选`standard`和50–54°/63–67° | 4参考×2背景，共8行；核心与周围配对差值的差，不是已识别SAPS效应 |
| `hkw_focus_membership_summary.csv` | 同专项`radar_audit/focus_membership_summary.csv`原样复制 | 不同高度、时间容差、质量层下的GUVI中心覆盖，缺测与慢LOS分开 |

参考标签：`pre_near`为前日近地理轨121634；`pre_MLT`为前日远地MLT/SZA参照121637；`same_before`/`same_after`为同日相邻轨121648/121650。后两者与目标约相差1.61小时、千公里，不是同地时间序列。

`ratio_of_medians`是目标/参照两组中位数之比；`median_paired_ratio`是逐点比值的中位数，两者不能互换。比值为柱积分O/N₂，无量纲，不是固定高度局地数密度比。

参考对应点来自固定的几何规则，相关采样、未知逐点误差和检索足迹没有通过导出CSV被消除。原始来源相对路径和限定见[联合观测报告](../../reports/SAPS_ON2_JOINT_OBSERVATIONS_20261015.md)。
