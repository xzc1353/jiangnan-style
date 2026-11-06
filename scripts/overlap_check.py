#!/usr/bin/env python3
"""
overlap_check.py —— 原创度守门

检测产出文本与本地语料（corpus/source/，用户合法持有、不入库）之间的
最长公共子串。≥15 字（默认阈值）即报警。

用法:
    python overlap_check.py <产出文件或目录> --corpus corpus/source/ [--threshold 15] [--json]

原理:
    把语料的所有 n-gram（n = threshold）装进集合，滑动扫描产出的每个
    n-gram，命中即定位并扩展到最长公共子串。
    内存: 语料 1000 万字 -> ~1000 万个 15-gram 哈希，约 1-2 GB；
    可用 --threshold 20 显著降低内存（约 400 MB）。逐章比对模式见 --stream。

依赖: 仅 Python 标准库。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def norm(text: str) -> str:
    """归一化：去空白与标点差异，保留汉字/字母/数字，避免标点差异漏检。"""
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[，。！？；：、“”\"'‘’（）()《》<>…—·\-]", "", text)
    return text


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8", "utf-16", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def grams(s: str, n: int):
    for i in range(len(s) - n + 1):
        yield s[i:i + n]


def load_corpus_index(corpus: Path, n: int, max_files: int | None = None):
    """返回 ({hash(gram): 文件名}, 文件数)。哈希键省内存；碰撞由 src.find(g) 精确校验过滤。"""
    index: dict[int, str] = {}
    files = sorted(corpus.rglob("*.txt"))
    if max_files:
        files = files[:max_files]
    for f in files:
        text = norm(read_text(f))
        for g in grams(text, n):
            h = hash(g)
            if h not in index:
                index[h] = f.name
    return index, len(files)


def check_file(target: Path, index: dict[str, str], n: int, corpus_dir: Path) -> list[dict]:
    text = norm(read_text(target))
    hits: list[dict] = []
    checked_spans: list[tuple[int, int]] = []

    def in_checked(a: int, b: int) -> bool:
        return any(a >= s and b <= e for s, e in checked_spans)

    i = 0
    raw = text
    while i <= len(raw) - n:
        g = raw[i:i + n]
        if hash(g) in index and not in_checked(i, i + n):
            # 在对应语料文件内扩展到最长公共子串；src.find(g) 精确校验可过滤哈希碰撞
            src_file = index[hash(g)]
            src = norm(read_text(corpus_dir / src_file)) if (corpus_dir / src_file).exists() else ""
            length = n
            confirmed = False
            if src:
                j = src.find(g)
                if j >= 0:
                    confirmed = True
                    while (i + length < len(raw) and j + length < len(src)
                           and raw[i + length] == src[j + length]):
                        length += 1
            if confirmed:
                hits.append({
                    "file": str(target),
                    "corpus_file": src_file,
                    "position": i,
                    "excerpt": raw[i:i + min(length, 60)],
                    "length": length,
                })
            checked_spans.append((i, i + length))
            i += length
        else:
            i += 1
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description="产出 vs 本地语料 重合检测")
    ap.add_argument("target", type=Path, help="产出文本文件或目录")
    ap.add_argument("--corpus", type=Path, default=ROOT / "corpus/source")
    ap.add_argument("--threshold", type=int, default=15, help="报警的最长公共子串长度（默认 15）")
    ap.add_argument("--max-files", type=int, default=None, help="仅装载语料前 N 个文件（冒烟测试用）")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not args.corpus.exists():
        print("[warn] 本地语料目录不存在，跳过查重（无语料无法自证，请自行人工核对）", file=sys.stderr)
        return 0

    n = args.threshold
    print(f"[1/2] 装载语料 n-gram 索引 (n={n}) …")
    index, nfiles = load_corpus_index(args.corpus, n, args.max_files)
    print(f"      语料 {nfiles} 个文件, 索引 {len(index):,} 个 {n}-gram")

    targets = ([p for p in args.target.rglob("*.txt")] + [p for p in args.target.rglob("*.md")]
               if args.target.is_dir() else [args.target])

    print("[2/2] 扫描产出 …")
    all_hits: list[dict] = []
    for t in targets:
        all_hits.extend(check_file(t, index, n, args.corpus))

    # 过滤：低于阈值的扩展命中不算
    all_hits = [h for h in all_hits if h["length"] >= n]

    if args.json:
        print(json.dumps({"target": str(args.target), "threshold": n,
                          "hits": all_hits,
                          "verdict": "FAIL" if all_hits else "PASS"},
                         ensure_ascii=False, indent=1))
    else:
        if not all_hits:
            print(f"✓ 通过：未发现 ≥{n} 字的重合片段（共扫描 {len(targets)} 个文件）")
        else:
            print(f"✗ 未通过：发现 {len(all_hits)} 处 ≥{n} 字重合：")
            for h in all_hits[:20]:
                print(f"  [{h['length']}字] {h['file']} @ {h['position']}  与 {h['corpus_file']} 重合:")
                print(f"      “{h['excerpt']}”")

    # 报告落盘（本地）
    report_dir = ROOT / "corpus/stats"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "overlap.json").write_text(
        json.dumps({"target": str(args.target), "threshold": n, "hits": all_hits},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    return 1 if all_hits else 0


if __name__ == "__main__":
    sys.exit(main())
