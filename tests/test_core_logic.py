# -*- coding: utf-8 -*-
"""V3.4 测试 ② — 核心业务逻辑（P1-4 补缺：之前 0 覆盖）"""
import unittest
import sys
import tempfile
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from insurance_review import classify, to_cny, is_group, valid, diagnose, detect_conflicts, _fmt_gap


class TestClassify(unittest.TestCase):
    def test_重疾(self):
        self.assertEqual(classify({"name": "平安重大疾病保险"}), "重疾险")

    def test_医疗(self):
        self.assertEqual(classify({"name": "百万医疗险"}), "医疗险")

    def test_意外(self):
        self.assertEqual(classify({"name": "综合意外险"}), "意外险")

    def test_寿险(self):
        self.assertEqual(classify({"name": "定期寿险"}), "寿险")

    def test_年金(self):
        self.assertEqual(classify({"name": "养老年金险"}), "年金险")

    def test_type字段也能分类(self):
        self.assertEqual(classify({"name": "", "type": "重疾"}), "重疾险")

    def test_空输入(self):
        self.assertEqual(classify({}), "其他")


class TestToCny(unittest.TestCase):
    def test_CNY不变(self):
        self.assertEqual(to_cny(100000, "CNY"), 100000)

    def test_HKD换算(self):
        self.assertEqual(to_cny(100000, "HKD"), 93000)

    def test_USD换算(self):
        self.assertEqual(to_cny(100000, "USD"), 725000)

    def test_未知币种默认CNY(self):
        self.assertEqual(to_cny(100000, "JPY"), 100000)

    def test_返回int不是float(self):
        """P2 修复验证：to_cny 返回 int"""
        self.assertIsInstance(to_cny(100000, "HKD"), int)


class TestIsGroup(unittest.TestCase):
    def test_公司(self):
        self.assertTrue(is_group({"holder": "某科技公司"}))

    def test_集团(self):
        self.assertTrue(is_group({"holder": "某某集团"}))

    def test_有限公司(self):
        self.assertTrue(is_group({"holder": "某某有限公司"}))

    def test_个人(self):
        self.assertFalse(is_group({"holder": "张三"}))

    def test_英文Co(self):
        self.assertTrue(is_group({"holder": "ABC Co., Ltd."}))

    def test_空(self):
        self.assertFalse(is_group({"holder": ""}))


class TestValid(unittest.TestCase):
    def test_有保费有效(self):
        self.assertTrue(valid({"premium": 100}))

    def test_零保费无效(self):
        self.assertFalse(valid({"premium": 0}))

    def test_缺字段无效(self):
        self.assertFalse(valid({}))


class TestDiagnose(unittest.TestCase):
    def setUp(self):
        self.family = {"annual_income": 500000, "debt": 1500000}
        # 寿险需求 = 500000*10 + 1500000 = 6500000

    def test_寿险缺口(self):
        policies = [{"name": "寿险", "coverage": 1000000, "premium": 2000, "currency": "CNY", "kind": "寿险"}]
        r = diagnose(policies, self.family)
        self.assertEqual(r["寿险缺口"], 5500000)

    def test_寿险充足无缺口(self):
        policies = [{"name": "寿险", "coverage": 7000000, "premium": 2000, "currency": "CNY", "kind": "寿险"}]
        r = diagnose(policies, self.family)
        self.assertEqual(r["寿险缺口"], 0)

    def test_重疾缺口(self):
        policies = [{"name": "重疾", "coverage": 200000, "premium": 5000, "currency": "CNY", "kind": "重疾险"}]
        r = diagnose(policies, self.family)
        self.assertEqual(r["重疾缺口"], 300000)

    def test_重疾充足(self):
        policies = [{"name": "重疾", "coverage": 600000, "premium": 5000, "currency": "CNY", "kind": "重疾险"}]
        r = diagnose(policies, self.family)
        self.assertEqual(r["重疾缺口"], 0)

    def test_医疗险重复(self):
        policies = [
            {"name": "医疗", "coverage": 4000000, "premium": 800, "currency": "CNY", "kind": "医疗险"},
            {"name": "医疗", "coverage": 2000000, "premium": 500, "currency": "CNY", "kind": "医疗险"},
        ]
        r = diagnose(policies, self.family)
        self.assertTrue(r["医疗险重复"])

    def test_医疗险不重复(self):
        policies = [{"name": "医疗", "coverage": 4000000, "premium": 800, "currency": "CNY", "kind": "医疗险"}]
        r = diagnose(policies, self.family)
        self.assertFalse(r["医疗险重复"])

    def test_团险被排除(self):
        policies = [{"name": "寿险", "holder": "某公司", "coverage": 10000000, "premium": 100, "currency": "CNY", "kind": "寿险"}]
        r = diagnose(policies, self.family)
        # 团险被排除，寿险缺口=全量
        self.assertEqual(r["寿险缺口"], 6500000)

    def test_多币种换算(self):
        policies = [{"name": "寿险", "coverage": 100000, "premium": 2000, "currency": "USD", "kind": "寿险"}]
        # 100000 USD = 725000 CNY
        r = diagnose(policies, self.family)
        self.assertEqual(r["寿险缺口"], 5775000)

    def test_现金价值合计(self):
        policies = [
            {"name": "年金", "coverage": 500000, "premium": 50000, "currency": "CNY", "kind": "年金险", "cash_value": 200000},
            {"name": "重疾", "coverage": 300000, "premium": 12000, "currency": "CNY", "kind": "重疾险", "cash_value": 50000},
        ]
        r = diagnose(policies, self.family)
        self.assertEqual(r["可质押现金价值"], 250000)

    def test_缺字段不崩(self):
        """P2 修复验证：family 缺字段不崩"""
        r = diagnose([], {})
        self.assertEqual(r["寿险缺口"], 0)


class TestDetectConflicts(unittest.TestCase):
    def test_医疗险重复警告(self):
        policies = [
            {"name": "医疗", "coverage": 1, "premium": 800, "currency": "CNY", "kind": "医疗险"},
            {"name": "医疗", "coverage": 1, "premium": 500, "currency": "CNY", "kind": "医疗险"},
        ]
        w = detect_conflicts(policies)
        self.assertTrue(any("医疗险" in x for x in w))

    def test_高现金价值警告(self):
        policies = [{"name": "年金", "coverage": 1, "premium": 50000, "currency": "CNY", "kind": "年金险", "cash_value": 200000}]
        w = detect_conflicts(policies)
        self.assertTrue(any("高现金价值" in x for x in w))

    def test_团险排除提示(self):
        policies = [{"name": "寿险", "holder": "某公司", "coverage": 1, "premium": 100, "currency": "CNY", "kind": "寿险"}]
        w = detect_conflicts(policies)
        self.assertTrue(any("团险" in x for x in w))

    def test_无冲突返回空(self):
        policies = [{"name": "寿险", "coverage": 1, "premium": 2000, "currency": "CNY", "kind": "寿险"}]
        w = detect_conflicts(policies)
        self.assertEqual(w, [])

    def test_无效保单不触发冲突(self):
        policies = [
            {"name": "医疗", "coverage": 1, "premium": 0, "currency": "CNY", "kind": "医疗险"},
            {"name": "医疗", "coverage": 1, "premium": 0, "currency": "CNY", "kind": "医疗险"},
        ]
        w = detect_conflicts(policies)
        self.assertEqual(w, [])


class TestFmtGap(unittest.TestCase):
    """P0-3 修复验证：¥True 不再出现"""

    def test_bool_是(self):
        self.assertEqual(_fmt_gap(True), "是")

    def test_bool_否(self):
        self.assertEqual(_fmt_gap(False), "否")

    def test_int_加千分位(self):
        self.assertEqual(_fmt_gap(5500000), "¥5,500,000")

    def test_float转int(self):
        self.assertEqual(_fmt_gap(5500000.0), "¥5,500,000")

    def test_字符串不变(self):
        self.assertEqual(_fmt_gap("测试"), "测试")


if __name__ == "__main__":
    unittest.main(verbosity=2)
