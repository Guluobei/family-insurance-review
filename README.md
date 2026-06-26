# 家庭保单检视 Skill

> Privacy-first family policy review — 60 lines of Python, zero cloud, zero tracking.

[English](#english) | [中文](#中文)

---

## 中文

一份保单进，一份报告出。**零云端、零追踪、零泄露**。

### 特性

- 🛡️ **隐私优先**：默认脱敏身份证/银行卡/手机号
- 🔒 **安全模式**：`--safe-mode` 禁用任何外部网络
- 📂 **本地 PDF**：不上传云端，本地解析
- 💱 **多币种**：CNY/HKD/USD/EUR 自动换算
- 🚫 **团险识别**：自动排除，不计入个人缺口
- ⚠️ **冲突检测**：医疗险重复、现金价值质押提示

### 快速上手

```bash
# 1. 准备数据
echo '[{"name":"平安重疾险","holder":"张三","coverage":300000,"premium":12000,"currency":"CNY"}]' > policies.json
echo '{"annual_income":500000,"debt":1500000}' > family.json

# 2. 生成报告
python insurance_review.py --safe-mode --anonymize
```

### CLI

| 参数 | 说明 |
|---|---|
| `-p` | 保单 JSON 路径 |
| `-f` | 家庭信息 JSON 路径 |
| `-o` | 报告输出路径 |
| `--safe-mode` | 禁用外部网络 |
| `--anonymize` | 强制脱敏 |
| `--local-pdf DIR` | 本地 PDF 目录 |

### 测试

```bash
python3 -m unittest discover tests -v
```

---

## English

Policy in, report out. **Zero cloud, zero tracking, zero leakage.**

### Features

- 🛡️ **Privacy-first**: Auto-mask ID cards, bank cards, phone numbers
- 🔒 **Safe mode**: `--safe-mode` disables all external network calls
- 📂 **Local PDF**: Parse locally, never upload
- 💱 **Multi-currency**: Auto-convert CNY/HKD/USD/EUR
- 🚫 **Group insurance**: Auto-detect and exclude
- ⚠️ **Conflict detection**: Duplicate medical, cash value pledge alerts

### Quick Start

```bash
python insurance_review.py --safe-mode --anonymize
```

### License

MIT
