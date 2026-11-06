"""audit_style 单元测试：python -m unittest tests.test_audit -v"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from audit_style import compute_metrics, judge, load_thresholds  # noqa: E402

SAMPLE = """深夜的训练馆只剩他一个人，灯一盏一盏灭下去，汗水在地板上洇出一个人形。他把绷带重新缠了一遍，又拆开，再缠上。

他还没赢过。

“你到底图什么？”师姐站在门口，手里拎着两个塑料袋。

“图个明白。”他说。

窗外开始下雨。雨水顺着铁皮屋檐滴落，敲打着一排旧杠铃，叮叮当当，像是有人在很远的地方数着拍子练琴。"""


class TestMetrics(unittest.TestCase):
    def setUp(self):
        self.m = compute_metrics(SAMPLE)

    def test_basic_counts(self):
        self.assertGreater(self.m["chars_han"], 100)
        self.assertGreater(self.m["sentences"], 5)

    def test_metric_keys_complete(self):
        for key in ["M1_avg_sentence_len", "M2_short_sentence_ratio", "M3_single_sentence_para_ratio",
                    "M4_dialogue_line_ratio", "M6_simile_per_kilo", "M9_cold_punch_rate",
                    "M12_de_per_kilo"]:
            self.assertIn(key, self.m)

    def test_simile_masking(self):
        # “好像”应计 1 次而不是 2 次（像 不重复计）
        t = "他觉得好像有什么东西在看他。"
        m = compute_metrics(t)
        self.assertEqual(round(m["M6_simile_per_kilo"] * m["chars_han"] / 1000), 1)

    def test_cold_punch_detected(self):
        # “他还没赢过。”是典型的长铺陈后短句独立段
        self.assertGreater(self.m["M9_cold_punch_rate"], 0)


class TestJudge(unittest.TestCase):
    def test_uncalibrated(self):
        j = judge(compute_metrics(SAMPLE), {"_status": "uncalibrated"}, "fiction")
        self.assertEqual(j["status"], "uncalibrated")

    def test_ok_and_violation(self):
        th = {"_status": "calibrated", "fiction": {
            "M1_avg_sentence_len": {"target": [20, 30], "tolerate": [15, 35]},
            "M2_short_sentence_ratio": {"target": [0.2, 0.4], "tolerate": [0.1, 0.5]},
        }}
        m = compute_metrics(SAMPLE)
        j = judge(m, th, "fiction")
        self.assertEqual(j["status"], "ok")
        self.assertIn(j["verdict"]["M2_short_sentence_ratio"]["level"],
                      ("OK", "OUT_OF_TARGET", "OUT_OF_TOLERANCE"))

    def test_out_of_tolerance(self):
        th = {"_status": "calibrated", "fiction": {
            "M1_avg_sentence_len": {"target": [2, 3], "tolerate": [1, 4]},
        }}
        j = judge(compute_metrics(SAMPLE), th, "fiction")
        self.assertEqual(j["verdict"]["M1_avg_sentence_len"]["level"], "OUT_OF_TOLERANCE")


class TestThresholdsFile(unittest.TestCase):
    def test_repo_thresholds_calibrated(self):
        p = Path(__file__).parent.parent / "assets/schemas/thresholds.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(data.get("_status"), "calibrated")
        self.assertIn("fiction", data)


if __name__ == "__main__":
    unittest.main()
