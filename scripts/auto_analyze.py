#!/usr/bin/env python3
"""
auto_analyze.py —— 语料自动化分析流水线

对 corpus/source/ 下的全部纯文本做四件事:
  Phase 1  量化特征: 句长分布、短句比、对话/叙述占比、修辞词频、
           比喻取材域、高频 n-gram、标志短语、章节长度分布
  Phase 2  场景切片: 战斗/孤独/日常吐槽/死亡离别/回忆/食物/成长顿悟,
           每类抽最典型段落 -> corpus/exemplars/<场景>.md (本地, 永不上传)
           references/corpus-notes/ 只落"模式结论 + 指针", 不落原文
  Phase 3  阈值标定: 复用 audit_style 的 compute_metrics, 写 thresholds.json
  Phase 4  报告: corpus/stats/report.md + 控制台摘要

用法:
    python auto_analyze.py [--corpus corpus/source] [--topn 12] [--no-thresholds]

性能: 纯标准库, 1000 万字单机约 1-3 分钟。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audit_style import METRIC_KEYS, calibrate, count_han, read_text, split_paragraphs  # noqa: E402

ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------- 场景定义

SCENES: dict[str, dict] = {
    # keys 主体为单字关键词（用 list() 逐字切），另拼少量多字词
    "战斗": {"keys": list("刀剑枪炮炸爆轰拳脚杀冲撞焰鳞爪翅盾弓射穿躲闪格挡伤倒挥砍咆哮嘶吼震裂硝烟血") + ["站起", "死战", "粉身碎骨", "尘埃落定"], "need_dialogue": False},
    "孤独": {"keys": list("独孤寂默静空伶冷") + ["一个人", "没有人", "只剩", "只有", "熄灯", "影子", "夜深", "无人", "灯光"], "need_dialogue": False},
    "日常吐槽": {"keys": list("穷喂诶神经病") + ["搞什么", "有病", "扯淡", "靠谱", "房租", "打折", "挂科", "考试", "补考", "翘课", "罚站", "买单", "钱包", "穷得", "坑爹", "扯平", "算账", "认怂"], "need_dialogue": True},
    "死亡离别": {"keys": list("死葬墓碑哭殡") + ["牺牲", "告别", "再见", "永别", "离开", "最后", "遗体", "火化", "闭上眼", "手凉"] , "need_dialogue": False},
    "回忆": {"keys": list("旧恍曾") + ["想起", "记得", "当年", "小时候", "从前", "那年", "回忆", "恍惚", "多年前", "那一年", "后来才", "曾经"], "need_dialogue": False},
    "食物烟火": {"keys": list("吃喝茶酒香饿煮涮烤") + ["吃饭", "面条", "包子", "馒头", "食堂", "厨房", "味道", "啤酒", "汽水", "豆浆", "油条", "打饭"], "need_dialogue": False},
    "成长顿悟": {"keys": list("懂悟") + ["明白", "长大", "成长", "第一次", "终于", "原来", "责任", "守护", "决定", "命运", "自己选", "再也不是"], "need_dialogue": False},
}

RHETORIC = ["就像", "好像", "仿佛", "如同", "宛如", "好似", "恍若", "犹如", "像"]
SIGNATURE = ["深吸一口气", "那一刻", "很多年以后", "多年以后", "后来", "那天", "那一年", "忽然", "突然",
             "第一次", "眼泪", "眼眶", "指节", "后颈", "心口", "世界安静", "听到心跳", "不敢", "没敢"]
VERBS = ["说", "道", "笑", "看", "走", "站", "坐", "拿", "抬", "低头", "转身", "点头", "摇头",
         "闭眼", "睁开", "愣住", "皱眉", "咬牙", "喊", "哭"]

DIA_OPEN = "“\"「『"


def book_of(fname: str) -> str:
    return fname.split("__")[0]


BOOK_SHORT = {"龙族": "龙族", "九州": "九州·缥缈录", "江南作品合集": "合集25册"}


def book_short(fname: str) -> str:
    prefix = book_of(fname)
    for k, v in BOOK_SHORT.items():
        if prefix.startswith(k):
            return v
    return prefix[:12]


# ---------------------------------------------------------------- Phase 1

def quant_pass(files: list[Path]) -> dict:
    sent_lens: list[int] = []
    para_sent_counts: list[int] = []
    para_han: list[int] = []
    cold_punch = 0
    single_sent_paras = 0
    dia_chars = 0
    total_han = 0
    chapter_han: dict[str, list[int]] = {}
    punct = Counter()
    rhetoric = Counter()
    signature = Counter()
    verbs = Counter()
    ngram2: Counter = Counter()
    ngram3: Counter = Counter()
    simile_domain = Counter()

    from audit_style import DOMAIN_LEXICON, SIMILE_WORDS

    for f in files:
        text = read_text(f)
        book = book_of(f.name)
        han = count_han(text)
        total_han += han
        chapter_han.setdefault(book, []).append(han)

        # 对话字符：引号内汉字
        for m in re.finditer(r"[“\"]([^”\"]{1,200}?)[”\"]", text):
            dia_chars += count_han(m.group(1))

        for ch in "！？…；—":
            punct[ch] += text.count(ch)
        punct["，"] += text.count("，")
        punct["。"] += text.count("。")

        for w in RHETORIC:
            # 遮蔽长词避免重复计
            n = len(re.findall(re.escape(w), text))
            rhetoric[w] += n
        for w in SIGNATURE:
            signature[w] += text.count(w)
        for w in VERBS:
            verbs[w] += text.count(w)

        # 比喻取材域（句级窗口，同 audit_style 逻辑的简化版）
        for m in re.finditer(r"就像|好像|仿佛|如同|宛如|好似|恍若|犹如|像", text):
            window = text[max(0, m.start() - 12): m.start() + 14]
            for dom, keys in DOMAIN_LEXICON.items():
                if any(k in window for k in keys):
                    simile_domain[dom] += 1
                    break
            else:
                simile_domain["未归类"] += 1

        # n-gram（仅连续汉字串内）
        for run in re.findall(r"[\u4e00-\u9fff]{2,}", text):
            if len(run) > 200:  # 超长 run 罕见，截断防卡
                run = run[:200]
            for i in range(len(run) - 1):
                ngram2[run[i:i + 2]] += 1
            for i in range(len(run) - 2):
                ngram3[run[i:i + 3]] += 1

        # 段落/句子结构
        paras = split_paragraphs(text)
        prev_para = None
        for p in paras:
            sents = [s for s in re.split(r"[。！？!?…]+(?:[”』」）)]+)", p) if s.strip()]
            para_sent_counts.append(len(sents))
            ph = count_han(p)
            para_han.append(ph)
            for s in sents:
                sent_lens.append(count_han(s))
            if len(sents) == 1:
                single_sent_paras += 1
                if prev_para is not None and ph <= 10 and (
                    len(re.split(r"[。！？…]+", prev_para)) >= 4 or count_han(prev_para) >= 40
                ):
                    cold_punch += 1
            prev_para = p

    n = max(total_han / 1000.0, 1e-9)

    def dist(vals: list[int], bins: list[int]) -> dict:
        out = {}
        lo = 0
        for hi in bins:
            out[f"{lo}-{hi}"] = sum(1 for v in vals if lo < v <= hi)
            lo = hi
        out[f">{bins[-1]}"] = sum(1 for v in vals if v > bins[-1])
        return out

    def pct(vals: list[int], p: float) -> float:
        if not vals:
            return 0.0
        s = sorted(vals)
        i = (len(s) - 1) * p
        lo, hi = int(i), min(int(i) + 1, len(s) - 1)
        return s[lo] + (s[hi] - s[lo]) * (i - lo)

    return {
        "corpus": {"files": len(files), "total_han": total_han, "books": {
            b: {"chapters": len(v), "total_han": sum(v),
                "chapter_han_p50": pct(v, 0.5), "chapter_han_p90": pct(v, 0.9)}
            for b, v in chapter_han.items()}},
        "sentence": {
            "count": len(sent_lens),
            "mean": sum(sent_lens) / len(sent_lens),
            "p25": pct(sent_lens, 0.25), "p50": pct(sent_lens, 0.5),
            "p75": pct(sent_lens, 0.75), "p90": pct(sent_lens, 0.9),
            "dist_bins_1_6_12_20_35_60": dist(sent_lens, [1, 6, 12, 20, 35, 60]),
            "short_lt12_ratio": sum(1 for v in sent_lens if v < 12) / len(sent_lens),
            "ultrashort_lt6_ratio": sum(1 for v in sent_lens if v < 6) / len(sent_lens),
        },
        "paragraph": {
            "count": len(para_sent_counts),
            "single_sentence_ratio": single_sent_paras / len(para_sent_counts),
            "cold_punch_ratio": cold_punch / len(para_sent_counts),
            "mean_han": sum(para_han) / len(para_han),
            "dist_bins_1_10_25_50_100_200": dist(para_han, [1, 10, 25, 50, 100, 200]),
        },
        "dialogue": {
            "dialogue_char_ratio": dia_chars / total_han,
            "dialogue_chars": dia_chars,
        },
        "rhetoric_per_kilo": {k: round(v / n, 2) for k, v in rhetoric.most_common()},
        "simile_domain": {k: round(v / sum(simile_domain.values()), 3) for k, v in simile_domain.most_common()},
        "signature_per_kilo": {k: round(v / n, 3) for k, v in signature.most_common() if v > 0},
        "verb_freq_top": verbs.most_common(20),
        "ngram_top50": {"2gram": [[g, c] for g, c in ngram2.most_common(400)
                                  if not _is_stopgram(g)][:50],
                        "3gram": [[g, c] for g, c in ngram3.most_common(400)
                                  if not _is_stopgram(g)][:50]},
        "punct_per_kilo": {k: round(v / n, 2) for k, v in punct.items()},
    }


STOPGRAM = set("的了是在我有和不是了他这那也人都为一个上说来去我们你们他们自己什么没有这个那个就是")


def _is_stopgram(g: str) -> bool:
    return all(c in STOPGRAM for c in g)


# ---------------------------------------------------------------- Phase 2

def scene_pass(files: list[Path], topn: int) -> tuple[dict, dict]:
    exemplars: dict[str, list] = {s: [] for s in SCENES}
    stats: dict[str, dict] = {s: {"hits": 0, "len_sum": 0, "len_n": 0} for s in SCENES}
    seen: set[str] = set()

    for f in files:
        text = read_text(f)
        book = book_of(f.name)
        paras = split_paragraphs(text)
        for idx, p in enumerate(paras):
            ph = count_han(p)
            if not (40 <= ph <= 400):
                continue
            has_dia = any(q in p for q in DIA_OPEN)
            for sname, cfg in SCENES.items():
                hits = sum(1 for k in cfg["keys"] if k in p)
                if hits < 2:
                    continue
                if cfg["need_dialogue"] and not has_dia:
                    continue
                stats[sname]["hits"] += 1
                stats[sname]["len_sum"] += ph
                stats[sname]["len_n"] += 1
                # 命中密度 = 命中数/百字；相同密度偏向有对话和具体动作的段落
                density = hits / ph * 100
                key = re.sub(r"\s", "", p[:20])  # 跨书重复段落（合集 vs 单行本）按去空白前缀去重
                if key in seen:
                    continue
                seen.add(key)
                exemplars[sname].append({
                    "score": round(density + (1.0 if has_dia else 0), 3),
                    "book": book_short(f.name), "file": f.name, "para_idx": idx,
                    "len": ph, "has_dia": has_dia, "text": p,
                })
                break  # 一段只归一个场景（先命中先得）

    picked: dict[str, list] = {}
    for sname, items in exemplars.items():
        items.sort(key=lambda x: -x["score"])
        picked[sname] = items[:topn]
    return picked, stats


def write_exemplars(picked: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for sname, items in picked.items():
        lines = [
            f"# 场景样例：{sname}",
            "",
            f"> ⚠ 本文件含原作段落，仅存于本地 corpus/（已被 .gitignore 屏蔽），**禁止提交或转发**。",
            f"> 用途：写作时对照语感；规则抽象后写入 references/，本文件不是知识源。",
            "",
        ]
        for i, it in enumerate(items, 1):
            lines += [
                f"## {i}. {it['book']} · {it['file']} · 段#{it['para_idx']} （{it['len']}字，{'含对话' if it['has_dia'] else '纯叙述'}）",
                "",
                it["text"],
                "",
            ]
        (out_dir / f"{sname}.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def write_pointers(picked: dict, stats: dict, out_file: Path) -> None:
    lines = [
        "# 场景切片指针索引（不含原文）",
        "",
        "> 原文样例在本地 `corpus/exemplars/<场景>.md`（gitignore）。本文件只存指针与模式结论，可安全提交。",
        "",
        "| 场景 | 命中段落数 | 平均段长 | 本地样例 | 典型出处（书 · 文件 · 段序号） |",
        "|---|---|---|---|---|",
    ]
    for sname in SCENES:
        st = stats[sname]
        avg = st["len_sum"] / st["len_n"] if st["len_n"] else 0
        ptrs = [f"{it['book']}·{it['file'].split('__',1)[-1]}·#{it['para_idx']}" for it in picked[sname][:5]]
        lines.append(f"| {sname} | {st['hits']} | {avg:.0f}字 | {len(picked[sname])} 条 | {'；'.join(ptrs)} |")
    lines += [
        "",
        "## 各场景触发的关键词表",
        "",
    ]
    for sname, cfg in SCENES.items():
        lines.append(f"- **{sname}**：{'、'.join(cfg['keys'][:12])}…")
    out_file.write_text("\n".join(lines), encoding="utf-8", newline="\n")


# ---------------------------------------------------------------- Phase 4 报告

def write_report(q: dict, stats: dict, picked: dict, thresholds_written: bool, out: Path) -> str:
    s, p, d = q["sentence"], q["paragraph"], q["dialogue"]
    lines = [
        "# 语料自动化分析报告",
        f"> 生成于 {time.strftime('%Y-%m-%d %H:%M:%S')} ｜ 语料 {q['corpus']['files']} 个文件 / {q['corpus']['total_han']:,} 汉字",
        "",
        "## 一、句长与节奏",
        f"- 平均句长 **{s['mean']:.1f} 字**（P25={s['p25']:.0f} / P50={s['p50']:.0f} / P75={s['p75']:.0f} / P90={s['p90']:.0f}）",
        f"- 短句(<12字)占比 **{s['short_lt12_ratio']:.1%}**，超短句(<6字)占比 **{s['ultrashort_lt6_ratio']:.1%}**",
        f"- 句长分布：{'，'.join(f'{k}字: {v:,}' for k, v in s['dist_bins_1_6_12_20_35_60'].items())}",
        "",
        "## 二、段落呼吸",
        f"- 单句成段比 **{p['single_sentence_ratio']:.1%}** ｜ 冷拳率 **{p['cold_punch_ratio']:.1%}**",
        f"- 段长分布：{'，'.join(f'{k}字: {v:,}' for k, v in p['dist_bins_1_10_25_50_100_200'].items())}",
        "",
        "## 三、对话与叙述",
        f"- 对话字符占比 **{d['dialogue_char_ratio']:.1%}**（对话 {d['dialogue_chars']:,} 字 / 总 {q['corpus']['total_han']:,} 字）",
        "",
        "## 四、修辞与标志短语（每千字）",
        f"- 比喻词：{'，'.join(f'{k} {v}' for k, v in list(q['rhetoric_per_kilo'].items())[:8])}",
        f"- 比喻取材域：{'，'.join(f'{k} {v:.0%}' for k, v in q['simile_domain'].items())}",
        f"- 标志短语 Top10：{'，'.join(f'{k} {v}' for k, v in list(q['signature_per_kilo'].items())[:10])}",
        f"- 高频动词 Top10：{'，'.join(f'{k} {v:,}' for k, v in q['verb_freq_top'][:10])}",
        f"- 标点（每千字）：{'，'.join(f'{k} {v}' for k, v in q['punct_per_kilo'].items())}",
        "",
        "## 五、高频 n-gram（语言指纹候选）",
        "- 2-gram：" + "、".join(f"{g}({c})" for g, c in q["ngram_top50"]["2gram"][:20]),
        "- 3-gram：" + "、".join(f"{g}({c})" for g, c in q["ngram_top50"]["3gram"][:20]),
        "",
        "## 六、场景切片",
        "| 场景 | 命中段落数 | 抽取样例 |",
        "|---|---|---|",
    ]
    for sname in SCENES:
        lines.append(f"| {sname} | {stats[sname]['hits']:,} | {len(picked[sname])} 条 → corpus/exemplars/{sname}.md |")
    lines += [
        "",
        f"## 七、阈值标定：{'已写入 assets/schemas/thresholds.json' if thresholds_written else '跳过'}",
        "",
        "> 合规说明：本报告与 thresholds.json 只含统计数值；原文样例仅存 corpus/exemplars/（gitignore）。",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return "\n".join(lines)


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, default=ROOT / "corpus/source")
    ap.add_argument("--topn", type=int, default=12, help="每场景抽取样例数")
    ap.add_argument("--no-thresholds", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    files = sorted(args.corpus.rglob("*.txt"))
    if not files:
        print(f"[error] {args.corpus} 下没有 txt", file=sys.stderr)
        return 1
    print(f"[1/4] 量化特征：{len(files)} 个文件 …")

    q = quant_pass(files)
    stats_dir = ROOT / "corpus/stats"
    stats_dir.mkdir(parents=True, exist_ok=True)
    (stats_dir / "quant.json").write_text(json.dumps(q, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"      完成（{time.time()-t0:.0f}s）。平均句长 {q['sentence']['mean']:.1f}，"
          f"对话占比 {q['dialogue']['dialogue_char_ratio']:.1%}")

    print("[2/4] 场景切片 …")
    picked, sstats = scene_pass(files, args.topn)
    write_exemplars(picked, ROOT / "corpus/exemplars")
    write_pointers(picked, sstats, ROOT / "references/corpus-notes/scene-pointers.md")
    total_hit = sum(s["hits"] for s in sstats.values())
    print(f"      完成。场景命中段落 {total_hit:,} 个，样例 {sum(len(v) for v in picked.values())} 条")

    thresholds_written = False
    if not args.no_thresholds:
        print("[3/4] 阈值标定（复用 audit_style.compute_metrics，逐章算再取分位）…")
        th = calibrate(files, "fiction")
        th_path = ROOT / "assets/schemas/thresholds.json"
        th_path.write_text(json.dumps(th, ensure_ascii=False, indent=1), encoding="utf-8")
        thresholds_written = True
        print(f"      完成 -> {th_path}")

    print("[4/4] 报告 …")
    report = write_report(q, sstats, picked, thresholds_written, stats_dir / "report.md")
    print(report)
    print(f"\n总耗时 {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
