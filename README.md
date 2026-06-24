# 家庭保单检视 Skill V3.2

> 50 行核心代码 · 11 个测试用例 · 5 大 AI 助手兼容 · 零第三方依赖

## 特性

- 隐私脱敏（L4-L5 字段自动屏蔽：身份证、银行卡、手机号）
- 险种智能分类（中英文：寿险/重疾险/医疗险/意外险/年金险）
- 保障缺口诊断（寿险 + 重疾，缺口公式：保障需要 - 可用资产）
- 冲突检测（医疗险重复 + 团险识别 + 质押贷款提示）
- 多币种支持（CNY/HKD/USD/EUR）
- HTML 可视化报告

## 快速开始

### 1. 准备数据

创建 `policies.json` 和 `family.json`：

```json
// policies.json
[
  {"holder": "户主", "name": "平安寿险", "type": "寿险", "coverage": 1000000, "premium": 12000}
]
```

```json
// family.json
{"members": ["户主", "配偶"], "annual_income": 500000, "debt": 2000000, "dependents": 1}
```

### 2. 安装 Skill

```bash
./install.sh trae        # 安装到 TRAE
./install.sh claude      # 安装到 Claude Code
./install.sh opencode    # 安装到 OpenCode
./install.sh codex       # 安装到 Codex
./install.sh cursor      # 安装到 Cursor
./install.sh all         # 全部安装
```

### 3. 运行

```bash
python insurance_review.py
```

输出 `report.html` 到当前目录。

## 测试

```bash
python tests/test_all.py
```

## 字段说明

| 字段 | 必填 | 默认 | 说明 |
|---|---|---|---|
| holder | 是 | - | 投保人（团险填公司名） |
| name | 是 | - | 产品名称 |
| type | 否 | 自动 | 险种 |
| coverage | 是 | - | 保额 |
| premium | 是 | - | 年保费 |
| currency | 否 | CNY | CNY/HKD/USD/EUR |
| cash_value | 否 | 0 | 现金价值 |

## 隐私声明

本 Skill 默认启用隐私保护模式。保单数据仅在本地处理，不上传至任何云端。L4-L5 字段（身份证、银行卡、健康告知原文）禁止进入 AI 助手上下文。

## 依据

- 《中华人民共和国保险法》第 22-26 条
- 《健康保险管理办法》第 5、41 条
- 中国保险行业协会 T/IAC 53-2024
- 长城人寿 × 北京大学经济学院《中国家庭风险保障体系白皮书》2025
- 清华大学五道口金融学院《中国家庭风险保障体系白皮书》2023
- 中国精算师协会《国民防范重大疾病健康教育读本》

## 许可

MIT
