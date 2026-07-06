#!/bin/bash
# install.sh - Install Traffic Reset Manager (Python version)

set -e

REPO_URL="https://raw.githubusercontent.com/Mahersaber2024/Auto-Reset-traffic-3x-ui-/main"
INSTALL_DIR="/usr/local/bin"
CONFIG_DIR="/etc/x3-traffic-reset"
SERVICE_DIR="/etc/systemd/system"
VENV_DIR="/opt/x3-traffic-reset-venv"

echo "🚀 Installing Traffic Reset Manager (Python version)..."
echo ""

# Check Python and install venv if needed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Installing..."
    apt-get update && apt-get install -y python3 python3-pip python3-venv
fi

# Create virtual environment
echo "🐍 Creating virtual environment..."
sudo python3 -m venv "$VENV_DIR"
sudo "$VENV_DIR/bin/pip" install --upgrade pip

# Create directories
sudo mkdir -p "$CONFIG_DIR"
sudo mkdir -p "/var/log"

# Download files
echo "📥 Downloading required files..."
sudo curl -s -o "$INSTALL_DIR/reset_daemon.py" "$REPO_URL/reset_daemon.py"
sudo curl -s -o "$INSTALL_DIR/manager.py" "$REPO_URL/manager.py"
sudo curl -s -o "$CONFIG_DIR/config.conf" "$REPO_URL/config.conf"
sudo curl -s -o "$SERVICE_DIR/x3-tf.service" "$REPO_URL/x3-tf.service"
sudo curl -s -o "$SERVICE_DIR/x3-tf.timer" "$REPO_URL/x3-tf.timer"
sudo curl -s -o "/tmp/requirements.txt" "$REPO_URL/requirements.txt"

# Install Python dependencies in venv
echo "📦 Installing Python dependencies in virtual environment..."
sudo "$VENV_DIR/bin/pip" install -r /tmp/requirements.txt

# Set permissions
sudo chmod +x "$INSTALL_DIR/reset_daemon.py"
sudo chmod +x "$INSTALL_DIR/manager.py"
sudo chmod 600 "$CONFIG_DIR/config.conf"

# Fix shebang to use venv Python
sudo sed -i "1s|^#!/usr/bin/env python3|#!$VENV_DIR/bin/python3|" "$INSTALL_DIR/reset_daemon.py"
sudo sed -i "1s|^#!/usr/bin/env python3|#!$VENV_DIR/bin/python3|" "$INSTALL_DIR/manager.py"

# Create symlink
sudo ln -sf "$INSTALL_DIR/manager.py" "$INSTALL_DIR/x3-tf"

# Ask for panel settings
echo ""
echo "⚙️ Please enter your 3xUI panel settings:"
read -p "Panel IP address or domain (e.g. 192.168.1.100): " PANEL_IP
read -p "Panel port (e.g. 2053): " PANEL_PORT
read -p "Username: " PANEL_USER
read -s -p "Password: " PANEL_PASS
echo ""

# Apply settings to Python script
sudo sed -i "s|PANEL_URL = \".*\"|PANEL_URL = \"https://${PANEL_IP}:${PANEL_PORT}\"|" "$INSTALL_DIR/reset_daemon.py"
sudo sed -i "s/USERNAME = \".*\"/USERNAME = \"${PANEL_USER}\"/" "$INSTALL_DIR/reset_daemon.py"
sudo sed -i "s/PASSWORD = \".*\"/PASSWORD = \"${PANEL_PASS}\"/" "$INSTALL_DIR/reset_daemon.py"

# Enable service
echo "🔧 Enabling service (default interval: daily)..."
sudo systemctl daemon-reload
sudo systemctl enable x3-tf.timer
sudo systemctl start x3-tf.timer

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "📋 You can now run: x3-tf"
echo ""
echo "📋 Useful commands:"
echo "  - Open manager:        sudo x3-tf"
echo "  - Check timer status:  sudo systemctl status x3-tf.timer"
echo "  - View logs:           sudo journalctl -u x3-tf.service -f"
