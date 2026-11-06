# jiangnan-style

> 一个用于**分析并复现中文作家江南（《龙族》《九州·缥缈录》《此间的少年》作者）行文技法**的 Agent Skill。非官方粉丝项目，仓库不含任何原作文本。

## 它能做什么

| 模式 | 输入 | 输出 |
|---|---|---|
| A 生成 | 设定/大纲/一句话需求 | 江南腔原创文本 |
| B 改写 | 任意既有文本 | 保意的江南腔版本（v0.2） |
| C 续写 | 前文片段 | 指纹一致的后文 |
| D 诊断 | 一段文本 | 12 项量化指标 + 像不像的报告 |

核心思路：**文风 = 骨架（叙事结构）× 皮肤（语言习惯）**。骨架与皮肤都被拆成可执行规则（`references/`），再用 12 项量化指标（`scripts/audit_style.py`）检验"结构上像不像"，人工评分卡检验"整体上像不像"。

## 快速开始

### 作为 Agent Skill 使用

复制到你的 agent 技能目录（WorkBuddy / Claude Code / 其他兼容 agent 的 `skills/` 目录）：

```bash
cp -r jiangnan-style ~/.workbuddy/skills/   # WorkBuddy
cp -r jiangnan-style ~/.claude/skills/      # Claude Code
```

然后直接说："用江南的文风写一个……"或"把这段改成江南的风格"。

### 作为工具脚本使用

```bash
# 文本体检（12 项指标，阈值未标定时输出 uncalibrated）
python scripts/audit_style.py 我的章节.md

# 标定：用你本地合法持有的语料算阈值（只输出统计值，不输出原文）
python scripts/audit_style.py corpus/source/ --calibrate -o assets/schemas/thresholds.json

# EPUB 抽文本到本地语料目录
python scripts/extract_epub.py "某本书.epub" -o corpus/source/
```

依赖：仅 Python 3.10+ 标准库。

## 目录导览

```
SKILL.md            入口：任务路由（7 模式）+ 八条铁律
references/         风格知识（style/ 骨架与皮肤 · adapters/ 题材×体裁 · rewrite/ · guardrails/ · corpus-notes/）
workflows/          场景 SOP（生成 / 改写 / 续写 / 诊断 / 润色 / 大纲 / 同人）
scripts/            audit_style.py · diff_style.py · overlap_check.py · extract_epub.py · add_reference.py
assets/             模板 · 评分卡 · JSON Schema（阈值）
examples/           全部自撰示例（before-after · prompts · golden · anti-examples）
corpus/             本地语料，永久 gitignore，绝不入库
docs/               ARCHITECTURE.md · ROADMAP.md · CONTRIBUTING.md
```

设计与决策详见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 合规边界（重要）

- 本项目**不含、不分发、不引用**江南作品原文；所有示例为本项目自撰。
- `references/` 只包含对写作技法的**抽象分析**；文风本身不受著作权保护，具体表达才受。
- 产出为 AI 原创仿写，**严禁标注为江南本人作品**或用于冒充。
- 同人创作默认关闭，启用时强制前置"非商用 + 标注出处"提示。
- 完整声明见 [NOTICE.md](NOTICE.md)；语料纪律见 [corpus/README.md](corpus/README.md)。

## 状态

**v1.0.0**（2026-11-06）：七模式全通（生成 / 改写 / 续写 / 诊断 / 润色 / 大纲 / 同人）。12 项指标阈值已用 846 万字语料标定，5 个脚本 + 12 个单测 + CI 守卫就绪。

下一步（v1.1）为盲测：把自撰样本混在真人作品里请人判断，目标 ≥80% 无法分辨。见 [CHANGELOG.md](CHANGELOG.md) 与 [docs/ROADMAP.md](docs/ROADMAP.md)。

## 安装与使用

> 📖 **第一次用请先读 [docs/使用教程.md](docs/使用教程.md)** —— 全文大白话，含七个场景的说话模板、报告怎么读、完整实战演示、20 条 FAQ 和术语表。下面是速览。

**方式一：装成本地 skill**（WorkBuddy / Claude Code 通用）

```bash
# 目录名必须与 SKILL.md 里的 name 一致
cp -r jiangnan-style ~/.workbuddy/skills/jiangnan-style
```

装好后直接说话即可触发，不需要敲命令：

- "用江南的文风写一个雨夜里的告别" → A 生成
- "把这段改成江南腔" → B 改写
- "接着这段往下写" → C 续写
- "这段像不像江南？打个分" → D 诊断
- "只帮我润色一下，别改内容" → F 润色
- "先给我一个中篇的大纲" → G 大纲

**方式二：不装 skill，直接跑脚本**

```bash
python scripts/audit_style.py 你的文本.txt        # 12 项指标体检
python scripts/diff_style.py 原文.txt 改后.txt     # 改写前后对照
python scripts/overlap_check.py 你的产出.txt --corpus corpus/source/   # 查重（需本地语料）
```

**本地语料是可选的。** 没有语料时：`audit_style.py` 用仓库内已标定的阈值照常工作；`overlap_check.py` 不可用（无参照）；`--calibrate` 会失败。详见 [corpus/README.md](corpus/README.md)。

## License

[MIT](LICENSE)。再次强调：本授权覆盖的是本项目自身的代码与文档，不含任何第三方作品内容。
