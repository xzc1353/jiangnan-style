# ROADMAP

## 已完成

- **v0.1.0**（2026-11-06）：架构底座 + 生成链（SKILL.md / style 01,02,09 / wf-generate / audit_style.py）
- **v0.2.0**（2026-11-06）：自动化标定 + 规则提取（auto_analyze.py / style 03-08 / 阈值正式标定 / 场景切片）
- **v0.3.0**（2026-11-06）：改写链 + 适配层 + 守卫（rewrite 四件套 / wf-rewrite / overlap_check.py / CI / adapters 5×5 / 模板 / guardrails）

## 待办

### v0.4 · 盲测与调优
- [ ] 用 `assets/rubric/style-scorecard.md` 组织 3 人以上盲测（自撰样本混真作干扰项）
- [ ] 盲测误判率 ≥80% 为 v1.0 门槛；未达标则回头修 style 规则
- [ ] 生成一篇 5000 字完整短篇走全流程，记录失败模式

### v0.5 · 实用性增强
- [ ] `scripts/add_reference.py` 脚手架（新题材适配器自动登记）
- [ ] `diff_style.py`（改写前后维度对照 JSON + 人读摘要）
- [ ] essay 模式阈值单独标定（现与 fiction 共用）

### v1.0 · 发布
- [ ] README 补安装动图与示例输出
- [ ] GitHub 建仓推送（需 credential-manager 授权）
- [ ] 首个公开版本号 1.0.0，附完整合规声明

## 长期方向（不承诺时间）

- 反馈闭环：用户报告"不像"的案例 → 反向修正 style 规则
- 多作者扩展：骨架（style/01）与皮肤（02+）分离的架构天然支持"换皮肤"——新增作者只需新增皮肤文件集
