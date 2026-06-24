"""测试 3：币种换算 to_cny()"""
import pytest
from insurance_review import to_cny, FX


class TestCurrency:
    """多币种换算测试"""

    def test_cny_passthrough(self):
        """人民币原值"""
        assert to_cny(100, "CNY") == 100
        assert to_cny(0, "CNY") == 0
        assert to_cny(1000000, "CNY") == 1000000

    def test_hkd_exchange(self):
        """港币换算"""
        assert to_cny(100, "HKD") == 93.0
        # 默认汇率 0.93
        assert to_cny(100, "HKD") == 100 * FX["HKD"]

    def test_usd_exchange(self):
        """美元换算"""
        assert to_cny(100, "USD") == 725.0
        assert to_cny(100, "USD") == 100 * FX["USD"]

    def test_eur_exchange(self):
        """欧元换算"""
        assert to_cny(100, "EUR") == 785.0
        assert to_cny(100, "EUR") == 100 * FX["EUR"]

    def test_unknown_currency_defaults_to_1(self):
        """未知币种默认按 1.0 处理"""
        assert to_cny(100, "JPY") == 100
        assert to_cny(100, "XYZ") == 100

    def test_no_currency_defaults_to_1(self):
        """无币种字段默认按 1.0 处理"""
        assert to_cny(100, "") == 100
        assert to_cny(100, None) == 100
