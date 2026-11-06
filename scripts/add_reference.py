#!/usr/bin/env python3
"""add_reference.py —— 新增题材/体裁适配器的脚手架

用法：
    python scripts/add_reference.py genre wuxia --title "武侠 / 江湖" --when "写刀剑江湖、门派恩怨时"
    python scripts/add_reference.py form flash --title "微小说（<1000字）" --when "写超短篇时"

做三件事：
  1. 在 references/adapters/{genres|forms}/ 下生成一个骨架文件（不覆盖已存在文件，除非 --force）
  2. 往 references/00-INDEX.md 的 adapters 表格里登记一行（幂等，重复运行不会重复登记）
  3. 打印下一步该填什么

设计意图：适配器是这套架构里唯一需要高频新增的东西（新题材/新体裁）。把它做成
一条命令，避免"加了文件忘了登记索引"——那样文件等于不存在，因为 SKILL.md 只按索引找。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "references" / "00-INDEX.md"

KIND_DIR = {"genre": "genres", "form": "forms"}
KIND_CN = {"genre": "题材", "form": "体裁"}

TEMPLATE = """# {kind_cn}适配器 · {title}

> 配合 `style/01-09` 使用。本文件只回答：{question}**不得覆盖 style 规则。**

## 世界物料清单

- **空间**：
- **物件**：
- **事件**：

## 权重调整

| style 规则 | 调整 |
|---|---|
| 意象域（03） |  |
| 幽默（07） |  |
| 战斗 / 高潮（08） |  |
| 对话（05） |  |

## 独有规则

1.
2.

## 禁区

-
"""

QUESTION = {
    "genre": "这个世界里能出现什么、哪些 style 规则在此题材下的权重变化。",
    "form": "这个长度下节奏怎么排、信息释放密度如何调整。",
}


def register(slug: str, kind: str, title: str, when: str) -> tuple[bool, str]:
    """在 00-INDEX.md 的 adapters 表格末尾追加一行。已登记则返回 False。"""
    text = INDEX.read_text(encoding="utf-8")
    row = f"| `adapters/{KIND_DIR[kind]}/{slug}.md` | {title} | {when} |"
    if f"{slug}.md" in text:
        return False, "已在索引中登记，跳过"

    lines = text.splitlines()
    # 定位 "## adapters/" 段内的表格的最后一行
    try:
        start = next(i for i, ln in enumerate(lines) if ln.startswith("## adapters/"))
    except StopIteration:
        return False, "未找到 `## adapters/` 段，索引结构可能被改动，请手工登记"

    last_row = -1
    for i in range(start, len(lines)):
        if lines[i].startswith("## ") and i != start:
            break
        if lines[i].strip().startswith("|"):
            last_row = i
    if last_row < 0:
        return False, "adapters 段内没有表格，请手工登记"

    lines.insert(last_row + 1, row)
    INDEX.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True, f"已登记到 {INDEX.relative_to(ROOT)}"


def main() -> int:
    ap = argparse.ArgumentParser(description="新增题材/体裁适配器并登记索引")
    ap.add_argument("kind", choices=["genre", "form"], help="genre=题材，form=体裁")
    ap.add_argument("slug", help="英文短名，用作文件名（小写、连字符）")
    ap.add_argument("--title", required=True, help="中文标题，如「武侠 / 江湖」")
    ap.add_argument("--when", default="写作时按需读", help="何时该读这个适配器")
    ap.add_argument("--force", action="store_true", help="覆盖已存在的文件")
    args = ap.parse_args()

    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,30}", args.slug):
        print("[error] slug 只能用小写字母/数字/连字符，2-31 字符", file=sys.stderr)
        return 2

    target_dir = ROOT / "references" / "adapters" / KIND_DIR[args.kind]
    target = target_dir / f"{args.slug}.md"

    if target.exists() and not args.force:
        print(f"[skip] 已存在：{target.relative_to(ROOT)}（要覆盖加 --force）")
    else:
        target_dir.mkdir(parents=True, exist_ok=True)
        target.write_text(TEMPLATE.format(
            kind_cn=KIND_CN[args.kind], title=args.title,
            question=QUESTION[args.kind],
        ), encoding="utf-8")
        print(f"[ok] 已创建：{target.relative_to(ROOT)}")

    added, msg = register(args.slug, args.kind, args.title, args.when)
    print(("[ok] " if added else "[skip] ") + msg)

    print("\n下一步：")
    print(f"  1. 打开 {target.relative_to(ROOT)}，把四节填实（物料清单 / 权重调整 / 独有规则 / 禁区）")
    print("  2. 权重调整必须引用 style/ 的具体编号，不许写「适当调整」这种空话")
    print("  3. 提交时在 PR 描述里说明：这个适配器相对 campus.md 多解决了什么问题")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
