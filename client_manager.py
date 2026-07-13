#!/usr/bin/env python3
# client_manager.py - Client management module for 3x-UI

import json
import requests
import sys
from pathlib import Path
from datetime import datetime, timedelta

# ========== Settings ==========
API_BASE_URL = "http://localhost:8080"  # Default 3x-UI port
API_USERNAME = "admin"
API_PASSWORD = "admin"
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
                # Store cookies for session
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
        """
        Create a new client
        
        Parameters:
        - email: Client email (required)
        - total_gb: Total traffic in GB
        - expiry_days: Days until expiry
        - limit_ip: IP limit (0 = unlimited)
        - enable: Enable/disable client
        - inbound_ids: List of inbound IDs to attach client to
        """
        # Calculate expiry time in milliseconds
        if expiry_days > 0:
            expiry_time = int((datetime.now() + timedelta(days=expiry_days)).timestamp() * 1000)
        else:
            expiry_time = 0  # Never expires
        
        # Convert GB to bytes
        total_bytes = int(total_gb * 1073741824)  # GB to bytes
        
        # Get inbounds if not provided
        if inbound_ids is None:
            inbounds = self.get_inbounds()
            if not inbounds:
                print(f"{Colors.RED}❌ No inbounds available{Colors.NC}")
                return False
            # Show available inbounds to user
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
        
        # Prepare client data
        client_data = {
            "email": email,
            "totalGB": total_bytes,
            "expiryTime": expiry_time,
            "limitIp": limit_ip,
            "enable": enable,
            "inboundIds": inbound_ids
        }
        
        # Create client
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
                    print(f"  {Colors.GREEN}●{Colors.NC} Expiry: {expiry_days} days")
                    print(f"  {Colors.GREEN}●{Colors.NC} Inbounds: {inbound_ids}")
                    # Try to get the generated secrets
                    if 'obj' in data and data['obj']:
                        client_info = data['obj']
                        if 'id' in client_info:
                            print(f"  {Colors.GREEN}●{Colors.NC} Client ID: {client_info['id']}")
                        if 'secret' in client_info:
                            print(f"  {Colors.GREEN}●{Colors.NC} Secret: {client_info['secret']}")
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
    while True:
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        print(f"{Colors.BLUE}👤 Client Management{Colors.NC}")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        print(f"  {Colors.GREEN}1.{Colors.NC} Create new client")
        print(f"  {Colors.GREEN}2.{Colors.NC} List all clients")
        print(f"  {Colors.GREEN}3.{Colors.NC} Show client details")
        print(f"  {Colors.GREEN}4.{Colors.NC} Delete client")
        print(f"  {Colors.GREEN}5.{Colors.NC} Update client settings")
        print(f"  {Colors.GREEN}0.{Colors.NC} Back to main menu")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        
        choice = input("Select option: ").strip()
        
        if choice == '1':
            create_client_interactive()
        elif choice == '2':
            list_clients()
        elif choice == '3':
            show_client_details()
        elif choice == '4':
            delete_client()
        elif choice == '5':
            update_client()
        elif choice == '0':
            break
        else:
            print(f"{Colors.RED}❌ Invalid option!{Colors.NC}")
            input("Press any key to continue...")

def create_client_interactive():
    """Interactive client creation"""
    print(f"{Colors.BLUE}📝 Create New Client{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    # Get API configuration
    base_url = input(f"Enter API base URL [{API_BASE_URL}]: ").strip()
    if not base_url:
        base_url = API_BASE_URL
    
    username = input(f"Enter API username [{API_USERNAME}]: ").strip()
    if not username:
        username = API_USERNAME
    
    password = input(f"Enter API password [{API_PASSWORD}]: ").strip()
    if not password:
        password = API_PASSWORD
    
    manager = ClientManager(base_url, username, password)
    
    # Get client details
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
    
    # Get inbounds
    inbounds = manager.get_inbounds()
    if not inbounds:
        print(f"{Colors.YELLOW}⚠️ No inbounds available. Adding client without inbound...{Colors.NC}")
        inbound_ids = []
    else:
        print(f"{Colors.BLUE}📋 Available inbounds:{Colors.NC}")
        for idx, inbound in enumerate(inbounds, 1):
            protocol = inbound.get('protocol', 'unknown')
            port = inbound.get('port', 'unknown')
            remark = inbound.get('remark', 'no name')
            print(f"  {Colors.GREEN}{idx}.{Colors.NC} {protocol} - {remark} (Port: {port})")
        
        print(f"{Colors.YELLOW}💡 Enter number or comma-separated numbers (e.g., 1,3,5){Colors.NC}")
        inbound_choice = input("Select inbound(s): ").strip()
        
        if inbound_choice:
            if ',' in inbound_choice:
                selected = [int(x.strip()) for x in inbound_choice.split(',')]
                inbound_ids = [inbounds[i-1].get('id') for i in selected if 1 <= i <= len(inbounds)]
            else:
                try:
                    idx = int(inbound_choice)
                    if 1 <= idx <= len(inbounds):
                        inbound_ids = [inbounds[idx-1].get('id')]
                    else:
                        print(f"{Colors.RED}❌ Invalid selection!{Colors.NC}")
                        return
                except ValueError:
                    print(f"{Colors.RED}❌ Invalid input!{Colors.NC}")
                    return
        else:
            inbound_ids = []
    
    # Create client
    manager.create_client(email, total_gb, expiry_days, limit_ip, enable, inbound_ids)
    input("\nPress any key to continue...")

def list_clients():
    """List all clients"""
    print(f"{Colors.BLUE}📋 List Clients{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    base_url = input(f"Enter API base URL [{API_BASE_URL}]: ").strip()
    if not base_url:
        base_url = API_BASE_URL
    
    manager = ClientManager(base_url)
    
    try:
        url = f"{base_url}/panel/api/clients/list"
        response = manager.session.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                clients = data.get('obj', [])
                if clients:
                    print(f"{Colors.GREEN}✅ Found {len(clients)} clients:{Colors.NC}")
                    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
                    for idx, client in enumerate(clients, 1):
                        email = client.get('email', 'N/A')
                        total_gb = client.get('totalGB', 0) / 1073741824
                        used_gb = client.get('usedGB', 0) / 1073741824
                        enable = client.get('enable', False)
                        status = f"{Colors.GREEN}🟢 Active{Colors.NC}" if enable else f"{Colors.RED}🔴 Disabled{Colors.NC}"
                        
                        print(f"  {Colors.GREEN}{idx}.{Colors.NC} Email: {Colors.BOLD}{email}{Colors.NC}")
                        print(f"     Traffic: {used_gb:.2f} GB / {total_gb:.2f} GB")
                        print(f"     Status: {status}")
                        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
                else:
                    print(f"{Colors.YELLOW}⚠️ No clients found.{Colors.NC}")
            else:
                print(f"{Colors.RED}❌ Failed to list clients: {data.get('msg')}{Colors.NC}")
        else:
            print(f"{Colors.RED}❌ API error: {response.status_code}{Colors.NC}")
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.NC}")
    
    input("\nPress any key to continue...")

def show_client_details():
    """Show detailed client information"""
    print(f"{Colors.BLUE}🔍 Client Details{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    email = input("Enter client email: ").strip()
    if not email:
        print(f"{Colors.RED}❌ Email cannot be empty!{Colors.NC}")
        return
    
    base_url = input(f"Enter API base URL [{API_BASE_URL}]: ").strip()
    if not base_url:
        base_url = API_BASE_URL
    
    manager = ClientManager(base_url)
    
    try:
        url = f"{base_url}/panel/api/clients/find/{email}"
        response = manager.session.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                client = data.get('obj', {})
                if client:
                    print(f"{Colors.GREEN}✅ Client details:{Colors.NC}")
                    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
                    for key, value in client.items():
                        if key in ['totalGB', 'usedGB']:
                            value = f"{value / 1073741824:.2f} GB"
                        elif key == 'expiryTime' and value > 0:
                            date = datetime.fromtimestamp(value / 1000)
                            value = date.strftime('%Y-%m-%d %H:%M:%S')
                        elif key == 'expiryTime' and value == 0:
                            value = "Unlimited"
                        print(f"  {Colors.BOLD}{key}:{Colors.NC} {value}")
                    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
                else:
                    print(f"{Colors.YELLOW}⚠️ Client not found.{Colors.NC}")
            else:
                print(f"{Colors.RED}❌ Failed to get client details: {data.get('msg')}{Colors.NC}")
        else:
            print(f"{Colors.RED}❌ API error: {response.status_code}{Colors.NC}")
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.NC}")
    
    input("\nPress any key to continue...")

def delete_client():
    """Delete a client"""
    print(f"{Colors.RED}🗑️ Delete Client{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    email = input("Enter client email to delete: ").strip()
    if not email:
        print(f"{Colors.RED}❌ Email cannot be empty!{Colors.NC}")
        return
    
    confirm = input(f"Are you sure you want to delete client '{email}'? (y/N): ").strip().lower()
    if confirm != 'y':
        print(f"{Colors.YELLOW}⚠️ Operation cancelled.{Colors.NC}")
        return
    
    base_url = input(f"Enter API base URL [{API_BASE_URL}]: ").strip()
    if not base_url:
        base_url = API_BASE_URL
    
    manager = ClientManager(base_url)
    
    try:
        url = f"{base_url}/panel/api/clients/delete/{email}"
        response = manager.session.delete(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"{Colors.GREEN}✅ Client '{email}' deleted successfully!{Colors.NC}")
            else:
                print(f"{Colors.RED}❌ Failed to delete client: {data.get('msg')}{Colors.NC}")
        else:
            print(f"{Colors.RED}❌ API error: {response.status_code}{Colors.NC}")
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.NC}")
    
    input("\nPress any key to continue...")

def update_client():
    """Update client settings"""
    print(f"{Colors.BLUE}⚙️ Update Client Settings{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    email = input("Enter client email to update: ").strip()
    if not email:
        print(f"{Colors.RED}❌ Email cannot be empty!{Colors.NC}")
        return
    
    base_url = input(f"Enter API base URL [{API_BASE_URL}]: ").strip()
    if not base_url:
        base_url = API_BASE_URL
    
    manager = ClientManager(base_url)
    
    # Get client details first
    try:
        url = f"{base_url}/panel/api/clients/find/{email}"
        response = manager.session.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                client = data.get('obj', {})
                if not client:
                    print(f"{Colors.RED}❌ Client not found!{Colors.NC}")
                    input("Press any key to continue...")
                    return
                
                print(f"{Colors.GREEN}✅ Current client details:{Colors.NC}")
                print(f"  Email: {client.get('email')}")
                print(f"  Total GB: {client.get('totalGB', 0) / 1073741824:.2f}")
                print(f"  Used GB: {client.get('usedGB', 0) / 1073741824:.2f}")
                print(f"  Enabled: {client.get('enable')}")
                print("")
                
                # Get updates
                new_total = input(f"New total GB (current: {client.get('totalGB', 0) / 1073741824:.2f}, enter to skip): ").strip()
                new_expiry = input(f"New expiry days (0=unlimited, current: {client.get('expiryTime', 0)}, enter to skip): ").strip()
                new_enable = input(f"Enable client? (y/n, current: {client.get('enable')}, enter to skip): ").strip().lower()
                
                updates = {}
                
                if new_total:
                    try:
                        updates['totalGB'] = int(float(new_total) * 1073741824)
                    except ValueError:
                        print(f"{Colors.RED}❌ Invalid total GB value!{Colors.NC}")
                        return
                
                if new_expiry:
                    try:
                        days = int(new_expiry)
                        if days > 0:
                            updates['expiryTime'] = int((datetime.now() + timedelta(days=days)).timestamp() * 1000)
                        else:
                            updates['expiryTime'] = 0
                    except ValueError:
                        print(f"{Colors.RED}❌ Invalid expiry value!{Colors.NC}")
                        return
                
                if new_enable:
                    updates['enable'] = new_enable == 'y'
                
                if not updates:
                    print(f"{Colors.YELLOW}⚠️ No updates provided.{Colors.NC}")
                    return
                
                # Apply updates
                url = f"{base_url}/panel/api/clients/update/{email}"
                response = manager.session.put(url, json=updates)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print(f"{Colors.GREEN}✅ Client '{email}' updated successfully!{Colors.NC}")
                    else:
                        print(f"{Colors.RED}❌ Failed to update client: {data.get('msg')}{Colors.NC}")
                else:
                    print(f"{Colors.RED}❌ API error: {response.status_code}{Colors.NC}")
            else:
                print(f"{Colors.RED}❌ Failed to get client details: {data.get('msg')}{Colors.NC}")
        else:
            print(f"{Colors.RED}❌ API error: {response.status_code}{Colors.NC}")
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.NC}")
    
    input("\nPress any key to continue...")

# Main entry point if run directly
if __name__ == "__main__":
    show_client_menu()
