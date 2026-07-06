#!/bin/bash
# uninstall.sh - Uninstall Traffic Reset Manager

echo "🗑️ Uninstalling Traffic Reset Manager..."

sudo systemctl stop x3-tf.timer 2>/dev/null
sudo systemctl disable x3-tf.timer 2>/dev/null
sudo rm -f /etc/systemd/system/x3-tf.service
sudo rm -f /etc/systemd/system/x3-tf.timer
sudo rm -f /usr/local/bin/x3-tf
sudo rm -f /usr/local/bin/reset_daemon.sh
sudo rm -rf /etc/x3-traffic-reset
sudo systemctl daemon-reload

echo "✅ Uninstallation completed!"