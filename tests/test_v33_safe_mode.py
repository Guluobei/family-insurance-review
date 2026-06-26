# -*- coding: utf-8 -*-
"""V3.3 新功能测试 ① — --safe-mode / 通用 CLI 参数"""
import unittest
import subprocess
import sys
import os
import tempfile
import json
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "insurance_review.py"

class TestSafeMode(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.policies = Path(self.tmp) / "p.json"
        self.family = Path(self.tmp) / "f.json"
        self.output = Path(self.tmp) / "r.html"
        self.policies.write_text(json.dumps([
            {"name": "重疾", "holder": "张三", "coverage": 300000,
             "premium": 12000, "currency": "CNY"}
        ], ensure_ascii=False), encoding="utf-8")
        self.family.write_text(json.dumps(
            {"annual_income": 500000, "debt": 1000000}
        ), encoding="utf-8")

    def test_help_列出所有参数(self):
        """--help 应列出 V3.3 全部 5 个参数"""
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True, text=True
        )
        self.assertEqual(r.returncode, 0)
        for flag in ["--safe-mode", "--anonymize", "--local-pdf", "-p", "-f", "-o"]:
            self.assertIn(flag, r.stdout, f"缺少参数 {flag}")

    def test_safe_mode_提示(self):
        """--safe-mode 应输出安全模式提示"""
        r = subprocess.run(
            [sys.executable, str(SCRIPT),
             "-p", str(self.policies), "-f", str(self.family),
             "-o", str(self.output), "--safe-mode"],
            capture_output=True, text=True
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("安全模式", r.stdout)
        self.assertIn("纯本地运行", r.stdout)

    def test_output_参数化(self):
        """-o 应支持自定义输出路径"""
        custom = Path(self.tmp) / "custom_report.html"
        r = subprocess.run(
            [sys.executable, str(SCRIPT),
             "-p", str(self.policies), "-f", str(self.family),
             "-o", str(custom)],
            capture_output=True, text=True
        )
        self.assertEqual(r.returncode, 0)
        self.assertTrue(custom.exists(), f"报告未生成到 {custom}")
        content = custom.read_text(encoding="utf-8")
        self.assertIn("家庭保单检视报告 V3.3", content)

    def test_无效路径_优雅退出(self):
        """-p 指向不存在的文件应优雅退出"""
        r = subprocess.run(
            [sys.executable, str(SCRIPT),
             "-p", "/nonexistent.json", "-f", str(self.family),
             "-o", str(self.output)],
            capture_output=True, text=True
        )
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
