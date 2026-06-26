# -*- coding: utf-8 -*-
"""V3.4 测试 ③ — --safe-mode / CLI 参数 / 错误处理"""
import unittest
import subprocess
import sys
import tempfile
import json
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "insurance_review.py"


class TestCLI(unittest.TestCase):
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

    def _run(self, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT),
             "-p", str(self.policies), "-f", str(self.family),
             "-o", str(self.output)] + list(extra),
            capture_output=True, text=True
        )

    def test_help_列出所有参数(self):
        r = subprocess.run([sys.executable, str(SCRIPT), "--help"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        for flag in ["--safe-mode", "--anonymize", "--local-pdf", "-p", "-f", "-o"]:
            self.assertIn(flag, r.stdout)

    def test_safe_mode_拦截代理(self):
        """P1-3 修复：safe-mode 应真正禁用代理"""
        r = self._run("--safe-mode")
        self.assertEqual(r.returncode, 0)
        self.assertIn("禁用代理", r.stdout)

    def test_output_参数化(self):
        custom = Path(self.tmp) / "custom.html"
        r = self._run("-o", str(custom))
        self.assertTrue(custom.exists())
        content = custom.read_text(encoding="utf-8")
        self.assertIn("V3.4", content)

    def test_保单文件不存在_优雅退出(self):
        """P2 修复：文件不存在应有友好提示"""
        r = subprocess.run(
            [sys.executable, str(SCRIPT),
             "-p", "/nonexistent.json", "-f", str(self.family),
             "-o", str(self.output)],
            capture_output=True, text=True
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("不存在", r.stderr)

    def test_JSON格式错误_优雅退出(self):
        """P2 修复：JSON 格式错误应有友好提示"""
        bad = Path(self.tmp) / "bad.json"
        bad.write_text("not a json {{{", encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(SCRIPT),
             "-p", str(bad), "-f", str(self.family),
             "-o", str(self.output)],
            capture_output=True, text=True
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("JSON", r.stderr)

    def test_报告不含True(self):
        """P0-3 修复：报告中不应出现 ¥True"""
        # 2 份医疗险触发医疗险重复=True
        self.policies.write_text(json.dumps([
            {"name": "医疗", "holder": "张三", "coverage": 100, "premium": 800, "currency": "CNY"},
            {"name": "医疗", "holder": "李四", "coverage": 100, "premium": 500, "currency": "CNY"},
        ], ensure_ascii=False), encoding="utf-8")
        r = self._run()
        self.assertEqual(r.returncode, 0)
        content = self.output.read_text(encoding="utf-8")
        self.assertNotIn("¥True", content)
        self.assertNotIn("¥False", content)

    def test_金额千分位(self):
        """P0-3 修复：金额应显示千分位"""
        r = self._run()
        content = self.output.read_text(encoding="utf-8")
        # 寿险缺口 = 500000*10+1000000 - 0 = 6000000，应显示 ¥6,000,000
        self.assertIn("6,000,000", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
