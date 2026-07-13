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
apt install -y git python3 python3-venv python3-pip curl jq

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

# Install requirements
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    # Create requirements.txt if not exists
    echo "requests>=2.28.0" > requirements.txt
    echo "python-dotenv>=1.0.0" >> requirements.txt
    pip install -r requirements.txt
fi

# ============================================
# Get settings from the user
# ============================================
echo ""
echo -e "${BOLD}${YELLOW}⚙️ Please enter your 3xUI panel settings:${NC}"
read -p "Panel IP address or domain (e.g. 192.168.1.100): " PANEL_IP
read -p "Panel port (default: 2053): " PANEL_PORT
PANEL_PORT=${PANEL_PORT:-2053}
read -p "Web Base Path (e.g. /KqOZWNk3zx7VDf1pDS, or press Enter if none): " PANEL_PATH
read -p "Username: " PANEL_USER
read -s -p "Password: " PANEL_PASS
echo ""

# ============================================
# Create the environment file (.env)
# ============================================
cat > .env <<EOF
PANEL_BASE=https://${PANEL_IP}:${PANEL_PORT}${PANEL_PATH}
PANEL_URL=https://${PANEL_IP}:${PANEL_PORT}${PANEL_PATH}
USERNAME=${PANEL_USER}
PASSWORD=${PANEL_PASS}
API_BASE_URL=https://${PANEL_IP}:${PANEL_PORT}${PANEL_PATH}
API_USERNAME=${PANEL_USER}
API_PASSWORD=${PANEL_PASS}
CONFIG_FILE=/etc/x3-traffic-reset/config.conf
LOG_FILE=/var/log/x3-traffic-reset.log
EOF

# ============================================
# Copy configuration files
# ============================================
mkdir -p /etc/x3-traffic-reset
if [ -f config.conf ]; then
    cp -f config.conf /etc/x3-traffic-reset/config.conf
else
    # Create default config file
    touch /etc/x3-traffic-reset/config.conf
    echo "# Add client emails here, one per line" > /etc/x3-traffic-reset/config.conf
    echo "# Example:" >> /etc/x3-traffic-reset/config.conf
    echo "# user1@example.com" >> /etc/x3-traffic-reset/config.conf
    echo "# user2@example.com" >> /etc/x3-traffic-reset/config.conf
fi

# ============================================
# Install the management scripts
# ============================================
echo -e "${BLUE}📋 Installing management scripts...${NC}"

# Install main manager
if [ -f manager.py ]; then
    cp -f manager.py /usr/local/bin/x3-tf
    chmod +x /usr/local/bin/x3-tf
else
    echo -e "${RED}❌ manager.py not found!${NC}"
    exit 1
fi

# Install client manager module
if [ -f client_manager.py ]; then
    cp -f client_manager.py /usr/local/bin/x3-client
    chmod +x /usr/local/bin/x3-client
    echo -e "${GREEN}✅ Client manager installed as 'x3-client'${NC}"
else
    echo -e "${YELLOW}⚠️ client_manager.py not found, creating it...${NC}"
    # Create client_manager.py from the provided code
    cat > /usr/local/bin/x3-client <<'EOF'
#!/usr/bin/env python3
# client_manager.py - Client management module for 3x-UI

import json
import requests
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ========== Settings from .env ==========
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8080')
API_USERNAME = os.getenv('API_USERNAME', 'admin')
API_PASSWORD = os.getenv('API_PASSWORD', 'admin')
# ===============================

# Colors (ANSI escape codes)
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'
    BOLD = '\033[1m'

class ClientManager:
    def __init__(self, base_url=None, username=None, password=None):
        self.base_url = base_url or API_BASE_URL
        self.username = username or API_USERNAME
        self.password = password or API_PASSWORD
        self.session = requests.Session()
        # Disable SSL verification for self-signed certs
        self.session.verify = False
        self.cookie_jar = {}
        self.login()
    
    def login(self):
        """Login to 3x-UI panel"""
        try:
            login_url = f"{self.base_url}/login"
            payload = {
                "username": self.username,
                "password": self.password
            }
            response = self.session.post(login_url, json=payload)
            
            if response.status_code == 200:
                self.cookie_jar = self.session.cookies.get_dict()
                print(f"{Colors.GREEN}✅ Successfully logged in to 3x-UI{Colors.NC}")
                return True
            else:
                print(f"{Colors.RED}❌ Login failed: {response.text}{Colors.NC}")
                return False
        except Exception as e:
            print(f"{Colors.RED}❌ Login error: {e}{Colors.NC}")
            return False
    
    def get_inbounds(self):
        """Get list of all inbounds"""
        try:
            url = f"{self.base_url}/panel/api/inbounds/list"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('obj', [])
                else:
                    print(f"{Colors.RED}❌ Failed to get inbounds: {data.get('msg')}{Colors.NC}")
                    return []
            else:
                print(f"{Colors.RED}❌ API error: {response.status_code}{Colors.NC}")
                return []
        except Exception as e:
            print(f"{Colors.RED}❌ Error getting inbounds: {e}{Colors.NC}")
            return []
    
    def create_client(self, email, total_gb, expiry_days, limit_ip=0, enable=True, inbound_ids=None):
        """Create a new client"""
        if expiry_days > 0:
            expiry_time = int((datetime.now() + timedelta(days=expiry_days)).timestamp() * 1000)
        else:
            expiry_time = 0
        
        total_bytes = int(total_gb * 1073741824)
        
        if inbound_ids is None:
            inbounds = self.get_inbounds()
            if not inbounds:
                print(f"{Colors.RED}❌ No inbounds available{Colors.NC}")
                return False
            print(f"{Colors.BLUE}📋 Available inbounds:{Colors.NC}")
            for idx, inbound in enumerate(inbounds, 1):
                protocol = inbound.get('protocol', 'unknown')
                port = inbound.get('port', 'unknown')
                remark = inbound.get('remark', 'no name')
                print(f"  {Colors.GREEN}{idx}.{Colors.NC} {protocol} - {remark} (Port: {port})")
            
            try:
                choice = input(f"Select inbound number (1-{len(inbounds)}), or comma-separated for multiple: ").strip()
                if ',' in choice:
                    selected = [int(x.strip()) for x in choice.split(',')]
                    inbound_ids = [inbounds[i-1].get('id') for i in selected if 1 <= i <= len(inbounds)]
                else:
                    idx = int(choice)
                    if 1 <= idx <= len(inbounds):
                        inbound_ids = [inbounds[idx-1].get('id')]
                    else:
                        print(f"{Colors.RED}❌ Invalid selection{Colors.NC}")
                        return False
            except ValueError:
                print(f"{Colors.RED}❌ Invalid input{Colors.NC}")
                return False
        
        client_data = {
            "email": email,
            "totalGB": total_bytes,
            "expiryTime": expiry_time,
            "limitIp": limit_ip,
            "enable": enable,
            "inboundIds": inbound_ids
        }
        
        try:
            url = f"{self.base_url}/panel/api/clients/add"
            response = self.session.post(url, json=client_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"{Colors.GREEN}✅ Client '{email}' created successfully!{Colors.NC}")
                    print(f"{Colors.BLUE}📊 Client details:{Colors.NC}")
                    print(f"  {Colors.GREEN}●{Colors.NC} Email: {email}")
                    print(f"  {Colors.GREEN}●{Colors.NC} Traffic: {total_gb} GB")
                    print(f"  {Colors.GREEN}●{Colors.NC} Expiry: {expiry_days} days" if expiry_days > 0 else f"  {Colors.GREEN}●{Colors.NC} Expiry: Unlimited")
                    print(f"  {Colors.GREEN}●{Colors.NC} Inbounds: {inbound_ids}")
                    return True
                else:
                    print(f"{Colors.RED}❌ Failed to create client: {data.get('msg', 'Unknown error')}{Colors.NC}")
                    return False
            else:
                print(f"{Colors.RED}❌ API error: {response.status_code}{Colors.NC}")
                print(f"{Colors.RED}Response: {response.text}{Colors.NC}")
                return False
        except Exception as e:
            print(f"{Colors.RED}❌ Error creating client: {e}{Colors.NC}")
            return False

def show_client_menu():
    """Display client management menu"""
    print(f"{Colors.BLUE}👤 Client Management for 3x-UI{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    # Use settings from environment
    manager = ClientManager()
    
    print(f"\n{Colors.BLUE}📝 Create New Client{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    email = input("Enter client email: ").strip()
    if not email:
        print(f"{Colors.RED}❌ Email cannot be empty!{Colors.NC}")
        return
    
    try:
        total_gb = float(input("Enter total traffic (GB): ").strip())
        if total_gb <= 0:
            print(f"{Colors.RED}❌ Traffic must be greater than 0!{Colors.NC}")
            return
    except ValueError:
        print(f"{Colors.RED}❌ Invalid traffic value!{Colors.NC}")
        return
    
    try:
        expiry_days = int(input("Enter expiry time (days, 0 for unlimited): ").strip())
        if expiry_days < 0:
            print(f"{Colors.RED}❌ Expiry days cannot be negative!{Colors.NC}")
            return
    except ValueError:
        print(f"{Colors.RED}❌ Invalid expiry days!{Colors.NC}")
        return
    
    try:
        limit_ip = int(input("Enter IP limit (0 for unlimited): ").strip())
        if limit_ip < 0:
            print(f"{Colors.RED}❌ IP limit cannot be negative!{Colors.NC}")
            return
    except ValueError:
        print(f"{Colors.RED}❌ Invalid IP limit!{Colors.NC}")
        return
    
    enable_input = input("Enable client? (y/n, default: y): ").strip().lower()
    enable = enable_input != 'n'
    
    # Create client
    manager.create_client(email, total_gb, expiry_days, limit_ip, enable)
    input("\nPress any key to continue...")

if __name__ == "__main__":
    try:
        show_client_menu()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⏹️ Operation cancelled.{Colors.NC}")
        sys.exit(0)
EOF
    chmod +x /usr/local/bin/x3-client
    echo -e "${GREEN}✅ Client manager created as 'x3-client'${NC}"
fi

# ============================================
# Create symbolic links for easy access
# ============================================
ln -sf /usr/local/bin/x3-tf /usr/local/bin/x3-manager
ln -sf /usr/local/bin/x3-client /usr/local/bin/x3-client-manager

# ============================================
# Create systemd service
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
Restart=no
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# ============================================
# Create systemd timer
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
# Commands Guide
# ============================================
echo -e "${BOLD}${BLUE}📋 AVAILABLE COMMANDS${NC}"
echo -e "${CYAN}──────────────────────────────────────────────────────────────${NC}"
echo -e "  ${GREEN}▶${NC} ${WHITE}x3-tf${NC}           - Main traffic reset manager"
echo -e "  ${GREEN}▶${NC} ${WHITE}x3-client${NC}       - Client management (create new clients)"
echo -e "  ${GREEN}▶${NC} ${WHITE}x3-manager${NC}      - Alias for x3-tf"
echo -e "  ${GREEN}▶${NC} ${WHITE}x3-client-manager${NC} - Alias for x3-client"
echo ""

# ============================================
# Support
echo -e "${BOLD}${PURPLE}🌟 SPONSOR${NC}"
echo -e "  ${BOLD}Jade Tunnel${NC} - ${WHITE}https://t.me/jadetunnell${NC}"
echo -e "  ${BOLD}Contact:${NC} ${WHITE}@jadetunnel${NC}"
echo ""

echo -e "${GREEN}${BOLD}🎯 Quick Start:${NC}"
echo -e "  • Run ${BOLD}x3-tf${NC} to manage traffic reset"
echo -e "  • Run ${BOLD}x3-client${NC} to create new clients"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
