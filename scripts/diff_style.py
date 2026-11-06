#!/usr/bin/env python3
"""diff_style.py —— 改写前后维度级对照报告（不是文本 diff）

用法：
    python scripts/diff_style.py <原文> <产出> [--mode fiction] [--json] [--strict]

它回答三个问题：
  1. 哪些风格维度真的变了，变了多少（12 项指标逐项对照）
  2. 这一改属于哪一级手术（据字数与维度位移反推 L1/L2/L3）
  3. 有没有动到不该动的东西（数字串、引号内台词）→ 保意红线

设计原则：只做确定性计算，不做语义判断。凡需语义判断的项一律标"需人工确认"，
不假装能自动判定。纯标准库，无第三方依赖。
"""

from __future__ import annotations

import argparse
import unicodedata
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_style import METRIC_KEYS, compute_metrics, load_thresholds, read_text  # noqa: E402

# 指标的"好"方向：用于判断位移是变强还是变弱，而非变好变坏
DIRECTION_HINT = {
    "M1_avg_sentence_len": "句长",
    "M2_short_sentence_ratio": "短句密度",
    "M3_single_sentence_para_ratio": "单句成段",
    "M4_dialogue_line_ratio": "对话行占比",
    "M5_avg_dialogue_len": "对话回合长度",
    "M6_simile_per_kilo": "比喻密度",
    "M8_first_person_index": "第一人称",
    "M9_cold_punch_rate": "冷拳率",
    "M10_punct_per_kilo": "标点密度",
    "M10b_excl_per_kilo": "感叹号密度",
    "M11_fourchar_per_kilo": "四字格密度",
    "M12_de_per_kilo": "「的」字密度",
}

# 变化幅度达到多少算"显著位移"（相对值或绝对值取大者）
SIGNIFICANT = 0.15

ARABIC_NUM = re.compile(r"\d+(?:\.\d+)?%?")
QUOTED = re.compile(r"[“「『]([^”」』]{2,})[”」』]")


def numbers_of(text: str) -> set[str]:
    """抽取阿拉伯数字串。中文数字（三天/两百）无法确定性识别，不做处理，
    在报告里显式声明这是已知盲区，避免给出虚假的"事实未变"结论。"""
    return set(ARABIC_NUM.findall(text.replace("０", "0").replace("１", "1")
                                   .replace("２", "2").replace("３", "3")
                                   .replace("４", "4").replace("５", "5")
                                   .replace("６", "6").replace("７", "7")
                                   .replace("８", "8").replace("９", "9")))


def quotes_of(text: str) -> list[str]:
    return [q.strip() for q in QUOTED.findall(text) if q.strip()]


def infer_level(o_han: int, d_han: int, moved: list[str]) -> dict:
    """据字数位移幅度与显著位移维度数反推手术级别。
    这是启发式，不是判决——报告里给的是"最可能属于"，供人工复核。"""
    ratio = abs(d_han - o_han) / max(1, o_han)
    if ratio < 0.10 and len(moved) <= 2:
        level, why = "L1", "字数位移 <10% 且显著位移维 ≤2，接近句级微调"
    elif ratio < 0.35 or len(moved) <= 5:
        level, why = "L2", "字数位移 10–35% 或显著位移维 ≤5，接近段级重铸"
    else:
        level, why = "L3", "字数位移 >35% 或显著位移维 >5，已接近全篇重写"
    return {"level": level, "char_shift_ratio": round(ratio, 4), "reason": why}


def compare(orig_text: str, out_text: str, mode: str, thresholds: dict) -> dict:
    mo = compute_metrics(orig_text, mode)
    mn = compute_metrics(out_text, mode)

    rows = []
    moved = []
    for k in METRIC_KEYS:
        a, b = mo.get(k, 0.0), mn.get(k, 0.0)
        delta = round(b - a, 4)
        if a == 0:
            # 改前为 0 时相对变化无意义（除法会炸成天文数字），只报绝对位移
            delta_pct = None
            significant = abs(delta) >= 0.5
        else:
            delta_pct = round(abs(delta) / a * 100, 1)
            significant = delta_pct >= SIGNIFICANT * 100 and abs(delta) > 0.01
        if significant:
            moved.append(k)
        rows.append({
            "metric": k,
            "label": DIRECTION_HINT.get(k, k),
            "before": round(a, 2),
            "after": round(b, 2),
            "delta": delta,
            "delta_pct": delta_pct,
            "significant": significant,
        })

    # 保意粗检
    no, nn = numbers_of(orig_text), numbers_of(out_text)
    qo, qn = quotes_of(orig_text), quotes_of(out_text)
    qn_join = "".join(qn)
    lost_quotes = [q for q in qo if q not in qn_join]
    dropped_numbers = sorted(no - nn)
    added_numbers = sorted(nn - no)
    fact_alerts = [f"数字消失：{x}" for x in dropped_numbers] + \
                  [f"新增数字：{x}" for x in added_numbers]

    level = infer_level(mo["chars_han"], mn["chars_han"], moved)

    return {
        "mode": mode,
        "before": {"chars_han": mo["chars_han"], "paragraphs": mo["paragraphs"],
                   "sentences": mo["sentences"]},
        "after": {"chars_han": mn["chars_han"], "paragraphs": mn["paragraphs"],
                  "sentences": mn["sentences"]},
        "metrics": rows,
        "significant_moved": moved,
        "inferred_level": level,
        "preserve_check": {
            "numbers_before": sorted(no),
            "numbers_after": sorted(nn),
            "fact_alerts": fact_alerts,
            "quotes_before": len(qo),
            "quotes_after": len(qn),
            "quotes_missing": lost_quotes[:10],
            "note": "中文数字（三天/两百/十年）与专名变更本脚本无法确定性识别，需人工确认。",
        },
        "thresholds_loaded": thresholds.get("_status") != "uncalibrated",
    }


def dw_pad(s: str, width: int, align: str = "left") -> str:
    """按终端显示宽度补空格（CJK 占 2 列）。str.ljust 会把「短句密度」当 4 字符，
    导致表头与数据整体错位。"""
    w = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)
    pad = max(0, width - w)
    return s + " " * pad if align == "left" else " " * pad + s


def render(rep: dict) -> str:
    b, a = rep["before"], rep["after"]
    out = []
    out.append("=" * 72)
    out.append("改写前后维度对照报告（diff_style）")
    out.append("=" * 72)
    out.append(f"字数：{b['chars_han']} → {a['chars_han']}"
               f"（{a['chars_han'] - b['chars_han']:+d}）"
               f"   段落：{b['paragraphs']} → {a['paragraphs']}"
               f"   句数：{b['sentences']} → {a['sentences']}")
    out.append("")
    out.append(dw_pad("维度", 18) + dw_pad("改前", 10, "right") + dw_pad("改后", 10, "right")
               + dw_pad("变化", 10, "right") + dw_pad("幅度", 10, "right"))
    out.append("-" * 72)
    for r in rep["metrics"]:
        mark = " ●" if r["significant"] else ""
        pct = "—" if r["delta_pct"] is None else f"{r['delta_pct']:.1f}%"
        out.append(dw_pad(r["label"], 18)
                   + f"{r['before']:>10.2f}{r['after']:>10.2f}{r['delta']:>+10.2f}"
                   + dw_pad(pct, 10, "right") + mark)
    out.append("  （● 显著位移；幅度「—」表示改前为 0，相对幅度无意义，只看绝对位移）")
    out.append("")

    lv = rep["inferred_level"]
    out.append(f"【反推手术级别】{lv['level']} —— {lv['reason']}")
    out.append(f"（字数位移 {lv['char_shift_ratio'] * 100:.1f}%，显著位移维 {len(rep['significant_moved'])} 项）")
    out.append("")

    pc = rep["preserve_check"]
    out.append("【保意核查】")
    if pc["fact_alerts"]:
        for msg in pc["fact_alerts"]:
            out.append(f"  ✗ {msg}")
    else:
        out.append("  ✓ 阿拉伯数字串完全一致")
    if pc["quotes_missing"]:
        out.append(f"  ✗ {len(pc['quotes_missing'])} 条台词在改后文本中找不到：")
        for q in pc["quotes_missing"][:5]:
            out.append(f"      「{q[:30]}」")
    else:
        out.append(f"  ✓ {pc['quotes_before']} 条引号台词全部保留" if pc['quotes_before'] else "  － 原文无引号台词")
    out.append(f"  ! {pc['note']}")
    out.append("")
    ok = not pc["fact_alerts"] and not pc["quotes_missing"]
    out.append("结论：" + ("✅ 未发现事实性变更（仍需人工确认语义）"
                          if ok else "❌ 存在事实性变更，需回退该处"))
    out.append("=" * 72)
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="改写前后维度级对照")
    ap.add_argument("original", type=Path, help="原文文件")
    ap.add_argument("revised", type=Path, help="改写后文件")
    ap.add_argument("--mode", default="fiction", choices=["fiction", "essay"])
    ap.add_argument("--thresholds", type=Path, default=None)
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--strict", action="store_true", help="发现事实性变更时以非零码退出")
    args = ap.parse_args()

    for p in (args.original, args.revised):
        if not p.exists():
            print(f"[error] 文件不存在: {p}", file=sys.stderr)
            return 2

    th = load_thresholds(args.thresholds) if args.thresholds else {"_status": "uncalibrated"}
    rep = compare(read_text(args.original), read_text(args.revised), args.mode, th)

    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(render(rep))

    if args.strict:
        pc = rep["preserve_check"]
        if pc["fact_alerts"] or pc["quotes_missing"]:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
