# ROADMAP

## 已完成

- **v0.1.0**（2026-11-06）：架构底座 + 生成链（SKILL.md / style 01,02,09 / wf-generate / audit_style.py）
- **v0.2.0**（2026-11-06）：自动化标定 + 规则提取（auto_analyze.py / style 03-08 / 阈值正式标定 / 场景切片）
- **v0.3.0**（2026-11-06）：改写链 + 适配层 + 守卫（rewrite 四件套 / wf-rewrite / overlap_check.py / CI / adapters 5×5 / 模板 / guardrails）
- **v1.0.0**（2026-11-06）：七模式全通（补 wf-continue / critique / polish / outline / fanfic）+ diff_style.py + add_reference.py + 自撰 golden 样本与反面教材 + 27 个单测；公开仓库上线，CI 全绿

## 待办

### v1.1 · 盲测与调优（下一个里程碑）

- [ ] 用 `assets/rubric/style-scorecard.md` 组织 3 人以上盲测（自撰样本混入非江南的中文小说片段做干扰项）
- [ ] 盲测"无法分辨"率 ≥80% 为达标线；未达标则按评分卡失分维度回头修 style 规则
- [ ] 生成一篇 5000 字完整短篇走全流程（含 diff_style 与 overlap_check），把失败模式写进 `examples/anti-examples/`
- [ ] 补 `examples/golden/` 第二、三篇：不同题材各一（现只有都市/生活向一篇）

### v1.2 · 实用性增强

- [ ] essay 模式阈值单独标定（当前与 fiction 共用一套）
- [ ] `audit_style.py` 增加 `--per-section`：长文分段体检，指出"哪一段不像"而非只给全文均值
- [ ] `diff_style.py` 增加语义级保意提示（现只查数字与引号台词，中文数字/专名是已知盲区）
- [ ] 网页版试用页（粘贴文本 → 体检报告），可选

### 已知限制（诚实清单）

- 单篇 <1500 字的文本不适合逐项对阈值：M9 冷拳率、M2 短句占比会因篇幅产生噪声（见 `examples/golden/样本01-评注.md`）
- `overlap_check.py` 需要本地语料才可用；仓库不含语料（合规约束），使用者需自备
- 中文数字（三天/两百）与专名变更无法被 `diff_style.py` 确定性识别，必须人工确认
- 情感与幽默的"分寸"无法量化，只能靠 `assets/rubric/` 人工评分

## 长期方向（不承诺时间）

- 反馈闭环：用户报告"不像"的案例 → 反向修正 style 规则
- 多作者扩展：骨架（style/01）与皮肤（02+）分离的架构天然支持"换皮肤"——新增作者只需新增皮肤文件集
