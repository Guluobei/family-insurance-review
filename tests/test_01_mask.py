"""测试 1：脱敏函数 mask() - 8 个边界场景"""
import pytest
from insurance_review import mask


class TestMask:
    """脱敏函数测试"""

    def test_id_card_18_digits(self):
        """18 位身份证：保留前 6 + 后 4"""
        assert mask("110101199001011234") == "110101****1234"

    def test_id_card_with_x(self):
        """身份证末位 X"""
        assert mask("11010119900101123X") == "110101****123X"

    def test_bank_card_16_digits(self):
        """16 位银行卡：仅保留后 4"""
        assert mask("6225880138888888") == "****8888"

    def test_bank_card_19_digits(self):
        """19 位银行卡"""
        result = mask("6225880138888888888")
        assert result.startswith("****")
        assert result.endswith("8888")

    def test_phone_11_digits(self):
        """11 位手机号：前 3 + 后 4"""
        assert mask("13800138000") == "138****8000"

    def test_empty_string(self):
        """空字符串"""
        assert mask("") == ""

    def test_none_input(self):
        """None 输入"""
        assert mask(None) == ""

    def test_normal_text_unchanged(self):
        """普通文本不受影响"""
        assert mask("平安保险") == "平安保险"
        assert mask("寿险") == "寿险"

    def test_mixed_string(self):
        """混合字符串中身份证被脱敏"""
        result = mask("姓名张三 110101199001011234 余额 100")
        assert "110101****1234" in result
        assert "姓名张三" in result
        assert "100" in result

    def test_multiple_id_cards(self):
        """多个身份证都被脱敏"""
        result = mask("张三 110101199001011234 李四 110101198501011235")
        assert "110101****1234" in result
        assert "110101****1235" in result
        # 原始完整身份证不应存在
        assert "110101199001011234" not in result
        assert "110101198501011235" not in result

    def test_sensitive_data_in_dict(self):
        """脱敏后字典不包含敏感字段（关键安全验证）"""
        policies = [
            {"holder": "张三 110101199001011234 13800138000 6225880138888888",
             "name": "重疾险", "type": "重疾", "coverage": 200000, "premium": 5000}
        ]
        for p in policies:
            p["holder"] = mask(p["holder"])
        holder = policies[0]["holder"]
        assert "110101199001011234" not in holder
        assert "13800138000" not in holder
        assert "6225880138888888" not in holder
        assert "****" in holder
