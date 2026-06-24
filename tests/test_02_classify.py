"""测试 2：险种分类 classify() - 中英文 + 边界"""
import pytest
from insurance_review import classify


class TestClassify:
    """险种分类测试"""

    @pytest.mark.parametrize("name,expected", [
        # 中文产品
        ("平安平安福终身寿险", "寿险"),
        ("中国人寿康宁重疾险", "重疾险"),
        ("友邦友如意重疾", "重疾险"),
        ("众安尊享e生医疗险", "医疗险"),
        ("平安e生保医疗", "医疗险"),
        ("平安意外险", "意外险"),
        ("苏黎世意外保险", "意外险"),
        ("平安颐享年年年金险", "年金险"),
        ("泰康养老年金", "年金险"),
        # 英文产品
        ("AIA Critical Illness Plan", "重疾险"),
        ("Prudential Life Insurance", "寿险"),
        ("Manulife Health Medical Plus", "医疗险"),
        ("AXA Accident Care", "意外险"),
        ("Allianz Annuity Plan", "年金险"),
        # 防癌属于重疾
        ("平安防癌险", "重疾险"),
        # 边界 case
        ("某某公司XX产品", "其他"),
    ])
    def test_classify(self, name, expected):
        result = classify({"name": name, "type": ""})
        assert result == expected, f"'{name}' 期望 {expected}，实际 {result}"

    def test_classify_with_type_field(self):
        """type 字段参与分类"""
        assert classify({"name": "", "type": "重疾"}) == "重疾险"

    def test_classify_combined(self):
        """name + type 组合分类"""
        assert classify({"name": "平安", "type": "寿险"}) == "寿险"

    def test_classify_case_insensitive(self):
        """英文大小写不敏感"""
        assert classify({"name": "CRITICAL ILLNESS", "type": ""}) == "重疾险"
        assert classify({"name": "critical illness", "type": ""}) == "重疾险"
