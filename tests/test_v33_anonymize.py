# -*- coding: utf-8 -*-
"""V3.4 测试 ① — mask / anonymize / classify_by_text（引用 privacy.py）"""
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from privacy import mask, anonymize, classify_by_text, KIND_PATTERNS


class TestMask(unittest.TestCase):
    def test_身份证_18位(self):
        self.assertEqual(mask("110101199003078888"), "110101****8888")

    def test_身份证_末尾X(self):
        self.assertEqual(mask("11010119900307888X"), "110101****888X")

    def test_银行卡_16位(self):
        self.assertEqual(mask("6222021234567890"), "****7890")

    def test_银行卡_19位(self):
        self.assertEqual(mask("6222021234567890123"), "****0123")

    def test_手机号_11位(self):
        self.assertEqual(mask("13800138000"), "138****8000")

    def test_手机号_12位不误伤(self):
        self.assertEqual(mask("138001380001"), "138001380001")

    def test_20位不误伤(self):
        self.assertNotIn("****", mask("12345678901234567890"))

    def test_混合文本(self):
        out = mask("客户张三，身份证110101199003078888，手机13800138000")
        self.assertNotIn("110101199003078888", out)
        self.assertNotIn("13800138000", out)

    def test_空值(self):
        self.assertEqual(mask(""), "")
        self.assertEqual(mask(None), "")


class TestAnonymize(unittest.TestCase):
    def test_字典递归(self):
        data = {"holder": "张三 110101199003078888", "note": "电话13800138000"}
        out = anonymize(data)
        self.assertNotIn("110101199003078888", out["holder"])
        self.assertNotIn("13800138000", out["note"])

    def test_列表嵌套(self):
        data = [{"id": "110101199003078888"}, {"id": "13800138000"}]
        out = anonymize(data)
        self.assertNotIn("110101199003078888", out[0]["id"])

    def test_非字符串不变(self):
        data = {"coverage": 300000, "active": True}
        self.assertEqual(anonymize(data), data)

    def test_数字型ID脱敏(self):
        """P1-1 修复：11位以上数字也应脱敏"""
        data = {"id_card": 110101199003078888}
        out = anonymize(data)
        self.assertNotIn("110101199003078888", str(out["id_card"]))
        self.assertIn("****", str(out["id_card"]))

    def test_小数字不脱敏(self):
        """保费 12000 不应被误脱敏"""
        data = {"premium": 12000, "coverage": 300000}
        out = anonymize(data)
        self.assertEqual(out["premium"], 12000)
        self.assertEqual(out["coverage"], 300000)

    def test_空结构(self):
        self.assertEqual(anonymize({}), {})
        self.assertEqual(anonymize([]), [])
        self.assertEqual(anonymize(""), "")


class TestClassifyByText(unittest.TestCase):
    """P0-2 修复验证：classify 与 detect_kind 共用同一关键词表"""

    def test_5类全覆盖(self):
        cases = {
            "平安重大疾病保险": "重疾险",
            "百万医疗险": "医疗险",
            "综合意外伤害": "意外险",
            "定期寿险": "寿险",
            "养老年金险": "年金险",
            "某某奇怪险种": "其他",
        }
        for text, expected in cases.items():
            self.assertEqual(classify_by_text(text), expected, f"分类错误: {text}")

    def test_英文关键词(self):
        self.assertEqual(classify_by_text("Critical Illness Coverage"), "重疾险")
        self.assertEqual(classify_by_text("Medical Insurance"), "医疗险")
        self.assertEqual(classify_by_text("Accident Plan"), "意外险")
        self.assertEqual(classify_by_text("Whole Life Insurance"), "寿险")
        self.assertEqual(classify_by_text("Annuity Plan"), "年金险")

    def test_教育金关键词(self):
        """P0-2 修复：教育金之前只在 pdf_parser 有，现在统一"""
        self.assertEqual(classify_by_text("子女教育金保险"), "年金险")

    def test_重大疾病关键词(self):
        """P0-2 修复：重大疾病之前 classify() 漏掉"""
        self.assertEqual(classify_by_text("重大疾病保险"), "重疾险")


if __name__ == "__main__":
    unittest.main(verbosity=2)
