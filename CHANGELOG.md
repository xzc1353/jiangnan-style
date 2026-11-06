# Changelog

本项目的版本号遵循 [SemVer](https://semver.org/)。

## [Unreleased]

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
