"""diff_style.py 的单元测试：只测确定性逻辑，不测语义判断。"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from diff_style import compare, infer_level, numbers_of, quotes_of  # noqa: E402

BEFORE = "他的内心充满了悲伤，仿佛整个世界都崩塌了，他不禁想起了三年前的往事，窗外的雨下了3个小时。"

AFTER_SAME_FACTS = "雨下了3个小时。他坐在台阶上，校服湿透了。三年前也是这样。"

AFTER_LOST_NUMBER = "雨下了很久。他坐在台阶上，校服湿透了。"


class TestNumbers(unittest.TestCase):
    def test_extract_arabic(self):
        self.assertEqual(numbers_of("他等了3个小时，又跑了5公里"), {"3", "5"})

    def test_fullwidth_digits(self):
        self.assertEqual(numbers_of("温度是２５度"), {"25"})

    def test_percent_kept(self):
        self.assertEqual(numbers_of("涨了12.5%"), {"12.5%"})


class TestQuotes(unittest.TestCase):
    def test_chinese_quotes(self):
        self.assertEqual(quotes_of("「我不行。」他说"), ["我不行。"])

    def test_corner_quotes(self):
        self.assertEqual(quotes_of("『好吧』"), ["好吧"])

    def test_ignores_short(self):
        self.assertEqual(quotes_of("「嗯」"), [])


class TestCompare(unittest.TestCase):
    def test_identity_no_shift(self):
        rep = compare(BEFORE, BEFORE, "fiction", {"_status": "calibrated"})
        self.assertEqual(rep["significant_moved"], [])
        self.assertEqual(rep["before"]["chars_han"], rep["after"]["chars_han"])

    def test_number_change_alerts(self):
        rep = compare(BEFORE, AFTER_LOST_NUMBER, "fiction", {"_status": "calibrated"})
        self.assertTrue(rep["preserve_check"]["fact_alerts"])
        self.assertIn("3", " ".join(rep["preserve_check"]["fact_alerts"]))

    def test_no_false_alert(self):
        rep = compare(BEFORE, AFTER_SAME_FACTS, "fiction", {"_status": "calibrated"})
        self.assertEqual(rep["preserve_check"]["fact_alerts"], [])

    def test_quote_loss_detected(self):
        rep = compare("他说：「我一定回来。」", "他说了句话。", "fiction", {"_status": "calibrated"})
        self.assertTrue(rep["preserve_check"]["quotes_missing"])

    def test_metrics_have_all_rows(self):
        rep = compare(BEFORE, AFTER_SAME_FACTS, "fiction", {"_status": "calibrated"})
        self.assertEqual(len(rep["metrics"]), 12)

    def test_zero_before_has_no_pct(self):
        """改前为 0 时相对幅度无意义，必须是 None 而不是天文数字。"""
        rep = compare("他走了。", "他走了。「好！」", "fiction", {"_status": "calibrated"})
        for row in rep["metrics"]:
            if row["before"] == 0:
                self.assertIsNone(row["delta_pct"])


class TestInferLevel(unittest.TestCase):
    def test_small_change_is_l1(self):
        self.assertEqual(infer_level(1000, 960, ["M1_avg_sentence_len"])["level"], "L1")

    def test_medium_change_is_l2(self):
        self.assertEqual(infer_level(1000, 750, ["M1", "M2"])["level"], "L2")

    def test_big_change_is_l3(self):
        self.assertEqual(infer_level(1000, 400, ["M1", "M2", "M3", "M4", "M5", "M6"])["level"], "L3")


if __name__ == "__main__":
    unittest.main()
