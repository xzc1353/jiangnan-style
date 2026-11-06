#!/usr/bin/env python3
"""
audit_style.py —— 江南文风量化审计

计算 references/style/09-dna.md 定义的 12 项指标，对照阈值给出判定。

用法:
    python audit_style.py <文件或目录> [--thresholds thresholds.json]
                          [--json] [--mode essay|fiction] [--calibrate] [-o OUT]

模式:
    默认        对目标文本算指标，对照阈值给 soft 判定（只提示不拦截）
    --calibrate 对 corpus 目录统计各指标 P10/P25/P50/P75/P90，
                生成 thresholds.json（只输出统计值，绝不输出原文）

依赖: 仅 Python 标准库。中文按字符计量，无分词依赖。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------- 语料工具

SENT_SPLIT = re.compile(r"[。！？!?…]+(?:[”』」）)]+)")  # 句末标点(可带右引号)
SIMILE_WORDS = ("像", "好像", "仿佛", "如同", "宛如", "好似", "恍若", "犹如")
QUOTE_CHARS = "“”\"「」『』"
DOMAIN_LEXICON = {
    "机械金属": "钢铁引擎齿轮机械枪炮刀剑甲弹舵缆",
    "光与火": "光火焰灯星阳月燃霞",
    "天气季节": "雨雪风雾雷电晴冬夏秋春云",
    "食物烟火": "饭面条茶酒糖肉汤食堂吃喝味",
    "宗教神话": "神佛祈祷祭十字天堂地狱龙咒",
    "身体": "血骨心脏眼手皮肤呼吸指节后颈",
}
WORD_RE = re.compile(r"[\u4e00-\u9fff]")


def is_han(ch: str) -> bool:
    return "\u4e00-\u9fff" <= ch <= "\u9fff" or "\u4e00" <= ch <= "\u9fff"


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8", "utf-16", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def split_paragraphs(text: str) -> list[str]:
    paras = []
    for block in re.split(r"\n\s*\n|\r\n\s*\r\n", text):
        block = block.strip()
        if block:
            paras.append(block)
    # 也兼容硬换行分段的纯文本：单换行且行较短时按段处理由调用方决定，这里保守用空行分段
    if len(paras) <= 1 and "\n" in text:
        paras = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return paras


def split_sentences(para: str) -> list[str]:
    sents = [s.strip() for s in SENT_SPLIT.split(para) if s.strip()]
    return sents


def count_han(s: str) -> int:
    return sum(1 for c in s if is_han(c))


# ---------------------------------------------------------------- 指标计算

def simile_domain(sentence: str, pos: int) -> str:
    window = sentence[max(0, pos - 12): pos + 14]
    for domain, keys in DOMAIN_LEXICON.items():
        if any(k in window for k in keys):
            return domain
    return "未归类"


def compute_metrics(text: str, mode: str = "fiction") -> dict:
    # 规范化：全角空白转半角、去掉 markdown 记号
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.M)
    text = re.sub(r"[*_`>#]+", "", text)

    paras = split_paragraphs(text)
    all_sents: list[str] = []
    sent_lens: list[int] = []
    for p in paras:
        for s in split_sentences(p):
            all_sents.append(s)
            sent_lens.append(count_han(s))

    total_han = count_han(text)
    n = total_han / 1000.0  # 每千字基数；短文本不稀释，宁可得出的密度偏大也不虚标
    if n <= 0:
        n = float("inf")

    # M1/M2
    avg_sent = sum(sent_lens) / len(sent_lens) if sent_lens else 0.0
    short_ratio = (sum(1 for l in sent_lens if 0 < l < 12) / len(sent_lens)) if sent_lens else 0.0

    # M3 单句成段
    single_sent_paras = 0
    for p in paras:
        if len(split_sentences(p)) == 1:
            single_sent_paras += 1
    m3 = single_sent_paras / len(paras) if paras else 0.0

    # M4/M5 对话行
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    dia_lines = [ln for ln in lines if any(q in ln for q in "“”\"「『")]
    m4 = len(dia_lines) / len(lines) if lines else 0.0
    dia_lens = [count_han(ln) for ln in dia_lines]
    m5 = sum(dia_lens) / len(dia_lens) if dia_lens else 0.0

    # M6/M7 比喻（最长匹配优先，遮蔽已命中片段，避免“好像”被拆成“好”+“像”重复计）
    simile_total = 0
    domain_counter: dict[str, int] = {}
    for s in all_sents:
        masked = list(s)
        for w in sorted(SIMILE_WORDS, key=len, reverse=True):
            start = 0
            while True:
                i = s.find(w, start)
                if i < 0:
                    break
                if all(c != "\x00" for c in masked[i:i + len(w)]):
                    for j in range(i, i + len(w)):
                        masked[j] = "\x00"
                    simile_total += 1
                    d = simile_domain(s, i)
                    domain_counter[d] = domain_counter.get(d, 0) + 1
                start = i + len(w)
    m6 = simile_total / n
    domain_dist = {k: (v / simile_total if simile_total else 0.0) for k, v in domain_counter.items()}

    # M8 人称指数
    c_wo = text.count("我")
    c_ta = text.count("他") + text.count("她") + text.count("它")
    m8 = (c_wo / c_ta) if c_ta else (99.0 if c_wo else 0.0)

    # M9 冷拳率
    cold_punch = 0
    prev_para: str | None = None
    for p in paras:
        sents_in = split_sentences(p)
        if (
            prev_para is not None
            and len(sents_in) == 1
            and count_han(p) <= 10
            and (len(split_sentences(prev_para)) >= 3 or count_han(prev_para) >= 40)
        ):
            cold_punch += 1
        prev_para = p
    m9 = cold_punch / len(paras) if paras else 0.0

    # M10 标点温度
    excl = text.count("！") + text.count("!")
    quest = text.count("？") + text.count("?")
    elli = text.count("……") + text.count("…")
    m10 = (excl + quest + elli) / n
    m10_excl = excl / n

    # M11 四字格（粗代理）
    four = re.findall(r"(?<![\u4e00-\u9fff])[\u4e00-\u9fff]{4}(?![\u4e00-\u9fff])", text)
    m11 = len(four) / n

    # M12 “的”密度
    m12 = text.count("的") / n

    return {
        "chars_han": total_han,
        "paragraphs": len(paras),
        "sentences": len(sent_lens),
        "M1_avg_sentence_len": round(avg_sent, 2),
        "M2_short_sentence_ratio": round(short_ratio, 4),
        "M3_single_sentence_para_ratio": round(m3, 4),
        "M4_dialogue_line_ratio": round(m4, 4),
        "M5_avg_dialogue_len": round(m5, 2),
        "M6_simile_per_kilo": round(m6, 2),
        "M7_simile_domain_dist": {k: round(v, 3) for k, v in sorted(domain_dist.items(), key=lambda x: -x[1])},
        "M8_first_person_index": round(m8, 3),
        "M9_cold_punch_rate": round(m9, 4),
        "M10_punct_per_kilo": round(m10, 2),
        "M10b_excl_per_kilo": round(m10_excl, 2),
        "M11_fourchar_per_kilo": round(m11, 2),
        "M12_de_per_kilo": round(m12, 2),
        "mode": mode,
    }


METRIC_KEYS = [
    "M1_avg_sentence_len", "M2_short_sentence_ratio", "M3_single_sentence_para_ratio",
    "M4_dialogue_line_ratio", "M5_avg_dialogue_len", "M6_simile_per_kilo",
    "M8_first_person_index", "M9_cold_punch_rate", "M10_punct_per_kilo",
    "M10b_excl_per_kilo", "M11_fourchar_per_kilo", "M12_de_per_kilo",
]


# ---------------------------------------------------------------- 阈值与判定

def load_thresholds(path: Path | None) -> dict:
    if path and path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("_status") == "uncalibrated":
            return {"_status": "uncalibrated"}
        return data
    return {"_status": "uncalibrated"}


def judge(metrics: dict, thresholds: dict, mode: str) -> dict:
    if thresholds.get("_status") == "uncalibrated":
        return {"status": "uncalibrated",
                "hint": "阈值未标定。先对本地语料运行 --calibrate 生成 thresholds.json，再重新审计。"}
    mode_th = thresholds.get(mode) or thresholds.get("fiction") or {}
    verdict = {}
    for key in METRIC_KEYS:
        band = mode_th.get(key) or {}
        v = metrics.get(key)
        if v is None or not band:
            continue
        target = band.get("target")  # [lo, hi]
        tolerate = band.get("tolerate")  # [lo, hi]
        lo_t, hi_t = target if target else (None, None)
        lo_x, hi_x = tolerate if tolerate else (None, None)
        if lo_x is not None and v < lo_x or hi_x is not None and v > hi_x:
            level = "OUT_OF_TOLERANCE"
        elif lo_t is not None and v < lo_t or hi_t is not None and v > hi_t:
            level = "OUT_OF_TARGET"
        else:
            level = "OK"
        verdict[key] = {"value": v, "level": level, "target": target, "tolerate": tolerate}
    return {"status": "ok", "verdict": verdict,
            "summary": _summarize(verdict)}


def _summarize(verdict: dict) -> str:
    bad = [k for k, v in verdict.items() if v["level"] == "OUT_OF_TOLERANCE"]
    warn = [k for k, v in verdict.items() if v["level"] == "OUT_OF_TARGET"]
    if bad:
        return f"偏离容忍区间 {len(bad)} 项（{', '.join(bad)}），建议定点重写。"
    if warn:
        return f"偏离目标区间 {len(warn)} 项（{', '.join(warn)}），可改可不改。"
    return "全部指标落在目标区间内。"


# ---------------------------------------------------------------- 校准

def calibrate(files: list[Path], mode: str) -> dict:
    buckets: dict[str, list[float]] = {k: [] for k in METRIC_KEYS}
    for f in files:
        try:
            m = compute_metrics(read_text(f), mode)
        except Exception as e:  # 坏文件跳过，不打断
            print(f"[skip] {f}: {e}", file=sys.stderr)
            continue
        if m["chars_han"] < 2000:  # 太短的样本不参与标定
            continue
        for k in METRIC_KEYS:
            buckets[k].append(m[k])

    def band(vals: list[float], lo_q: float, hi_q: float) -> list[float] | None:
        if len(vals) < 5:
            return None
        vals = sorted(vals)

        def q(p):
            i = (len(vals) - 1) * p
            lo, hi = int(i), min(int(i) + 1, len(vals) - 1)
            return vals[lo] + (vals[hi] - vals[lo]) * (i - lo)

        return [round(q(lo_q), 4), round(q(hi_q), 4)]

    th: dict = {"_status": "calibrated", "_n_files": len(buckets and files), mode: {}}
    for k, vals in buckets.items():
        target = band(vals, 0.25, 0.75)
        tolerate = band(vals, 0.10, 0.90)
        if target:
            th[mode][k] = {"target": target, "tolerate": tolerate}
    return th


# ---------------------------------------------------------------- CLI

def main() -> int:
    ap = argparse.ArgumentParser(description="江南文风量化审计")
    ap.add_argument("target", help="文本文件或目录")
    ap.add_argument("--thresholds", type=Path, default=Path(__file__).parent.parent / "assets/schemas/thresholds.json")
    ap.add_argument("--json", action="store_true", help="输出 JSON 报告")
    ap.add_argument("--mode", choices=["fiction", "essay"], default="fiction")
    ap.add_argument("--calibrate", action="store_true", help="对语料目录标定阈值")
    ap.add_argument("-o", "--output", type=Path, help="校准结果/报告写出路径")
    args = ap.parse_args()

    target = Path(args.target)
    if args.calibrate:
        files = [p for p in (target.rglob("*.txt") if target.is_dir() else [target])]
        th = calibrate(files, args.mode)
        out = json.dumps(th, ensure_ascii=False, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(out, encoding="utf-8")
            print(f"阈值已写出: {args.output}")
        else:
            print(out)
        return 0

    files = sorted(target.rglob("*.txt")) + sorted(target.rglob("*.md")) if target.is_dir() else [target]
    reports = []
    for f in files:
        if f.name.startswith(".") or f.name == "README.md" and f.parent.name == "corpus":
            continue
        m = compute_metrics(read_text(f), args.mode)
        j = judge(m, load_thresholds(args.thresholds), args.mode)
        reports.append({"file": str(f), "metrics": m, "judgement": j})

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
    else:
        for r in reports:
            m = r["metrics"]
            print("=" * 62)
            print(f"{r['file']}  (汉字 {m['chars_han']} / 段 {m['paragraphs']} / 句 {m['sentences']})")
            for k in METRIC_KEYS:
                print(f"  {k:34s} {m[k]}")
            print(f"  M7 比喻取材域: {m['M7_simile_domain_dist']}")
            print(f"  判定: {r['judgement'].get('summary', r['judgement'].get('hint'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
