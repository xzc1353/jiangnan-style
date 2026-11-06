---
name: jiangnan-style
description: 江南（《龙族》《九州·缥缈录》《此间的少年》作者）文风写作引擎。当用户要求以江南的文风生成、续写、改写中文文本，或要求对一段文本做"像不像江南"的诊断与评分时使用。也覆盖"少年感""热血青春""废柴逆袭""学院奇幻"等近似文风请求。本技能不收录、不输出任何原作文本，产出均为原创仿写。
license: MIT（另有 NOTICE.md 合规声明，二者同读）
allowed-tools:
disable: false
agent_created: true
---

# 江南文风写作引擎

把"写得像江南"拆解为可执行规则与可量化指标。本文件只做三件事：**判任务、给铁律、指路**。风格细节一律按需读 `references/`，不要凭记忆动笔。

## 第一步：任务路由（必做）

按优先级判断模式，判断不了就问用户：

| 用户意图 | 模式 | 必读文件 |
|---|---|---|
| 从零写一段/一篇（给设定、给大纲、给一句"帮我写个开头"） | **A 生成** | `workflows/wf-generate.md` + `references/style/01,02` + 对应 adapters |
| 已有文本改成江南腔（"帮我改成""润色成江南风"） | **B 改写** | 先跑 `scripts/audit_style.py` 体检，再读 `workflows/wf-rewrite.md`（v0.2 起可用，此前退化为 A 模式规则重写） |
| 接着上文继续写 | **C 续写** | A 模式流程 + 先对上文跑 `audit_style.py` 锁定指纹（人称、时态、称谓不许漂移） |
| 只要诊断不要改（"这段像不像江南""打个分"） | **D 诊断** | `scripts/audit_style.py` + `assets/rubric/style-scorecard.md`，只出报告 |
| 写龙族/九州等同人 | **E 同人（默认关闭）** | 先读 `references/guardrails/fanfic-policy.md`，前置合规提示，征得用户确认后才进入 A 模式流程 |

题材与体裁适配：每次写作前读 `references/adapters/genres/<题材>.md` 和 `adapters/forms/<体裁>.md` 各一份（v0.3 起提供；缺失时在报告中注明"该适配器未建，按 style 骨架直出"）。

## 八条铁律（任何模式都生效）

1. **情绪不直说。** 不写"他很难过"，写他做了什么小动作、看到了什么旧物、那天的天气如何。情绪是译文，原文必须是动作和物件。
2. **长铺陈之后一记冷拳。** 用两三个长句把画面推满，然后一个短句（≤10 字）单独成段收尾。此为最高频的节奏武器，但一段内至多用一次。
3. **对话推动叙事。** 能用对话带出的信息不用叙述带。对话允许答非所问、允许吐槽插科打诨，但每段对话必须至少推进一个信息点或一次关系变化。
4. **比喻取材于角色的生活半径。** 校园少年用食堂、试卷、球场；机甲世界用引擎、钢索、云层。禁止"岁月如歌""时光似水"这类无主通用比喻。
5. **镜头先于心理。** 先给可拍摄的画面（位置、光线、动作、物件），心理描写只在动作无法传达时出现，且单段不超过两句。
6. **高潮要克制。** 大事件用小反应写：世界末日那天，少年先想到的是晚饭。悲恸不喊出来，让它在细节里漏出来。
7. **配角有完整人生。** 配角出场自带来历、口头禅和私心，不许沦为推进剧情的NPC。师门/班级/团队是一个生态系统。
8. **守红线。** 产出中任何连续 15 字不得与江南已出版作品重合（交付前用 `scripts/overlap_check.py` 核查，本地语料在 `corpus/`）；不冒充原作者；同人需标注非商用。详见 `references/guardrails/`。

## 渐进式加载索引

| 要解决什么 | 读什么 |
|---|---|
| 节奏、断句、标点、口语、人称怎么定 | `references/style/02-voice.md` |
| 结构、视角、时间线、章节钩子怎么排 | `references/style/01-skeleton.md` |
| 意象怎么选、金句怎么造、幽默怎么分层 | `references/style/03~08`（v0.2 起提供） |
| "像不像"怎么判 | `references/style/09-dna.md` + `scripts/audit_style.py` |
| 新题材/新体裁怎么套 | `references/adapters/`（v0.3 起提供） |
| 合规边界 | `references/guardrails/`（copyright / originality / fanfic-policy） |

单次任务加载量控制在 8k–12k 字：`SKILL.md` 必读，`00-INDEX.md` 路由后读，其余按表按需。**禁止一次性读完整个 references/**。

## 工具

```bash
# 文本体检：9 项指标 + 阈值判定（默认只提示；--json 输出机器可读报告）
python scripts/audit_style.py <文本文件或目录> [--thresholds assets/schemas/thresholds.json] [--json] [--mode essay]

# 本地 EPUB 抽纯文本到 corpus/（永不入库）
python scripts/extract_epub.py "<epub路径>" -o corpus/source/

# 语料标定：算出 09-dna 阈值的目标区间（只输出统计值，不输出原文）
python scripts/audit_style.py corpus/source/ --calibrate -o assets/schemas/thresholds.json

# 查重：产出 vs 本地语料，最长公共片段 >=15 字即报警
python scripts/overlap_check.py <产出文件> --corpus corpus/source/
```

## 交付前自检（固化动作，不许跳）

1. `audit_style.py` 跑一遍，9 项指标与 `09-dna.md` 目标区间对照，超界项定点重写；
2. `overlap_check.py` 过一遍（有本地语料时），无 15 字以上重合；
3. 逐条核对八条铁律，在交付说明里用一行给出"铁律自检：1✓ 2✓ …"；
4. 若涉及同人，确认已带非商用标注。
