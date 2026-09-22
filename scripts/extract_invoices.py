import email, os, sys, json
from email import policy

SRC = r"<工作目录>\出差报销\_原始邮件附件"

def decode_hdr(v):
    if not v:
        return ""
    from email.header import decode_header, make_header
    try:
        return str(make_header(decode_header(v)))
    except Exception:
        return str(v)

for fn in sorted(os.listdir(SRC)):
    path = os.path.join(SRC, fn)
    if not os.path.isfile(path):
        continue
    print("=" * 70)
    print("FILE:", fn)
    if not fn.lower().endswith(".eml"):
        print("  (not eml, size=%d)" % os.path.getsize(path))
        continue
    with open(path, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)
    print("  subj:", decode_hdr(msg.get("Subject")))
    print("  from:", decode_hdr(msg.get("From")))
    print("  date:", msg.get("Date"))
    for i, part in enumerate(msg.walk()):
        if part.get_content_maintype() == "multipart":
            continue
        ctype = part.get_content_type()
        fname = part.get_filename()
        if fname:
            fname = decode_hdr(fname)
        payload = part.get_payload(decode=True)
        size = len(payload) if payload else 0
        print("   [%d] %s | name=%s | size=%d" % (i, ctype, fname, size))
        if ctype in ("text/plain", "text/html") and payload:
            try:
                txt = payload.decode(part.get_content_charset() or "utf-8", "ignore")
            except Exception:
                txt = ""
            txt = txt.replace("\r", "").replace("\n", " ")[:1200]
            print("        TEXT:", txt)
