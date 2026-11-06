#!/usr/bin/env python3
"""
extract_epub.py —— 本地 EPUB → 纯文本

按 OPF spine 顺序抽取正文，输出纯文本到 corpus/（该目录被 .gitignore 永久屏蔽）。
本脚本只做格式转换，不做任何风格分析；产物仅存本地，禁止提交。

用法:
    python extract_epub.py "<book.epub>" [-o corpus/source/] [--single-file]
"""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
from html import unescape
from pathlib import Path
from xml.etree import ElementTree as ET

NS_CONTAINER = "{urn:oasis:names:tc:opendocument:xmlns:container}"
NS_OPF = "{http://www.idpf.org/2007/opf}"
NS_DC = "{http://purl.org/dc/elements/1.1/}"


def find_opf(zf: zipfile.ZipFile) -> str:
    container = zf.read("META-INF/container.xml")
    root = ET.fromstring(container)
    rf = root.find(f".//{NS_CONTAINER}rootfile")
    if rf is None:
        raise ValueError("container.xml 中找不到 rootfile")
    return rf.get("full-path")  # type: ignore[return-value]


def parse_opf(zf: zipfile.ZipFile, opf_path: str):
    root = ET.fromstring(zf.read(opf_path))
    base = Path(opf_path).parent

    title_el = root.find(f".//{NS_DC}title")
    title = title_el.text.strip() if title_el is not None and title_el.text else Path(opf_path).stem

    manifest: dict[str, str] = {}
    for item in root.findall(f".//{NS_OPF}manifest/{NS_OPF}item"):
        mid, href = item.get("id"), item.get("href")
        if mid and href:
            # zipfile 条目一律使用正斜杠；Windows 下 Path 会拼出反斜杠，必须归一化
            full = str(base / href).replace("\\", "/")
            manifest[mid] = full

    spine = [manifest.get(it.get("idref")) for it in root.findall(f".//{NS_OPF}spine/{NS_OPF}itemref")]
    return title, [h for h in spine if h]


BLOCK_TAGS = re.compile(
    r"<(/?)(p|div|h[1-6]|li|br|blockquote|section|article|tr)\b[^>]*>", re.I
)
SKIP_RE = re.compile(r"<(script|style)\b.*?</\1>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
HEADING_RE = re.compile(r"<h([1-6])\b[^>]*>(.*?)</h\1>", re.I | re.S)


def html_to_text(html: str) -> str:
    html = COMMENT_RE.sub("", html)
    html = SKIP_RE.sub("", html)

    # 标题行保留为可读分隔
    def heading_sub(m: re.Match) -> str:
        return f"\n\n{'#' * int(m.group(1))} {clean(m.group(2))}\n\n"

    html = HEADING_RE.sub(heading_sub, html)
    html = BLOCK_TAGS.sub(lambda m: "\n" if m.group(1) else "", html)
    return clean(html)


def clean(s: str) -> str:
    s = unescape(TAG_RE.sub("", s))
    s = re.sub(r"[ \t\u3000]+", " ", s)
    s = re.sub(r" ?\n ?", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def extract(epub_path: Path, out_dir: Path, single_file: bool) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    with zipfile.ZipFile(epub_path) as zf:
        opf = find_opf(zf)
        title, docs = parse_opf(zf, opf)

        safe_title = re.sub(r'[\\/:*?"<>|]', "_", title).strip() or epub_path.stem
        parts: list[str] = [f"《{title}》\n"]

        for href in docs:
            try:
                raw = zf.read(href)
            except KeyError:
                print(f"[warn] spine 条目不存在: {href}", file=sys.stderr)
                continue
            html = raw.decode("utf-8", errors="replace")
            text = html_to_text(html)
            if not text:
                continue
            if single_file:
                parts.append(f"\n\n----- {Path(href).name} -----\n\n{text}")
            else:
                # NTFS 会把 "::" 解析为备用数据流(ADS)导致 PermissionError，用 "__" 分隔
                out = out_dir / f"{safe_title}__{Path(href).stem}.txt"
                out.write_text(text, encoding="utf-8", newline="\n")
                outputs.append(out)

        if single_file or not outputs:
            out = out_dir / f"{safe_title}.txt"
            out.write_text("".join(parts) if single_file else f"《{title}》\n(逐章抽取失败，见告警)",
                           encoding="utf-8", newline="\n")
            outputs.insert(0, out)

    return outputs


def main() -> int:
    ap = argparse.ArgumentParser(description="EPUB → 纯文本（输出到 corpus/，永不提交）")
    ap.add_argument("epub", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=Path(__file__).parent.parent / "corpus/source")
    ap.add_argument("--single-file", action="store_true", help="整本合并为一个 txt（默认逐章）")
    args = ap.parse_args()

    if not args.epub.exists():
        print(f"文件不存在: {args.epub}", file=sys.stderr)
        return 1

    outs = extract(args.epub, args.out, args.single_file)
    total_chars = sum(len(p.read_text(encoding="utf-8")) for p in outs)
    print(f"完成: {len(outs)} 个文本文件, 共 {total_chars} 字符")
    print(f"输出目录: {args.out.resolve()}")
    print("提醒: corpus/ 已被 .gitignore 屏蔽, 请勿移动产物到仓库其他位置。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
