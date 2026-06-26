# -*- coding: utf-8 -*-
"""
privacy.py — V3.4 共享隐私模块
单一数据源：mask / anonymize / KIND_PATTERNS / classify_by_text
消除 insurance_review.py 与 pdf_parser.py 的重复定义
"""

import re

# === 1. 险种关键词（单一数据源，不再分散两处） ===
KIND_PATTERNS = [
    ("重疾险", ["重疾", "重大疾病", "防癌", "critical illness", "critical", "cancer"]),
    ("医疗险", ["医疗", "住院", "百万医疗", "medical", "health"]),
    ("意外险", ["意外", "accident"]),
    ("寿险", ["寿险", "身故", "定期寿", "终身寿", "life", "whole life"]),
    ("年金险", ["年金", "养老", "教育金", "annuity", "pension"]),
]

def classify_by_text(text):
    """根据文本返回险种类别，供 classify() 和 detect_kind() 共用"""
    if not text:
        return "其他"
    t = str(text).lower()
    for kind, keys in KIND_PATTERNS:
        if any(k.lower() in t for k in keys):
            return kind
    return "其他"

# === 2. 隐私脱敏 ===
def mask(text):
    if text is None:
        return ""
    text = str(text)
    # 18位身份证（末尾可为 X）
    text = re.sub(r'(?<!\d)\d{17}[\dXx](?!\d)',
                  lambda m: m.group()[:6] + '****' + m.group()[-4:], text)
    # 16-19位银行卡
    text = re.sub(r'(?<!\d)\d{16,19}(?!\d)',
                  lambda m: '****' + m.group()[-4:], text)
    # 11位手机号
    text = re.sub(r'(?<!\d)1[3-9]\d{9}(?!\d)',
                  lambda m: m.group()[:3] + '****' + m.group()[-4:], text)
    return text

def anonymize(obj):
    """递归脱敏：支持 dict / list / str / int（修复 P1-1：数字型 ID 遗漏）"""
    if isinstance(obj, dict):
        return {k: anonymize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [anonymize(x) for x in obj]
    if isinstance(obj, str):
        return mask(obj)
    # P1-1 修复：11 位以上数字也可能是身份证/银行卡
    if isinstance(obj, int) and len(str(abs(obj))) >= 11:
        return mask(str(obj))
    return obj
