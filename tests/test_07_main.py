"""测试 7：主入口 main() - 端到端集成"""
import pytest
import json
from pathlib import Path
from insurance_review import main


class TestMain:
    """主入口端到端测试"""

    def test_main_end_to_end(self, tmp_path, monkeypatch):
        """端到端：main() 应读取 JSON、生成报告"""
        policies = [
            {"holder": "户主", "name": "平安寿险", "type": "寿险",
             "coverage": 1000000, "premium": 12000, "currency": "CNY"},
            {"holder": "配偶", "name": "友邦重疾", "type": "重疾",
             "coverage": 300000, "premium": 8000, "currency": "CNY"},
        ]
        family = {"members": ["户主", "配偶"], "annual_income": 500000,
                  "debt": 2000000, "dependents": 1}

        # 写入临时文件
        policies_file = tmp_path / "policies.json"
        family_file = tmp_path / "family.json"
        policies_file.write_text(json.dumps(policies, ensure_ascii=False), encoding="utf-8")
        family_file.write_text(json.dumps(family, ensure_ascii=False), encoding="utf-8")

        # 切换到临时目录
        monkeypatch.chdir(tmp_path)

        # 执行 main
        main()

        # 验证 report.html 生成
        report = tmp_path / "report.html"
        assert report.exists()
        content = report.read_text(encoding="utf-8")
        assert "家庭保单检视报告" in content
        assert "寿险缺口" in content

    def test_main_with_empty_policies(self, tmp_path, monkeypatch):
        """空保单列表"""
        policies_file = tmp_path / "policies.json"
        family_file = tmp_path / "family.json"
        policies_file.write_text("[]", encoding="utf-8")
        family_file.write_text(json.dumps({"members": [], "annual_income": 0, "debt": 0, "dependents": 0}), encoding="utf-8")

        monkeypatch.chdir(tmp_path)
        main()

        report = tmp_path / "report.html"
        assert report.exists()
        content = report.read_text(encoding="utf-8")
        # 空保单时无冲突
        assert "无重大冲突" in content

    def test_main_classifies_invalid_policies(self, tmp_path, monkeypatch):
        """无效保单（保费 0）应被标记为无效"""
        policies = [
            {"holder": "h", "name": "正常", "type": "寿险", "coverage": 100000, "premium": 1000},
            {"holder": "h", "name": "异常", "type": "寿险", "coverage": 100000, "premium": 0},
        ]
        family = {"members": ["h"], "annual_income": 100000, "debt": 0, "dependents": 0}
        policies_file = tmp_path / "policies.json"
        family_file = tmp_path / "family.json"
        policies_file.write_text(json.dumps(policies, ensure_ascii=False), encoding="utf-8")
        family_file.write_text(json.dumps(family, ensure_ascii=False), encoding="utf-8")

        monkeypatch.chdir(tmp_path)
        main()

        report = tmp_path / "report.html"
        content = report.read_text(encoding="utf-8")
        # 异常保单应在报告中标记为"无效"
        assert "无效" in content
        # 仅 1 份有效保单
        assert "有效保单: 1" in content
