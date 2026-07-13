#!/usr/bin/env python3
# client_manager.py - 3xUI Client Management Module

import os
import sys
import json
import requests
import re
from urllib.parse import urlsplit
from datetime import datetime, timedelta
from pathlib import Path

# ========== Settings ==========
ENV_FILE = "/opt/x3-traffic-reset/.env"
CONFIG_DIR = "/etc/x3-traffic-reset"
TOKEN_FILE = f"{CONFIG_DIR}/api_token.json"
# ===============================

# Colors
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'
    BOLD = '\033[1m'

def read_env():
    """Read .env file"""
    env = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r') as f:
            for line in f:
                line = line.rstrip('\n')
                if not line or line.strip().startswith('#'):
                    continue
                if '=' in line:
                    key, _, value = line.partition('=')
                    env[key.strip()] = value.strip()
    return env

def get_panel_info():
    """Get panel URL, username, password from .env"""
    env = read_env()
    panel_base = env.get("PANEL_BASE", "")
    username = env.get("USERNAME", "")
    password = env.get("PASSWORD", "")
    
    if not panel_base or not username or not password:
        print(f"{Colors.RED}❌ Panel settings not found. Please run option 7 to configure.{Colors.NC}")
        return None, None, None
    
    return panel_base, username, password

def get_token(panel_base, username, password):
    """Get API token from panel"""
    # Check if token is cached and still valid
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as f:
                data = json.load(f)
                if data.get('panel_base') == panel_base:
                    # Token valid for 24 hours
                    created = datetime.fromisoformat(data.get('created', '2000-01-01'))
                    if datetime.now() - created < timedelta(hours=24):
                        return data.get('token')
        except:
            pass
    
    # Get new token
    login_url = f"{panel_base}/panel/api/auth/login"
    try:
        response = requests.post(
            login_url,
            json={"username": username, "password": password},
            verify=False,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        token = data.get('token')
        if not token:
            token = data.get('data', {}).get('token')
        
        if token:
            # Cache token
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(TOKEN_FILE, 'w') as f:
                json.dump({
                    'token': token,
                    'panel_base': panel_base,
                    'created': datetime.now().isoformat()
                }, f)
            return token
        
        print(f"{Colors.RED}❌ Failed to get token. Server response: {data}{Colors.NC}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}❌ Connection error: {e}{Colors.NC}")
        return None

def get_headers(token):
    """Get headers for API requests"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def list_clients(panel_base, token, show_all=True):
    """List all clients from panel"""
    url = f"{panel_base}/panel/api/clients/list"
    try:
        response = requests.get(
            url,
            headers=get_headers(token),
            verify=False,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        clients = data.get('obj', [])
        if not clients:
            clients = data.get('data', {}).get('obj', [])
        
        return clients
    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}❌ Error fetching clients: {e}{Colors.NC}")
        return []

def create_client(panel_base, token, email, total_gb, expiry_days, inbound_ids, enable=True, limit_ip=0):
    """Create a new client in panel"""
    # Calculate expiry time in milliseconds
    if expiry_days:
        expiry_time = int((datetime.now() + timedelta(days=expiry_days)).timestamp() * 1000)
    else:
        expiry_time = 0  # No expiry
    
    payload = {
        "client": {
            "email": email,
            "totalGB": total_gb * 1024 * 1024 * 1024,  # Convert GB to bytes
            "expiryTime": expiry_time,
            "tgId": 0,
            "limitIp": limit_ip,
            "enable": enable
        },
        "inboundIds": inbound_ids
    }
    
    url = f"{panel_base}/panel/api/clients/add"
    try:
        response = requests.post(
            url,
            json=payload,
            headers=get_headers(token),
            verify=False,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        return result.get('success', False), result.get('msg', 'Unknown')
    except requests.exceptions.RequestException as e:
        return False, str(e)

def delete_client(panel_base, token, email, keep_traffic=False):
    """Delete a client by email"""
    keep = "?keepTraffic=1" if keep_traffic else ""
    url = f"{panel_base}/panel/api/clients/del/{email}{keep}"
    try:
        response = requests.post(
            url,
            headers=get_headers(token),
            verify=False,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        return result.get('success', False), result.get('msg', 'Unknown')
    except requests.exceptions.RequestException as e:
        return False, str(e)

def reset_client_traffic(panel_base, token, email):
    """Reset traffic for a client by email"""
    url = f"{panel_base}/panel/api/clients/resetTraffic/{email}"
    try:
        response = requests.post(
            url,
            headers=get_headers(token),
            verify=False,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        return result.get('success', False), result.get('msg', 'Unknown')
    except requests.exceptions.RequestException as e:
        return False, str(e)

def get_client_info(panel_base, token, email):
    """Get client info by email"""
    url = f"{panel_base}/panel/api/clients/get/{email}"
    try:
        response = requests.get(
            url,
            headers=get_headers(token),
            verify=False,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        return result.get('obj'), result.get('success', False)
    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.NC}")
        return None, False

def display_client_info(client):
    """Display client information in a formatted way"""
    if not client:
        return
    
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    print(f"  {Colors.BOLD}Email:{Colors.NC} {client.get('email', 'N/A')}")
    print(f"  {Colors.BOLD}UUID:{Colors.NC} {client.get('uuid', 'N/A')}")
    print(f"  {Colors.BOLD}Total Traffic:{Colors.NC} {client.get('totalGB', 0) / (1024*1024*1024):.2f} GB")
    print(f"  {Colors.BOLD}Used:{Colors.NC} {client.get('usedGB', 0) / (1024*1024*1024):.2f} GB")
    print(f"  {Colors.BOLD}IP Limit:{Colors.NC} {client.get('limitIp', 0)}")
    print(f"  {Colors.BOLD}Enabled:{Colors.NC} {'✅' if client.get('enable', True) else '❌'}")
    
    # Expiry
    expiry_time = client.get('expiryTime', 0)
    if expiry_time:
        expiry_date = datetime.fromtimestamp(expiry_time / 1000)
        print(f"  {Colors.BOLD}Expires:{Colors.NC} {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"  {Colors.BOLD}Expires:{Colors.NC} Never")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")

def menu():
    """Interactive menu for client management"""
    panel_base, username, password = get_panel_info()
    if not panel_base:
        return
    
    token = get_token(panel_base, username, password)
    if not token:
        print(f"{Colors.RED}❌ Failed to authenticate. Check your panel settings.{Colors.NC}")
        return
    
    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    while True:
        print(f"{Colors.CYAN}{Colors.BOLD}╔═════════════════════════════════════════════════════════════════════╗{Colors.NC}")
        print(f"{Colors.CYAN}{Colors.BOLD}║              📋 Client Manager for 3xUI Panel                     ║{Colors.NC}")
        print(f"{Colors.CYAN}{Colors.BOLD}╚═════════════════════════════════════════════════════════════════════╝{Colors.NC}")
        print("")
        print(f"  {Colors.GREEN}1.{Colors.NC} 📋 List all clients")
        print(f"  {Colors.GREEN}2.{Colors.NC} ➕ Create new client")
        print(f"  {Colors.GREEN}3.{Colors.NC} 🔍 Show client info")
        print(f"  {Colors.GREEN}4.{Colors.NC} 🗑️ Delete client")
        print(f"  {Colors.GREEN}5.{Colors.NC} 🔄 Reset client traffic")
        print(f"  {Colors.GREEN}0.{Colors.NC} 🔙 Back to main menu")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        
        choice = input(f"{Colors.BOLD}{Colors.PURPLE}Select option: {Colors.NC}").strip()
        
        if choice == '0':
            break
        
        elif choice == '1':
            print(f"{Colors.BLUE}📋 Fetching clients...{Colors.NC}")
            clients = list_clients(panel_base, token)
            if not clients:
                print(f"{Colors.YELLOW}⚠️ No clients found.{Colors.NC}")
            else:
                print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
                print(f"{'Email':<30} | {'UUID':<38} | {'Total GB':<10} | {'Status'}")
                print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
                for client in clients:
                    email = client.get('email', 'N/A')[:30]
                    uuid = client.get('uuid', 'N/A')[:38]
                    total = client.get('totalGB', 0) / (1024*1024*1024)
                    status = "✅ Active" if client.get('enable', True) else "❌ Disabled"
                    print(f"{email:<30} | {uuid:<38} | {total:<10.2f} | {status}")
                print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
            input(f"{Colors.YELLOW}Press Enter to continue...{Colors.NC}")
        
        elif choice == '2':
            print(f"{Colors.BLUE}➕ Create New Client{Colors.NC}")
            print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
            
            email = input(f"{Colors.BOLD}{Colors.PURPLE}Enter client email: {Colors.NC}").strip()
            if not email:
                print(f"{Colors.RED}❌ Email is required.{Colors.NC}")
                input(f"{Colors.YELLOW}Press Enter to continue...{Colors.NC}")
                continue
            
            total_gb = input(f"{Colors.BOLD}{Colors.PURPLE}Enter traffic limit (GB, 0 for unlimited): {Colors.NC}").strip()
            try:
                total_gb = float(total_gb) if total_gb else 0
            except:
                total_gb = 0
            
            expiry_days = input(f"{Colors.BOLD}{Colors.PURPLE}Enter expiry days (0 for no expiry): {Colors.NC}").strip()
            try:
                expiry_days = int(expiry_days) if expiry_days else 0
            except:
                expiry_days = 0
            
            inbound_ids_str = input(f"{Colors.BOLD}{Colors.PURPLE}Enter inbound IDs (comma-separated, e.g. 1,2,3): {Colors.NC}").strip()
            try:
                inbound_ids = [int(x.strip()) for x in inbound_ids_str.split(',') if x.strip()]
            except:
                inbound_ids = []
            
            if not inbound_ids:
                print(f"{Colors.YELLOW}⚠️ No inbound IDs provided. Using default [1].{Colors.NC}")
                inbound_ids = [1]
            
            enable = input(f"{Colors.BOLD}{Colors.PURPLE}Enable client? (Y/n): {Colors.NC}").strip().lower() != 'n'
            
            print(f"{Colors.CYAN}📋 Creating client...{Colors.NC}")
            success, msg = create_client(panel_base, token, email, total_gb, expiry_days, inbound_ids, enable)
            
            if success:
                print(f"{Colors.GREEN}✅ Client created successfully!{Colors.NC}")
                # Show the client info
                client, _ = get_client_info(panel_base, token, email)
                if client:
                    display_client_info(client)
            else:
                print(f"{Colors.RED}❌ Failed to create client: {msg}{Colors.NC}")
            
            input(f"{Colors.YELLOW}Press Enter to continue...{Colors.NC}")
        
        elif choice == '3':
            email = input(f"{Colors.BOLD}{Colors.PURPLE}Enter client email: {Colors.NC}").strip()
            if not email:
                print(f"{Colors.RED}❌ Email is required.{Colors.NC}")
                input(f"{Colors.YELLOW}Press Enter to continue...{Colors.NC}")
                continue
            
            client, success = get_client_info(panel_base, token, email)
            if success and client:
                display_client_info(client)
            else:
                print(f"{Colors.RED}❌ Client not found or error occurred.{Colors.NC}")
            
            input(f"{Colors.YELLOW}Press Enter to continue...{Colors.NC}")
        
        elif choice == '4':
            email = input(f"{Colors.BOLD}{Colors.PURPLE}Enter client email to delete: {Colors.NC}").strip()
            if not email:
                print(f"{Colors.RED}❌ Email is required.{Colors.NC}")
                input(f"{Colors.YELLOW}Press Enter to continue...{Colors.NC}")
                continue
            
            # Confirm
            confirm = input(f"{Colors.RED}⚠️ Are you sure you want to delete '{email}'? (y/N): {Colors.NC}").strip().lower()
            if confirm != 'y':
                print(f"{Colors.YELLOW}❌ Cancelled.{Colors.NC}")
                input(f"{Colors.YELLOW}Press Enter to continue...{Colors.NC}")
                continue
            
            keep_traffic = input(f"{Colors.BOLD}{Colors.PURPLE}Keep traffic records? (y/N): {Colors.NC}").strip().lower() == 'y'
            
            success, msg = delete_client(panel_base, token, email, keep_traffic)
            if success:
                print(f"{Colors.GREEN}✅ Client '{email}' deleted successfully.{Colors.NC}")
            else:
                print(f"{Colors.RED}❌ Failed to delete client: {msg}{Colors.NC}")
            
            input(f"{Colors.YELLOW}Press Enter to continue...{Colors.NC}")
        
        elif choice == '5':
            email = input(f"{Colors.BOLD}{Colors.PURPLE}Enter client email to reset traffic: {Colors.NC}").strip()
            if not email:
                print(f"{Colors.RED}❌ Email is required.{Colors.NC}")
                input(f"{Colors.YELLOW}Press Enter to continue...{Colors.NC}")
                continue
            
            confirm = input(f"{Colors.RED}⚠️ Reset traffic for '{email}'? (y/N): {Colors.NC}").strip().lower()
            if confirm != 'y':
                print(f"{Colors.YELLOW}❌ Cancelled.{Colors.NC}")
                input(f"{Colors.YELLOW}Press Enter to continue...{Colors.NC}")
                continue
            
            success, msg = reset_client_traffic(panel_base, token, email)
            if success:
                print(f"{Colors.GREEN}✅ Traffic reset successfully for '{email}'.{Colors.NC}")
            else:
                print(f"{Colors.RED}❌ Failed to reset traffic: {msg}{Colors.NC}")
            
            input(f"{Colors.YELLOW}Press Enter to continue...{Colors.NC}")
        
        else:
            print(f"{Colors.RED}❌ Invalid option!{Colors.NC}")
            input(f"{Colors.YELLOW}Press Enter to continue...{Colors.NC}")

if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}👋 Goodbye!{Colors.NC}")
        sys.exit(0)
