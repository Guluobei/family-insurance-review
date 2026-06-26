# -*- coding: utf-8 -*-
"""V3.3 新功能测试 ② — --anonymize / mask() / anonymize()"""
import unittest
import subprocess
import sys
import tempfile
import json
from pathlib import Path

# 直接 import 主模块以测试函数
sys.path.insert(0, str(Path(__file__).parent.parent))
from insurance_review import mask, anonymize  # noqa

SCRIPT = Path(__file__).parent.parent / "insurance_review.py"

class TestMaskFunction(unittest.TestCase):
    """mask() 单元测试"""

    def test_身份证_18位(self):
        self.assertEqual(mask("110101199003078888"),
                         "110101****8888")

    def test_身份证_末尾字母(self):
        self.assertEqual(mask("11010119900307888X"),
                         "110101****888X")

    def test_银行卡_16位(self):
        self.assertEqual(mask("6222021234567890"),
                         "****7890")

    def test_银行卡_19位(self):
        self.assertEqual(mask("6222021234567890123"),
                         "****0123")

    def test_手机号_11位(self):
        self.assertEqual(mask("13800138000"),
                         "138****8000")

    def test_手机号_边界不误伤(self):
        """138001380001 是 12 位，不应被当作手机号"""
        result = mask("138001380001")
        self.assertEqual(result, "138001380001")  # 不变

    def test_混合_一句话含多种敏感信息(self):
        text = "客户张三，身份证110101199003078888，手机13800138000"
        out = mask(text)
        self.assertIn("****", out)
        self.assertNotIn("110101199003078888", out)
        self.assertNotIn("13800138000", out)

    def test_空值_不崩(self):
        self.assertEqual(mask(""), "")
        self.assertEqual(mask(None), "")

    def test_数字边界_不误伤19位以上的卡号被截断为19位部分(self):
        """20 位以上不应被识别为银行卡"""
        result = mask("12345678901234567890")
        self.assertNotIn("****", result)


class TestAnonymizeRecursive(unittest.TestCase):
    """anonymize() 递归脱敏测试"""

    def test_字典_全部字段脱敏(self):
        data = {
            "holder": "张三 110101199003078888",
            "note": "联系电话 13800138000",
            "policy_no": "6222021234567890"
        }
        out = anonymize(data)
        for v in out.values():
            self.assertNotIn("110101199003078888", v)
            self.assertNotIn("13800138000", v)
            self.assertNotIn("6222021234567890", v)

    def test_列表_嵌套字典(self):
        data = [
            {"holder": "张三 110101199003078888"},
            {"holder": "李四 13800138000"}
        ]
        out = anonymize(data)
        self.assertNotIn("110101199003078888", out[0]["holder"])
        self.assertNotIn("13800138000", out[1]["holder"])

    def test_非字符串_不变(self):
        data = {"coverage": 300000, "premium": 12000, "active": True}
        out = anonymize(data)
        self.assertEqual(out, data)

    def test_空结构(self):
        self.assertEqual(anonymize({}), {})
        self.assertEqual(anonymize([]), [])
        self.assertEqual(anonymize(""), "")


class TestAnonymizeCLI(unittest.TestCase):
    """--anonymize CLI 集成测试"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.policies = Path(self.tmp) / "p.json"
        self.family = Path(self.tmp) / "f.json"
        self.output = Path(self.tmp) / "r.html"
        self.policies.write_text(json.dumps([
            {"name": "平安重疾险", "holder": "张三 110101199003078888",
             "coverage": 300000, "premium": 12000, "currency": "CNY"}
        ], ensure_ascii=False), encoding="utf-8")
        self.family.write_text(json.dumps(
            {"annual_income": 500000, "debt": 1000000}
        ), encoding="utf-8")

    def test_anonymize_提示出现(self):
        r = subprocess.run(
            [sys.executable, str(SCRIPT),
             "-p", str(self.policies), "-f", str(self.family),
             "-o", str(self.output), "--anonymize"],
            capture_output=True, text=True
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("强制脱敏", r.stdout)

    def test_anonymize_报告不含敏感信息(self):
        r = subprocess.run(
            [sys.executable, str(SCRIPT),
             "-p", str(self.policies), "-f", str(self.family),
             "-o", str(self.output), "--anonymize"],
            capture_output=True, text=True
        )
        self.assertEqual(r.returncode, 0)
        content = self.output.read_text(encoding="utf-8")
        self.assertNotIn("110101199003078888", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
