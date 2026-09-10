# Codex 执行入口：SSUSI–SuperDARN–GOLD 柱 O/N₂ 观测统计

日期：2026-09-10。

**本文件是执行任务书，不是已实现的软件或已经生成的科学结果。默认任务是完成 P0–P2 的审计、实现、测试与小样本试运行；尚未冻结科学协议前，不运行多年确认性统计。**

## 0. 先读这些文件

1. 本文件：决定工作顺序、范围、交付物与停止条件。
2. [科学执行方案 V2](SSUSI_SuperDARN_GOLD_ON2_execution_plan_v2_20260910.md)：科学问题、观测标准、估计量和分类逻辑。
3. [参数模板 V2](SSUSI_SuperDARN_GOLD_ON2_protocol_v2_20260910.yaml)：拟实施参数、字段要求、参考依据。
4. [既有进展快照](../reports/SAPS_ON2_CURRENT_PROGRESS_20260908.md)：只用于了解历史成果和证据边界，不把旧候选数当作新分支结果。
5. [复现说明](reproduction_notes.md)：现存脚本可能依赖原工作空间、未上传原始数据和旧导入路径。

若仓库有 AGENTS.md 等局地开发规范，按适用范围阅读。现有 scripts、入口包装器和导入依赖必须逐项检查；不能因文件名或旧计划写了“已实现”就认定代码完整可运行。

**优先级：实际仪器元数据与可核查官方说明 > 经记录的科学决策 > V2 中的待验证默认值。遇到冲突先生成差异与依据，不静默修改协议。**

## 1. 本轮任务与非目标

主链条：DMSP/SSUSI 提供局地极光边界；SuperDARN 独立识别边界赤道侧的增强西向流并跟踪局地过程；GOLD 官方 L2 ON2 记录对应区域的柱成分。DMSP SSJ/SSIES 只用于有观测机会时的独立验证，不要求每个事件都有原位穿越。

本轮先回答：

- 哪些时间和区域具有真实的三仪器联合观测支持？
- 现有代码能复用什么，缺少哪些实际解析器、矢量反演和质量检查？
- 少量真实事件能否产生有边界、有局地速度、有原生 GOLD 足迹的共位记录？
- 哪些事件具备空间对照，哪些进一步具备时间响应约束？

非目标：不重跑整年 TIEGCM；不开展 TREx/GLOW 化学与光学闭环；不开发 SSUSI 绝对 O/N₂ 反演；不将 2015 GUVI/proxy 数字混入 GOLD 统计；不为获得更多降低事件或更小 p 值调整门限。

## 2. 保留历史分支与建立工作目录

不要删除或改写已有 2015 观测快照、图件、V3 门控结论、GUVI/DMSP 旧协议。旧代码若需修补导入和路径，须有独立提交与回归检查。

建议新模块放在 `scripts/ssusi_superdarn_gold/`，测试放在 `tests/ssusi_superdarn_gold/`。以下目录是拟建立约定，不表示已存在：

```text
config/local_paths.yaml                                  # 本地私有，gitignore
config/ssusi_superdarn_gold/pilot_events.csv               # 小型、可追溯试点清单
config/ssusi_superdarn_gold/known_product_issues.csv        # 有官方来源的问题掩膜
config/ssusi_superdarn_gold/native_variable_mapping.json   # 真实变量/维度映射
scripts/ssusi_superdarn_gold/
tests/ssusi_superdarn_gold/
data_work/ssusi_superdarn_gold/<run_id>/                    # 原始/大体积/中间结果，不上传
summaries/ssusi_superdarn_gold/<run_id>/                    # 可公开小表与审计报告
figures/ssusi_superdarn_gold/<run_id>/                      # 经检查的代表图
reports/SSUSI_SUPERDARN_GOLD_<run_id>_progress.md
```

在获取数据前添加必要的 .gitignore 保护。数据根目录由配置或环境变量指定，禁止硬编码某个人的盘符。认证使用已有合法凭据；不提交口令、cookie、token、认证邮箱、机器绝对路径或带签名下载链接。公共清单可保留公开源地址、文件基名、大小和 SHA256。

不要重置、清理或覆盖用户未提交修改。开工记录基础 commit 与工作树状态。依赖先审计再安装到隔离环境，不盲目升级已有环境。

## 3. P0：资产、文献与规则审计

### P0-A 仓库与运行环境

读取真实代码、requirements 和数据清单，检查入口是否只是包装器、被引用模块是否存在、旧绝对路径是否可替换。产出 `implementation_inventory.csv`：模块、现存路径、实际能力、依赖、真实数据测试状态、缺口、复用/新建决策。

### P0-B 参数来源与仪器元数据

建立 `method_evidence_ledger.csv`，字段至少包括 parameter_id、当前默认值、official/literature/project、原始来源、页码/章节、适用仪器、核查状态、冲突及行动。

重点核查：SSUSI 能流变量、单位、日辉处理和光学边界与 b1e/b2e 的区别；雷达拟合几何和实际支持尺度；GOLD ON2 产品版本、DQI 位、原生时间、足迹与误差字段；已知仪器问题的日期/UT。

V2 中的文献转述和产品版本是此前方案记录，不代替本轮原文/文件核查。0.2 能流参考、250 m/s、15 min、5 min、50% 足迹、±10% 等默认值不能未经审计就被宣称为统一物理标准。GYM ±10日是保守项目筛选，不是自动认定整个窗口均为官方坏数据。

文献或元数据不可取得时记录 pending/blocked。缺少关键信息不得用经验常数假造原生变量、边界误差或速度误差。

### P0-C 获取与真实解析

先查本地已存在的合法文件，再查询官方目录和清单：SuperDARN FITACF、SSUSI EDR-AURORA、GOLD L2 ON2；需要检查背景和辐射时获取对应 L1C；Dst/其他上下文指数作为补充。

先获取清单和小样本，不直接下载六年全量数据。实现限速、超时、有限重试、断点续传、缓存和校验。下载200状态或扩展名正确都不是成功标准：必须识别文件格式、排除HTML登录页面、检查变量和时间覆盖。

认证/网络/权限失败只阻塞对应路径；继续处理已可用数据和其他事件。不得绕过授权，不把下载失败记为科学 nonmatch。

**P0验收：**代码能力、产品字段、合法获取路径和阻塞均可追溯；至少对可获得的真实文件完成解析检查。任何未通过项如实保留，不把“代码写好”写成“仪器科学就绪”。

## 4. P1：共同覆盖试点与盲检清单

候选总体暂为2019–2024，2025单列外部验证；先按实际扫描模式、日辉条件与回波覆盖评估，不保证最终每年都能贡献同等样本。

优先审计下列此前讨论的文献事件；它们只是资料检索入口，不保证三仪器同时有效：

| event_id | 检索日期（UTC） | 用途 |
|---|---|---|
| pilot_20190927 | 2019-09-27 至 2019-09-28 | 早期 GOLD 采样模式候选 |
| pilot_20211103 | 2021-11-03 至 2021-11-04 | 降频之后的采样候选 |
| pilot_20230226 | 2023-02-26 至 2023-02-28 | 长持续流动/成分资料候选 |
| pilot_20240510 | 2024-05-10 至 2024-05-12 | 近期资料与已有背景模型候选 |

清单以闭区间日历日期表达；代码必须转换为明确的UTC起点和次日00:00的排他终点。起始前参考和结束后跟踪数据另加缓冲，不把00:00当作SAPS起始。没有联合覆盖时保存原因，不为保住“标杆”跨几小时强行配准。

另从可观测机会总体中，按季节、活动水平、实际GOLD采样和MLT分层抽约20个时段，用固定随机种子20260910；清单在查看ON2异常前写入并留哈希。多时段属于同一风暴时不得拆进训练与验证两边。样本不足可少于20，必须报告实际数，不补造记录。

覆盖表分两层：

1. 计划/文件/几何覆盖：与ON2取值高低无关。
2. 原生QC后覆盖：保留各质量位和潜在信号依赖缺测，不能把这层当作完全无选择偏差。

先生成各仪器覆盖及交集。SSUSI观测边界有效期、雷达真实矢量支持、GOLD像元时间均独立计算。不要用雷达名义视场替代回波，也不要用整个扫描日期替代像元时间。

**P1验收：**给出实际共同覆盖率、原生文件与数据量、失败原因和可进入下一步的候选。若无共同覆盖，提交可信的覆盖报告，仍属有效试点结果，不虚构科学事件。

## 5. P2：实现最小可验证流程并跑真实标杆

### 模块与接口

实现或复用以下功能；名称是目标接口，不是当前可运行命令：

1. inventory_sources：源清单、字段映射、质量状态与共同覆盖。
2. extract_ssusi_boundary：局地实测边界、时间、误差和SSJ验证字段。
3. fit_superdarn_vectors：定量速度、方向、误差、原始支持范围及独立低流分支。
4. track_saps_episodes：连通通道、父事件、固定ROI、起始/消退区间。
5. match_gold_and_controls：原生足迹、像元时间、固定区域与对照。
6. classify_and_analyze：空间差异、事件后增量、时滞区间和分类。
7. build_report：真实计数、图件、失败项、测试与证据链。

可建立统一入口 `scripts/ssusi_superdarn_gold/run_pipeline.py`，支持 inventory、coverage、boundary、vectors、episodes、match、analyze、report 子命令；至少接受 --protocol、--events、--data-root、--output-root、--run-id。先实现 --help 和配置校验后才在报告中给出可运行命令。加入 --dry-run；分析命令不得隐式触发多年下载。

### 数据合同

每个表须有确定的schema、单位、时区、版本、主键和外键；空表也保留schema及缺失原因。建议至少：

| 表 | 核心字段 |
|---|---|
| source_manifest | source_id, instrument, public_basename, version, time_start/end, sha256, parse_status |
| observation_opportunity | cell_time_id, planned_coverage, native_qc_coverage, boundary_support, vector_support, gold_support, reason_codes |
| ssusi_local_boundaries | boundary_id, source_id, local_time_utc, mlt, mlat, uncertainty, support_type, particle_boundary_validation |
| superdarn_local_vectors | vector_id, time_utc, lat/lon, mlat/mlt, Vw, direction, uncertainty, support_ids, fit_domain, quality |
| saps_parent_tracks | parent_track_id, storm_id, observed_extent, gaps, recurrence_links |
| saps_local_episodes | episode_id, parent_track_id, fixed_roi_id, onset_left/right, peak_time, end_left/right, timing_quality |
| gold_native_pixels | pixel_id, scan_id, source_id, pixel_time, footprint, ON2, DQI, SZA, emission_angle, uncertainties |
| roi_control_sets | roi_id, target_or_control, footprint_ids, fixed_weights, preselection_hash, exposure_status |
| paired_timeseries | episode_id, scan_id, pixel_ids, dt_match, overlap, boundary_age, A, D, relative_increment, uncertainty |
| response_intervals | episode_id, onset_interval, detectable_transition_interval, lag_left/right, censoring_reason |
| classification_and_gates | episode_id, spatial_eligible, controlled_eligible, timing_eligible, preexisting, time_class, direction, persistence, reason_codes |

像元唯一标识建议含产品版本、原生文件、扫描和原生行列，不能只用四舍五入后的经纬度。每个派生产物保存 source hashes、processing commit、protocol hash 和 run_id。多个失败原因允许并存。

### 必须处理的逻辑细节

- 固定ROI只由雷达和几何选择，不能追着ON2最低值移动；跨通道剖面与固定ROI时序分别保存。
- 时间分箱、平滑是否使用未来数据须明确。用于展示的中心平滑不能决定更早的起始；起始使用原生4min格及区间，事后确认不把起始推后到确认结束。
- 12min稳健强度、250m/s入口和4min起始门限属于不同字段；记录一致性，不混为一个速度。显著增强的非零基线没有预先定义增量门限时，只作已有流动事件，不假造 onset。
- 0–1、1–3、3–6h采用明确且不重叠的端点约定：[0,1]、(1,3]、(3,6]。跨边界的时滞区间留为 ambiguous。
- 完整未来峰值仅用于事后描述分档，不能用来解释此前响应或反选ROI。低流对照必须有有效测量，强东向流另列，不作为普通低流对照。
- 不能有“低ON2才入样”、高—低—高才通过、伪造SSUSI绝对ON2、GOLD夜间辐射当ON2、T-slope当中性输运速度等逻辑。
- 同一GOLD观测支持被重复使用时，不增加独立成分样本数；完整事件通过同一 parent_track_id/storm_id 关联。
- 真实资料与synthetic fixtures完全分离；合成数据仅测算法，不得进入观测图、事件数或science-ready报告。

### 科学就绪分层

co-location、controlled-effect、resolved-spatial-profile、timing-response四个标签独立保存。时间资料不完整不自动淘汰空间配对。未知边界不推为实测，误差缺失不填零；不同资料路径只能在其能力范围内晋级。

两位人工审阅尚未完成时写 `human_review_pending`。自动交叉规则不等于两位独立研究者审阅；不能代填人工通过。可先完成自动测试和候选图并交付审阅包，继续其他不依赖人工标签的任务。

**P2验收：**至少形成可追溯真实候选的联合图和计数，或对无法形成候选的原因作完整说明；测试实际运行且有结果；可获得字段都来自原始资料。标杆目标是3–5例，不是保证数量，零响应和不确定结果照常交付。

## 6. 强制测试与交付检查

至少实现并运行：

1. 无回波不等于无流动；无文件不等于科学nonmatch。
2. 模型填补边界不等于实测，边界年龄/误差超限会正确阻塞。
3. SSUSI光学边界不被直接重命名为b1e。
4. LOS负号、东西方向、MLT跨24h、半球/参考高度均有测试。
5. 一个原生GOLD像元不能构成三个独立区域或多次独立观测。
6. 像元时间与扫描中心不同、跨UTC午夜、时间差符号均正确。
7. 时滞区间跨1h不能强制分类；第一幅低值图不是变化开始点。
8. 日落/质量缺测/雷达中断不是恢复，未知误差不是零。
9. 多对多匹配和多雷达重叠不重复增加独立样本。
10. 已有异常与后续增量可以并存，统计分类不要求ON2必须降低。
11. 对照被SAPS影响时停止对应比较，不按后期ON2挑替代者。
12. YAML重复键、类型和单位非法时拒绝执行；空表、断点重跑和缓存过期处理可复核。

初轮进展报告必须列出：基础/执行commit、协议hash、真实运行命令、环境锁定信息、源文件数、解析结果、各层实际候选与独立风暴数、空间/时间子集交集、失败原因、执行过的测试、未执行部分、缺失的人审与下一步。

若生成科学图，注明原生采样和插值区别，显式显示缺测与误差，不连跨缺口实线制造持续性。只有合成fixture的测试时，结论只能是软件测试通过，不能是观测验证通过。

## 7. P3–P4：通过门控后才开展的后续阶段

P3：完成独立审阅/验证与参数依据核查，冻结新协议版本与盲检/留出清单；若有修改，保存新版本和差异，不能覆盖本次V2快照。再扩展真实共同覆盖支持的年份和风暴总体。

P4：按局地事件与风暴聚类报告连续效应、速度分档、时滞区间、采样降级实验及阈值敏感性。报告选择函数和未知精度类别，不宣称已证明因果。观测问题稳定后，再选个例做模型，不在本轮自动启动。

**本次默认停在P2审计包交付。缺少科学门控时不自动进入多年确认性统计；不因某个文件阻塞就停止全部可执行工作。**

## 8. 完成后提交什么

允许提交：新代码和测试、小型脱敏CSV/JSON、运行说明、方法依据表、报告及必要代表图。禁止提交：原始多年卫星/雷达数据、缓存、凭据、未公开稿件和大量重复图片。

提交前检查 git diff --stat、敏感信息、文件大小、相对链接和实际测试结果；只提交本任务相关内容，不覆盖他人修改。不运行强制推送。若已有用户授权推送，按仓库流程提交新分支或普通commit，并返回实际commit和入口路径。

## 9. 可直接给Codex的任务指令

> 阅读本执行入口及链接的科学方案和YAML，先审计仓库真实代码和本地数据，然后按P0→P1→P2实施。不要只再写计划：完成可执行的资料盘点、获取/解析、质量检查、测试与小样本试运行，并生成真实进展报告。优先检查四个指定候选事件及约20个不依赖O/N₂结果选择的时段。缺数据时记录阻塞并继续其他可做工作，不用合成数据冒充观测。SSUSI约束边界、SuperDARN识别西向通道、GOLD记录官方柱O/N₂，保留旧2015分支。不要启动全期下载、多年确认性统计或TIEGCM运行，直至本轮门控和独立审阅完成。交付实际执行命令、测试结果、共同覆盖、事件分层计数、代表图或无法成图的原因，以及未完成项目。
