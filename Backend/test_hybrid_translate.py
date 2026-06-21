import requests
import fitz

BASE = "http://localhost:8000"

# Upload test PDF
doc = fitz.open()
page = doc.new_page()
page.insert_text((50, 50), "Artificial Intelligence and Machine Learning have transformed technology. Deep learning models like BERT and GPT achieved remarkable results. Transfer learning has become standard practice.", fontsize=10)
doc.save("/tmp/test_trans.pdf")
doc.close()

with open("/tmp/test_trans.pdf", "rb") as f:
    r = requests.post(f"{BASE}/api/upload/pdf", files={"file": ("test.pdf", f)})
fn = r.json()["filename"]
print(f"Uploaded: {fn}")

# Extract + Clean
requests.post(f"{BASE}/api/extract/text/{fn}?use_ocr=false")
requests.post(f"{BASE}/api/clean/text/{fn}?remove_stopwords=true&normalize_whitespace=true&remove_special_chars=true&min_sentence_length=10")
print("Extracted + Cleaned")

# Formatted Hybrid Summary
r = requests.post(f"{BASE}/api/summarize/formatted-hybrid/{fn}?extractive_ratio=0.5&max_length=200&min_length=30")
print(f"Hybrid Summary: {r.status_code}")

# Translate Hybrid to Hindi
r = requests.post(f"{BASE}/api/translate/summary/{fn}?target_language=hindi&summary_type=formatted-hybrid")
data = r.json()
print(f"Translate Hindi: {r.status_code} - {data.get('message', data.get('detail', ''))}")
if r.status_code == 200:
    print(f"  Translation: {data.get('translated_summary', '')[:100]}...")

# Translate Hybrid to Marathi
r = requests.post(f"{BASE}/api/translate/summary/{fn}?target_language=marathi&summary_type=formatted-hybrid")
data = r.json()
print(f"Translate Marathi: {r.status_code} - {data.get('message', data.get('detail', ''))}")
if r.status_code == 200:
    print(f"  Translation: {data.get('translated_summary', '')[:100]}...")

print("ALL DONE!")
