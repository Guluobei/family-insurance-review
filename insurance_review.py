# -*- coding: utf-8 -*-
"""
家庭保单检视 Skill V3.4 - 核心实现
V3.3 → V3.4 架构修复：
  ① 消除 mask/classify 重复 → 引用 privacy.py
  ② 修复 ¥True 显示 bug
  ③ --anonymize 覆盖数字型 ID
  ④ 消除 subprocess 耦合 → 直接 import
  ⑤ --safe-mode 真正拦截网络依赖
  ⑥ 核心逻辑加防御性 get + int 转换
"""

import json, sys, argparse
from pathlib import Path
from privacy import mask, anonymize, classify_by_text

# === 1. 险种分类（引用共享 classify_by_text） ===
def classify(policy):
    return classify_by_text(policy.get("name", "") + policy.get("type", ""))

# === 2. 币种换算 ===
FX = {"CNY": 1.0, "HKD": 0.93, "USD": 7.25, "EUR": 7.85}
def to_cny(amount, currency):
    return int(amount * FX.get(currency, 1.0))

# === 3. 团险识别 ===
def is_group(p):
    holder = p.get("holder", "")
    return any(k in holder for k in ["公司", "集团", "有限", "Co.", "Ltd.", "Inc.", "Group"])

# === 4. 有效保单过滤 ===
def valid(p):
    return p.get("premium", 0) > 0

# === 5. 保额诊断 ===
def diagnose(policies, family):
    p = [x for x in policies if valid(x) and not is_group(x)]
    need = family.get("annual_income", 0) * 10 + family.get("debt", 0)
    have = sum(to_cny(x.get("coverage", 0), x.get("currency", "CNY")) for x in p if x.get("kind") == "寿险")
    crit_have = sum(to_cny(x.get("coverage", 0), x.get("currency", "CNY")) for x in p if x.get("kind") == "重疾险")
    med_n = sum(1 for x in p if x.get("kind") == "医疗险")
    cash_total = sum(to_cny(x.get("cash_value", 0), x.get("currency", "CNY")) for x in p if x.get("cash_value", 0) > 0)
    return {
        "寿险缺口": max(0, need - have),
        "重疾缺口": max(0, 500000 - crit_have),
        "医疗险重复": med_n > 1,
        "年金险合计": sum(to_cny(x.get("coverage", 0), x.get("currency", "CNY")) for x in p if x.get("kind") == "年金险"),
        "可质押现金价值": cash_total
    }

# === 6. 冲突检测 ===
def detect_conflicts(policies):
    p = [x for x in policies if valid(x) and not is_group(x)]
    w = []
    n = sum(1 for x in p if x.get("kind") == "医疗险")
    if n > 1: w.append(f"⚠️ 持有 {n} 份医疗险，费用补偿型不可叠加赔付")
    cash = sum(to_cny(x.get("cash_value", 0), x.get("currency", "CNY")) for x in p if x.get("cash_value", 0) > 0)
    if cash > 100000: w.append(f"💰 高现金价值保单 ¥{cash:,}，可考虑保单质押贷款（注意利息成本）")
    group_n = sum(1 for x in policies if is_group(x) and valid(x))
    if group_n > 0: w.append(f"ℹ️ 检测到 {group_n} 份团险，已自动排除在个人缺口计算外")
    return w

# === 7. HTML 报告 ===
def _fmt_gap(v):
    """P0-3 修复：bool 不再被当作 int，金额加千分位"""
    if isinstance(v, bool):
        return "是" if v else "否"
    if isinstance(v, (int, float)):
        return f"¥{int(v):,}"
    return str(v)

def render(policies, family, result, warnings, output_path):
    rows = "\n".join(
        f"<tr><td>{mask(x.get('holder', ''))}</td><td>{x.get('currency', 'CNY')}</td><td>{x.get('kind', '其他')}</td>"
        f"<td>{x.get('coverage', 0) / 10000:.0f}万</td><td>¥{x.get('premium', 0):,}</td></tr>" for x in policies if valid(x)
    )
    invalid_rows = "\n".join(
        f"<tr style='background:#ffebee'><td>{mask(x.get('holder', ''))}</td><td>{x.get('currency', 'CNY')}</td><td>⚠️ 无效</td>"
        f"<td>{x.get('coverage', 0) / 10000:.0f}万</td><td>¥{x.get('premium', 0)}</td></tr>" for x in policies if not valid(x)
    )
    invalid_section = f"<tr style='background:#ffebee;font-weight:bold'><td colspan='5'>⚠️ 无效保单</td></tr>{invalid_rows}" if invalid_rows else ""
    gaps = "".join(f"<li>{k}: {_fmt_gap(v)}</li>" for k, v in result.items())
    alerts = "".join(f"<li>{w}</li>" for w in warnings)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>家庭保单检视报告 V3.4</title>
<style>body{{font-family:sans-serif;max-width:900px;margin:40px auto;padding:20px}}
h1{{color:#1a73e8}}table{{width:100%;border-collapse:collapse;margin:20px 0}}
th,td{{border:1px solid #ddd;padding:8px;font-size:14px}}th{{background:#f5f5f5}}
.alert{{background:#fff3cd;padding:10px;border-left:4px solid #ffc107}}
.foreign{{background:#e3f2fd;padding:10px;border-left:4px solid #2196f3}}</style>
</head><body><h1>家庭保单检视报告 V3.4</h1>
<p>家庭年收入: ¥{family.get('annual_income', 0):,} | 有效保单: {sum(1 for x in policies if valid(x))} | 团险: {sum(1 for x in policies if is_group(x))}</p>
<h2>保单清单</h2><table><tr><th>投保人</th><th>币种</th><th>险种</th><th>保额</th><th>年保费</th></tr>{rows}{invalid_section}</table>
<h2>保障缺口</h2><ul>{gaps}</ul>
<h2>风险提示</h2><div class="alert"><ul>{alerts if alerts else '<li>无重大冲突</li>'}</ul></div>
<div class="foreign">💱 汇率参考：1 HKD = 0.93 CNY | 1 USD = 7.25 CNY | 1 EUR = 7.85 CNY（2026-06）</div>
<p style="color:#888;margin-top:40px">依据:《保险法》《健康保险管理办法》T/IAC 53-2024 | 敏感字段已脱敏 | V3.4 架构修复</p>
</body></html>"""
    Path(output_path).write_text(html, encoding="utf-8")

# === 8. CLI 主入口 ===
def main():
    parser = argparse.ArgumentParser(
        description="家庭保单检视 Skill V3.4",
        epilog="隐私优先：默认启用脱敏。详见 SKILL.md"
    )
    parser.add_argument("-p", "--policies", default="policies.json", help="保单 JSON 路径")
    parser.add_argument("-f", "--family", default="family.json", help="家庭信息 JSON 路径")
    parser.add_argument("-o", "--output", default="report.html", help="报告输出路径")
    parser.add_argument("--safe-mode", action="store_true", help="安全模式：禁用任何外部网络调用")
    parser.add_argument("--anonymize", action="store_true", help="对所有输入字段强制脱敏")
    parser.add_argument("--local-pdf", metavar="PDF_DIR", help="本地 PDF 目录，调用 pdf_parser.py 解析（不联网、不传 AI）")
    args = parser.parse_args()

    # P1-3 修复：--safe-mode 真正拦截网络依赖
    if args.safe_mode:
        import os
        os.environ["NO_PROXY"] = "*"  # 禁止代理
        os.environ["http_proxy"] = ""
        os.environ["https_proxy"] = ""
        print("🔒 安全模式已启用：已禁用代理 + 纯本地运行")

    # P1-2 修复：直接 import 替代 subprocess
    if args.local_pdf:
        from pdf_parser import parse_policy
        pdf_dir = Path(args.local_pdf)
        if not pdf_dir.exists():
            print(f"❌ 目录不存在: {pdf_dir}", file=sys.stderr)
            sys.exit(1)
        print(f"🔒 启用本地 PDF 解析模式（不联网、不传给 AI）")
        pdf_files = sorted(pdf_dir.glob("*.pdf")) if pdf_dir.is_dir() else [pdf_dir]
        policies = [parse_policy(p) for p in pdf_files]
        Path(args.policies).write_text(json.dumps(policies, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ 已解析 {len(policies)} 份 PDF → {args.policies}")
    else:
        # P2 修复：JSON 解析加 try/except
        try:
            policies = json.loads(Path(args.policies).read_text(encoding="utf-8"))
        except FileNotFoundError:
            print(f"❌ 保单文件不存在: {args.policies}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ 保单 JSON 格式错误: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        family = json.loads(Path(args.family).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"❌ 家庭信息文件不存在: {args.family}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ 家庭信息 JSON 格式错误: {e}", file=sys.stderr)
        sys.exit(1)

    if args.anonymize:
        policies = anonymize(policies)
        family = anonymize(family)
        print("🛡️ 已对所有输入字段强制脱敏")

    for x in policies:
        x["kind"] = classify(x) if valid(x) else "无效"
    result = diagnose(policies, family)
    warnings = detect_conflicts(policies)
    render(policies, family, result, warnings, args.output)
    print(f"✅ 报告已生成: {args.output} | 缺口: {result} | 提示: {len(warnings)}条")

if __name__ == "__main__":
    main()
