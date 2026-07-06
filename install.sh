#!/usr/bin/env bash
set -e

APP_DIR="/opt/x3-traffic-reset"
REPO_URL="https://github.com/Mahersaber2024/Auto-Reset-traffic-3x-ui-.git"
SERVICE_USER="root"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'
BOLD='\033[1m'

echo -e "${BOLD}${CYAN}🚀 Installing Traffic Reset Manager for 3xUI...${NC}"
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
    echo -e "${RED}❌ Git clone failed. Check repository URL.${NC}"
    exit 1
  }
else
  cd "$APP_DIR"
  git pull || {
    echo -e "${RED}❌ Git pull failed.${NC}"
    exit 1
  }
fi

cd "$APP_DIR"

# ============================================
# Create the virtual environment
# ============================================
echo -e "${BLUE}🐍 Creating virtual environment...${NC}"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ============================================
# Get settings from the user
# ============================================
echo ""
echo -e "${BOLD}${YELLOW}⚙️ Please enter your 3xUI panel settings:${NC}"
read -p "Panel IP address or domain (e.g. 192.168.1.100): " PANEL_IP
read -p "Panel port (e.g. 2053): " PANEL_PORT
read -p "Web Base Path (e.g. /KqOZWNk3zx7VDf1pDS, or press Enter if none): " PANEL_PATH
read -p "Username: " PANEL_USER
read -s -p "Password: " PANEL_PASS
echo ""

# ============================================
# Create the environment file (.env)
# ============================================
cat > .env <<EOF
PANEL_BASE=https://${PANEL_IP}:${PANEL_PORT}${PANEL_PATH}
USERNAME=${PANEL_USER}
PASSWORD=${PANEL_PASS}
CONFIG_FILE=${APP_DIR}/config.conf
LOG_FILE=/var/log/x3-traffic-reset.log
EOF

# ============================================
# Copy configuration files
# ============================================
mkdir -p /etc/x3-traffic-reset
cp -f config.conf /etc/x3-traffic-reset/config.conf

# ============================================
# Install the management script (NEW)
# ============================================
echo -e "${BLUE}📋 Installing management script...${NC}"
sudo cp -f manager.py /usr/local/bin/x3-tf
sudo chmod +x /usr/local/bin/x3-tf

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
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║         ${BOLD}✅ INSTALLATION COMPLETED SUCCESSFULLY${NC}${CYAN}         ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================
# Service Status
# ============================================
echo -e "${BOLD}${BLUE}📊 SERVICE STATUS${NC}"
echo -e "${CYAN}──────────────────────────────────────────────────────────────${NC}"

if [ "$TIMER_STATUS" = "active" ]; then
  echo -e "  ${GREEN}●${NC} Traffic Reset Service: ${GREEN}ACTIVE${NC} ✓"
else
  echo -e "  ${RED}●${NC} Traffic Reset Service: ${RED}FAILED${NC} ✗"
fi

echo -e "  ${BLUE}●${NC} Config File: ${WHITE}/etc/x3-traffic-reset/config.conf${NC}"
echo -e "  ${BLUE}●${NC} Log File: ${WHITE}/var/log/x3-traffic-reset.log${NC}"
echo -e "  ${BLUE}●${NC} Install Dir: ${WHITE}${APP_DIR}${NC}"
echo ""

# ============================================
# How to Run the Menu
# ============================================
echo -e "${BOLD}${PURPLE}🎮 HOW TO RUN THE MANAGEMENT MENU${NC}"
echo -e "${CYAN}──────────────────────────────────────────────────────────────${NC}"
echo -e "  ${YELLOW}Just type:${NC} ${BOLD}${WHITE}x3-tf${NC}"
echo -e "  ${YELLOW}Or:${NC}         ${BOLD}${WHITE}sudo x3-tf${NC}"
echo ""
echo -e "  ${GREEN}▶${NC} This will open the interactive menu where you can:"
echo -e "     ${WHITE}•${NC} Add/remove users from auto-reset list"
echo -e "     ${WHITE}•${NC} Change reset interval (hourly, daily, custom)"
echo -e "     ${WHITE}•${NC} Run manual reset"
echo -e "     ${WHITE}•${NC} View logs"
echo ""

# ============================================
# Service Management Guide
# ============================================
echo -e "${BOLD}${CYAN}🔧 SERVICE MANAGEMENT${NC}"
echo -e "${CYAN}──────────────────────────────────────────────────────────────${NC}"
echo -e "  ${GREEN}▶${NC} Check status:     ${WHITE}systemctl status x3-tf.timer${NC}"
echo -e "  ${GREEN}▶${NC} Stop service:     ${WHITE}systemctl stop x3-tf.timer${NC}"
echo -e "  ${GREEN}▶${NC} Start service:    ${WHITE}systemctl start x3-tf.timer${NC}"
echo -e "  ${GREEN}▶${NC} Restart service:  ${WHITE}systemctl restart x3-tf.timer${NC}"
echo -e "  ${GREEN}▶${NC} View logs:        ${WHITE}journalctl -u x3-tf.service -f${NC}"
echo -e "  ${GREEN}▶${NC} Manual reset:     ${WHITE}systemctl start x3-tf.service${NC}"
echo ""

# ============================================
# Edit User List
# ============================================
echo -e "${BOLD}${YELLOW}📝 EDIT USER LIST${NC}"
echo -e "${CYAN}──────────────────────────────────────────────────────────────${NC}"
echo -e "  ${WHITE}nano /etc/x3-traffic-reset/config.conf${NC}"
echo -e "  ${YELLOW}💡${NC} Add one User ID per line (find IDs in 3xUI panel)"
echo ""

# ============================================
# Support
# ============================================
echo -e "${BOLD}${PURPLE}🌟 SPONSOR${NC}"
echo -e "${CYAN}──────────────────────────────────────────────────────────────${NC}"
echo -e "  ${BOLD}HeySolo${NC} - ${WHITE}https://t.me/HeySoloATM${NC}"
echo ""

echo -e "${GREEN}${BOLD}🎯 Quick Start:${NC} Just run ${BOLD}x3-tf${NC} to start managing your users!${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
