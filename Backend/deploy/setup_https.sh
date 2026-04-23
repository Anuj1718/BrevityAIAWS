#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/ubuntu/BrevityAIAWS/Backend}"
DOMAIN="${PUBLIC_DOMAIN:-brevity.duckdns.org}"
ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-https://main.degqsw0mhmm75.amplifyapp.com,http://localhost:5173}"

if ! command -v caddy >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
  sudo apt-get update
  sudo apt-get install -y caddy
fi

sudo tee /etc/systemd/system/brevity-backend.service >/dev/null <<EOF
[Unit]
Description=Brevity AI backend API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=${APP_DIR}
Environment="ALLOWED_ORIGINS=${ALLOWED_ORIGINS}"
Environment="PUBLIC_DOMAIN=${DOMAIN}"
Environment="BACKEND_HOST=127.0.0.1"
Environment="PORT=8000"
ExecStart=${APP_DIR}/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/caddy/Caddyfile >/dev/null <<EOF
${DOMAIN} {
  encode gzip zstd
  reverse_proxy 127.0.0.1:8000
}
EOF

sudo systemctl daemon-reload
sudo systemctl enable brevity-backend
sudo systemctl restart brevity-backend
sudo systemctl enable caddy
sudo systemctl restart caddy

echo "Backend service and Caddy reverse proxy installed."
echo "Point ${DOMAIN} to this instance, then verify: https://${DOMAIN}/health"