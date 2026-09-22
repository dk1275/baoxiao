# -*- coding: utf-8 -*-
"""按要求精简：只留发票，删结账单/明细单；行程单归入 打车/行程单"""
import os, ctypes, ctypes.wintypes, shutil

B = r"<工作目录>\出差报销"

class SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = [("hwnd", ctypes.wintypes.HWND),
                ("wFunc", ctypes.wintypes.UINT),
                ("pFrom", ctypes.wintypes.LPCWSTR),
                ("pTo", ctypes.wintypes.LPCWSTR),
                ("fFlags", ctypes.c_uint16),
                ("fAnyOperationsAborted", ctypes.wintypes.BOOL),
                ("hNameMappings", ctypes.c_void_p),
                ("lpszProgressTitle", ctypes.wintypes.LPCWSTR)]

FO_DELETE, FOF_ALLOWUNDO, FOF_NOCONFIRMATION, FOF_SILENT = 3, 0x0040, 0x0010, 0x0004

def recycle(paths):
    p = "\0".join(paths) + "\0\0"
    op = SHFILEOPSTRUCTW(None, FO_DELETE, p, None,
                         FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT, False, None, None)
    return ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))

# 1. 删除非发票凭证（结账单 / 消费明细单）—— 送回收站
kill = []
for d in ["酒店", "请客户", "打车", "机票"]:
    p = os.path.join(B, d)
    if not os.path.isdir(p):
        continue
    for f in os.listdir(p):
        if "结账单" in f or "明细单" in f:
            kill.append(os.path.join(p, f))
if kill:
    r = recycle(kill)
    print("recycle(非发票凭证) result:", r)
    for k in kill:
        print("   removed:", os.path.relpath(k, B), "| exists:", os.path.exists(k))
else:
    print("no 结账单/明细单 found")

# 2. 行程单归入 打车/行程单
trip_dir = os.path.join(B, "打车", "行程单")
os.makedirs(trip_dir, exist_ok=True)
moved = 0
for f in os.listdir(os.path.join(B, "打车")):
    p = os.path.join(B, "打车", f)
    if os.path.isfile(p) and "行程单" in f:
        shutil.move(p, os.path.join(trip_dir, f))
        moved += 1
print("moved 行程单:", moved)

print("\n=== FINAL ===")
for root, dirs, files in os.walk(B):
    d = os.path.relpath(root, B)
    if d.startswith("_"):
        print("[%s] %d files" % (d, len(files)))
        continue
    print("[%s] %d" % (d, len(files)))
    for f in sorted(files):
        print("   ", f)
