#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR"

if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

python download_nltk.py

export ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-http://localhost:5173,https://main.degqsw0mhmm75.amplifyapp.com}"
export PUBLIC_DOMAIN="${PUBLIC_DOMAIN:-brevity.duckdns.org}"
export UPLOADS_DIR="${UPLOADS_DIR:-$BASE_DIR/app/uploads}"
export OUTPUTS_DIR="${OUTPUTS_DIR:-$BASE_DIR/app/outputs}"

mkdir -p "$UPLOADS_DIR" "$OUTPUTS_DIR"

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"