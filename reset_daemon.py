#!/usr/bin/env python3
# reset_daemon.py - Reset traffic using email and CSRF token

import os
import sys
import json
import logging
import requests

# ========== Fallback Settings (if .env not found) ==========
DEFAULT_PANEL_BASE = "https://mashine.ikcogo.ir:2053/KqOZWNk3zx7VDf1pDS"
DEFAULT_USERNAME = "Ed2GDE8uC9"
DEFAULT_PASSWORD = "BQ6NPEp22Z"
DEFAULT_CONFIG_FILE = "/etc/x3-traffic-reset/config.conf"
DEFAULT_LOG_FILE = "/var/log/x3-traffic-reset.log"
# ============================================================

# Try to load .env, but if not, use defaults
try:
    from dotenv import load_dotenv
    load_dotenv('/opt/x3-traffic-reset/.env')
    PANEL_BASE = os.getenv('PANEL_BASE', DEFAULT_PANEL_BASE)
    USERNAME = os.getenv('USERNAME', DEFAULT_USERNAME)
    PASSWORD = os.getenv('PASSWORD', DEFAULT_PASSWORD)
    CONFIG_FILE = os.getenv('CONFIG_FILE', DEFAULT_CONFIG_FILE)
    LOG_FILE = os.getenv('LOG_FILE', DEFAULT_LOG_FILE)
    print("✅ Loaded settings from .env")
except:
    PANEL_BASE = DEFAULT_PANEL_BASE
    USERNAME = DEFAULT_USERNAME
    PASSWORD = DEFAULT_PASSWORD
    CONFIG_FILE = DEFAULT_CONFIG_FILE
    LOG_FILE = DEFAULT_LOG_FILE
    print("⚠️ Using default settings (fallback)")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

logger.info(f"📡 Panel: {PANEL_BASE}")
logger.info(f"📁 Config: {CONFIG_FILE}")

def read_emails():
    """Read email list from config file"""
    if not os.path.exists(CONFIG_FILE):
        logger.error(f"❌ Config file not found: {CONFIG_FILE}")
        return []
    
    emails = []
    with open(CONFIG_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                emails.append(line)
    return emails

def login_to_panel():
    """Login and get session + CSRF token"""
    session = requests.Session()
    
    # 1. Get CSRF token
    csrf_url = f"{PANEL_BASE}/csrf-token"
    try:
        resp = session.get(csrf_url, verify=False)
        resp.raise_for_status()
        csrf_token = resp.json().get('obj')
        if not csrf_token:
            logger.error("❌ CSRF token not found")
            return None, None
        logger.info("✅ CSRF token obtained")
    except Exception as e:
        logger.error(f"❌ Failed to get CSRF token: {e}")
        return None, None

    # 2. Login with CSRF token
    login_url = f"{PANEL_BASE}/login"
    try:
        resp = session.post(
            login_url,
            json={"username": USERNAME, "password": PASSWORD},
            headers={"x-csrf-token": csrf_token},
            verify=False
        )
        resp.raise_for_status()
        logger.info("✅ Login successful")
        return session, csrf_token
    except Exception as e:
        logger.error(f"❌ Login failed: {e}")
        return None, None

def reset_traffic_by_email(session, csrf_token, email):
    """Reset traffic using email"""
    reset_url = f"{PANEL_BASE}/panel/api/clients/resetTraffic/{email}"
    headers = {
        "x-csrf-token": csrf_token,
        "accept": "application/json"
    }
    try:
        resp = session.post(reset_url, headers=headers, verify=False)
        if resp.status_code == 200:
            result = resp.json()
            return result.get('success', False)
        else:
            logger.error(f"Reset failed: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error resetting {email}: {e}")
        return False

def main():
    logger.info("🔄 Starting traffic reset for specified users...")
    
    emails = read_emails()
    if not emails:
        logger.warning("⚠️ No emails in reset list.")
        return 0
    
    logger.info(f"📋 Found {len(emails)} users: {emails}")
    
    session, csrf_token = login_to_panel()
    if not session or not csrf_token:
        logger.error("❌ Login failed")
        return 1
    
    success_count = 0
    for email in emails:
        logger.info(f"🔄 Resetting: {email}")
        if reset_traffic_by_email(session, csrf_token, email):
            logger.info(f"✅ {email} reset successfully.")
            success_count += 1
        else:
            logger.error(f"❌ Failed to reset {email}")
    
    logger.info(f"📊 Summary: {success_count}/{len(emails)} users reset")
    logger.info("✅ Operation completed.")
    return 0

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    sys.exit(main())
