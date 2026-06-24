"""测试 6：HTML 报告 render() - 端到端 + 敏感数据反向验证"""
import pytest
import re
from pathlib import Path
from insurance_review import render, mask, classify, valid, diagnose, detect_conflicts


def _classify_all(policies):
    for p in policies:
        p["kind"] = classify(p) if valid(p) else "无效"
    return policies


class TestRender:
    """HTML 报告生成测试"""

    def test_render_creates_file(self, tmp_path, standard_policies, standard_family):
        """render 应创建文件"""
        _classify_all(standard_policies)
        for p in standard_policies:
            p["holder"] = mask(p["holder"])
        result = diagnose(standard_policies, standard_family)
        warnings = detect_conflicts(standard_policies)
        output = tmp_path / "report.html"
        render(standard_policies, standard_family, result, warnings, str(output))
        assert output.exists()
        assert output.stat().st_size > 0

    def test_render_contains_required_sections(self, tmp_path, standard_policies, standard_family):
        """报告应包含必要章节"""
        _classify_all(standard_policies)
        for p in standard_policies:
            p["holder"] = mask(p["holder"])
        result = diagnose(standard_policies, standard_family)
        warnings = detect_conflicts(standard_policies)
        output = tmp_path / "report.html"
        render(standard_policies, standard_family, result, warnings, str(output))
        content = output.read_text(encoding="utf-8")
        assert "家庭保单检视报告" in content
        assert "保单清单" in content
        assert "保障缺口" in content
        assert "风险提示" in content
        assert "依据" in content

    def test_render_contains_gap_values(self, tmp_path, standard_policies, standard_family):
        """报告应包含缺口数值"""
        _classify_all(standard_policies)
        for p in standard_policies:
            p["holder"] = mask(p["holder"])
        result = diagnose(standard_policies, standard_family)
        warnings = detect_conflicts(standard_policies)
        output = tmp_path / "report.html"
        render(standard_policies, standard_family, result, warnings, str(output))
        content = output.read_text(encoding="utf-8")
        assert "寿险缺口" in content
        assert "重疾缺口" in content
        assert "医疗险重复" in content

    def test_render_no_sensitive_data_leak(self, tmp_path):
        """关键安全测试：原始敏感数据不应出现在报告中"""
        sensitive_policies = [
            {"holder": "张三 110101199001011234 13800138000 6225880138888888",
             "name": "重疾险", "type": "重疾", "coverage": 200000, "premium": 5000},
        ]
        family = {"members": ["h"], "annual_income": 100000, "debt": 500000, "dependents": 1}
        # 关键：先脱敏
        for p in sensitive_policies:
            p["holder"] = mask(p["holder"])
        _classify_all(sensitive_policies)
        result = diagnose(sensitive_policies, family)
        warnings = detect_conflicts(sensitive_policies)
        output = tmp_path / "report.html"
        render(sensitive_policies, family, result, warnings, str(output))
        content = output.read_text(encoding="utf-8")
        # 原始敏感数据必须不在报告中
        assert "110101199001011234" not in content, "身份证号泄露"
        assert "13800138000" not in content, "手机号泄露"
        assert "6225880138888888" not in content, "银行卡号泄露"
        # 脱敏标记必须存在
        assert "****" in content, "脱敏标记缺失"

    def test_render_currency_column(self, tmp_path):
        """报告应包含币种列"""
        policies = [
            {"holder": "h", "name": "AIA寿险", "type": "寿险",
             "coverage": 1000000, "premium": 20000, "currency": "HKD"},
            {"holder": "h", "name": "境内重疾", "type": "重疾",
             "coverage": 500000, "premium": 15000, "currency": "CNY"},
        ]
        family = {"members": ["h"], "annual_income": 500000, "debt": 1000000, "dependents": 1}
        _classify_all(policies)
        result = diagnose(policies, family)
        warnings = detect_conflicts(policies)
        output = tmp_path / "report.html"
        render(policies, family, result, warnings, str(output))
        content = output.read_text(encoding="utf-8")
        assert "HKD" in content
        assert "CNY" in content
        assert "汇率参考" in content

    def test_render_annuity_summary(self, tmp_path):
        """年金险应单独显示"""
        policies = [
            {"holder": "h", "name": "平安年金", "type": "年金",
             "coverage": 0, "premium": 100000, "currency": "CNY"},
        ]
        family = {"members": ["h"], "annual_income": 100000, "debt": 0, "dependents": 0}
        _classify_all(policies)
        result = diagnose(policies, family)
        warnings = detect_conflicts(policies)
        output = tmp_path / "report.html"
        render(policies, family, result, warnings, str(output))
        content = output.read_text(encoding="utf-8")
        assert "年金险" in content

    def test_render_html_validity(self, tmp_path, standard_policies, standard_family):
        """生成的 HTML 应有基本结构"""
        _classify_all(standard_policies)
        result = diagnose(standard_policies, standard_family)
        warnings = detect_conflicts(standard_policies)
        output = tmp_path / "report.html"
        render(standard_policies, standard_family, result, warnings, str(output))
        content = output.read_text(encoding="utf-8")
        # HTML 标签平衡检查
        assert content.count("<html>") == 1
        assert content.count("</html>") == 1
        assert content.count("<body>") == 1
        assert content.count("</body>") == 1
        assert content.count("<table>") == 1
        assert content.count("</table>") == 1
