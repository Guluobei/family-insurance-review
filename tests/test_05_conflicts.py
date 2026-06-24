"""测试 5：冲突检测 detect_conflicts() - 医疗险重复/团险/质押"""
import pytest
from insurance_review import detect_conflicts, classify, valid, is_group


def _classify_all(policies):
    for p in policies:
        p["kind"] = classify(p) if valid(p) else "无效"
    return policies


class TestIsGroup:
    """团险识别测试"""

    @pytest.mark.parametrize("holder,expected", [
        ("某科技公司有限公司", True),
        ("某科技集团有限公司", True),
        ("AIA Co. Ltd.", True),
        ("Prudential Inc.", True),
        ("Manulife Group", True),
        ("户主", False),
        ("配偶", False),
        ("张三", False),
    ])
    def test_is_group(self, holder, expected):
        assert is_group({"holder": holder}) is expected


class TestDetectConflicts:
    """冲突检测测试"""

    def test_no_medical_no_conflict(self):
        """无医疗险：无冲突"""
        policies = [
            {"holder": "h", "name": "寿险", "type": "寿险", "coverage": 100000, "premium": 1000},
        ]
        _classify_all(policies)
        assert detect_conflicts(policies) == []

    def test_one_medical_no_conflict(self):
        """1 份医疗险：无冲突"""
        policies = [
            {"holder": "h", "name": "医疗", "type": "医疗", "coverage": 6000000, "premium": 800},
        ]
        _classify_all(policies)
        warnings = detect_conflicts(policies)
        assert not any("医疗险" in w for w in warnings)

    def test_two_medical_triggers_warning(self):
        """2 份医疗险：触发冲突"""
        policies = [
            {"holder": "h", "name": "医疗A", "type": "医疗", "coverage": 6000000, "premium": 800},
            {"holder": "h", "name": "医疗B", "type": "医疗", "coverage": 6000000, "premium": 600},
        ]
        _classify_all(policies)
        warnings = detect_conflicts(policies)
        assert any("2 份" in w and "医疗险" in w for w in warnings)

    def test_four_medical_triggers_warning(self):
        """4 份医疗险：触发冲突"""
        policies = [
            {"holder": "h", "name": f"医疗{i}", "type": "医疗", "coverage": 6000000, "premium": 1000}
            for i in range(4)
        ]
        _classify_all(policies)
        warnings = detect_conflicts(policies)
        assert any("4 份" in w for w in warnings)

    def test_high_cash_value_triggers_loan_alert(self):
        """高现金价值触发质押贷款提示"""
        policies = [
            {"holder": "h", "name": "年金", "type": "年金", "coverage": 0,
             "premium": 50000, "cash_value": 300000}
        ]
        _classify_all(policies)
        warnings = detect_conflicts(policies)
        assert any("质押" in w for w in warnings)
        assert any("300000" in w for w in warnings)

    def test_low_cash_value_no_loan_alert(self):
        """低现金价值不触发质押提示"""
        policies = [
            {"holder": "h", "name": "年金", "type": "年金", "coverage": 0,
             "premium": 5000, "cash_value": 50000}
        ]
        _classify_all(policies)
        warnings = detect_conflicts(policies)
        assert not any("质押" in w for w in warnings)

    def test_group_excluded_from_medical_count(self):
        """团险不计入个人医疗险数量"""
        policies = [
            {"holder": "h", "name": "医疗A", "type": "医疗", "coverage": 6000000, "premium": 800},
            {"holder": "某科技公司有限公司", "name": "团体医疗", "type": "医疗",
             "coverage": 2000000, "premium": 0},  # 团险保费 0，会被 valid 过滤
        ]
        _classify_all(policies)
        # 仅 1 份有效保单（团险被过滤）
        warnings = detect_conflicts(policies)
        # 团险保费 0 时被 valid 过滤，不会触发医疗险重复
        # 但可能触发"团险已排除"提示
        medical_warnings = [w for w in warnings if "医疗险" in w and "份" in w]
        assert len(medical_warnings) == 0

    def test_invalid_premium_filtered(self):
        """异常保费保单被过滤"""
        policies = [
            {"holder": "h", "name": "寿险", "type": "寿险", "coverage": 100000, "premium": 1000},
            {"holder": "h", "name": "测试0", "type": "寿险", "coverage": 100000, "premium": 0},
            {"holder": "h", "name": "测试负", "type": "寿险", "coverage": 100000, "premium": -100},
        ]
        _classify_all(policies)
        # 只有 1 份有效保单
        warnings = detect_conflicts(policies)
        # 异常保单不应触发额外冲突
        assert len(warnings) == 0
