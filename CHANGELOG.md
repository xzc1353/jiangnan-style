# Changelog

本项目的版本号遵循 [SemVer](https://semver.org/)。

## [Unreleased]

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
