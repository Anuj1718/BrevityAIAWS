import fitz
try:
    doc = fitz.open("/data/uploads/20260621_100903_DT20268015982_OL.pdf")
    print(f"Pages: {doc.page_count}")
    print(f"Encrypted: {doc.is_encrypted}")
    print(f"Needs pass: {doc.needs_pass}")
    page = doc[0]
    text = page.get_text()
    print(f"Text preview: {text[:200]}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
