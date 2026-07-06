#!/bin/bash
# uninstall.sh - Uninstall Traffic Reset Manager

set -e

APP_DIR="/opt/x3-traffic-reset"
CONFIG_DIR="/etc/x3-traffic-reset"
VENV_DIR="/opt/x3-traffic-reset-venv"
INSTALL_DIR="/usr/local/bin"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${YELLOW}🗑️  Uninstalling Traffic Reset Manager...${NC}"
echo ""

# ============================================
# Stop and disable services
# ============================================
echo -e "${CYAN}⏹️  Stopping services...${NC}"
sudo systemctl stop x3-tf.timer 2>/dev/null || true
sudo systemctl disable x3-tf.timer 2>/dev/null || true
sudo systemctl stop x3-tf.service 2>/dev/null || true
sudo systemctl disable x3-tf.service 2>/dev/null || true

# ============================================
# Remove service files
# ============================================
echo -e "${CYAN}🗑️  Removing service files...${NC}"
sudo rm -f /etc/systemd/system/x3-tf.service
sudo rm -f /etc/systemd/system/x3-tf.timer
sudo systemctl daemon-reload

# ============================================
# Remove installed files and directories
# ============================================
echo -e "${CYAN}🗑️  Removing installed files...${NC}"
sudo rm -rf "$APP_DIR"
sudo rm -rf "$CONFIG_DIR"
sudo rm -rf "$VENV_DIR"
sudo rm -f "$INSTALL_DIR/x3-tf"
sudo rm -f "$INSTALL_DIR/reset_daemon.py"
sudo rm -f "$INSTALL_DIR/manager.py"
sudo rm -f /var/log/x3-traffic-reset.log
sudo rm -f /tmp/requirements.txt

# ============================================
# Final message
# ============================================
echo ""
echo -e "${GREEN}✅ Uninstallation completed successfully!${NC}"
echo ""
echo -e "${CYAN}📋 Removed:${NC}"
echo "  - Systemd services (x3-tf.service, x3-tf.timer)"
echo "  - Application directory: $APP_DIR"
echo "  - Configuration directory: $CONFIG_DIR"
echo "  - Virtual environment: $VENV_DIR"
echo "  - Symlinks and scripts in /usr/local/bin"
echo "  - Log files"
