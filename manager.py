#!/usr/bin/env python3
# manager.py - Interactive menu for traffic reset management (Email-based)

import os
import sys
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

# ========== Settings ==========
CONFIG_FILE = "/etc/x3-traffic-reset/config.conf"
ENV_FILE = "/opt/x3-traffic-reset/.env"
SERVICE_NAME = "x3-tf"
VERSION = "2.4.1"
SPONSOR_NAME = "Jade Tunnel"
SPONSOR_LINK = "https://t.me/jadetunnell"
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

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def show_header():
    """Display header with logo"""
    clear_screen()
    print(f"{Colors.CYAN}{Colors.BOLD}╔═════════════════════════════════════════════════════════════════════╗{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║       ██╗  █████╗  ██████╗  ███████╗                                ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║       ██║ ██╔══██╗ ██╔══██╗ ██╔════╝                                ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║       ██║ ███████║ ██║  ██║ █████╗                                  ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║  ██   ██║ ██╔══██║ ██║  ██║ ██╔══╝                                  ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║  ╚█████╔╝ ██║  ██║ ██████╔╝ ███████╗                                ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║   ╚════╝  ╚═╝  ╚═╝ ╚═════╝  ╚══════╝                                ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║                                                                     ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║   ████████╗ ██╗   ██╗ ███╗   ██╗ ███╗   ██╗ ███████╗ ██╗            ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║   ╚══██╔══╝ ██║   ██║ ████╗  ██║ ████╗  ██║ ██╔════╝ ██║            ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║      ██║    ██║   ██║ ██╔██╗ ██║ ██╔██╗ ██║ █████╗   ██║            ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║      ██║    ██║   ██║ ██║╚██╗██║ ██║╚██╗██║ ██╔══╝   ██║            ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║      ██║    ╚██████╔╝ ██║ ╚████║ ██║ ╚████║ ███████╗ ███████╗       ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║      ╚═╝     ╚═════╝  ╚═╝  ╚═══╝ ╚═╝  ╚═══╝ ╚══════╝ ╚══════╝       ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║                                                                     ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║                  Traffic Reset Manager  -  v{VERSION}                   ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}║                      (Reset User Traffic Only)                      ║{Colors.NC}")
    print(f"{Colors.CYAN}{Colors.BOLD}╚═════════════════════════════════════════════════════════════════════╝{Colors.NC}")
    print("")
    print(f"{Colors.PURPLE}{Colors.BOLD}🌟 Sponsored by: {SPONSOR_NAME}{Colors.NC}")
    print(f"{Colors.PURPLE}🔗 {SPONSOR_LINK}{Colors.NC}")
    print(f"{Colors.PURPLE}📩 Contact: @jadetunnel{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    print("")

def get_current_interval():
    """Get current reset interval from timer"""
    timer_file = f"/etc/systemd/system/{SERVICE_NAME}.timer"
    if not os.path.exists(timer_file):
        return "Not installed"
    
    try:
        with open(timer_file, 'r') as f:
            for line in f:
                if 'OnCalendar' in line:
                    interval = line.split('=')[1].strip()
                    return interval
    except:
        return "Not configured"
    
    return "Not configured"

def count_users():
    """Count users (emails) in config file"""
    if not os.path.exists(CONFIG_FILE):
        return 0
    
    count = 0
    with open(CONFIG_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                count += 1
    return count

def list_users():
    """Display list of user emails"""
    if not os.path.exists(CONFIG_FILE):
        print(f"{Colors.RED}❌ Config file not found!{Colors.NC}")
        return
    
    print(f"{Colors.BLUE}📋 Users (emails) in traffic reset list:{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    count = 0
    with open(CONFIG_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                count += 1
                print(f"  {Colors.GREEN}{count}.{Colors.NC} Email: {Colors.BOLD}{line}{Colors.NC}")
    
    if count == 0:
        print(f"  {Colors.YELLOW}⚠️ No emails in the list.{Colors.NC}")
    
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")

def add_user():
    """Add an email to the config"""
    print(f"{Colors.BLUE}➕ Add User to Traffic Reset List{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    email = input("Enter client email: ").strip()
    
    if not email:
        print(f"{Colors.RED}❌ Email cannot be empty!{Colors.NC}")
        return
    
    # Check if email already exists
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            for line in f:
                if line.strip() == email:
                    print(f"{Colors.YELLOW}⚠️ Email {email} is already in the list.{Colors.NC}")
                    return
    
    # Add email
    with open(CONFIG_FILE, 'a') as f:
        f.write(f"{email}\n")
    
    print(f"{Colors.GREEN}✅ Email {email} added to traffic reset list!{Colors.NC}")

def remove_user():
    """Remove an email from the config"""
    print(f"{Colors.RED}➖ Remove User from Traffic Reset List{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    if not os.path.exists(CONFIG_FILE):
        print(f"{Colors.RED}❌ Config file not found!{Colors.NC}")
        return
    
    # Read all emails
    emails = []
    with open(CONFIG_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                emails.append(line)
    
    if not emails:
        print(f"{Colors.YELLOW}⚠️ No emails in the list to remove.{Colors.NC}")
        return
    
    # Display emails
    print(f"{Colors.BLUE}Select email to remove:{Colors.NC}")
    for i, email in enumerate(emails, 1):
        print(f"  {Colors.GREEN}{i}.{Colors.NC} {email}")
    
    try:
        choice = int(input(f"Enter number (1-{len(emails)}): ").strip())
        if choice < 1 or choice > len(emails):
            print(f"{Colors.RED}❌ Invalid selection!{Colors.NC}")
            return
    except ValueError:
        print(f"{Colors.RED}❌ Invalid input!{Colors.NC}")
        return
    
    # Remove email
    email_to_remove = emails[choice - 1]
    with open(CONFIG_FILE, 'r') as f:
        lines = f.readlines()
    
    with open(CONFIG_FILE, 'w') as f:
        for line in lines:
            if line.strip() != email_to_remove:
                f.write(line)
    
    print(f"{Colors.GREEN}✅ Email {email_to_remove} removed from traffic reset list!{Colors.NC}")

def set_interval():
    """Set reset interval"""
    print(f"{Colors.BLUE}⏰ Set Traffic Reset Interval{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    print(f"  {Colors.GREEN}1.{Colors.NC} Every 1 hour")
    print(f"  {Colors.GREEN}2.{Colors.NC} Every 2 hours")
    print(f"  {Colors.GREEN}3.{Colors.NC} Every 3 hours")
    print(f"  {Colors.GREEN}4.{Colors.NC} Every 4 hours")
    print(f"  {Colors.GREEN}5.{Colors.NC} Every 6 hours")
    print(f"  {Colors.GREEN}6.{Colors.NC} Every 12 hours")
    print(f"  {Colors.GREEN}7.{Colors.NC} Every day (midnight)")
    print(f"  {Colors.GREEN}8.{Colors.NC} Custom (enter manually)")
    print(f"  {Colors.GREEN}0.{Colors.NC} Back")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
    
    choice = input("Select option: ").strip()
    
    schedules = {
        '1': ("Every 1 hour", "*-*-* *:00:00"),
        '2': ("Every 2 hours", "*-*-* *:00:00,02:00:00,04:00:00,06:00:00,08:00:00,10:00:00,12:00:00,14:00:00,16:00:00,18:00:00,20:00:00,22:00:00"),
        '3': ("Every 3 hours", "*-*-* *:00:00,03:00:00,06:00:00,09:00:00,12:00:00,15:00:00,18:00:00,21:00:00"),
        '4': ("Every 4 hours", "*-*-* *:00:00,04:00:00,08:00:00,12:00:00,16:00:00,20:00:00"),
        '5': ("Every 6 hours", "*-*-* *:00:00,06:00:00,12:00:00,18:00:00"),
        '6': ("Every 12 hours", "*-*-* *:00:00,12:00:00"),
        '7': ("Daily (midnight)", "daily"),
    }
    
    if choice == '0':
        return
    elif choice == '8':
        custom = input("Enter custom schedule (e.g., '*-*-* 03:30:00'): ").strip()
        if custom:
            create_timer_file(f"Custom: {custom}", custom)
    elif choice in schedules:
        desc, schedule = schedules[choice]
        create_timer_file(desc, schedule)
    else:
        print(f"{Colors.RED}❌ Invalid option!{Colors.NC}")

def create_timer_file(desc, schedule):
    """Create timer file with given schedule"""
    timer_content = f"""[Unit]
Description=Timer for x3-tf - {desc}
Requires=x3-tf.service

[Timer]
OnCalendar={schedule}
Persistent=true

[Install]
WantedBy=timers.target
"""
    
    timer_file = f"/etc/systemd/system/{SERVICE_NAME}.timer"
    with open(timer_file, 'w') as f:
        f.write(timer_content)
    
    subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=False)
    subprocess.run(['sudo', 'systemctl', 'restart', f'{SERVICE_NAME}.timer'], check=False)
    
    print(f"{Colors.GREEN}✅ Traffic reset interval updated to: {desc}{Colors.NC}")

def manual_reset():
    """Run manual reset"""
    print(f"{Colors.BLUE}🔄 Running manual traffic reset...{Colors.NC}")
    subprocess.run(['sudo', 'systemctl', 'start', f'{SERVICE_NAME}.service'], check=False)
    print(f"{Colors.GREEN}✅ Traffic reset executed. Check logs for details.{Colors.NC}")
    print(f"{Colors.YELLOW}💡 View logs: sudo journalctl -u {SERVICE_NAME}.service -f{Colors.NC}")

def show_logs():
    """Show logs with submenu for last lines or live follow"""
    while True:
        print(f"{Colors.BLUE}📋 Service Logs{Colors.NC}")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        print(f"  {Colors.GREEN}1.{Colors.NC} Show last 20 lines")
        print(f"  {Colors.GREEN}2.{Colors.NC} Show last 50 lines")
        print(f"  {Colors.GREEN}3.{Colors.NC} Follow live logs (real-time, press Ctrl+C to stop)")
        print(f"  {Colors.GREEN}0.{Colors.NC} Back to main menu")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        
        choice = input("Select option: ").strip()
        
        if choice == '1':
            subprocess.run(['sudo', 'journalctl', '-u', f'{SERVICE_NAME}.service', '-n', '20', '--no-pager'])
            input("\nPress any key to continue...")
        elif choice == '2':
            subprocess.run(['sudo', 'journalctl', '-u', f'{SERVICE_NAME}.service', '-n', '50', '--no-pager'])
            input("\nPress any key to continue...")
        elif choice == '3':
            print(f"{Colors.YELLOW}💡 Following logs live. Press Ctrl+C to stop.{Colors.NC}")
            print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
            try:
                subprocess.run(['sudo', 'journalctl', '-u', f'{SERVICE_NAME}.service', '-f'])
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}⏹️ Stopped following logs.{Colors.NC}")
            input("\nPress any key to continue...")
        elif choice == '0':
            break
        else:
            print(f"{Colors.RED}❌ Invalid option!{Colors.NC}")
            input("Press any key to continue...")

def read_env():
    """Read .env file into a dict, preserving key order"""
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

def write_env(env):
    """Write dict back to .env file, preserving a stable key order"""
    key_order = ["PANEL_BASE", "USERNAME", "PASSWORD", "CONFIG_FILE", "LOG_FILE"]
    # include any extra keys that might exist but aren't in key_order
    extra_keys = [k for k in env.keys() if k not in key_order]
    ordered_keys = key_order + extra_keys

    lines = []
    for key in ordered_keys:
        if key in env:
            lines.append(f"{key}={env[key]}\n")

    with open(ENV_FILE, 'w') as f:
        f.writelines(lines)

def parse_panel_base(panel_base):
    """Split PANEL_BASE URL into ip/domain, port, and base path"""
    try:
        parts = urlsplit(panel_base)
        host = parts.hostname or ""
        port = str(parts.port) if parts.port else ""
        path = parts.path or ""
        scheme = parts.scheme or "https"
        return scheme, host, port, path
    except Exception:
        return "https", "", "", ""

def build_panel_base(scheme, host, port, path):
    """Rebuild PANEL_BASE URL from parts"""
    netloc = host
    if port:
        netloc = f"{host}:{port}"
    if path and not path.startswith('/'):
        path = '/' + path
    return f"{scheme}://{netloc}{path}"

def edit_panel_settings():
    """Edit the 3xUI panel connection settings stored in .env"""
    print(f"{Colors.BLUE}⚙️  Edit Panel Settings{Colors.NC}")
    print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")

    if not os.path.exists(ENV_FILE):
        print(f"{Colors.RED}❌ .env file not found at {ENV_FILE}!{Colors.NC}")
        return

    env = read_env()
    current_panel_base = env.get("PANEL_BASE", "")
    current_user = env.get("USERNAME", "")
    current_pass = env.get("PASSWORD", "")

    scheme, host, port, path = parse_panel_base(current_panel_base)
    if not port:
        port = "2053"

    print(f"{Colors.YELLOW}💡 Press Enter to keep the current value shown in [brackets].{Colors.NC}")
    print("")

    new_ip = input(f"Panel IP address or domain [{host}]: ").strip()
    new_ip = new_ip if new_ip else host

    new_port = input(f"Panel port [{port}]: ").strip()
    new_port = new_port if new_port else port

    masked_path = path if path else "(none)"
    new_path = input(f"Web Base Path [{masked_path}]: ").strip()
    if new_path == "":
        new_path = path
    elif new_path.lower() in ("none", "-", "/"):
        new_path = ""

    masked_user = current_user if current_user else "(none)"
    new_user = input(f"Username [{masked_user}]: ").strip()
    new_user = new_user if new_user else current_user

    print(f"Password [{'*' * len(current_pass) if current_pass else '(none)'}]")
    new_pass = input("New password (leave empty to keep current): ").strip()
    new_pass = new_pass if new_pass else current_pass

    if not new_ip or not new_user or not new_pass:
        print(f"{Colors.RED}❌ IP/domain, username, and password cannot be empty. Aborted.{Colors.NC}")
        return

    new_panel_base = build_panel_base(scheme, new_ip, new_port, new_path)

    print("")
    print(f"{Colors.BLUE}📋 New settings summary:{Colors.NC}")
    print(f"  Panel URL: {Colors.BOLD}{new_panel_base}{Colors.NC}")
    print(f"  Username:  {Colors.BOLD}{new_user}{Colors.NC}")
    print(f"  Password:  {Colors.BOLD}{'*' * len(new_pass)}{Colors.NC}")
    print("")
    confirm = input("Save these settings? (y/N): ").strip().lower()
    if confirm != 'y':
        print(f"{Colors.YELLOW}⚠️ Cancelled, no changes were made.{Colors.NC}")
        return

    env["PANEL_BASE"] = new_panel_base
    env["USERNAME"] = new_user
    env["PASSWORD"] = new_pass
    env.setdefault("CONFIG_FILE", CONFIG_FILE)
    env.setdefault("LOG_FILE", "/var/log/x3-traffic-reset.log")

    write_env(env)
    print(f"{Colors.GREEN}✅ Panel settings updated successfully!{Colors.NC}")

    apply = input("Restart the service now to apply changes? (Y/n): ").strip().lower()
    if apply != 'n':
        subprocess.run(['sudo', 'systemctl', 'restart', f'{SERVICE_NAME}.timer'], check=False)
        print(f"{Colors.GREEN}✅ Service restarted with new settings.{Colors.NC}")
    else:
        print(f"{Colors.YELLOW}💡 Remember to restart manually: sudo systemctl restart {SERVICE_NAME}.timer{Colors.NC}")

def uninstall():
    """Uninstall the service"""
    print(f"{Colors.RED}⚠️ Are you sure you want to uninstall? (y/N): {Colors.NC}")
    confirm = input().strip().lower()
    if confirm == 'y':
        subprocess.run(['bash', '<(curl -Ls https://raw.githubusercontent.com/Mahersaber2024/Auto-Reset-traffic-3x-ui-/main/uninstall.sh)'], shell=True)
        sys.exit(0)

def main():
    """Main menu loop"""
    while True:
        show_header()
        
        # Show status
        user_count = count_users()
        interval = get_current_interval()
        service_status = subprocess.run(
            ['systemctl', 'is-active', f'{SERVICE_NAME}.timer'],
            capture_output=True,
            text=True
        ).stdout.strip()
        
        print(f"{Colors.BLUE}📊 Status:{Colors.NC}")
        print(f"  {Colors.GREEN}●{Colors.NC} Users (emails) in reset list: {Colors.BOLD}{user_count}{Colors.NC}")
        print(f"  {Colors.GREEN}●{Colors.NC} Reset interval: {Colors.BOLD}{interval}{Colors.NC}")
        print(f"  {Colors.GREEN}●{Colors.NC} Service status: {Colors.BOLD}{service_status}{Colors.NC}")
        print("")
        
        print(f"{Colors.BLUE}📋 Menu:{Colors.NC}")
        print(f"  {Colors.GREEN}1.{Colors.NC} 📋 List users (emails) in reset list")
        print(f"  {Colors.GREEN}2.{Colors.NC} ➕ Add user (by email)")
        print(f"  {Colors.GREEN}3.{Colors.NC} ➖ Remove user (by email)")
        print(f"  {Colors.GREEN}4.{Colors.NC} ⏰ Set reset interval")
        print(f"  {Colors.GREEN}5.{Colors.NC} 🔄 Run manual traffic reset now")
        print(f"  {Colors.GREEN}6.{Colors.NC} 📋 View logs")
        print(f"  {Colors.GREEN}7.{Colors.NC} ⚙️  Edit panel settings")
        print(f"  {Colors.GREEN}8.{Colors.NC} 📋 Client Manager (3xUI Panel)")
        print(f"  {Colors.GREEN}9.{Colors.NC} ❌ Uninstall service")
        print(f"  {Colors.GREEN}0.{Colors.NC} 🚪 Exit")
        print(f"{Colors.CYAN}─────────────────────────────────────────────────────────────────{Colors.NC}")
        
        choice = input("Select option: ").strip()
        
        if choice == '1':
            list_users()
        elif choice == '2':
            add_user()
        elif choice == '3':
            remove_user()
        elif choice == '4':
            set_interval()
        elif choice == '5':
            manual_reset()
        elif choice == '6':
            show_logs()
        elif choice == '7':
            edit_panel_settings()
        elif choice == '8':
            # Run client_manager.py
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_manager.py')
            if os.path.exists(script_path):
                subprocess.run(['python3', script_path], check=False)
            else:
                # Try alternative path
                alt_path = '/usr/local/bin/client_manager.py'
                if os.path.exists(alt_path):
                    subprocess.run(['python3', alt_path], check=False)
                else:
                    print(f"{Colors.RED}❌ client_manager.py not found!{Colors.NC}")
                    input(f"{Colors.YELLOW}Press Enter to continue...{Colors.NC}")
        elif choice == '9':
            uninstall()
        elif choice == '0':
            print(f"{Colors.GREEN}👋 Goodbye!{Colors.NC}")
            sys.exit(0)
        else:
            print(f"{Colors.RED}❌ Invalid option!{Colors.NC}")
        
        if choice not in ['0', '6']:
            print("")
            print(f"{Colors.YELLOW}Press any key to continue...{Colors.NC}")
            input()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}👋 Goodbye!{Colors.NC}")
        sys.exit(0)
