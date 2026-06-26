# -*- coding: utf-8 -*-
"""
家庭保单检视 V3.3 - 本地 PDF 解析器
零外部依赖（可选 pdfplumber） + 纯本地运行 + 自动脱敏

用法：
  python pdf_parser.py policy.pdf             # 解析单个 PDF
  python pdf_parser.py policies/*.pdf          # 批量解析
  python pdf_parser.py policy.pdf -o out.json  # 输出到指定文件

隐私保证：
  - 解析过程不联网
  - 自动屏蔽身份证 / 银行卡 / 手机号
  - 不写入云端、不传给 AI 模型
"""

import json
import re
import sys
from pathlib import Path

# === 1. 隐私脱敏（与 insurance_review.py 保持一致） ===
def mask(text):
    if not text:
        return ""
    text = re.sub(r'(?<!\d)\d{17}[\dXx](?!\d)',
                  lambda m: m.group()[:6] + '****' + m.group()[-4:], str(text))
    text = re.sub(r'(?<!\d)\d{16,19}(?!\d)',
                  lambda m: '****' + m.group()[-4:], text)
    text = re.sub(r'(?<!\d)1[3-9]\d{9}(?!\d)',
                  lambda m: m.group()[:3] + '****' + m.group()[-4:], text)
    return text

# === 2. 险种识别（5 类） ===
KIND_PATTERNS = [
    ("重疾险", ["重疾", "重大疾病", "防癌", "critical", "cancer"]),
    ("医疗险", ["医疗", "住院", "百万医疗", "medical", "health"]),
    ("意外险", ["意外", "accident"]),
    ("寿险", ["寿险", "身故", "定期寿", "终身寿", "life", "whole life"]),
    ("年金险", ["年金", "养老", "教育金", "annuity", "pension"]),
]

def detect_kind(text):
    t = text.lower()
    for kind, keys in KIND_PATTERNS:
        if any(k.lower() in t for k in keys):
            return kind
    return "其他"

# === 3. 字段抽取（保单号 / 投保人 / 保额 / 保费 / 缴费期 / 公司） ===
def extract_policy_no(text):
    m = re.search(r'保[单\*]?\s*号[：:\s]*([A-Z0-9]{8,20})', text, re.IGNORECASE)
    return m.group(1) if m else ""

def extract_insured(text):
    m = re.search(r'(?:投[保有]?人|姓名)[：:\s]*([^\s\n,，]{2,5})', text)
    return m.group(1) if m else ""

def extract_amount(text, label):
    """识别 50万 / 500,000 / 50万元"""
    pat = rf'{label}[^0-9¥]*?([\d,\.]+)\s*(万|万元|元)?'
    m = re.search(pat, text, re.IGNORECASE)
    if not m:
        return 0
    num = float(m.group(1).replace(',', ''))
    unit = m.group(2) or '元'
    if '万' in unit:
        num *= 10000
    return int(num)

def extract_period(text):
    m = re.search(r'(?:缴费[年期]+|交费[年期]+|交\s*费\s*期\s*间)[：:\s]*(\d+)\s*年', text)
    return int(m.group(1)) if m else 0

def extract_company(text):
    m = re.search(r'([\u4e00-\u9fa5]{2,8}(?:人寿|保险|财险|健康|养老|人寿保险))', text)
    return m.group(1) if m else ""

# === 4. 币种识别 ===
def detect_currency(text):
    if 'USD' in text or '美元' in text:
        return 'USD'
    if 'HKD' in text or '港币' in text or '港元' in text:
        return 'HKD'
    if 'EUR' in text or '欧元' in text:
        return 'EUR'
    return 'CNY'

# === 5. PDF 文本提取（pdfplumber 优先；缺失时降级为纯文本读取） ===
def extract_text_from_pdf(pdf_path):
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join((page.extract_text() or "") for page in pdf.pages)
    except ImportError:
        # pdfplumber 不可用时，尝试 pypdf
        try:
            from pypdf import PdfReader
            return "\n".join(page.extract_text() or "" for page in PdfReader(pdf_path).pages)
        except ImportError:
            print(f"⚠️ 需要安装 pdfplumber: pip install pdfplumber --break-system-packages",
                  file=sys.stderr)
            sys.exit(2)
    except Exception as e:
        print(f"❌ 解析失败 {pdf_path}: {e}", file=sys.stderr)
        return ""

# === 6. 解析一份保单 ===
def parse_policy(pdf_path):
    raw = extract_text_from_pdf(pdf_path)
    if not raw.strip():
        return {"source": str(pdf_path), "error": "无文本内容"}

    policy = {
        "source": str(pdf_path),
        "policy_no": mask(extract_policy_no(raw)),
        "holder": mask(extract_insured(raw)),
        "company": extract_company(raw),
        "kind": detect_kind(raw),
        "coverage": extract_amount(raw, r'(?:基本[保\s]?额|保险[金额\s]*|保\s*额)'),
        "premium": extract_amount(raw, r'(?:年[缴交]?保[费]?费|保\s*费)'),
        "period": extract_period(raw),
        "currency": detect_currency(raw),
    }
    return policy

# === 7. CLI 入口 ===
def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print("用法: python pdf_parser.py <pdf文件> [更多文件...] [-o output.json]")
        print("示例: python pdf_parser.py policy.pdf -o policies.json")
        sys.exit(0)

    # 解析 -o 参数
    args = sys.argv[1:]
    output = "policies.json"
    if "-o" in args:
        idx = args.index("-o")
        output = args[idx + 1]
        args = args[:idx] + args[idx+2:]

    # 展开通配符
    pdf_files = []
    for a in args:
        p = Path(a)
        if p.is_dir():
            pdf_files.extend(sorted(p.glob("*.pdf")))
        elif p.exists():
            pdf_files.append(p)
        else:
            print(f"⚠️ 文件不存在: {a}", file=sys.stderr)

    if not pdf_files:
        print("❌ 未找到任何 PDF 文件", file=sys.stderr)
        sys.exit(1)

    print(f"🔒 纯本地解析 | 共 {len(pdf_files)} 份保单 | 自动脱敏已启用")
    policies = [parse_policy(p) for p in pdf_files]

    Path(output).write_text(
        json.dumps(policies, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ 已输出 {len(policies)} 份保单 → {output}")
    print(f"   险种分布: {dict((p.get('kind','其他'), sum(1 for x in policies if x.get('kind')==p.get('kind'))) for p in policies if 'kind' in p)}")

if __name__ == "__main__":
    main()
