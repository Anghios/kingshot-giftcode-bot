# -*- coding: utf-8 -*-
"""
Utility functions for Kingshot Bot
"""

import sys
import subprocess
import re
import os
import platform

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_SCRAPING = True
except ImportError:
    HAS_SCRAPING = False


def check_and_install_dependencies():
    """Check if required dependencies are installed and install if missing"""
    missing_packages = []

    # Check for requests
    try:
        import requests
    except ImportError:
        missing_packages.append('requests')

    # Check for beautifulsoup4
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        missing_packages.append('beautifulsoup4')

    # Check for selenium
    try:
        from selenium import webdriver
    except ImportError:
        missing_packages.append('selenium')

    if missing_packages:
        return missing_packages
    return None


def install_packages(packages):
    """Install missing packages using pip"""
    try:
        print(f"[*] Installing missing packages: {', '.join(packages)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        print("[+] Packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install packages: {str(e)}")
        return False


def fetch_active_gift_codes():
    """Fetch active gift codes from kingshot.net"""
    if not HAS_SCRAPING:
        # This shouldn't happen if GUI checked dependencies, but just in case
        return []

    url = "https://kingshot.net/gift-codes"

    try:
        print("[*] Fetching active codes from kingshot.net...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        all_text = soup.get_text()
        active_codes = []

        # Exact pattern: Active + code + (Copy or Expires)
        pattern = r'Active([A-Za-z0-9]{5,20})(?:Copy|Expires)'
        matches = re.findall(pattern, all_text)

        for code in matches:
            if code not in active_codes:
                active_codes.append(code)

        active_codes = list(dict.fromkeys(active_codes))[:20]
        if active_codes:
            print(f"[+] Found {len(active_codes)} active codes:")
            for code in active_codes:
                print(f"    - {code}")
            return active_codes
        else:
            print("[!] No active codes found")
            return []

    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        return []


def detect_available_browsers():
    """Detect which Chromium-based browsers are installed"""
    available_browsers = []
    system = platform.system()

    if system == "Windows":
        # Chrome
        chrome_paths = [
            os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'Google\\Chrome\\Application\\chrome.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 'Google\\Chrome\\Application\\chrome.exe'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google\\Chrome\\Application\\chrome.exe'),
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                available_browsers.append(('Chrome', path))
                break

        # Brave
        brave_paths = [
            os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'BraveSoftware\\Brave-Browser\\Application\\brave.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 'BraveSoftware\\Brave-Browser\\Application\\brave.exe'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'BraveSoftware\\Brave-Browser\\Application\\brave.exe'),
        ]
        for path in brave_paths:
            if os.path.exists(path):
                available_browsers.append(('Brave', path))
                break

        # Edge
        edge_paths = [
            os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'Microsoft\\Edge\\Application\\msedge.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 'Microsoft\\Edge\\Application\\msedge.exe'),
        ]
        for path in edge_paths:
            if os.path.exists(path):
                available_browsers.append(('Edge (may have issues)', path))
                break

    elif system == "Linux":
        # Chrome
        if os.path.exists('/usr/bin/google-chrome') or os.path.exists('/usr/bin/google-chrome-stable'):
            available_browsers.append(('Chrome', '/usr/bin/google-chrome'))
        # Brave
        if os.path.exists('/usr/bin/brave-browser') or os.path.exists('/usr/bin/brave'):
            available_browsers.append(('Brave', '/usr/bin/brave-browser'))
        # Chromium
        if os.path.exists('/usr/bin/chromium-browser') or os.path.exists('/usr/bin/chromium'):
            available_browsers.append(('Chromium', '/usr/bin/chromium-browser'))
        # Edge
        if os.path.exists('/usr/bin/microsoft-edge'):
            available_browsers.append(('Edge', '/usr/bin/microsoft-edge'))

    elif system == "Darwin":  # macOS
        # Chrome
        chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        if os.path.exists(chrome_path):
            available_browsers.append(('Chrome', chrome_path))
        # Brave
        brave_path = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
        if os.path.exists(brave_path):
            available_browsers.append(('Brave', brave_path))
        # Edge
        edge_path = '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'
        if os.path.exists(edge_path):
            available_browsers.append(('Edge', edge_path))

    return available_browsers


def get_preferred_browser():
    """Get the preferred browser (first available in order: Chrome, Brave, Edge)"""
    browsers = detect_available_browsers()

    if not browsers:
        return None, None

    # Priority order: Chrome, Brave, Edge, others
    priority = ['Chrome', 'Brave', 'Edge', 'Chromium']

    for browser_name in priority:
        for name, path in browsers:
            if name == browser_name:
                return name, path

    # Return first available if none match priority
    return browsers[0]
