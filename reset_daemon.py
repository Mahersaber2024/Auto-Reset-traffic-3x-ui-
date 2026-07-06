#!/usr/bin/env python3
# reset_daemon.py - Reset traffic for specific users (Python version)

import os
import sys
import json
import logging
import requests
from datetime import datetime
from pathlib import Path

# ========== Settings ==========
CONFIG_FILE = "/etc/x3-traffic-reset/config.conf"
LOG_FILE = "/var/log/x3-traffic-reset.log"
PANEL_URL = "https://YOUR_PANEL_IP:2053"
USERNAME = "admin"
PASSWORD = "YourPassword"
# ===============================

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

def read_user_ids():
    """Read user IDs from config file"""
    if not os.path.exists(CONFIG_FILE):
        logger.error(f"❌ Config file not found: {CONFIG_FILE}")
        return []
    
    user_ids = []
    with open(CONFIG_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#'):
                user_ids.append(line)
    
    return user_ids

def login_to_panel():
    """Login to 3xUI panel and get CSRF token"""
    login_url = f"{PANEL_URL}/login"
    session = requests.Session()
    
    try:
        response = session.post(
            login_url,
            json={"username": USERNAME, "password": PASSWORD},
            verify=False  # For self-signed certificates
        )
        response.raise_for_status()
        
        # Extract CSRF token from cookies
        for cookie in session.cookies:
            if cookie.name == 'x-ui_csrf':
                return session, cookie.value
        
        logger.error("❌ CSRF token not found in cookies")
        return None, None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Login failed: {e}")
        return None, None

def reset_user_traffic(session, csrf_token, user_id):
    """Reset traffic for a specific user"""
    reset_url = f"{PANEL_URL}/api/client/resetClientTraffic/{user_id}"
    
    try:
        response = session.post(
            reset_url,
            headers={"x-csrf-token": csrf_token},
            verify=False
        )
        response.raise_for_status()
        result = response.json()
        return result.get('success', False)
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error resetting user {user_id}: {e}")
        return False
    except json.JSONDecodeError:
        logger.error(f"❌ Invalid response from panel for user {user_id}")
        return False

def main():
    """Main function"""
    logger.info("🔄 Starting traffic reset for specified users...")
    
    # Read user IDs
    user_ids = read_user_ids()
    if not user_ids:
        logger.warning("⚠️ No users in the traffic reset list.")
        return 0
    
    logger.info(f"📋 Found {len(user_ids)} users in reset list")
    
    # Login to panel
    session, csrf_token = login_to_panel()
    if not session or not csrf_token:
        logger.error("❌ Failed to login to panel")
        return 1
    
    logger.info("✅ Successfully logged in to panel")
    
    # Reset traffic for each user
    success_count = 0
    for user_id in user_ids:
        logger.info(f"🔄 Resetting traffic for user ID: {user_id}")
        
        if reset_user_traffic(session, csrf_token, user_id):
            logger.info(f"✅ Traffic for user {user_id} reset successfully.")
            success_count += 1
        else:
            logger.error(f"❌ Failed to reset traffic for user {user_id}")
    
    # Summary
    logger.info(f"📊 Summary: {success_count}/{len(user_ids)} users reset successfully")
    logger.info("✅ Traffic reset operation completed.")
    
    return 0

if __name__ == "__main__":
    # Disable SSL warnings for self-signed certificates
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    sys.exit(main())