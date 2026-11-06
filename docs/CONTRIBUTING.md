# CONTRIBUTING

## 铁律（违反 = PR 直接关闭）

1. **禁止提交任何原作文本**：`corpus/` 全目录 gitignore；PR 中出现电子书内容、原文摘录、批量原文段落即拒。
2. **示例必须自撰**：`examples/`、模板、正文中出现的示范文字一律自己写，不引用原作。
3. **规则必须标注依据**：修改 `references/style/` 的规则时，注明依据（语料实测数值 / 盲测结果 / 明确的推理），拒绝"我觉得"。

## 流程

1. Fork → 分支（`feat/xxx` 或 `fix/xxx`）→ 改动 → 本地测试全绿：
   ```bash
   python -m unittest discover -s tests -v
   python scripts/audit_style.py examples/golden/   # 若改了阈值或指标
   ```
2. 提交信息遵循现有格式（`vX.Y.Z:` 或 `模块名: 动作`）。
3. PR 描述包含：改了什么 / 为什么 / 对 12 项指标的影响（若涉及）。

## 改动分层规范

| 层 | 谁 | 约束 |
|---|---|---|
| `scripts/` | 代码改动必须配测试 | 纯标准库；Windows 兼容（路径、编码） |
| `references/style/` | 每个文件 ≤1500 字 | 有"数据依据"节；负向清单只增不删除非实证推翻 |
| `references/adapters/` | 不许覆盖 style 规则 | 只做权重调整与物料清单 |
| `assets/schemas/thresholds.json` | 仅由 `--calibrate` 生成 | 不许手改数值 |

## 语料纪律

本地语料（`corpus/`）的获取方式由贡献者自行负责且自行承担合规责任；本项目不分发、不链接、不指路盗版资源。
