# Changelog

本项目的版本号遵循 [SemVer](https://semver.org/)。

## [Unreleased]

## [1.0.2] - 2026-11-07

### Fixed

- **M11 指标设计缺陷（第二个测量 bug）**：旧正则 `[\u4e00-\u9fff]{4}` 匹配"任意被标点隔开的 4 连汉字"（"林小满说"也算四字格），与标点密度强相关，跨文本比较失真。改为只数 AABB / ABAB 叠词四字格，阈值重标定：5.4–9.6 → **0.45–1.43/千字**（语料实测江南极少用叠词格，中位约 0.9/千字）
- 连带同步 `style/09-dna.md`（定义 + 阈值 + 局限）、`docs/使用教程.md`

### Added

- `examples/golden/样本02-停电的晚自习.md`：**端到端自测产物**。从零生成 1850 字短篇，三轮定点改写后 12 项指标全部进入容忍区（初稿 6 项超容忍 → 0），`overlap_check.py` 查重 586 万 15-gram 零重合。附三轮指标演变表与四条方法论结论（初稿偏差可预测、冷拳最易超标、M12 是首查项、指标按耦合组改）

## [1.0.1] - 2026-11-06

## [1.0.1] - 2026-11-06

### Fixed

- **断句正则 bug（影响全部句长类指标）**：`SENT_SPLIT` 要求句末标点后**必须**跟右引号，导致所有无引号的叙述句不被切分——M1"平均句长"实际算成了"每段字数"，虚高近一倍（41 字 vs 真实 25 字），M3 单句成段比虚高到 70%（真实 38%）。
  - 修复：正则改为 `[。！？!?…]+[”』」）)]*`（右引号可有可无）
  - **全部 12 项阈值已重标定**（33.4 万句 / 846 万汉字）：M1 目标区间 36.3–49.1 → **22.8–29.5 字**，M3 62.4–79.5% → **30.2–45.4%**
  - 连带修正 `style/02`（长句论断）、`style/08`（"句长双峰"结论作废，实为右偏分布）、`style/09`（阈值表）、`corpus-notes/quant-findings`（第 1、2 条）、`corpus-notes/三本书对照`（全表重算）、`examples/anti-examples`、`workflows/wf-critique`、`examples/golden/样本01-评注`
- **新增 4 个回归测试**（`TestSentenceSplit`）：锁死"纯叙述句必须切分"这一行为，防止同类 bug 复发。总测试 31 个。

### Changed

- `examples/golden/样本01` 重排段落结构以贴近新基准，评注改为**如实记录 4 项超界并说明原因**（不再宣称"完美样本"）；定位改为"回归基准"

## [1.0.0] - 2026-11-06

首个完整版：**七个任务模式全部有 SOP，所有脚本实测通过，文档与实现无悬空引用。**

### Added

- `workflows/` 补齐五个：`wf-continue`（续写：六项指纹锁定表）/ `wf-critique`（诊断：只出报告不改文，三条最优先改法）/ `wf-polish`（润色：只动字词句，禁改结构）/ `wf-outline`（大纲：内核→三问→卷幕→章节表→伏笔账本）/ `wf-fanfic`（同人：四行合规确认前置）
- `scripts/diff_style.py`：改写前后**维度级**对照（12 项指标位移 + 保意核查：数字串/台词丢失 + 反推手术级别 L1/L2/L3），含 CJK 列宽对齐
- `scripts/add_reference.py`：新增题材/体裁适配器并自动登记进 `00-INDEX.md`（幂等，实测）
- `examples/golden/样本01-修车铺的雨.md` + 评注：自撰合格样本，**附实测指标与偏差分析**
- `examples/anti-examples/五种假江南.md`：五种高频失败模式的错例/病灶/改法
- `references/corpus-notes/三本书对照.md`：分册中位数对照，验证指纹跨作品稳定 + 古装↔现代趋势
- `tests/test_diff.py`：15 个新测试（总 27 个）

### Fixed

- **`style/02-voice.md` 与实测冲突**：原写"短句独立成段预算千字 3–4 次"，但语料实测单句成段占 70%（是常态而非武器），真正的冷拳只占段落 0–3.5%（约千字 1 次）。已改写定义并同步 `wf-generate.md`
- `SKILL.md` / `00-INDEX.md` / `ARCHITECTURE.md` 把指标数写成"9 项"（实际 12 项），全部校正
- `README.md` 状态段停留在 v0.1.0、把已完成的功能标为"v0.4 待做"，已重写并补「安装与使用」章节
- 删除 19 个已有实文件目录里的冗余 `.gitkeep`，删除空目录 `tests/fixtures`、`.github/ISSUE_TEMPLATE`

### Changed

- 任务路由表从 5 模式扩到 7 模式（新增 F 润色、G 大纲），并显式警告 F 与 B 判错就越权改结构

## [0.3.0] - 2026-11-06

### Added

- **改写链全通**：`references/rewrite/` 四件套（三级手术/保意规则/AI 腔六类清单/报告格式）+ `workflows/wf-rewrite.md`（定级→锁定→手术→验收→报告）
- `scripts/overlap_check.py`：n-gram 原创度守门（哈希索引省内存，src 精确校验滤碰撞），双向实测通过（原创 PASS / 74 字抄袭 FAIL）
- `tests/`：12 个单元测试全绿（audit 8 + overlap 4）
- `.github/workflows/ci.yml`：测试 + 三道守卫（语料零入库 / 长原文扫描 / frontmatter 校验）
- `references/adapters/`：5 题材（校园/都市奇幻/东方奇幻/科幻/回忆散文）× 5 体裁（短篇/中篇/连载/片段/非虚构）打样
- `assets/templates/`：开篇模板（四式）、章节模板（起承转钩）、改写对照表、伏笔账本
- `references/guardrails/` 三件套落地：copyright（含引用 ≤3 处×25 字上限）/ originality（A-D 分档）/ fanfic-policy（四行强制确认）
- `examples/before-after/` 首个 AI 腔→江南腔改写对照示例
- `docs/ROADMAP.md` + `docs/CONTRIBUTING.md`

## [0.2.0] - 2026-11-06

### Added

- `scripts/auto_analyze.py`：全自动分析流水线（量化特征 + 场景切片 + 阈值标定 + 报告），1007 万字 29 秒跑完
- `references/style/03-imagery.md` ～ `08-setpiece.md`：六份风格规则文件，全部基于语料实证（每个文件标注"数据依据"）
- `references/corpus-notes/quant-findings.md`：十大核心发现（句长双峰、单句成段 69.8%、对话双口径、比喻朴素直给、"忽然"扳机词等）
- `references/corpus-notes/scene-pointers.md`：7 类场景切片指针索引（不含原文）
- `assets/schemas/thresholds.json`：12 项指标阈值正式标定（`_status: calibrated`），09-dna.md 已回填

### Fixed

- `extract_epub.py`：Windows 文件名三连坑（非法字符 / NTFS ADS 触发符 / 撞名覆盖），章节文件改为"spine 序号 + 净化名"，三本 EPUB 全量重抽成功（1680 章 / 1007 万字符）

### Compliance

- 场景样例原文仅存 `corpus/exemplars/`（gitignore）；`references/` 只存模式结论与指针，仓库保持零原文


## [0.1.0] - 2026-11-06

### Added

- 三层架构落地：路由层 `SKILL.md` / 知识层 `references/` / 执行层 `workflows/` + `scripts/` + `assets/`
- `SKILL.md`：任务路由表、八条写作铁律、渐进式加载索引
- `references/style/01-skeleton.md`：叙事骨架（视角、时间线、结构、信息释放）
- `references/style/02-voice.md`：语言皮肤（句法、断句、标点、口语配比、人称）
- `references/style/09-dna.md`：9 项可量化风格指纹的定义（阈值待语料标定）
- `workflows/wf-generate.md`：从零生成的五步 SOP
- `scripts/audit_style.py`：风格量化审计（9 指标 + 阈值判定 + `--calibrate` 标定模式）
- `scripts/extract_epub.py`：本地 EPUB → 纯文本抽取（输出到 `corpus/`，永不入库）
- `assets/schemas/audit-report.schema.json` + `assets/schemas/thresholds.json`（占位未标定）
- `assets/rubric/style-scorecard.md`：9 维度人工盲测评分卡
- `examples/prompts/`：3 个典型调用样例
- 版权底座：MIT `LICENSE` + `NOTICE.md` + `.gitignore` 语料守卫 + `corpus/README.md`

### 明确不做（Non-goals）

- 不收录、不分发任何江南作品原文
- 不提供"绕过 AI 检测"类功能
- 不默认产出江南作品人物的同人文（模式存在但默认关闭）
