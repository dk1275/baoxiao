# -*- coding: utf-8 -*-
import os, ctypes, ctypes.wintypes, shutil

B = r"<工作目录>\出差报销"

# ---------- 1. OFD 送回收站 ----------
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
    res = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    return res, op.fAnyOperationsAborted

ofds = []
for root, dirs, files in os.walk(B):
    for f in files:
        if f.lower().endswith(".ofd"):
            ofds.append(os.path.join(root, f))
if ofds:
    res, aborted = recycle(ofds)
    print("recycle result:", res, "aborted:", aborted, "count:", len(ofds))
    for p in ofds:
        print("   removed:", os.path.relpath(p, B), "| still exists:", os.path.exists(p))

# ---------- 2. 重构目录 ----------
NEW = ["酒店", "请客户", "打车", "高铁", "机票"]
for d in NEW:
    os.makedirs(os.path.join(B, d), exist_ok=True)

def move(src, dst_dir, newname=None):
    if not os.path.exists(src):
        print("  MISS:", src); return
    dst = os.path.join(B, dst_dir, newname or os.path.basename(src))
    shutil.move(src, dst)
    print("  ->", dst_dir + "/" + os.path.basename(dst))

# 酒店
for f in os.listdir(os.path.join(B, "02_住宿")):
    move(os.path.join(B, "02_住宿", f), "酒店")
# 请客户
for f in os.listdir(os.path.join(B, "03_餐饮")):
    move(os.path.join(B, "03_餐饮", f), "请客户")
# 打车
for f in os.listdir(os.path.join(B, "01_交通", "高德打车")):
    move(os.path.join(B, "01_交通", "高德打车", f), "打车")
for f in os.listdir(os.path.join(B, "01_交通")):
    p = os.path.join(B, "01_交通", f)
    if os.path.isfile(p):
        if "通行费" in f:
            move(p, "打车", f.replace("通行费发票", "高速过路费"))
        elif "机票" in f or "乘机" in f:
            move(p, "机票")
        else:
            move(p, "打车")

# 清理旧空目录
for old in ["01_交通", "02_住宿", "03_餐饮", "04_其他"]:
    p = os.path.join(B, old)
    if os.path.isdir(p):
        rest = []
        for root, dirs, files in os.walk(p):
            rest += files
        if not rest:
            shutil.rmtree(p)
            print("  removed empty dir:", old)
        else:
            print("  NOT empty:", old, rest)

print("\n=== FINAL TREE ===")
for root, dirs, files in os.walk(B):
    d = os.path.relpath(root, B)
    if d == ".":
        d = "(根)"
    print("[%s] %d" % (d, len(files)))
