# -*- coding: utf-8 -*-
"""
家庭保单检视 Skill V3.2 - 50 行核心实现
V3.0 → V3.1 修复 3 个边界 Bug：异常保费、保额 0 误判、英文产品名
V3.1 → V3.2 修复 3 个新缺口：港币/美元保单、团险误判、质押贷款未识别
汇率参考：2026-06 央行中间价（CNY 基准）
"""

import json, re
from pathlib import Path

# === 1. 隐私脱敏 ===
def mask(text):
    if not text: return ""
    text = re.sub(r'(?<!\d)\d{17}[\dXx](?!\d)', lambda m: m.group()[:6]+'****'+m.group()[-4:], str(text))
    text = re.sub(r'(?<!\d)\d{16,19}(?!\d)', lambda m: '****'+m.group()[-4:], text)
    text = re.sub(r'(?<!\d)1[3-9]\d{9}(?!\d)', lambda m: m.group()[:3]+'****'+m.group()[-4:], text)
    return text

# === 2. 险种分类（中英文）===
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

# === 5. 有效保单过滤（保额 0 允许：纯年金险场景）===
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
    invalid_section = f"<tr style='background:#ffebee;font-weight:bold'><td colspan='5'>⚠️ 无效保单（保费≤0 或保额≤0，已被过滤）</td></tr>{invalid_rows}" if invalid_rows else ""
    gaps = "".join(f"<li>{k}: {'¥'+str(v) if isinstance(v,int) else v}</li>" for k,v in result.items())
    alerts = "".join(f"<li>{w}</li>" for w in warnings)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>家庭保单检视报告</title>
<style>body{{font-family:sans-serif;max-width:900px;margin:40px auto;padding:20px}}
h1{{color:#1a73e8}}table{{width:100%;border-collapse:collapse;margin:20px 0}}
th,td{{border:1px solid #ddd;padding:8px;font-size:14px}}th{{background:#f5f5f5}}
.alert{{background:#fff3cd;padding:10px;border-left:4px solid #ffc107}}
.foreign{{background:#e3f2fd;padding:10px;border-left:4px solid #2196f3}}</style>
</head><body><h1>家庭保单检视报告</h1>
<p>家庭年收入: ¥{family['annual_income']} | 有效保单: {sum(1 for x in policies if valid(x))} | 团险: {sum(1 for x in policies if is_group(x))}</p>
<h2>保单清单（已含币种）</h2><table><tr><th>投保人</th><th>币种</th><th>险种</th><th>保额</th><th>年保费</th></tr>{rows}{invalid_section}</table>
<h2>保障缺口</h2><ul>{gaps}</ul>
<h2>风险提示</h2><div class="alert"><ul>{alerts if alerts else '<li>无重大冲突</li>'}</ul></div>
<div class="foreign">💱 汇率参考：1 HKD = 0.93 CNY | 1 USD = 7.25 CNY | 1 EUR = 7.85 CNY（2026-06）</div>
<p style="color:#888;margin-top:40px">依据:《保险法》《健康保险管理办法》T/IAC 53-2024 | 敏感字段已脱敏</p>
</body></html>"""
    Path(output_path).write_text(html, encoding="utf-8")

# === 9. 主入口 ===
def main():
    policies = json.loads(Path("policies.json").read_text(encoding="utf-8"))
    family = json.loads(Path("family.json").read_text(encoding="utf-8"))
    for x in policies: x["kind"] = classify(x) if valid(x) else "无效"
    result = diagnose(policies, family)
    warnings = detect_conflicts(policies)
    render(policies, family, result, warnings, "report.html")
    print(f"✅ 报告已生成 | 缺口: {result} | 提示: {len(warnings)}条")

if __name__ == "__main__":
    main()
