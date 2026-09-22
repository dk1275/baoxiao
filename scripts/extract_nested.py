import email, os, zipfile, re
from email import policy
from email.header import decode_header, make_header

BASE = r"<工作目录>\出差报销"
SRC = os.path.join(BASE, "_原始邮件附件")
TMP = os.path.join(BASE, "_tmp_extract")
os.makedirs(TMP, exist_ok=True)

def dh(v):
    if not v:
        return ""
    try:
        return str(make_header(decode_header(v)))
    except Exception:
        return str(v)

def clean(name):
    # 去掉乱码/非法字符
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    name = re.sub(r'[^\w\u4e00-\u9fff.\-\(\)（）\[\]【】]', '', name)
    return name.strip()

# 1. 抽取 eml 内嵌附件
for fn in sorted(os.listdir(SRC)):
    p = os.path.join(SRC, fn)
    if not fn.lower().endswith(".eml"):
        continue
    with open(p, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)
    stem = os.path.splitext(fn)[0]
    out = os.path.join(TMP, clean(stem)[:40])
    os.makedirs(out, exist_ok=True)
    n = 0
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        fname = part.get_filename()
        if not fname:
            continue
        fname = dh(fname)
        if fname.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        safe = clean(fname)
        if not os.path.splitext(safe)[1]:
            safe += ".bin"
        with open(os.path.join(out, safe), "wb") as w:
            w.write(payload)
        n += 1
    print("eml:", stem[:35], "->", n, "files")

# 2. 拷贝/解压顶层 zip
for fn in sorted(os.listdir(SRC)):
    p = os.path.join(SRC, fn)
    if fn.lower().endswith(".zip"):
        out = os.path.join(TMP, clean(os.path.splitext(fn)[0])[:40])
        os.makedirs(out, exist_ok=True)
        with zipfile.ZipFile(p) as z:
            for zinfo in z.infolist():
                raw = zinfo.filename
                try:
                    nm = raw.encode("cp437").decode("gbk")
                except Exception:
                    nm = raw
                nm = clean(os.path.basename(nm))
                if not nm:
                    continue
                data = z.read(zinfo)
                with open(os.path.join(out, nm), "wb") as w:
                    w.write(data)
        print("zip:", fn, "->", os.listdir(out))

print("\n--- TMP TREE ---")
for root, dirs, files in os.walk(TMP):
    for f in files:
        fp = os.path.join(root, f)
        print(os.path.relpath(fp, TMP), "|", os.path.getsize(fp))
