#!/usr/bin/env bash
# ==============================================
#  Brevity AI — EC2 GPU Deployment Script
#  Instance: g4dn.xlarge (NVIDIA T4, 16GB VRAM)
#  AMI: Deep Learning AMI GPU PyTorch (Ubuntu 22.04)
# ==============================================
set -euo pipefail

echo "=========================================="
echo "  BREVITY AI — GPU BACKEND DEPLOYMENT"
echo "=========================================="

# 1. Install Tesseract OCR + language packs
echo ">>> [1/7] Installing Tesseract OCR..."
sudo apt-get update && sudo apt-get install -y --no-install-recommends \
  tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin tesseract-ocr-mar

# 2. Clone the repository
echo ">>> [2/7] Cloning Brevity-AI repository..."
cd /home/ubuntu
if [ -d "Brevity-AI" ]; then
  echo "    Directory exists, pulling latest..."
  cd Brevity-AI && git pull && cd ..
else
  git clone https://github.com/Anuj1718/Brevity-AI.git
fi
cd Brevity-AI/Backend

# 3. Create production .env
echo ">>> [3/7] Creating production .env..."
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "UNKNOWN")
cat > .env << ENVEOF
ALLOWED_ORIGINS=*
PUBLIC_DOMAIN=${PUBLIC_IP}
UPLOADS_DIR=/data/uploads
OUTPUTS_DIR=/data/outputs
TESSERACT_CMD=/usr/bin/tesseract
FREE_TIER_MODE=false
PORT=8000
BACKEND_HOST=0.0.0.0
ENVEOF

# 4. Build Docker image with GPU support
echo ">>> [4/7] Building Docker image (this takes 5-10 minutes)..."
sudo docker build -t brevity-gpu .

# 5. Stop any existing container
echo ">>> [5/7] Stopping any existing container..."
sudo docker rm -f brevity 2>/dev/null || true

# 6. Run container with GPU access
echo ">>> [6/7] Starting container with NVIDIA T4 GPU..."
sudo docker run -d \
  --name brevity \
  --gpus all \
  -p 8000:8000 \
  --env-file .env \
  -v brevity-uploads:/data/uploads \
  -v brevity-outputs:/data/outputs \
  --restart unless-stopped \
  brevity-gpu

# 7. Wait for startup and health check
echo ">>> [7/7] Waiting for server to start..."
for i in $(seq 1 12); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    HEALTH=$(curl -s http://localhost:8000/health)
    echo "    ✅ Health: $HEALTH"
    break
  fi
  echo "    Waiting... (attempt $i/12)"
  sleep 10
done

echo ""
echo "=========================================="
echo "  ✅ BACKEND IS LIVE!"
echo ""
echo "  API:    http://${PUBLIC_IP}:8000"
echo "  Docs:   http://${PUBLIC_IP}:8000/docs"
echo "  Health: http://${PUBLIC_IP}:8000/health"
echo ""
echo "  The BART model is preloading automatically."
echo "  Check status: curl http://localhost:8000/health"
echo "  (bart_loaded will be true when ready)"
echo ""
echo "  NEXT STEPS:"
echo "  1. Deploy frontend on Vercel:"
echo "     - Set VITE_API_URL=http://${PUBLIC_IP}:8000"
echo "     - Set VITE_FREE_TIER_MODE=false"
echo "  2. Update CORS after Vercel deploy:"
echo "     - Edit .env: ALLOWED_ORIGINS=https://your-app.vercel.app"
echo "     - Run: sudo docker restart brevity"
echo "=========================================="
