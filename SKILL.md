---
name: family-insurance-review
description: 家庭保单自助检视工具。覆盖保单分类、保额诊断、冲突检测、HTML 报告生成。内置隐私脱敏、币种换算、团险识别、质押贷款提示。
version: 3.2
author: TRAE Skill Architect
license: MIT
platforms:
  trae: true
  claude-code: true
  opencode: true
  codex: true
  cursor: true
triggers:
  - 保单检视
  - 家庭保险
  - policy review
  - insurance analysis
privacy-tier: high
requires:
  python: ">=3.8"
  dependencies: []
---

# 家庭保单检视 Skill V3.2

## 隐私保护（强制）

保单属于敏感个人信息（依据《个人信息保护法》第 4 条）。L4-L5 字段（身份证、银行卡、健康告知）**禁止**进入 AI 助手上下文。所有分析在本地沙盒完成，不上传云端。

## 工作流

1. 用户提供 `policies.json` 和 `family.json`
2. Skill 执行 `python insurance_review.py`
3. 输出 `report.html` 到工作目录

## 输入格式

### policies.json

```json
[
  {
    "holder": "户主",
    "name": "平安平安福终身寿险",
    "type": "寿险",
    "coverage": 1000000,
    "premium": 12000,
    "currency": "CNY"
  }
]
```

### family.json

```json
{
  "members": ["户主", "配偶", "子女"],
  "annual_income": 500000,
  "debt": 2000000,
  "dependents": 1
}
```

## 输出

- `report.html`：可视化报告（含保障缺口、风险提示）

## 字段说明

| 字段 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| holder | 是 | - | 投保人（团险填公司名） |
| name | 是 | - | 产品名称 |
| type | 否 | 自动识别 | 险种 |
| coverage | 是 | - | 保额（数字） |
| premium | 是 | - | 年保费（数字） |
| currency | 否 | CNY | 币种：CNY/HKD/USD/EUR |
| cash_value | 否 | 0 | 现金价值 |

## 命令

```bash
python insurance_review.py
```

## 测试

```bash
python tests/test_all.py
```

## 依据

- 《中华人民共和国保险法》第 22-26 条
- 《健康保险管理办法》第 5、41 条
- 中国保险行业协会 T/IAC 53-2024（2025-02-19 实施）
- 中国精算师协会《国民防范重大疾病健康教育读本》
- 长城人寿 × 北京大学经济学院《中国家庭风险保障体系白皮书》2025
- 清华大学五道口金融学院《中国家庭风险保障体系白皮书》2023

## 多平台安装

| 平台 | 安装命令 |
|---|---|
| TRAE | `./install.sh trae` |
| Claude Code | `./install.sh claude` |
| OpenCode | `./install.sh opencode` |
| Codex | `./install.sh codex` |
| Cursor | `./install.sh cursor` |
| 全部 | `./install.sh all` |
