import requests
import json
import time
import sys

BASE = "http://localhost:8000"

def test(name, method, url, **kwargs):
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"  {method} {url}")
    try:
        if method == "GET":
            r = requests.get(f"{BASE}{url}", timeout=120)
        elif method == "POST":
            r = requests.post(f"{BASE}{url}", timeout=120, **kwargs)
        print(f"  Status: {r.status_code}")
        try:
            data = r.json()
            # Print summary, not full response
            if isinstance(data, dict):
                for k, v in data.items():
                    val_str = str(v)[:100] + "..." if len(str(v)) > 100 else str(v)
                    print(f"  {k}: {val_str}")
            return r.status_code, data
        except:
            print(f"  Response: {r.text[:200]}")
            return r.status_code, r.text
    except Exception as e:
        print(f"  ERROR: {e}")
        return 0, str(e)

# Test 1: Health Check
code, data = test("Health Check", "GET", "/health")
assert code == 200, "Health check failed!"
assert data.get("bart_loaded") == True, "BART not loaded!"
print("  >>> PASS")

# Test 2: Upload PDF
print(f"\n{'='*60}")
print("TEST: Upload PDF")
# Create a simple test PDF
try:
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    text = """Artificial Intelligence and Machine Learning have transformed the way we interact with technology.
Deep learning models, particularly transformer-based architectures like BERT and GPT, have achieved
remarkable results in natural language processing tasks. These models are trained on vast amounts of
text data and can perform tasks such as text classification, question answering, and text generation.
The field continues to evolve rapidly, with new architectures and training techniques being developed
regularly. Transfer learning has become a standard practice, allowing models pre-trained on large
datasets to be fine-tuned for specific tasks with limited data. This approach has democratized AI,
making it accessible to researchers and practitioners with limited computational resources.
Computer vision has also seen significant advances, with models like ResNet, EfficientNet, and
Vision Transformers achieving superhuman performance on image classification benchmarks.
Natural language processing continues to push boundaries with large language models that can
understand context, generate coherent text, and even write code."""
    page.insert_text((50, 50), text, fontsize=10)
    pdf_path = "/tmp/test_brevity.pdf"
    doc.save(pdf_path)
    doc.close()
    print(f"  Created test PDF: {pdf_path}")
except Exception as e:
    print(f"  Could not create PDF with fitz: {e}")
    # Fallback: use an existing PDF
    import glob
    pdfs = glob.glob("/data/uploads/*.pdf")
    if pdfs:
        pdf_path = pdfs[0]
        print(f"  Using existing PDF: {pdf_path}")
    else:
        print("  No PDF available for testing!")
        sys.exit(1)

with open(pdf_path, "rb") as f:
    code, data = test("Upload PDF", "POST", "/api/upload/pdf", files={"file": ("test.pdf", f, "application/pdf")})
assert code == 200, f"Upload failed with {code}!"
filename = data.get("filename", "")
print(f"  >>> PASS - Filename: {filename}")

# Test 3: Detect Text Type
code, data = test("Detect Text Type", "GET", f"/api/extract/detect-text-type/{filename}")
if code == 200:
    print("  >>> PASS")
elif code == 404:
    print("  >>> SKIP (endpoint may not exist)")

# Test 4: Extract Text
code, data = test("Extract Text", "POST", f"/api/extract/text/{filename}?use_ocr=false&lang=eng&chunk_size=50")
assert code == 200, f"Extract failed with {code}!"
print("  >>> PASS")

# Test 5: Clean Text
code, data = test("Clean Text", "POST", f"/api/clean/text/{filename}?remove_stopwords=true&normalize_whitespace=true&remove_special_chars=true&min_sentence_length=15&ocr_mode=false")
assert code == 200, f"Clean failed with {code}!"
print("  >>> PASS")

# Test 6: Extractive Summary (TextRank)
code, data = test("Extractive Summary (TextRank)", "POST", f"/api/summarize/extractive/{filename}?use_cache=true&summary_ratio=0.35&algorithm=textrank")
assert code == 200, f"Extractive summary failed with {code}!"
print("  >>> PASS")

# Test 7: Extractive Summary (TF-IDF)
code, data = test("Extractive Summary (TF-IDF)", "POST", f"/api/summarize/extractive/{filename}?use_cache=false&summary_ratio=0.35&algorithm=tfidf")
assert code == 200, f"TF-IDF summary failed with {code}!"
print("  >>> PASS")

# Test 8: Extractive Summary (LSA)
code, data = test("Extractive Summary (LSA)", "POST", f"/api/summarize/extractive/{filename}?use_cache=false&summary_ratio=0.35&algorithm=lsa")
assert code == 200, f"LSA summary failed with {code}!"
print("  >>> PASS")

# Test 9: Abstractive Summary (BART)
print("\n  (This may take 10-30 seconds for model inference...)")
start = time.time()
code, data = test("Abstractive Summary (BART)", "POST", f"/api/summarize/abstractive/{filename}?max_length=150&min_length=40&model=facebook/bart-large-cnn&use_pipeline=true")
elapsed = time.time() - start
print(f"  Time: {elapsed:.1f}s")
assert code == 200, f"Abstractive summary failed with {code}! Response: {data}"
print("  >>> PASS")

# Test 10: Hybrid Summary
start = time.time()
code, data = test("Hybrid (Formatted) Summary", "POST", f"/api/summarize/formatted-hybrid/{filename}?extractive_ratio=0.5&max_length=200&min_length=50&use_pipeline=true")
elapsed = time.time() - start
print(f"  Time: {elapsed:.1f}s")
if code == 200:
    print("  >>> PASS")
else:
    print(f"  >>> WARN - Status {code}")

# Test 11: Translation
code, data = test("Translate to Hindi", "POST", f"/api/translate/summary/{filename}?target_language=hindi&summary_type=extractive")
if code == 200:
    print("  >>> PASS")
else:
    print(f"  >>> WARN - Status {code} (translation may need external API)")

print(f"\n{'='*60}")
print("ALL CRITICAL TESTS PASSED!" if True else "SOME TESTS FAILED!")
print(f"{'='*60}")
