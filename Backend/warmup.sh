#!/usr/bin/env bash
# ==============================================
#  Brevity AI — Model Pre-Warming Script
#  Run this BEFORE your review to download and
#  load all ML models into GPU memory.
# ==============================================
set -euo pipefail

API="http://localhost:8000"

echo "=========================================="
echo "  BREVITY AI — MODEL PRE-WARMING"
echo "=========================================="

# Check if server is running
echo ">>> Checking server health..."
if ! curl -sf "$API/health" > /dev/null 2>&1; then
  echo "❌ Server is not running! Start it first."
  exit 1
fi
echo "    ✅ Server is healthy"

# Create a simple test PDF with enough text for summarization
echo ">>> Creating test PDF..."
python3 -c "
import struct
# Create a minimal but valid PDF with enough text for summarization
text = '''Machine learning is a subset of artificial intelligence that focuses on building systems
that learn from data. Unlike traditional programming where rules are explicitly coded, machine
learning algorithms use statistical techniques to give computers the ability to learn from data
without being explicitly programmed. Deep learning, a further subset of machine learning, uses
neural networks with many layers to analyze various factors of data. Natural language processing
enables computers to understand, interpret, and generate human language. Text summarization is
one important application of NLP that automatically creates a concise summary of a longer text
document. There are two main approaches: extractive summarization selects key sentences from the
original text, while abstractive summarization generates new sentences that capture the main ideas.
The BART model by Facebook AI is widely used for abstractive summarization tasks and produces
high quality results. Hybrid approaches combine both extractive and abstractive methods for better
accuracy. Translation systems convert text between languages using sequence to sequence models.
Optical character recognition extracts text from scanned documents and images. These technologies
together form a comprehensive document processing pipeline that can handle diverse input formats
and produce meaningful summaries in multiple languages.'''
pdf = b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n'
pdf += b'2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n'
pdf += b'3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n'
pdf += b'5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n'
content = f'BT /F1 10 Tf 50 750 Td ({text}) Tj ET'
content_bytes = content.encode()
pdf += f'4 0 obj<</Length {len(content_bytes)}>>stream\n'.encode()
pdf += content_bytes
pdf += b'\nendstream\nendobj\n'
xref_pos = len(pdf)
pdf += b'xref\n0 6\n'
pdf += b'0000000000 65535 f \n'
pdf += b'0000000009 00000 n \n'
pdf += b'0000000058 00000 n \n'
pdf += b'0000000115 00000 n \n'
pdf += b'0000000306 00000 n \n'
pdf += b'0000000259 00000 n \n'
pdf += b'trailer<</Size 6/Root 1 0 R>>\n'
pdf += b'startxref\n'
pdf += str(xref_pos).encode()
pdf += b'\n%%EOF'
with open('/tmp/warmup_test.pdf', 'wb') as f:
    f.write(pdf)
print('    ✅ Test PDF created')
"

# Upload the test PDF
echo ">>> Uploading test PDF..."
UPLOAD_RESPONSE=$(curl -sf -X POST -F "file=@/tmp/warmup_test.pdf" "$API/api/upload/pdf")
echo "    ✅ Upload response: $UPLOAD_RESPONSE"

# Extract filename from response
FILENAME=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('filename','warmup_test.pdf'))" 2>/dev/null || echo "warmup_test.pdf")
echo "    Using filename: $FILENAME"

# Extract text
echo ">>> Extracting text..."
curl -sf -X POST "$API/api/extract/text/$FILENAME" > /dev/null
echo "    ✅ Text extracted"

# Clean text
echo ">>> Cleaning text..."
curl -sf -X POST "$API/api/clean/text/$FILENAME" > /dev/null
echo "    ✅ Text cleaned"

# Extractive summary (TextRank)
echo ">>> Warming up Extractive Summary (TextRank)..."
curl -sf -X POST "$API/api/summarize/extractive/$FILENAME?algorithm=textrank" > /dev/null
echo "    ✅ Extractive (TextRank) ready"

# Extractive summary (TF-IDF)
echo ">>> Warming up Extractive Summary (TF-IDF)..."
curl -sf -X POST "$API/api/summarize/extractive/$FILENAME?algorithm=tfidf" > /dev/null
echo "    ✅ Extractive (TF-IDF) ready"

# Extractive summary (LSA)
echo ">>> Warming up Extractive Summary (LSA)..."
curl -sf -X POST "$API/api/summarize/extractive/$FILENAME?algorithm=lsa" > /dev/null
echo "    ✅ Extractive (LSA) ready"

# Abstractive summary (BART) — THIS DOWNLOADS THE 1.6 GB MODEL
echo ">>> Warming up Abstractive Summary (BART-large-CNN)..."
echo "    ⏳ First run downloads ~1.6 GB model — wait 2-3 minutes..."
curl -sf --max-time 600 -X POST "$API/api/summarize/abstractive/$FILENAME" > /dev/null
echo "    ✅ Abstractive (BART) ready — model loaded on GPU!"

# Hybrid summary
echo ">>> Warming up Hybrid Summary..."
curl -sf --max-time 600 -X POST "$API/api/summarize/hybrid/$FILENAME" > /dev/null
echo "    ✅ Hybrid ready"

# Translation to Hindi
echo ">>> Warming up Translation (Hindi)..."
curl -sf --max-time 120 -X POST "$API/api/translate/summary/$FILENAME?target_language=hindi&summary_type=extractive" > /dev/null
echo "    ✅ Hindi translation ready"

# Translation to Marathi
echo ">>> Warming up Translation (Marathi)..."
curl -sf --max-time 120 -X POST "$API/api/translate/summary/$FILENAME?target_language=marathi&summary_type=extractive" > /dev/null
echo "    ✅ Marathi translation ready"

# Check GPU utilization
echo ""
echo ">>> GPU Status:"
nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>/dev/null || echo "    (nvidia-smi not available outside container)"

echo ""
echo "=========================================="
echo "  ✅ ALL MODELS PRE-WARMED AND READY!"
echo ""
echo "  BART model is loaded on GPU memory."
echo "  Abstractive summaries will now run in 2-5 seconds."
echo "  You are ready for your review! 🎉"
echo "=========================================="
