"""测试 4：保额诊断 diagnose() - 标准/0 保单/高净值/混合场景"""
import pytest
from insurance_review import diagnose, classify, valid


def _classify_all(policies):
    for p in policies:
        p["kind"] = classify(p) if valid(p) else "无效"
    return policies


class TestDiagnose:
    """保额诊断测试"""

    def test_standard_family_4_policies(self, standard_policies, standard_family):
        """标准 4 份保单家庭"""
        _classify_all(standard_policies)
        result = diagnose(standard_policies, standard_family)
        # 寿险需要：500000*10 + 2000000 = 7,000,000
        # 寿险持有：1,000,000
        # 缺口：6,000,000
        assert result["寿险缺口"] == pytest.approx(6000000)
        # 重疾已持有 300,000，缺口 200,000
        assert result["寿险缺口"] == 6000000
        assert result["重疾缺口"] == 200000
        assert result["医疗险重复"] is True
        assert result["年金险合计"] == 0
        assert result["可质押现金价值"] == 0

    def test_zero_policies(self, standard_family):
        """0 保单边界"""
        result = diagnose([], standard_family)
        assert result["寿险缺口"] == 7000000
        assert result["重疾缺口"] == 500000
        assert result["医疗险重复"] is False

    def test_zero_income_zero_debt(self):
        """0 收入 0 负债家庭"""
        family = {"members": ["x"], "annual_income": 0, "debt": 0, "dependents": 0}
        result = diagnose([], family)
        assert result["寿险缺口"] == 0
        assert result["重疾缺口"] == 500000

    def test_high_net_worth_9_policies(self):
        """高净值 9 份保单"""
        policies = [
            {"holder": "h1", "name": "重疾A", "type": "重疾", "coverage": 2000000, "premium": 50000},
            {"holder": "h1", "name": "重疾B", "type": "重疾", "coverage": 1000000, "premium": 30000},
            {"holder": "h1", "name": "寿险A", "type": "寿险", "coverage": 5000000, "premium": 40000},
            {"holder": "h2", "name": "寿险B", "type": "寿险", "coverage": 3000000, "premium": 25000},
            {"holder": "h1", "name": "医疗A", "type": "医疗", "coverage": 6000000, "premium": 1500},
            {"holder": "h2", "name": "医疗B", "type": "医疗", "coverage": 6000000, "premium": 1500},
            {"holder": "h3", "name": "医疗C", "type": "医疗", "coverage": 6000000, "premium": 800},
            {"holder": "h1", "name": "医疗D", "type": "医疗", "coverage": 6000000, "premium": 1000},
            {"holder": "h1", "name": "意外险", "type": "意外", "coverage": 1000000, "premium": 500},
        ]
        family = {"members": ["h1","h2","h3","h4"], "annual_income": 5000000, "debt": 10000000, "dependents": 3}
        _classify_all(policies)
        result = diagnose(policies, family)
        # 寿险需要：5,000,000*10 + 10,000,000 = 60,000,000
        # 寿险持有：5,000,000 + 3,000,000 = 8,000,000
        # 缺口：52,000,000
        assert result["寿险缺口"] == 52000000
        # 重疾合计 3,000,000 > 500,000，缺口 0
        assert result["重疾缺口"] == 0
        # 医疗险 4 份
        assert result["医疗险重复"] is True

    def test_critical_fully_covered(self):
        """重疾完全覆盖"""
        policies = [{"holder": "h", "name": "重疾", "type": "重疾", "coverage": 1000000, "premium": 20000}]
        family = {"members": ["h"], "annual_income": 100000, "debt": 0, "dependents": 0}
        _classify_all(policies)
        result = diagnose(policies, family)
        assert result["重疾缺口"] == 0

    def test_critical_zero_coverage_triggers_full_gap(self):
        """重疾 0 保额触发 50 万全部缺口"""
        policies = [{"holder": "h", "name": "寿险", "type": "寿险", "coverage": 1000000, "premium": 10000}]
        family = {"members": ["h"], "annual_income": 100000, "debt": 0, "dependents": 0}
        _classify_all(policies)
        result = diagnose(policies, family)
        # 没有重疾险，触发全部 50 万缺口
        assert result["重疾缺口"] == 500000

    def test_annuity_does_not_count_as_critical(self):
        """年金险不计入重疾缺口"""
        policies = [{"holder": "h", "name": "年金", "type": "年金", "coverage": 0, "premium": 100000}]
        family = {"members": ["h"], "annual_income": 100000, "debt": 0, "dependents": 0}
        _classify_all(policies)
        result = diagnose(policies, family)
        # 年金险不参与重疾缺口计算
        assert result["重疾缺口"] == 500000
        # 但年金险合计单独列出
        assert result["年金险合计"] == 0  # 因为 coverage=0

    def test_cash_value_aggregated(self):
        """现金价值汇总"""
        policies = [
            {"holder": "h", "name": "年金", "type": "年金", "coverage": 0, "premium": 50000, "cash_value": 300000},
            {"holder": "h", "name": "年金2", "type": "年金", "coverage": 0, "premium": 30000, "cash_value": 200000},
        ]
        family = {"members": ["h"], "annual_income": 100000, "debt": 0, "dependents": 0}
        _classify_all(policies)
        result = diagnose(policies, family)
        assert result["可质押现金价值"] == 500000
