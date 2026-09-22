# -*- coding: utf-8 -*-
"""从 _原始邮件附件 里的 .eml 重新提取附件（归档后回补遗漏票据用）

场景：归档重构时若发现某个凭证丢了，而原始 .eml 还在 _原始邮件附件，
就用这个脚本重新解出来，避免重新去邮箱下载。

用法：
  1. 改 BASE 为你的报销根目录
  2. 按需改 KEYWORD / CATEGORY / OUT_NAME
  3. 直接跑；末尾会打印各分类目录的文件清单，方便核对
"""
import os
import email
from email import policy
from email.header import decode_header, make_header

# 报销根目录
BASE = r"<报销根目录绝对路径>"
SRC = os.path.join(BASE, "_原始邮件附件")

# 附件文件名里含这个关键词才提取（如 "结账单" / "消费明细单" / "行程单"）
KEYWORD = "结账单"
# 提取后落到哪个分类目录
CATEGORY = "酒店"
# 输出文件名（建议沿用统一命名规范 日期_类型_商家_金额元.pdf）
OUT_NAME = "MMDD_<商家>_<凭证名称>.pdf"


def decode_value(v):
    if not v:
        return ""
    try:
        return str(make_header(decode_header(v)))
    except Exception:
        return str(v)


def eml_attachments(path):
    """返回 [(附件文件名, 二进制内容), ...]"""
    with open(path, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)
    out = []
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        fn = part.get_filename()
        if not fn:
            continue
        data = part.get_payload(decode=True)
        if data:
            out.append((decode_value(fn), data))
    return out


if not os.path.isdir(SRC):
    raise SystemExit("找不到原始附件目录：%s" % SRC)

dst_dir = os.path.join(BASE, CATEGORY)
os.makedirs(dst_dir, exist_ok=True)
dst = os.path.join(dst_dir, OUT_NAME)
restored = 0

for name in sorted(os.listdir(SRC)):
    if not name.lower().endswith(".eml"):
        continue
    for fn, data in eml_attachments(os.path.join(SRC, name)):
        if KEYWORD in fn and fn.lower().endswith(".pdf"):
            with open(dst, "wb") as w:
                w.write(data)
            print("restored: %s  <- %s  (%d bytes)" % (OUT_NAME, name, len(data)))
            restored += 1
            break
    if restored:
        break

if not restored:
    print("未在 _原始邮件附件 中找到含「%s」的 PDF 附件，请检查 KEYWORD。" % KEYWORD)

print("\n=== 分类目录清单（核对用）===")
for cat in ["酒店", "请客户", "打车", "高速过路费", "高铁", "机票"]:
    d = os.path.join(BASE, cat)
    if not os.path.isdir(d):
        continue
    print("--- %s (%d) ---" % (cat, len(os.listdir(d))))
    for f in sorted(os.listdir(d)):
        print("   ", f)
