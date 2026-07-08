#!/usr/bin/env bash
# Full server setup for Smart School Canteen API
# Run on the VPS as root: bash setup-server.sh

set -euo pipefail

APP_DIR="/opt/canteen-server"
REPO_URL="https://github.com/mohammedhamza123/School-system-and-smart-canteen-server.git"
SERVICE_NAME="canteen-api"
PORT=8000

echo "==> Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git python3 python3-pip python3-venv curl

echo "==> Cloning or updating repository..."
if [ -d "$APP_DIR/.git" ]; then
  cd "$APP_DIR"
  git pull origin main
else
  rm -rf "$APP_DIR"
  git clone "$REPO_URL" "$APP_DIR"
  cd "$APP_DIR"
fi

echo "==> Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "==> Creating environment file..."
if [ ! -f "$APP_DIR/.env" ]; then
  JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")
  cat > "$APP_DIR/.env" <<EOF
JWT_SECRET_KEY=${JWT_SECRET}
FIREBASE_NOTIFICATIONS_ENABLED=false
EOF
  echo "Created .env (Firebase disabled until you upload firebase-service-account.json)"
fi

echo "==> Creating systemd service..."
cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=Smart School Canteen API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
Environment=FIREBASE_CREDENTIALS_PATH=${APP_DIR}/firebase-service-account.json
ExecStart=${APP_DIR}/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "==> Enabling and starting service..."
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"

echo "==> Opening firewall port ${PORT} (if ufw is active)..."
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
  ufw allow "${PORT}/tcp" || true
fi

sleep 2
echo ""
echo "==> Service status:"
systemctl status "${SERVICE_NAME}" --no-pager -l || true

echo ""
echo "==> Health check:"
curl -sf "http://127.0.0.1:${PORT}/health" && echo "" || echo "Health check failed - check: journalctl -u ${SERVICE_NAME} -n 50"

echo ""
echo "============================================"
echo " Deployment complete!"
echo " API URL: http://$(curl -sf ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}'):${PORT}"
echo " Docs:    http://SERVER_IP:${PORT}/docs"
echo " Health:  http://SERVER_IP:${PORT}/health"
echo ""
echo " Next steps:"
echo " 1. Upload firebase-service-account.json to ${APP_DIR}/"
echo " 2. Set FIREBASE_NOTIFICATIONS_ENABLED=true in ${APP_DIR}/.env"
echo " 3. systemctl restart ${SERVICE_NAME}"
echo "============================================"
