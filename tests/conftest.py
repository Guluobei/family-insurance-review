"""pytest 共享 fixture 与路径配置"""
import sys
from pathlib import Path

# 把项目根目录加入 sys.path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from insurance_review import (
    mask, classify, valid, is_group, to_cny,
    diagnose, detect_conflicts, render, main
)


# ============== Fixture：标准家庭 ==============
@pytest.fixture
def standard_family():
    return {
        "members": ["户主", "配偶", "子女"],
        "annual_income": 500000,
        "debt": 2000000,
        "dependents": 1,
    }


@pytest.fixture
def standard_policies():
    return [
        {"holder": "户主", "name": "平安寿险", "type": "寿险",
         "coverage": 1000000, "premium": 12000, "currency": "CNY"},
        {"holder": "配偶", "name": "友邦重疾", "type": "重疾",
         "coverage": 300000, "premium": 8000, "currency": "CNY"},
        {"holder": "户主", "name": "众安医疗", "type": "医疗",
         "coverage": 6000000, "premium": 800, "currency": "CNY"},
        {"holder": "户主", "name": "平安医疗", "type": "医疗",
         "coverage": 6000000, "premium": 600, "currency": "CNY"},
    ]


@pytest.fixture
def tmp_policies_file(tmp_path, standard_policies):
    """把 policies 写入临时文件"""
    import json
    f = tmp_path / "policies.json"
    f.write_text(json.dumps(standard_policies, ensure_ascii=False), encoding="utf-8")
    return f


@pytest.fixture
def tmp_family_file(tmp_path, standard_family):
    import json
    f = tmp_path / "family.json"
    f.write_text(json.dumps(standard_family, ensure_ascii=False), encoding="utf-8")
    return f
