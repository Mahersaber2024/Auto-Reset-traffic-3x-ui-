#!/usr/bin/env bash
set -e

APP_DIR="/opt/x3-traffic-reset"
REPO_URL="https://github.com/Mahersaber2024/Auto-Reset-traffic-3x-ui-.git"
SERVICE_USER="root"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo "🚀 Installing Traffic Reset Manager for 3xUI..."
echo ""

# ============================================
# Install prerequisites
# ============================================
export DEBIAN_FRONTEND=noninteractive
apt update
apt install -y git python3 python3-venv python3-pip curl

# ============================================
# Clone or update the project
# ============================================
if [ ! -d "$APP_DIR/.git" ]; then
  rm -rf "$APP_DIR"
  git clone --depth 1 "$REPO_URL" "$APP_DIR" || {
    echo -e "${RED}Git clone failed. Check repository URL.${NC}"
    exit 1
  }
else
  cd "$APP_DIR"
  git pull || {
    echo -e "${RED}Git pull failed.${NC}"
    exit 1
  }
fi

cd "$APP_DIR"

# ============================================
# Create the virtual environment
# ============================================
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ============================================
# Get settings from the user
# ============================================
echo ""
echo "⚙️ Please enter your 3xUI panel settings:"
read -p "Panel IP address or domain (e.g. 192.168.1.100): " PANEL_IP
read -p "Panel port (e.g. 2053): " PANEL_PORT
read -p "Username: " PANEL_USER
read -s -p "Password: " PANEL_PASS
echo ""

# ============================================
# Create the environment file (.env)
# ============================================
cat > .env <<EOF
PANEL_URL=https://${PANEL_IP}:${PANEL_PORT}
USERNAME=${PANEL_USER}
PASSWORD=${PANEL_PASS}
CONFIG_FILE=${APP_DIR}/config.conf
LOG_FILE=/var/log/x3-traffic-reset.log
EOF

# ============================================
# Copy configuration files
# ============================================
cp -f config.conf /etc/x3-traffic-reset/config.conf 2>/dev/null || mkdir -p /etc/x3-traffic-reset && cp config.conf /etc/x3-traffic-reset/

# ============================================
# Create the systemd service
# ============================================
cat > /etc/systemd/system/x3-tf.service <<EOF
[Unit]
Description=Traffic Reset Service for 3xUI
After=network.target

[Service]
User=$SERVICE_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/.venv/bin/python $APP_DIR/reset_daemon.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# ============================================
# Create the systemd timer
# ============================================
cat > /etc/systemd/system/x3-tf.timer <<EOF
[Unit]
Description=Timer for Traffic Reset Service
Requires=x3-tf.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

# ============================================
# Start the services
# ============================================
systemctl daemon-reload
systemctl enable x3-tf.timer
systemctl restart x3-tf.timer

# ============================================
# Show installation status
# ============================================
TIMER_STATUS=$(systemctl is-active x3-tf.timer || true)

echo ""
echo -e "${CYAN}_________________________________${NC}"
echo -e "${CYAN}_________________________________${NC}"

if [ "$TIMER_STATUS" = "active" ]; then
  echo -e "${GREEN}Traffic Reset Service: ACTIVE${NC}"
else
  echo -e "${RED}Traffic Reset Service: FAILED${NC}"
fi

echo -e "${GREEN}Config File:${NC} /etc/x3-traffic-reset/config.conf"
echo -e "${GREEN}Log File:${NC} /var/log/x3-traffic-reset.log"

echo -e "${CYAN}_________________________________${NC}"
echo -e "${CYAN}_________________________________${NC}"

# ============================================
# Service management guide
# ============================================
echo -e "\n${CYAN}================== MANAGEMENT GUIDE ==================${NC}"
echo -e "${YELLOW}To check service status:${NC}"
echo "  systemctl status x3-tf.timer"

echo -e "\n${YELLOW}To stop the service:${NC}"
echo "  systemctl stop x3-tf.timer"

echo -e "\n${YELLOW}To restart the service:${NC}"
echo "  systemctl restart x3-tf.timer"

echo -e "\n${YELLOW}To view service logs:${NC}"
echo "  journalctl -u x3-tf.service -f"

echo -e "\n${YELLOW}To manually run a reset:${NC}"
echo "  systemctl start x3-tf.service"

echo -e "\n${YELLOW}To edit user list:${NC}"
echo "  nano /etc/x3-traffic-reset/config.conf"

echo -e "\n${GREEN}Installation completed successfully!${NC}"
