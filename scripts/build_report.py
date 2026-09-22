# -*- coding: utf-8 -*-
"""报销明细表生成脚本（模板）

用法：改 BASE 为报销目录绝对路径，按你的实际票据替换 rows，再跑一遍即可。
本文件是「模板」，示例数据均为虚构占位，请勿当成真实报销数据。
"""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# 报销根目录（改成你自己的路径）
BASE = r"<报销根目录绝对路径>"

# 发票抬头
W = "<发票抬头公司全称>"

# 日期, 类别, 事项, 金额, 发票号码, 抬头, 备注, 归档文件
# 金额填 None 表示该凭证无金额（不计入合计，如登机牌）
rows = [
    ["MM-DD", "酒店", "示例酒店（N晚）", 0.00,
     "<20位发票号码>", W, "增值税专用发票，开票日MM-DD", "酒店/MMDD_示例酒店发票_0元.pdf"],
    ["MM-DD", "请客户", "示例餐饮店 餐费（请客户吃饭）", 0.00,
     "<20位发票号码>", W, "增值税普通发票，开票日MM-DD", "请客户/MMDD_示例餐饮发票_0元.pdf"],
    ["MM-DD", "打车", "高速过路费（车牌 <车牌号>）", 0.00,
     "见PDF", W, "票根电子发票，开票日MM-DD", "打车/MMDD_高速过路费_车牌_0元.pdf"],
    ["MM-DD", "打车", "网约车行程（示例平台）", 0.00,
     "<20位发票号码>", W, "增值税电子发票+行程单，开票日MM-DD",
     "打车/MMDD_示例网约车_0元_发票.pdf"],
    ["MM-DD", "高铁", "铁路电子客票 G0000 示例站→示例站", 0.00,
     "<20位发票号码>", W, "铁路电子客票，开票日MM-DD", "高铁/MMDD_铁路电子客票_G0000_0元.pdf"],
    ["MM-DD", "机票", "示例航司机票款", 0.00,
     "<20位发票号码>", W, "增值税普通发票，销售方示例航司", "机票/MMDD_示例航司机票发票_0元.pdf"],
    ["MM-DD", "机票", "航班 XX0000 示例站→示例站（乘机凭证）", None,
     "-", "<乘机人姓名>", "电子登机凭证，无金额，不计入合计",
     "机票/MMDD_乘机凭证_XX0000.pdf"],
]

CATS = ["机票", "打车", "酒店", "请客户", "高铁"]
CAT_FILL = {"机票": "FFEDED", "打车": "E8F6FD", "酒店": "FFF4E0", "请客户": "EAF7EA", "高铁": "EDEDF5"}

wb = Workbook()
ws = wb.active
ws.title = "报销明细"

thin = Side(style="thin", color="CCCCCC")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

ws.merge_cells("A1:H1")
ws["A1"] = "出差报销明细（最后更新 YYYY-MM-DD，来源：<你的智能体邮箱>）"
ws["A1"].font = Font(name="微软雅黑", size=14, bold=True)
ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
ws.row_dimensions[1].height = 28

headers = ["日期", "类别", "事项", "金额(元)", "发票号码", "抬头", "备注", "归档文件"]
for i, h in enumerate(headers, 1):
    c = ws.cell(row=2, column=i, value=h)
    c.font = Font(name="微软雅黑", size=11, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor="00A0E9" if i <= 4 else "0084B4")
    c.alignment = Alignment(horizontal="center", vertical="center")
    c.border = border

r = 3
cat_sum = {c: 0.0 for c in CATS}
total = 0.0
for row in rows:
    for i, v in enumerate(row, 1):
        c = ws.cell(row=r, column=i, value=v)
        c.font = Font(name="微软雅黑", size=11)
        c.border = border
        c.alignment = Alignment(vertical="center", wrap_text=(i in (3, 7, 8)),
                                horizontal="center" if i in (1, 2, 4) else "left")
        c.fill = PatternFill("solid", fgColor=CAT_FILL[row[1]])
    if row[3] is not None:
        amt = float(row[3])
        c4 = ws.cell(row=r, column=4, value=amt)
        c4.number_format = "#,##0.00"
        total += amt
        cat_sum[row[1]] += amt
    r += 1

ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
ws.cell(row=r, column=1, value="发票金额合计").font = Font(name="微软雅黑", size=11, bold=True)
tc = ws.cell(row=r, column=4, value=total)
tc.font = Font(name="微软雅黑", size=12, bold=True, color="C00000")
tc.number_format = "#,##0.00"
ws.cell(row=r, column=5, value="仅统计有金额的发票凭证").font = Font(name="微软雅黑", size=10, color="808080")
for i in range(1, 9):
    ws.cell(row=r, column=i).fill = PatternFill("solid", fgColor="FFF2CC")
    ws.cell(row=r, column=i).border = border
r += 1

for cat in CATS:
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
    c = ws.cell(row=r, column=1, value="　%s小计" % cat)
    c.font = Font(name="微软雅黑", size=10)
    c.alignment = Alignment(horizontal="right", vertical="center")
    v = ws.cell(row=r, column=4, value=cat_sum[cat])
    v.font = Font(name="微软雅黑", size=10, bold=True)
    v.number_format = "#,##0.00"
    v.alignment = Alignment(horizontal="center")
    for i in range(1, 9):
        ws.cell(row=r, column=i).border = border
    r += 1
r += 1

notes = [
    "说明：",
    "1. 仅统计发票金额；无金额凭证（如登机牌/乘机凭证）列出但不计入合计。",
    "2. 目录按 5 类归档：酒店 / 请客户 / 打车 / 高铁 / 机票；另设 _原始邮件附件 存原始 .eml/.zip。",
    "3. 只保留 PDF（含 PDF 行程单），OFD/XML 已清理。",
    "4. 同一笔支出出现多张凭证（如消费明细单 + 正式发票）时二选一，勿重复报销。",
    "5. 多张住宿票日期可能交叉，报销前核对是否重复报销同一晚。",
    "6. 票面发票号文本乱码的（部分电子发票），以二维码或开票平台记录为准。",
]
for n in notes:
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
    c = ws.cell(row=r, column=1, value=n)
    c.font = Font(name="微软雅黑", size=10, bold=(n == "说明："), color="595959")
    c.alignment = Alignment(vertical="center", wrap_text=True)
    ws.row_dimensions[r].height = 30 if len(n) > 40 else 16
    r += 1

for i, w in enumerate([13, 8, 42, 11, 24, 20, 42, 44], 1):
    ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "A3"

out = os.path.join(BASE, "报销明细记录.xlsx")
wb.save(out)
print("saved:", out, "| total:", round(total, 2), "|", {k: round(v, 2) for k, v in cat_sum.items()})
