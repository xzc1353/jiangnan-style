# corpus/ —— 本地语料目录（永不提交）

这个目录**故意被 `.gitignore` 整个屏蔽**。它的存在只有一个目的：让你在自己的机器上做风格统计和原创度自查，而这些文件永远不进入 Git 历史。

## 放什么

```
corpus/
├── source/          # 从 epub / txt 抽取出来的纯文本（按书分文件）
├── stats/           # 统计脚本产出的指标快照（不含原文，可提交到 reports/ 另行处理）
└── README.md        # 本文件
```

## 为什么不提交

1. **著作权**：原作正文是受保护的表达，公开分发等于侵权，与"是不是免费"无关。
2. **技术必要性**：这个 skill 不靠"把书塞进上下文"来模仿风格，靠的是 `references/` 里抽象出来的规则。语料只是**标定数值**的参照物。
3. **可复现性**：别人 clone 仓库拿到的是方法和阈值定义，用自己合法持有的文本就能复现统计，不需要我们分发。

## 怎么用

```bash
# 1. 把 epub 抽成纯文本（输出到 corpus/source/）
python scripts/extract_epub.py "D:/Downloads/《龙族》1-5+前传.epub" -o corpus/source/

# 2. 统计风格指标，标定 references/style/09-dna.md 的阈值
python scripts/audit_style.py corpus/source/ --calibrate

# 3. 检查自己的产出有没有和原作撞句子
python scripts/overlap_check.py out/我的新章节.md --corpus corpus/source/
```

## 自检

提交前跑一次：

```bash
git status --porcelain | grep -i corpus   # 不应有任何 corpus/ 下的文件（README 除外）
```

CI 里也有一道同名守卫（见 `.github/workflows/ci.yml`），撞线会直接 fail。
