# 00-INDEX —— 知识层索引

> 用途：路由后查这张表，决定读哪几个文件。**不要整目录通读。**

## style/ —— 核心风格（跨题材通用）

| 文件 | 内容 | 何时读 |
|---|---|---|
| `style/01-skeleton.md` | 视角、时间线、章节结构、信息释放节奏、开篇四式 | 任何"写"的任务，第一个读 |
| `style/02-voice.md` | 句法节奏、断句、标点温度、口语配比、人称策略 | 任何"写"的任务，第二个读 |
| `style/03-imagery.md` | 意象系统分类与配比 | 需要场景描写、氛围段落时 |
| `style/04-character.md` | 少年感、师门生态、配角尊严 | 写人物、写群像时 |
| `style/05-dialogue.md` | 对话节奏、吐槽、答非所问 | 对话密集段落 |
| `style/06-emotion.md` | 情绪收放、金句公式 | 抒情段、高潮段 |
| `style/07-humor.md` | 幽默四层：自嘲/互损/荒诞/黑色 | 轻松段落 |
| `style/08-setpiece.md` | 名场面构造：镜头切分与冷拳位 | 高潮战役、关键转折 |
| `style/09-dna.md` | 9 项量化指纹与阈值 | 体检、自检、标定 |

## adapters/ —— 适配层（v0.3 起）

| 文件 | 何时读 |
|---|---|
| `adapters/genres/campus.md` 等 | 每次写作读**一个**题材适配器 |
| `adapters/forms/serial.md` 等 | 每次写作读**一个**体裁适配器 |

适配器只回答两个问题：这个世界里能出现什么；这个长度上节奏怎么排。**不允许适配器覆盖 style/ 的规则。**

## rewrite/ —— 改写专用（v0.2 起，仅 B 模式读）

| 文件 | 内容 |
|---|---|
| `rewrite/01-surgery-levels.md` | 三级手术：句级微调 / 段级重铸 / 全篇重写 |
| `rewrite/02-preserve-meaning.md` | 保意清单：事实、数字、专名、立场、结构 |
| `rewrite/03-ai-tells.md` | AI 腔清除清单 |
| `rewrite/04-diff-report.md` | 改写报告格式 |

## guardrails/ —— 红线（任何模式可读）

| 文件 | 何时读 |
|---|---|
| `guardrails/copyright.md` | 首次任务、产出涉及原作设定时 |
| `guardrails/originality.md` | 交付前自检 |
| `guardrails/fanfic-policy.md` | 涉及江南作品人物时（同人模式前置） |

## corpus-notes/ —— 语料观察笔记

只记**结构元数据**（卷章分布、篇幅、POV 规律），永不记原文。标定 `09-dna` 阈值时的结论存放处。

## 体积纪律

- 单次任务典型加载：`SKILL.md` + `00-INDEX`（本文件）+ `style/01,02` + 2 个 adapters ≈ 8k–10k 字
- 超过 12k 字仍未动笔 = 加载策略错了，回去砍文件
