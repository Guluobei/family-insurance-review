"""测试 8：fuzzing + property-based testing
- fuzzing：随机生成 1000 份保单，验证程序不崩溃
- property-based：用 hypothesis 验证数学不变量
"""
import pytest
import random
import string
from hypothesis import given, settings, strategies as st
from insurance_review import (
    mask, classify, valid, is_group, to_cny,
    diagnose, detect_conflicts, render, FX
)


# ============== Fuzzing：随机 1000 份保单 ==============
class TestFuzzing:
    """随机保单模糊测试"""

    def test_fuzz_1000_random_policies(self, tmp_path):
        """生成 1000 个随机保单，验证不崩溃"""
        types = ["寿险", "重疾", "医疗", "意外", "年金", "其他", ""]
        currencies = ["CNY", "HKD", "USD", "EUR", "INVALID"]
        holders = ["户主", "配偶", "子女", "父母",
                   "某科技公司有限公司", "AIA Co. Ltd.", "张三 110101199001011234"]

        for i in range(1000):
            policies = []
            for j in range(random.randint(0, 20)):
                p = {
                    "holder": random.choice(holders),
                    "name": random.choice(["平安寿险", "重疾险", "医疗险", "Critical Illness"]),
                    "type": random.choice(types),
                    "coverage": random.randint(0, 10000000),
                    "premium": random.randint(-10, 100000),
                    "currency": random.choice(currencies),
                    "cash_value": random.randint(0, 1000000),
                }
                policies.append(p)

            family = {
                "members": ["h1", "h2"],
                "annual_income": random.randint(0, 10000000),
                "debt": random.randint(0, 50000000),
                "dependents": random.randint(0, 5),
            }

            # 不应崩溃
            try:
                for p in policies:
                    p["kind"] = classify(p) if valid(p) else "无效"
                result = diagnose(policies, family)
                warnings = detect_conflicts(policies)
                # render 也应不崩溃
                output = tmp_path / f"fuzz_{i}.html"
                render(policies, family, result, warnings, str(output))
                assert output.exists()
            except Exception as e:
                pytest.fail(f"迭代 {i} 崩溃: {type(e).__name__}: {e}")

    def test_fuzz_extreme_values(self):
        """极值测试：0、负数、极大数"""
        extreme_policies = [
            {"holder": "h", "name": "寿险", "type": "寿险", "coverage": 0, "premium": 0},
            {"holder": "h", "name": "寿险", "type": "寿险", "coverage": 10**18, "premium": 10**12},
            {"holder": "h", "name": "寿险", "type": "寿险", "coverage": -100, "premium": 1000},
            {"holder": "h", "name": "寿险", "type": "寿险", "coverage": 100, "premium": -100},
        ]
        family = {"members": [], "annual_income": 0, "debt": 0, "dependents": 0}
        for p in extreme_policies:
            p["kind"] = classify(p) if valid(p) else "无效"
        # 不应崩溃
        result = diagnose(extreme_policies, family)
        assert isinstance(result, dict)
        assert all(k in result for k in ["寿险缺口", "重疾缺口", "医疗险重复", "年金险合计", "可质押现金价值"])


# ============== Property-based：数学不变量 ==============
class TestProperties:
    """数学不变量测试"""

    @given(st.text(min_size=0, max_size=200))
    @settings(max_examples=200, deadline=None)
    def test_mask_never_crashes(self, text):
        """mask() 对任何字符串都不崩溃"""
        result = mask(text)
        assert isinstance(result, str)

    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=200, deadline=None)
    def test_classify_returns_known_category(self, name):
        """classify() 总是返回已知类别"""
        result = classify({"name": name, "type": ""})
        assert result in ["重疾险", "医疗险", "意外险", "寿险", "年金险", "其他"]

    @given(
        st.integers(min_value=0, max_value=10**9),
        st.sampled_from(["CNY", "HKD", "USD", "EUR", "UNKNOWN"])
    )
    @settings(max_examples=100, deadline=None)
    def test_to_cny_idempotent(self, amount, currency):
        """to_cny 总是返回数字"""
        result = to_cny(amount, currency)
        assert isinstance(result, (int, float))
        assert result >= 0

    @given(
        st.lists(st.integers(min_value=100, max_value=10**7), min_size=0, max_size=10),
        st.integers(min_value=0, max_value=10**7),
        st.integers(min_value=0, max_value=10**7),
    )
    @settings(max_examples=100, deadline=None)
    def test_life_gap_is_non_negative(self, coverages, income, debt):
        """寿险缺口永远 ≥ 0（不变量）"""
        policies = [
            {"holder": "h", "name": f"寿险{i}", "type": "寿险",
             "coverage": c, "premium": 1000}
            for i, c in enumerate(coverages)
        ]
        family = {"members": ["h"], "annual_income": income, "debt": debt, "dependents": 0}
        for p in policies:
            p["kind"] = classify(p) if valid(p) else "无效"
        result = diagnose(policies, family)
        assert result["寿险缺口"] >= 0
        assert result["重疾缺口"] >= 0
        assert result["年金险合计"] >= 0
        assert result["可质押现金价值"] >= 0

    @given(
        st.lists(st.floats(min_value=0, max_value=10**7, allow_nan=False, allow_infinity=False),
                 min_size=0, max_size=20),
        st.sampled_from(["CNY", "HKD", "USD", "EUR"])
    )
    @settings(max_examples=100, deadline=None)
    def test_cash_value_aggregation_is_sum(self, cash_values, currency):
        """现金价值聚合 = 单个保单之和（不变量）"""
        policies = []
        for cv in cash_values:
            policies.append({
                "holder": "h", "name": "年金", "type": "年金",
                "coverage": 0, "premium": 1000, "cash_value": cv,
                "currency": currency
            })
        family = {"members": ["h"], "annual_income": 100000, "debt": 0, "dependents": 0}
        for p in policies:
            p["kind"] = classify(p) if valid(p) else "无效"
        result = diagnose(policies, family)
        # 现金价值聚合应等于 sum
        fx = FX.get(currency, 1.0)
        expected = sum(cv * fx for cv in cash_values)
        assert abs(result["可质押现金价值"] - expected) < 0.01
