# F16 DMSP/SSUSI 135.6/LBH O/N2 Proxy 可用性报告

日期：2026-06-29
个例：2015-03-17 St. Patrick storm, F16, 南半球 08:55:30-09:02:30 UT SAPS crossing
当前图件：`event_overlay_figures/dmsp_ssusi_20150317_0711_f16_focus_0900_0930/f16_focus_0900_south_only_ssusi_aeb_ssies.png`

## 结论

这组 SSUSI 数据可以使用，但必须按下面这个边界来使用：

**可以使用的表述：**

> DMSP/SSUSI SDR2-DISK OI 135.6 nm 与 N2 LBH 亮度比值提供了一个 relative O/N2-related radiance-ratio proxy。该 proxy 在 F16 南半球 SAPS-like 漂移峰附近和其后短时间内出现相对偏低，支持 SAPS 附近存在 O/N2-related 相对降低的迹象。

**不应使用的表述：**

> SSUSI 官方反演 O/N2 = 0.979。

也不要把这里的 `0.979` 和 GUVI/GOLD 官方 column `ΣO/N2` 的 `0.1-0.4` 量级直接比较。这里的 `0.979` 是两个 FUV 通道亮度的比值，不是经过辐射传输模型和 LUT 反演后的柱密度比。

综合判断：**相对 proxy 可用，绝对 O/N2 retrieval 不可用。**
可信等级：**中等偏高，用于个例辅助证据合适；不适合单独作为定量反演结论。**

## 外部资料依据

1. GOLD mission 论文明确说明，白天盘面 `O/N2` column density ratio 可由 atomic oxygen `135.6 nm` 和 `N2 LBH` emission intensities 得到。该论文也指出 GOLD 的 thermospheric composition 测量继承了 TIMED/GUVI 等 FUV remote sensing 的思路。

2. GOLD Public Science Data Products Guide Rev. 5.2 的 `ON2` 产品说明更具体：正式 `ΣO/N2` 是 thermospheric O column density 相对 N2 column density 的比值；算法 heritage 来自 CPI，曾用于 GUVI 和 SSUSI radiance images；理论基础是从 `O I 135.6 nm / N2 LBH` intensity ratio 反演 `ΣO/N2`，并使用 AURIC atmospheric radiance model 按 solar zenith angle 建 LUT。

3. 这说明 `135.6/LBH` 的物理方向是对的：`135.6 nm` 主要与原子氧相关，`LBH` 与分子氮相关，所以二者比值携带 O/N2 composition 信息。
   但正式产品不是简单相除，而是经过模型、几何、太阳天顶角、光谱污染、误差质量控制等处理。

因此，对你的 SSUSI 数据，最稳妥的定位是：

```text
135.6/LBHS 或 135.6/LBHL = O/N2-related radiance-ratio proxy
不是 official column O/N2 retrieval
```

## 当前处理方法的参考依据

我们的处理方法可以拆成四个有文献/资料依据的部分：

### 1. 用 135.6/LBH 作为 O/N2-related 指标

依据最强。GOLD Data Products Guide 的 ON2 部分说明，正式 `ΣO/N2` 反演的理论基础就是 dayside disk 的 `O I 135.6 nm` 与 `N2 LBH` 强度比；并且这个 disk ON2 retrieval algorithm 最初是为 GUVI 和 SSUSI radiance images 开发的。

因此，我们使用：

```text
I_135.6 / I_LBHS
I_135.6 / I_LBHL
```

作为相对 O/N2-related proxy，是有物理和算法传承依据的。但因为我们没有运行 AURIC/LUT 正式反演，所以只能称为 proxy。

对应参考：

```text
Strickland et al. (1995), Satellite remote sensing of thermospheric O/N2 and solar EUV: 1. Theory.
Evans et al. (1995), Satellite remote sensing of thermospheric O/N2 and solar EUV: 2. Data analysis.
Strickland et al. (1999), AURIC radiance model.
GOLD Public Science Data Products Guide, Section 5.3 ON2.
```

### 2. 使用 DQI、SZA、bad-channel、denominator 阈值做质量筛选

GOLD ON2/QEUV 的 DQI 表把这些项列为正式产品的质量控制项目：invalid solar zenith angle、invalid `135.6/N2 LBH` intensity ratio、invalid 135.6 radiance uncertainty、invalid N2 LBH uncertainty、lookup table failure、invalid emission angle、flatfield correction 等。

我们的 SSUSI 数据没有 GOLD 的同一套 ON2 DQI，但采用了同类思想：

```text
DQI = 0
SAA_COUNT = 0
SZA <= 75 deg
EXPOSURE > 0
denominator > 30 R
bad-channel bit clear
```

这不是官方 ON2 反演筛选，但属于保守的 radiance-ratio proxy 质量筛选。

### 3. 用 AEB 和 auroral LBHS 剔除极光污染

正式 O/N2 反演和 QEUV 算法都非常强调避开极光/粒子沉降污染，因为 auroral LBH 增强会改变分母并污染日辉成分信号。GOLD guide 的质量控制中也明确把 high background、LBH contamination、solar zenith angle、emission angle 等作为风险源。

我们的处理用 F16 SSUSI EDR-AURORA LBHS 估算 auroral equatorward boundary：

```text
AEB bright threshold = 1000 R LBHS
clean_subauroral:
  Delta MLAT to AEB < -2 deg
  nearest auroral LBHS < 1000 R
```

这一步不是官方 ON2 标准算法，而是为本个例设计的 contamination-control step。它的目的不是产生官方 O/N2，而是避免把极光椭圆内部的低 `135.6/LBHS` 误解释为 subauroral O/N2 depletion。

### 4. 同时检查 LBHS 与 LBHL 两个分母

正式算法使用综合的 N2 LBH 信息，并处理谱线污染；GOLD 资料也特别提到 GOLD 的光谱能力可减少 N2 LBH band 中原子发射线污染。SSUSI SDR2-DISK 这里不能完整做 GOLD 那样的谱反演，所以我们用两个简单 ratio 做一致性检查：

```text
135.6/LBHS = 主 proxy
135.6/LBHL = 辅助一致性检查
```

如果两个 ratio 在 SAPS 附近同向偏低，说明低值更可能是 135.6 相对偏低或 composition-related response，而不只是某一个 LBH 分母偶然 spike。

## 方法学定位

这套处理方法的准确定位是：

```text
文献支持的部分：
  135.6/LBH 与 O/N2 有物理关系；
  GUVI/SSUSI/GOLD ON2 算法 heritage 使用 135.6/LBH；
  正式算法需要 SZA、几何、污染和质量控制。

我们自定义的部分：
  不做 AURIC/LUT 反演；
  用 135.6/LBHS 作为相对 proxy；
  用 AEB + local LBHS 阈值做极光污染筛选；
  用 SAPS 附近同轨道相对变化解释，而非绝对 O/N2。
```

因此在论文里可以说：

> The processing follows the physical basis of FUV O/N2 remote sensing, in which OI 135.6 nm and N2 LBH intensities are used for O/N2 retrievals in GUVI/SSUSI/GOLD heritage algorithms. Here, because no official SSUSI ON2 retrieval or AURIC/LUT inversion is applied, we use the calibrated SSUSI SDR2-DISK 135.6/LBHS radiance ratio only as an AEB-screened relative O/N2-related proxy.

## 本地数据来源与处理链

当前使用的数据来自本地 SSUSI SDR2-DISK 文件：

```text
event_overlay_figures/ssusi_sdr2_disk_data/
dmspf16_ssusi_sdr2-disk_2015076T074225-2015076T092354-REV58873_vA8.2.0r000.nc
```

NetCDF 检查结果：

```text
DATA_PRODUCT_TYPE = SDR binned imaging data
SCAN_TYPE = DISK
SCAN_MODE = REDUCED
可用亮度变量包括：
DISK_INTENSITY_DAY
DISK_RECTIFIED_INTENSITY_DAY
DISK_RADIANCE_UNCERTAINTY_DAY
```

该文件中没有 `ON2`、`O_N2` 或 `O/N2` 官方反演变量。因此当前 proxy 是由 SDR2-DISK dayglow calibrated/rectified radiances 构造的自定义相对指标。

当前脚本采用的 SSUSI disk channel convention：

```text
0 = Lyman-alpha 121.6 nm
1 = OI 130.4 nm
2 = OI 135.6 nm
3 = N2 LBHS
4 = N2 LBHL
```

构造方法：

```text
on2_proxy_1356_lbhs = I_135.6 / I_LBHS
on2_proxy_1356_lbhl = I_135.6 / I_LBHL
```

质量筛选：

```text
DQI = 0
SAA_COUNT = 0
EXPOSURE > 0
SZA <= 75 deg
I_135.6 > 0
LBHS/LBHL denominator > 30 R
135.6、LBHS、LBHL bad-channel bit clear
```

极光污染筛选：

```text
AEB 由 F16 SSUSI EDR-AURORA LBHS 动态估算
AEB bright threshold = 1000 R LBHS
clean_subauroral 要求：
  Delta MLAT to AEB < -2 deg
  nearest auroral LBHS < 1000 R
```

这一步非常重要，因为极光区 LBH 增强会把 `135.6/LBHS` 压低，造成假的 O/N2 depletion。当前 clean proxy 已经排除了 AEB buffer、poleward auroral oval 和 local LBHS enhanced 像元。

## 当前 SAPS 点附近的数值证据

SAPS-like 点：

```text
time = 2015-03-17 08:59:17 UT
MLAT = -56.100667 deg
MLT = 16.920852 h
horizontal ion drift = +2366.2 m/s
Delta MLAT to AEB = -2.459928 deg
```

最近 clean SSUSI proxy 像元：

```text
time = 2015-03-17 08:59:34 UT
MLAT = -55.475540 deg
MLT = 16.628567 h
SZA = 74.952248 deg
Delta MLAT to AEB = -3.388385 deg
nearest auroral LBHS = 190.611923 R

I_135.6 = 623.692322 R
I_LBHS  = 636.870789 R
I_LBHL  = 413.884399 R

135.6/LBHS = 0.979307
135.6/LBHL = 1.506924
```

这个像元满足 clean_subauroral 条件：

```text
Delta MLAT to AEB = -3.39 deg < -2 deg
nearest auroral LBHS = 190.6 R << 1000 R
SZA <= 75 deg
denominators > 30 R
```

所以它不是明显极光椭圆内部污染点，也不是 denominator 太小导致的不稳定比值。

## 与低值阈值和时间序列的关系

当前低 proxy 阈值为全局高纬有效样本的 20% 分位：

```text
LOW_PROXY_THRESHOLD = 1.052049
```

在 AEB 筛选后，低值区间包括：

```text
2015-03-17 08:59:00-09:00:30 UT
median 135.6/LBHS proxy = 1.019902
n_30s_low_bins = 2
```

SAPS 最近 clean proxy：

```text
0.979307 < 1.052049
```

也就是说，SAPS-like 点附近的最近 proxy 确实落在低 ratio 区间内。

SAPS 后到 09:02 UT 的 clean proxy 序列：

```text
n = 29
135.6/LBHS min = 0.916246
135.6/LBHS median = 1.086972
135.6/LBHS max = 1.259710
<= 1.052049 的点数 = 9
```

这说明低值不是单独一个孤立点；SAPS 点之后短时间内存在一串低/近低阈值 proxy 像元，随后逐渐回升。

## 原始通道是否支持 proxy 解释

最近 clean proxy 像元处：

```text
I_135.6 = 623.7 R
I_LBHS  = 636.9 R
I_LBHL  = 413.9 R
```

对 SAPS 后 29 个 clean proxy 样本统计：

```text
I_135.6 median = 741.8 R
I_LBHS median  = 693.3 R
I_LBHL median  = 443.5 R
```

最近 SAPS proxy 的 `I_135.6` 明显低于后续样本中位数，而 `I_LBHS` 没有异常高到极光污染量级。也就是说，`135.6/LBHS` 的偏低不主要是 LBHS denominator 极端抬高造成的；它更像是 OI 135.6 相对偏低导致的 ratio decrease。

交叉检查 `135.6/LBHL`：

```text
nearest SAPS proxy 135.6/LBHL = 1.506924
post-SAPS median 135.6/LBHL = 1.657963
```

LBHL proxy 也偏低一些，方向与 LBHS proxy 一致，但 LBHL 波动更大。因此 LBHL 可作为辅助一致性检查，不建议作为主指标。

## 为什么不能把 0.979 当作 GUVI 那种 O/N2

GUVI/GOLD/SSUSI 正式 O/N2 反演的物理入口确实是 `135.6/LBH`，但正式产品还需要：

```text
辐射传输 / dayglow forward model
AURIC 或类似模型
solar zenith angle dependence
emission angle / viewing geometry
spectral contamination handling
look-up table interpolation
quality/error propagation
```

当前你的数值：

```text
0.979 = I_135.6 / I_LBHS
```

它只是亮度比值。由于两个通道的 Rayleigh 亮度本身都在几百 R 量级，比值落在 0.9-1.3 很正常。GUVI/GOLD 官方 column `ΣO/N2` 的 0.1-0.4 或类似量级来自模型反演后的柱密度比，不是两个亮度直接相除。

因此：

```text
可以比较：同一 SSUSI 轨道/同一处理链内部的相对高低
不可以比较：SSUSI proxy 的绝对数值 vs GUVI official O/N2 的绝对数值
```

## 推荐论文/报告写法

英文建议：

> We use the DMSP/SSUSI SDR2-DISK OI 135.6 nm to N2 LBHS radiance ratio as a relative O/N2-related proxy, not as an official column O/N2 retrieval. The use of this ratio is physically motivated by the heritage of FUV O/N2 remote sensing, where dayside O/N2 retrievals are based on the relationship between OI 135.6 nm and N2 LBH emissions. To reduce auroral contamination, only pixels equatorward of the SSUSI-derived auroral equatorward boundary by more than 2 deg MLAT and away from enhanced auroral LBHS are interpreted. Around the AEB-equatorward SAPS-like drift peak at 08:59:17 UT, the nearest clean-side SSUSI proxy pixel at 08:59:34 UT has 135.6/LBHS = 0.979, below the low-proxy threshold of 1.052. This supports a relative O/N2-related depletion signature near the SAPS crossing, but should not be interpreted as an absolute O/N2 value.

中文建议：

> 本文使用 DMSP/SSUSI SDR2-DISK 的 OI 135.6 nm 与 N2 LBHS 亮度比值作为相对 O/N2-related proxy，而非官方柱 O/N2 反演值。该 proxy 的物理依据来自 FUV 日辉 O/N2 遥感中 OI 135.6 nm 与 N2 LBH 强度关系。为减少极光污染，仅解释位于 SSUSI AEB 赤道侧超过 2 deg MLAT 且附近 auroral LBHS 不增强的像元。F16 在 08:59:17 UT 的 AEB 赤道侧 SAPS-like 漂移峰附近，最近 clean proxy 像元位于 08:59:34 UT，135.6/LBHS = 0.979，低于当前低值阈值 1.052，支持 SAPS 附近存在相对 O/N2-related 降低的迹象。但该数值不能解释为官方绝对 O/N2。

## 风险与进一步增强方案

当前结果可以支撑个例解释，但建议在正文或图注中保留限制说明。

主要风险：

```text
1. 不是官方 O/N2 retrieval，没有 AURIC/LUT/SZA 完整反演。
2. SZA 接近 75 deg 上限，几何/散射效应可能增强。
3. SSUSI 采样是扫描像元，和 SSIES SAPS 点存在约 17 s 时间差及空间偏移。
4. 极光污染已用 AEB 和 LBHS 做筛选，但不能完全排除次级粒子沉降或散射背景影响。
5. LBHL 与 LBHS 方向大体一致，但 LBHL 波动更大，不宜过度解释。
```

更强的后续验证：

```text
1. 若能获得 SSUSI official EDR-DISK ON2 或相应算法/LUT，优先使用官方 ON2。
2. 对 135.6/LBHS 做 SZA-bin 归一化或局部背景归一化，避免斜阳几何影响。
3. 与 GUVI/GOLD/TIE-GCM 在同一时段的 O/N2 depletion 区域做空间一致性比较。
4. 在 SAPS 前后取同一 AEB-relative 坐标的背景样本，报告相对百分比降低，而不是只报原始 ratio。
5. 对 `I_135.6`、`LBHS`、`LBHL` 分通道图保留在补充材料中，说明低 ratio 不是单纯 LBHS denominator spike。
```

## 最终判断

你的这组 DMSP/SSUSI O/N2 proxy 数据**可以用**，但使用层级应当是：

```text
强：支持 SAPS 附近存在 relative O/N2-related depletion signature
中：作为 SSIES SAPS 与中性成分响应之间的局地对应证据
弱/不可：作为官方绝对 O/N2 反演或与 GUVI 绝对数值直接比较
```

最推荐的图注关键词：

```text
DMSP/SSUSI 135.6/LBHS radiance-ratio proxy
relative O/N2-related proxy
AEB-screened clean-side pixels
not an absolute column O/N2 retrieval
```

## 参考资料

1. Eastes et al. (2017), The Global-Scale Observations of the Limb and Disk (GOLD) Mission, Space Science Reviews. https://link.springer.com/article/10.1007/s11214-017-0392-2
2. GOLD Public Science Data Products Guide Rev. 5.2, section 5.3 ON2 Data Product. https://gold.cs.ucf.edu/data/documentation/
3. GOLD Public Science Data Products Guide Rev. 5.2 PDF. https://gold.cs.ucf.edu/wp-content/documentation/GOLD_Public_Science_Data_Products_Guide_Rev5.2.pdf
4. Strickland, D. J., Evans, J. S., and Paxton, L. J. (1995), Satellite remote sensing of thermospheric O/N2 and solar EUV: 1. Theory, JGR. Listed in GOLD Data Products Guide ON2 references.
5. Evans, J. S., Strickland, D. J., and Huffman, R. E. (1995), Satellite remote sensing of thermospheric O/N2 and solar EUV: 2. Data analysis, JGR. Listed in GOLD Data Products Guide ON2 references.
6. Strickland et al. (1999), Atmospheric Ultraviolet Radiance Integrated Code (AURIC): theory, software architecture, inputs and selected results, JQSRT. Listed in GOLD Data Products Guide ON2 references.
7. Correira et al. (2021), Thermospheric composition and solar EUV flux from the GOLD mission, JGR Space Physics, doi:10.1029/2021JA029517. Listed in GOLD Data Products Guide ON2 references.
8. Christensen et al. (2003), Initial observations with the Global Ultraviolet Imager (GUVI) in the NASA TIMED satellite mission, JGR, doi:10.1029/2003JA009918. Listed in GOLD Data Products Guide ON2 references.
9. Bender, Espy, and Paxton (2021), Validation of SSUSI-derived auroral electron densities: Comparisons to EISCAT data, Ann. Geophys., 39, 899-910. https://doi.org/10.5194/angeo-39-899-2021
10. NASA CDAWeb DMSP/SSUSI public data archive path used by the processing scripts. https://cdaweb.gsfc.nasa.gov/pub/data/dmsp/
