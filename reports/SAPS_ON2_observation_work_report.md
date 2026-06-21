# SAPS 调制 O/N2 的观测工作整理报告

整理时间：2026-06-21  
工作目录：`C:\Users\Dell\Desktop\SAPS SAR arcs`

## 1. 工作主线

这个目录的主体工作可以分成两条线：

1. 论文和模拟主线：使用 SAPS-TIEGCM + GLOW 研究 2015-03-17 圣帕特里克磁暴期间，SAPS 对夜侧气辉的影响。论文主结论是：SAPS 引起 Joule heating 与中性上涌，增加 E/F 区 O2、N2 分子密度，增强 O2+ 生成和离解复合，从而产生弱 SAR arc-like 630.0 nm 红线增强，同时在 557.7 nm 绿线表现为明显减弱。
2. 观测补充主线：围绕“是否能在实际观测中看到 SAPS 与 O/N2 低值/成分扰动的时空对应”开展筛查。核心资料集中在 2026-06-14 到 2026-06-18 生成的 GUVI、DMSP、SuperDARN、SSUSI、RBSP、THEMIS、Swarm 叠加图和摘要文件。

本报告重点整理第二条线，也就是 SAPS 调制 O/N2 的观测工作记录。

## 2. 目录内容概览

根目录中与观测筛查直接相关的文件包括：

- TIMED/GUVI O/N2：`timed_guvi_l3-on2_2015075_Av0100r000.nc`、`timed_guvi_l3-on2_2015076_Av0100r000.nc`，以及一系列 `guvi_on2_*` 图件。
- DMSP SSIES：`dmsp_f17_ssies_20150317.EDR.gz`、`dmsp_f18_ssies_20150317.EDR.gz`、解析后的 `dmsp_f17_ssies_20150317_parsed.csv`、`dmsp_f18_ssies_20150317_parsed.csv`。
- DMSP/SSUSI：集中在 `chat_outputs_superdarn_guvi_20260618/dmsp_ssusi_guvi_overlay/`。
- SuperDARN：集中在 `chat_outputs_superdarn_guvi_20260618/` 与 `lt12_18_overlap_aacgm/`，包括南北半球 convection map quick-look 和 GUVI/DMSP 叠加。
- RBSP/THEMIS/Swarm：`rbsp_data/`、`themis_data/`、`swarm_*_track.csv` 及其筛查图和摘要。
- 脚本：根目录 `make_*.py` 以及 `chat_outputs_superdarn_guvi_20260618/**/make_*.py`。
- 论文文档：从 2024 年的图件/大纲到 2026 年的修订稿、审稿回复、SI，形成完整论文推进记录。

不适合直接作为 GitHub 正文上传的内容包括 `pip/cache`、`.codex_deps`、`__pycache__`、大体积 CDF/NetCDF/CSV 原始数据和多版中间 manuscript。整理版仓库只上传可读结果、脚本、摘要、代表性图件和索引。

## 3. 事件背景

观测工作均围绕 2015-03-17 磁暴展开。`geospacelab_style_20150317_observations_summary.txt` 给出的 OMNI HRO 1-min 风暴日指标为：

- SYM-H 最小值：-234 nT，2015-03-17 22:47 UT。
- GSM Bz 最小值：-26.0 nT，2015-03-17 13:07 UT。
- AE 最大值：2298 nT，2015-03-17 13:58 UT。

这一天也是论文模拟所选事件，论文正文中处理了 9、12、15、18 UT 等时刻的 SAPS-TIEGCM + GLOW 输出。观测补充工作则进一步检查 GUVI O/N2、DMSP drift、SuperDARN convection、SSUSI aurora、RBSP mapped E-field 等证据是否能支撑模型中的“成分扰动/中性上涌”图景。

## 4. GUVI O/N2 观测记录

使用的数据为 TIMED/GUVI L3 O/N2 日产品，主要覆盖 2015 年第 75、76 天。关键统计来自 `guvi_on2_20150317_global_subauroral_drift_overlay_summary.txt`：

- GUVI 原始有效 O/N2 点：n=12419，UT=0.89-22.62，median O/N2=0.723，min=0.009，max=1.189。
- 插值/网格后有限单元：n=20402，median=0.563，min=0.000，max=1.112。
- 以 centered-dipole |MLAT|=48-70 deg 定义亚极光带：
  - 北半球：n=1477，UT=0.89-21.93，median=0.263，p95=0.676，max=0.88。
  - 南半球：n=2046，UT=1.40-22.62，median=0.379，p95=0.707，max=0.891。

根目录中 `guvi_on2_20150317_saps_context.png`、`guvi_on2_target_sector_20150317.png`、`guvi_on2_global_with_saps_sector.png`、`guvi_on2_vs_lt_20150317.png`、`guvi_on2_global_lt_with_saps_sector.png` 记录了最初的 GUVI 全局分布、目标扇区与 LT/MLT 筛查。

## 5. DMSP SSIES 与 SAPS 候选窗口

DMSP F17/F18 SSIES 被用来识别亚极光区强水平离子漂移。`guvi_dmsp_westward_saps_candidate_window_summary.txt` 明确说明：正的 DMSP SSIES horizontal ion drift 被视作 westward。

根目录筛查的主要结果集中在南半球 MLT 12-24：

- Top 1：S MLT 12-24，UT 22.50-02.50，center 0.50，GUVI n=199，median O/N2=0.316，min=0.114；DMSP westward n=334，median=0.90 km/s，p95=4.03 km/s，max=4.84 km/s。
- Top 2：UT 21.00-01.00，center 23.00，GUVI median O/N2=0.300，min=0.114；DMSP westward n=718，median=0.85 km/s，p95=3.86 km/s，max=4.84 km/s。
- Top 3：UT 21.25-01.25，center 23.25，GUVI median O/N2=0.300，min=0.114；DMSP westward p95=3.82 km/s，max=4.84 km/s。

这些结果说明：南半球日昏至夜侧亚极光扇区中，GUVI O/N2 明显低值与 DMSP westward drift 增强存在可用的时间窗重叠。

## 6. AACGM 12-18 MLT 重叠筛查

后续工作在 `chat_outputs_superdarn_guvi_20260618/lt12_18_overlap_aacgm/` 中将 GUVI 和 DMSP 位置转换到 AACGMV2 2.7.1，重点聚焦 12-18 MLT。`lt12_18_overlap_aacgm_summary.txt` 给出更稳健的筛查结论：

- 目标：寻找 GUVI dayside O/N2 覆盖与 SAPS-relevant dusk sector 的重叠，尤其 12-18 MLT。
- 时间容差：主要使用 4 小时窗口；叠加时也使用 SSUSI 或 SuperDARN 前后 2 小时窗口。
- Top 12-18 MLT 候选窗口：
  - center=19.25 UT，window=17.25-21.25 UT，GUVI n=614，median O/N2=0.332，min=0.117；DMSP westward n=570，p95=3.35 km/s，max=5.10 km/s，score=8.89。
  - center=19.50 UT 与 19.00 UT 给出几乎相同的高分结果。
  - 18.00-19.75 UT 附近仍保持 GUVI median O/N2 约 0.32-0.33，DMSP westward max 5.10 km/s。

这一分支是目前最适合作为后续正式观测图基础的版本，因为它使用 AACGM 而不是 centered-dipole 筛查坐标。

## 7. SuperDARN/GUVI/DMSP 叠加

`geospacelab_style_20150317_observations_summary.txt` 记录了南半球 SuperDARN quick-look 与 GUVI/DMSP 的叠加：

- 使用南半球 SuperDARN quick-look，区间 2015-03-17 22:30-22:40 UT，五个 2-min panel。
- GUVI overlaid：n=139，UT=22.500-22.615，CD-MLAT=-70.0 到 -61.8，CD-MLT=12.9 到 17.1，O/N2 median=0.254，min=0.114。
- DMSP overlaid：n=386，drift median=-0.67 km/s，p95=0.79 km/s，max=1.86 km/s；摘要中说明正值被视作 westward。
- 解释性记录：22:30-22:40 UT 南半球 SuperDARN quick-look 显示 dusk-side/subauroral convection channel，GUVI 同时采样到 CD-MLAT 约 -70 到 -62、CD-MLT 约 13-17 的 O/N2 depleted track。

该图适合作为 screening/publication-planning figure。摘要也明确提醒：正式发表前应在 AACGM/Apex 坐标下重跑。

## 8. DMSP/SSUSI 与 GUVI/DMSP drift 叠加

SSUSI 分支用于把 auroral LBHS 背景、DMSP SSIES drift 和 GUVI O/N2 放到同一磁坐标图中。两个摘要给出了互补信息。

`dmsp_ssusi_lbhs_guvi_track_20150317_south_summary.txt` 中，南半球主图选择：

- F16 REV 58881，SSUSI south valid UT=22.11-22.49。
- GUVI 点：n=252，UT=22.00-22.68，MLAT=-75 到 -45，MLT=10.5-18.3。
- common-UT highlighted GUVI 点：n=100，落在 SSUSI valid UT=22.11-22.49。
- GUVI O/N2 p05/median=0.159/0.333。

`dmsp_ssusi_dmsp_velocity_arrows_guvi_global_style_best_NS_20150317_summary.txt` 中，成图采用 north/south 双面板：

- North：F17 REV 43159，SSUSI valid UT=19.94-21.61；DMSP 点 n=2154，|drift| p95/max=2.51/5.10 km/s；GUVI 点 n=194，UT=20.26-21.95，O/N2 p05=0.056。
- South：F17 REV 43160，SSUSI valid UT=22.42-22.79；DMSP 点 n=1504，|drift| p95/max=2.94/4.84 km/s；GUVI 点 n=252，UT=22.41-22.62，O/N2 p05=0.159。

这一证据链说明：在 auroral emission 背景、DMSP 轨道漂移、GUVI O/N2 低值之间，可以找到同一天、相近 MLT 和近时段的叠加窗口。

## 9. RBSP、THEMIS 与 Swarm 筛查

为了补充磁层侧或低轨侧的 SAPS 相关诊断，目录中还进行了 RBSP、THEMIS、Swarm 筛查。

RBSP 结果来自 `rbsp_magnetosphere_mapping_efield_saps_diagnostic_summary.txt`：

- 定义：subauroral footpoint 为 centered-dipole |MLAT|=48-70 deg；SAPS-relevant MLT sector 为 15-24 MLT；增强电场阈值为 |E_spinfit_MGSE| >= 5.0 mV/m。
- RBSP-A 在 15-24 MLT 亚极光区域的 p95 |E| 可达约 5.56-5.98 mV/m，max 16.11 mV/m。
- RBSP-B 在 15-24 MLT 亚极光区域的 p95 |E| 可达约 6.41-8.07 mV/m，max 15.50 mV/m。
- 候选增强电场区间包括 RBSP-A 19.97-20.33 UT、RBSP-B 17.68-18.20 UT、21.27-21.47 UT 等。

THEMIS 结果目前是 approximate centered-dipole inverse mapping，主要用于 screening。`global_guvi_dmsp_rbsp_themis_tracks_overlay_summary.txt` 显示 THEMIS mapped ion speed 在南北足点均有较高 p95，但摘要明确提醒映射为近似。

Swarm 分支在 `swarm_magnetosphere_mapping_screening_summary.txt` 中指出：本地只有 Swarm MAG orbit/magnetic-field track，没有 Swarm EFI/TCT02/TIE ion-drift CDF；VirES 下载需要 token/account，因此离子漂移分支暂时阻塞。当前 Swarm 只能作为轨道覆盖参考，不能作为 SAPS drift 证据。

## 10. 主要阶段时间线

- 2024-05 到 2024-12：整理 SAR arc 公式、图件、大纲、早期 manuscript 和组会材料。
- 2025-04 到 2025-12：形成 SAPS SAR arcs 多版 manuscript，逐步修订到 v7、查重稿。
- 2026-02 到 2026-03：形成 reviewer response、SI、修订稿和 track changes。
- 2026-06-14 到 2026-06-18：集中开展观测补充。先做 GUVI O/N2 目标扇区，再叠加 DMSP SSIES drift，随后加入 SuperDARN/SSUSI/AACGM/RBSP/THEMIS/Swarm 筛查，形成一套 SAPS 与 O/N2 对应关系的工作记录。

## 11. 当前可支撑的结论

1. GUVI 在 2015-03-17 的亚极光带存在明显 O/N2 低值，南半球若干扇区的 O/N2 median 可降至约 0.30-0.35，局地 min 约 0.114-0.117。
2. DMSP SSIES 在相近南半球 MLT 扇区给出强 westward drift/SAPS 候选，p95 常达约 3-4 km/s，max 可达约 4.8-5.1 km/s。
3. 使用 AACGM 的 12-18 MLT 分支给出最稳健的候选窗口：17.25-21.25 UT 附近，GUVI O/N2 低值与 DMSP westward drift 增强同时满足筛选条件。
4. 22.3-22.6 UT 附近还有 SuperDARN、SSUSI、GUVI、DMSP 的多源叠加证据，适合展示 SAPS/convection channel 与 O/N2 depleted track 的空间关系。
5. RBSP mapped E-field 提供磁层侧增强电场背景，THEMIS 和 Swarm 当前只能作为筛查或轨道覆盖辅助，不能单独作为确定性因果证据。

## 12. 局限与后续建议

- 坐标系统：早期图多用 centered-dipole，正式结果建议统一重跑 AACGM/Apex。
- 时间对应：GUVI 是轨道扫描/日产品，不是同步成像；DMSP、SuperDARN、SSUSI 时间窗存在前后 2-4 小时容差，报告和论文中需要清楚标注。
- 因果表述：观测记录支持“时空对应”和“与 SAPS 相关的成分扰动候选”，但不能单独证明 SAPS 导致 O/N2 降低。因果解释仍应由 SAPS-TIEGCM + GLOW 机制诊断支撑。
- Swarm 数据：若要使用 Swarm drift，需要下载 EFI/TIE 相关 CDF，而不是当前的 MAG 轨道文件。
- 最适合继续打磨的图件：`lt12_18_overlap_aacgm` 分支、`geospacelab_style_superdarn_guvi_dmsp_20150317_south.png`、`dmsp_ssusi_dmsp_velocity_arrows_guvi_global_style_best_NS_20150317.png`、`guvi_dmsp_westward_saps_candidate_window.png`。

