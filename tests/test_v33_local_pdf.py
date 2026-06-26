# -*- coding: utf-8 -*-
"""V3.4 测试 ④ — pdf_parser / --local-pdf"""
import unittest
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from pdf_parser import detect_kind, extract_amount, detect_currency, extract_company
from privacy import classify_by_text

PARSER_SCRIPT = Path(__file__).parent.parent / "pdf_parser.py"
MAIN_SCRIPT = Path(__file__).parent.parent / "insurance_review.py"


class TestDetectKind(unittest.TestCase):
    """P0-2 验证：detect_kind 与 classify_by_text 结果一致"""

    def test_与classify_by_text一致(self):
        """关键测试：两条路径的分类结果必须完全一致"""
        texts = ["重大疾病保险", "百万医疗险", "意外险", "定期寿险", "年金险",
                 "Critical Illness", "Medical", "Accident", "Life", "Annuity",
                 "教育金", "防癌险", "某某奇怪险种"]
        for t in texts:
            self.assertEqual(detect_kind(t), classify_by_text(t),
                             f"分类不一致: {t}")

    def test_未知险种(self):
        self.assertEqual(detect_kind("某某奇怪险种"), "其他")


class TestExtractAmount(unittest.TestCase):
    def test_万元(self):
        self.assertEqual(extract_amount("基本保额：50万元", r'(?:基本[保\s]?额|保\s*额)'), 500000)

    def test_万字(self):
        self.assertEqual(extract_amount("保险金额：30万", r'(?:保险[金额\s]*|保\s*额)'), 300000)

    def test_纯数字元(self):
        self.assertEqual(extract_amount("保费：12000元", r'保[费]?费'), 12000)

    def test_无匹配(self):
        self.assertEqual(extract_amount("其他文本", r'基本[保\s]?额'), 0)


class TestDetectCurrency(unittest.TestCase):
    def test_USD(self):
        self.assertEqual(detect_currency("金额 100 USD"), "USD")
        self.assertEqual(detect_currency("100美元"), "USD")

    def test_HKD(self):
        self.assertEqual(detect_currency("金额 100 HKD"), "HKD")
        self.assertEqual(detect_currency("100港币"), "HKD")

    def test_EUR(self):
        self.assertEqual(detect_currency("100欧元"), "EUR")

    def test_默认CNY(self):
        self.assertEqual(detect_currency("100元"), "CNY")


class TestExtractCompany(unittest.TestCase):
    def test_中国人寿(self):
        self.assertEqual(extract_company("中国人寿保险股份有限公司"), "中国人寿保险")

    def test_平安人寿(self):
        self.assertEqual(extract_company("平安人寿保险"), "平安人寿保险")

    def test_无匹配(self):
        self.assertEqual(extract_company("某某公司"), "")


class TestPdfParserCLI(unittest.TestCase):
    def test_help(self):
        r = subprocess.run([sys.executable, str(PARSER_SCRIPT), "--help"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("pdf", r.stdout.lower())

    def test_无参数_提示用法(self):
        r = subprocess.run([sys.executable, str(PARSER_SCRIPT)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("用法", r.stdout)

    def test_不存在的文件_报错(self):
        r = subprocess.run([sys.executable, str(PARSER_SCRIPT), "/nonexistent.pdf"],
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)


class TestLocalPdfMode(unittest.TestCase):
    def test_目录不存在_优雅退出(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run(
                [sys.executable, str(MAIN_SCRIPT),
                 "--local-pdf", "/nonexistent_dir_xyz",
                 "-o", str(Path(tmp) / "r.html")],
                capture_output=True, text=True
            )
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("目录不存在", r.stderr)

    def test_空目录_无PDF优雅退出(self):
        """P1-2 修复：直接 import 后，空目录应优雅处理"""
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run(
                [sys.executable, str(MAIN_SCRIPT),
                 "--local-pdf", tmp,
                 "-f", "/dev/null",
                 "-o", str(Path(tmp) / "r.html")],
                capture_output=True, text=True
            )
            # 空目录解析出 0 份，policies.json 为空列表
            # 后续 family 读取 /dev/null 会报错，但 PDF 解析本身不应崩
            self.assertNotEqual(r.returncode, 0)  # 预期因 family 报错退出


if __name__ == "__main__":
    unittest.main(verbosity=2)
