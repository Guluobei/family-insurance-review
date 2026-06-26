# -*- coding: utf-8 -*-
"""V3.3 新功能测试 ③ — --local-pdf / pdf_parser.py"""
import unittest
import subprocess
import sys
import tempfile
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# pdf_parser 必须能独立 import
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from pdf_parser import detect_kind, extract_amount, mask as pdf_mask, KIND_PATTERNS
    HAS_PARSER = True
except ImportError as e:
    HAS_PARSER = False
    print(f"⚠️ pdf_parser 不可 import: {e}")

PARSER_SCRIPT = Path(__file__).parent.parent / "pdf_parser.py"
MAIN_SCRIPT = Path(__file__).parent.parent / "insurance_review.py"


class TestDetectKind(unittest.TestCase):
    """险种识别测试 — 5 类全覆盖"""

    def test_重疾(self):
        self.assertEqual(detect_kind("平安重大疾病保险"), "重疾险")
        self.assertEqual(detect_kind("Critical Illness Coverage"), "重疾险")

    def test_医疗(self):
        self.assertEqual(detect_kind("百万医疗险"), "医疗险")
        self.assertEqual(detect_kind("住院医疗保险"), "医疗险")
        self.assertEqual(detect_kind("Medical Insurance"), "医疗险")

    def test_意外(self):
        self.assertEqual(detect_kind("综合意外伤害"), "意外险")
        self.assertEqual(detect_kind("Accident Plan"), "意外险")

    def test_寿险(self):
        self.assertEqual(detect_kind("定期寿险"), "寿险")
        self.assertEqual(detect_kind("Whole Life Insurance"), "寿险")

    def test_年金(self):
        self.assertEqual(detect_kind("养老年金险"), "年金险")
        self.assertEqual(detect_kind("Annuity Plan"), "年金险")

    def test_未知险种(self):
        self.assertEqual(detect_kind("某某奇怪的险种"), "其他")


class TestExtractAmount(unittest.TestCase):
    """保额抽取 + 单位换算"""

    def test_万元(self):
        text = "基本保额：50万元"
        self.assertEqual(extract_amount(text, r'(?:基本[保\s]?额|保\s*额)'), 500000)

    def test_万字(self):
        text = "保险金额：30万"
        self.assertEqual(extract_amount(text, r'(?:保险[金额\s]*|保\s*额)'), 300000)

    def test_纯数字元(self):
        text = "保费：12000元"
        self.assertEqual(extract_amount(text, r'保[费]?费'), 12000)

    def test_无匹配(self):
        self.assertEqual(extract_amount("其他文本", r'基本[保\s]?额'), 0)


class TestPdfParserCLI(unittest.TestCase):
    """pdf_parser.py CLI 测试"""

    def test_help(self):
        r = subprocess.run(
            [sys.executable, str(PARSER_SCRIPT), "--help"],
            capture_output=True, text=True
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("pdf", r.stdout.lower())

    def test_无参数_提示用法(self):
        r = subprocess.run(
            [sys.executable, str(PARSER_SCRIPT)],
            capture_output=True, text=True
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("用法", r.stdout)

    def test_不存在的文件_报错(self):
        r = subprocess.run(
            [sys.executable, str(PARSER_SCRIPT), "/nonexistent.pdf"],
            capture_output=True, text=True
        )
        self.assertNotEqual(r.returncode, 0)


class TestLocalPdfMode(unittest.TestCase):
    """--local-pdf 集成测试（不依赖真实 PDF，使用空目录测路径处理）"""

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
