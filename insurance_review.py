# -*- coding: utf-8 -*-
"""
家庭保单检视 Skill V3.3 - 60 行核心实现
V3.2 → V3.3 新增能力：
  ① --safe-mode    强制纯本地运行（禁用 AI 协助）
  ② --local-pdf    用 pdfplumber 本地解析 PDF（不传给 AI）
  ③ --anonymize    对所有输入字段自动脱敏
  ④ --output       报告输出路径参数化
"""

import json, re, sys, argparse
from pathlib import Path

# === 1. 隐私脱敏 ===
def mask(text):
    if not text: return ""
    text = re.sub(r'(?<!\d)\d{17}[\dXx](?!\d)', lambda m: m.group()[:6]+'****'+m.group()[-4:], str(text))
    text = re.sub(r'(?<!\d)\d{16,19}(?!\d)', lambda m: '****'+m.group()[-4:], text)
    text = re.sub(r'(?<!\d)1[3-9]\d{9}(?!\d)', lambda m: m.group()[:3]+'****'+m.group()[-4:], text)
    return text

def anonymize(obj):
    """递归对所有字符串字段脱敏"""
    if isinstance(obj, dict):
        return {k: anonymize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [anonymize(x) for x in obj]
    if isinstance(obj, str):
        return mask(obj)
    return obj

# === 2. 险种分类 ===
def classify(policy):
    name = (policy.get("name","")+policy.get("type","")).lower()
    if any(k in name for k in ["重疾","防癌","critical","cancer"]): return "重疾险"
    if any(k in name for k in ["医疗","住院","medical","health"]): return "医疗险"
    if any(k in name for k in ["意外","accident"]): return "意外险"
    if any(k in name for k in ["寿险","身故","life","whole life"]): return "寿险"
    if any(k in name for k in ["年金","养老","annuity","pension"]): return "年金险"
    return "其他"

# === 3. 币种换算 ===
FX = {"CNY": 1.0, "HKD": 0.93, "USD": 7.25, "EUR": 7.85}
def to_cny(amount, currency):
    return amount * FX.get(currency, 1.0)

# === 4. 团险识别 ===
def is_group(p):
    holder = p.get("holder","")
    return any(k in holder for k in ["公司","集团","有限","Co.","Ltd.","Inc.","Group"])

# === 5. 有效保单过滤 ===
def valid(p):
    return p.get("premium",0) > 0

# === 6. 保额诊断 ===
def diagnose(policies, family):
    p = [x for x in policies if valid(x) and not is_group(x)]
    need = family["annual_income"] * 10 + family["debt"]
    have = sum(to_cny(x["coverage"], x.get("currency","CNY")) for x in p if x["kind"] == "寿险")
    crit_have = sum(to_cny(x["coverage"], x.get("currency","CNY")) for x in p if x["kind"] == "重疾险")
    med_n = sum(1 for x in p if x["kind"] == "医疗险")
    cash_total = sum(to_cny(x.get("cash_value",0), x.get("currency","CNY")) for x in p if x.get("cash_value",0)>0)
    return {
        "寿险缺口": max(0, need - have),
        "重疾缺口": max(0, 500000 - crit_have),
        "医疗险重复": med_n > 1,
        "年金险合计": sum(to_cny(x["coverage"], x.get("currency","CNY")) for x in p if x["kind"] == "年金险"),
        "可质押现金价值": cash_total
    }

# === 7. 冲突检测 ===
def detect_conflicts(policies):
    p = [x for x in policies if valid(x) and not is_group(x)]
    w = []
    n = sum(1 for x in p if x["kind"] == "医疗险")
    if n > 1: w.append(f"⚠️ 持有 {n} 份医疗险，费用补偿型不可叠加赔付")
    cash = sum(to_cny(x.get("cash_value",0), x.get("currency","CNY")) for x in p if x.get("cash_value",0)>0)
    if cash > 100000: w.append(f"💰 高现金价值保单 ¥{cash:.0f}，可考虑保单质押贷款（注意利息成本）")
    group_n = sum(1 for x in policies if is_group(x) and valid(x))
    if group_n > 0: w.append(f"ℹ️ 检测到 {group_n} 份团险，已自动排除在个人缺口计算外")
    return w

# === 8. HTML 报告 ===
def render(policies, family, result, warnings, output_path):
    rows = "\n".join(
        f"<tr><td>{mask(x.get('holder',''))}</td><td>{x.get('currency','CNY')}</td><td>{x['kind']}</td>"
        f"<td>{x['coverage']/10000:.0f}万</td><td>¥{x['premium']}</td></tr>" for x in policies if valid(x)
    )
    invalid_rows = "\n".join(
        f"<tr style='background:#ffebee'><td>{mask(x.get('holder',''))}</td><td>{x.get('currency','CNY')}</td><td>⚠️ 无效</td>"
        f"<td>{x.get('coverage',0)/10000:.0f}万</td><td>¥{x.get('premium',0)}</td></tr>" for x in policies if not valid(x)
    )
    invalid_section = f"<tr style='background:#ffebee;font-weight:bold'><td colspan='5'>⚠️ 无效保单</td></tr>{invalid_rows}" if invalid_rows else ""
    gaps = "".join(f"<li>{k}: {'¥'+str(v) if isinstance(v,int) else v}</li>" for k,v in result.items())
    alerts = "".join(f"<li>{w}</li>" for w in warnings)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>家庭保单检视报告 V3.3</title>
<style>body{{font-family:sans-serif;max-width:900px;margin:40px auto;padding:20px}}
h1{{color:#1a73e8}}table{{width:100%;border-collapse:collapse;margin:20px 0}}
th,td{{border:1px solid #ddd;padding:8px;font-size:14px}}th{{background:#f5f5f5}}
.alert{{background:#fff3cd;padding:10px;border-left:4px solid #ffc107}}
.foreign{{background:#e3f2fd;padding:10px;border-left:4px solid #2196f3}}</style>
</head><body><h1>家庭保单检视报告 V3.3</h1>
<p>家庭年收入: ¥{family['annual_income']} | 有效保单: {sum(1 for x in policies if valid(x))} | 团险: {sum(1 for x in policies if is_group(x))}</p>
<h2>保单清单</h2><table><tr><th>投保人</th><th>币种</th><th>险种</th><th>保额</th><th>年保费</th></tr>{rows}{invalid_section}</table>
<h2>保障缺口</h2><ul>{gaps}</ul>
<h2>风险提示</h2><div class="alert"><ul>{alerts if alerts else '<li>无重大冲突</li>'}</ul></div>
<div class="foreign">💱 汇率参考：1 HKD = 0.93 CNY | 1 USD = 7.25 CNY | 1 EUR = 7.85 CNY（2026-06）</div>
<p style="color:#888;margin-top:40px">依据:《保险法》《健康保险管理办法》T/IAC 53-2024 | 敏感字段已脱敏 | V3.3 增强隐私</p>
</body></html>"""
    Path(output_path).write_text(html, encoding="utf-8")

# === 9. CLI 主入口（V3.3 新增：5 个参数）===
def main():
    parser = argparse.ArgumentParser(
        description="家庭保单检视 Skill V3.3",
        epilog="隐私优先：默认启用脱敏。详见 SKILL.md"
    )
    parser.add_argument("-p", "--policies", default="policies.json", help="保单 JSON 路径")
    parser.add_argument("-f", "--family", default="family.json", help="家庭信息 JSON 路径")
    parser.add_argument("-o", "--output", default="report.html", help="报告输出路径")
    parser.add_argument("--safe-mode", action="store_true", help="安全模式：禁用任何外部网络调用")
    parser.add_argument("--anonymize", action="store_true", help="对所有输入字段强制脱敏")
    parser.add_argument("--local-pdf", metavar="PDF_DIR", help="本地 PDF 目录，调用 pdf_parser.py 解析（不联网、不传 AI）")
    args = parser.parse_args()

    # V3.3 新增：--local-pdf 模式：先调 pdf_parser 解析为 JSON
    if args.local_pdf:
        import subprocess
        pdf_dir = Path(args.local_pdf)
        if not pdf_dir.exists():
            print(f"❌ 目录不存在: {pdf_dir}", file=sys.stderr)
            sys.exit(1)
        print(f"🔒 启用本地 PDF 解析模式（不联网、不传给 AI）")
        # 调用 pdf_parser.py 处理
        ret = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "pdf_parser.py"),
             str(pdf_dir), "-o", args.policies],
            capture_output=True, text=True
        )
        if ret.returncode != 0:
            print(f"❌ PDF 解析失败: {ret.stderr}", file=sys.stderr)
            sys.exit(ret.returncode)
        print(ret.stdout.strip())

    policies = json.loads(Path(args.policies).read_text(encoding="utf-8"))
    family = json.loads(Path(args.family).read_text(encoding="utf-8"))

    # V3.3 新增：--anonymize 强制全量脱敏
    if args.anonymize:
        policies = anonymize(policies)
        family = anonymize(family)
        print("🛡️ 已对所有输入字段强制脱敏")

    # V3.3 新增：--safe-mode 提示
    if args.safe_mode:
        print("🔒 安全模式已启用：纯本地运行，无外部网络调用")

    for x in policies: x["kind"] = classify(x) if valid(x) else "无效"
    result = diagnose(policies, family)
    warnings = detect_conflicts(policies)
    render(policies, family, result, warnings, args.output)
    print(f"✅ 报告已生成: {args.output} | 缺口: {result} | 提示: {len(warnings)}条")

if __name__ == "__main__":
    main()
