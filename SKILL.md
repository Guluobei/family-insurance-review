---
name: family-insurance-review
version: 3.4.0
description: 家庭保单检视 Skill - 隐私优先、纯本地、零外部依赖
platforms: [TRAE, Claude Code, OpenCode, Codex, Cursor]
privacy: 
  level: high
  default: anonymized
  network: disabled
---

# 家庭保单检视 Skill V3.4

> 📋 一份保单进，一份报告出。**零云端、零追踪、零泄露**。

## 🎯 核心能力

| 能力 | 说明 |
|---|---|
| 📂 保单解析 | 支持 JSON 输入 / 本地 PDF 自动解析 |
| 🛡️ 隐私脱敏 | 身份证/银行卡/手机号自动屏蔽（含数字型） |
| 🔍 缺口诊断 | 寿险/重疾/医疗/年金 4 大维度 |
| ⚠️ 冲突检测 | 医疗险重复、现金价值质押提示 |
| 💱 多币种 | CNY/HKD/USD/EUR 自动换算 |
| 🚫 团险识别 | 自动排除，不计入个人缺口 |

## 🚀 3 步上手

### Step 1：准备数据
```bash
# 方式 A：手填 JSON（推荐）
cat > policies.json <<'EOF'
[
  {"name":"平安重疾险","holder":"张三","coverage":300000,
   "premium":12000,"currency":"CNY","cash_value":50000}
]
EOF

# 方式 B：本地 PDF（不上传云端）
python pdf_parser.py ./我的保单/ -o policies.json
```

### Step 2：填写家庭信息
```bash
cat > family.json <<'EOF'
{"annual_income": 500000, "debt": 1500000}
EOF
```

### Step 3：生成报告
```bash
python insurance_review.py \
  -p policies.json \
  -f family.json \
  -o report.html \
  --safe-mode --anonymize
```

## 🛡️ 隐私保护（7 层防护）

1. **默认脱敏**：所有输出报告，敏感字段已 `****` 屏蔽
2. **`--anonymize`**：输入前再次强制脱敏（含数字型 ID）
3. **`--safe-mode`**：禁用代理 + 纯本地运行
4. **`--local-pdf`**：PDF 在本地解析，不传给 AI
5. **零外部依赖**：核心仅用 Python 标准库
6. **零日志输出**：不写日志文件
7. **零云存储**：报告只写到本地 `-o` 指定路径

## 🔧 CLI 参数

| 参数 | 说明 | 默认 |
|---|---|---|
| `-p, --policies` | 保单 JSON 路径 | `policies.json` |
| `-f, --family` | 家庭信息 JSON 路径 | `family.json` |
| `-o, --output` | 报告输出路径 | `report.html` |
| `--safe-mode` | 安全模式（禁用代理+网络） | 关 |
| `--anonymize` | 强制全量脱敏 | 关 |
| `--local-pdf DIR` | 本地 PDF 目录自动解析 | 无 |

## 📐 计算公式

```
寿险需求 = 年收入 × 10 + 房贷余额
寿险缺口 = max(0, 寿险需求 - 已有寿险保额)
重疾缺口 = max(0, 50万 - 已有重疾保额)
医疗险重复 = 医疗险份数 > 1
高现金价值阈值 = 10万
```

## 📚 监管依据

- 《保险法》
- 《健康保险管理办法》
- T/IAC 53-2024《人身保险产品销售规范》

## 🏗️ 部署到 TRAE 沙盒

TRAE 提供远程沙盒环境，目录约定：

| 目录 | 用途 |
|---|---|
| `/data/user/work/` | **临时**工作目录（中间产物、测试脚本） |
| `/workspace/` | **最终**交付目录（用户可见产物） |

### 沙盒使用流程
```bash
# 1. 上传代码到沙盒临时目录
cp insurance_review.py /data/user/work/
cp pdf_parser.py /data/user/work/
cp privacy.py /data/user/work/
cp policies.json /data/user/work/

# 2. 在沙盒中跑测试
cd /data/user/work
python3 insurance_review.py -p policies.json --safe-mode --anonymize

# 3. 把最终报告（HTML）放到 workspace
cp report.html /workspace/

# 4. 在 TRAE 中通过 computer:// 链接访问
# computer:///workspace/report.html
```

### 沙盒 vs 本地 vs 浏览器 — 对比

| 维度 | TRAE 沙盒 | 本地电脑 | 浏览器在线 |
|---|---|---|---|
| 隐私性 | ⭐⭐⭐⭐⭐ 文件不落地 | ⭐⭐⭐⭐ 文件在你电脑 | ⭐⭐ 数据在第三方 |
| 隔离性 | ⭐⭐⭐⭐⭐ 沙盒隔离 | ⭐⭐ 进程隔离 | ⭐⭐ 浏览器沙箱 |
| 复现性 | ⭐⭐⭐⭐⭐ 固定环境 | ⭐⭐ 依赖本地配置 | ⭐⭐⭐ 跨设备一致 |
| 适合场景 | 一次性检视 | 长期跟踪 | 协作共享 |

**推荐**：临时检视用 TRAE 沙盒（隐私 + 隔离），长期归档用本地。

## 🌍 多平台适配

| 平台 | 入口文件 | 安装方式 |
|---|---|---|
| TRAE | `SKILL.md` | 自动发现 |
| Claude Code | `.claude/skills/family-insurance-review/SKILL.md` | 复制到 `.claude/skills/` |
| OpenCode | `opencode.toml` (在 `[skills]` 段声明) | `cp opencode.toml ~/.config/opencode/` |
| Codex | `codex.json` | `codex skill install .` |
| Cursor | `.cursorrules` | 复制到项目根目录 |

## 📁 目录结构

```
family-insurance-review/
├── SKILL.md              # 本文件（Skill 入口）
├── insurance_review.py   # 核心实现（V3.4）
├── pdf_parser.py         # 本地 PDF 解析器
├── privacy.py            # V3.4 共享隐私模块（mask/anonymize/classify）
├── tests/                # 测试套件（85 个测试）
│   ├── test_v33_anonymize.py    # 脱敏/分类测试
│   ├── test_v33_safe_mode.py    # CLI/错误处理测试
│   ├── test_v33_local_pdf.py    # PDF 解析测试
│   └── test_core_logic.py       # 核心业务逻辑测试
├── README.md             # 英文版说明
└── CHANGELOG.md          # 变更日志
```

## ⚠️ 免责声明

本工具仅做规则化诊断，**不构成投资建议**。
最终决策请咨询持牌保险代理人 / 经纪人。

---
**版本**: V3.4 | **更新**: 2026-06 | **许可**: MIT
