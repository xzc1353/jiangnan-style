"""overlap_check 单元测试：python -m unittest tests.test_overlap -v"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from overlap_check import check_file, load_corpus_index, norm  # noqa: E402

CORPUS_LINE = ("帘子揭开，夹道的是虎豹骑的武士，全体下唐出使的随从也停留在远处，"
               "打着金色菊花的大旗，跟着拓拔山月进帐的竟然还有北都城里几乎所有的贵族。")


class TestOverlap(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.corpus = self.tmp / "corpus"
        self.corpus.mkdir()
        (self.corpus / "book1.txt").write_text(CORPUS_LINE * 3, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_norm_strips_punct(self):
        self.assertEqual(norm("你好，世界。"), norm("你好世界"))
        self.assertNotIn("，", norm("，。！"))

    def test_plagiarism_detected(self):
        target = self.tmp / "plag.txt"
        target.write_text("开头。" + CORPUS_LINE[:60] + "结尾。", encoding="utf-8")
        index, _ = load_corpus_index(self.corpus, 15)
        hits = check_file(target, index, 15, self.corpus)
        self.assertTrue(any(h["length"] >= 15 for h in hits))

    def test_original_passes(self):
        target = self.tmp / "orig.txt"
        target.write_text("夜里的操场只有风经过的声音，他把那双旧球鞋系在单杠上，鞋带打了个死结。",
                          encoding="utf-8")
        index, _ = load_corpus_index(self.corpus, 15)
        hits = check_file(target, index, 15, self.corpus)
        self.assertEqual(hits, [])

    def test_short_overlap_ignored(self):
        # 14 字重合（低于阈值 15）不应报警
        target = self.tmp / "short.txt"
        target.write_text("开头。" + CORPUS_LINE[:14] + "结尾。", encoding="utf-8")
        index, _ = load_corpus_index(self.corpus, 15)
        hits = check_file(target, index, 15, self.corpus)
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
