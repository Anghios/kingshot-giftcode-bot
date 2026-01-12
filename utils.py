# -*- coding: utf-8 -*-
"""
Utility functions for Kingshot Gift Code Bot
Refactored with retry logic, type hints, and better error handling
"""

from __future__ import annotations

import os
import platform
import random
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from config import (
    BROWSER_PATHS, BROWSER_PRIORITY, CODES_SOURCE_URL,
    MAX_CODES_TO_FETCH, RETRY_CONFIG, SCRAPING_PATTERN,
    TIMEOUTS, USER_AGENTS
)

# Lazy imports for optional dependencies
HAS_SCRAPING = False
requests = None
BeautifulSoup = None

try:
    import requests as _requests
    from bs4 import BeautifulSoup as _BeautifulSoup
    requests = _requests
    BeautifulSoup = _BeautifulSoup
    HAS_SCRAPING = True
except ImportError:
    pass


@dataclass
class BrowserInfo:
    """Information about a detected browser"""
    name: str
    path: str
    has_issues: bool = False

    def __str__(self) -> str:
        suffix = " (may have issues)" if self.has_issues else ""
        return f"{self.name}{suffix}"


class DependencyManager:
    """Manages package dependencies"""

    REQUIRED_PACKAGES = [
        ('requests', 'requests'),
        ('bs4', 'beautifulsoup4'),
        ('selenium', 'selenium'),
    ]

    @classmethod
    def check_missing(cls) -> List[str]:
        """Check for missing dependencies and return list of packages to install"""
        missing = []

        for module_name, package_name in cls.REQUIRED_PACKAGES:
            try:
                __import__(module_name)
            except ImportError:
                missing.append(package_name)

        return missing

    @classmethod
    def install(cls, packages: List[str]) -> bool:
        """Install packages using pip"""
        if not packages:
            return True

        try:
            print(f"[*] Installing packages: {', '.join(packages)}")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade"] + packages,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                print("[+] Packages installed successfully!")
                return True
            else:
                print(f"[ERROR] Installation failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("[ERROR] Installation timed out")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to install packages: {str(e)}")
            return False


class CodeFetcher:
    """Fetches gift codes from external sources with retry logic"""

    def __init__(self):
        self.url = CODES_SOURCE_URL
        self.pattern = re.compile(SCRAPING_PATTERN)

    def _get_random_user_agent(self) -> str:
        """Get a random user agent string"""
        return random.choice(USER_AGENTS)

    def _fetch_with_retry(self) -> Optional[str]:
        """Fetch URL content with retry logic"""
        if not HAS_SCRAPING:
            print("[ERROR] Scraping dependencies not available")
            return None

        headers = {"User-Agent": self._get_random_user_agent()}
        last_error = None

        for attempt in range(RETRY_CONFIG.max_attempts):
            try:
                if attempt > 0:
                    delay = RETRY_CONFIG.delay_between * (RETRY_CONFIG.backoff_multiplier ** (attempt - 1))
                    print(f"[*] Retry {attempt + 1}/{RETRY_CONFIG.max_attempts} after {delay:.1f}s...")
                    time.sleep(delay)

                response = requests.get(
                    self.url,
                    headers=headers,
                    timeout=TIMEOUTS.http_request
                )
                response.raise_for_status()
                return response.text

            except requests.exceptions.Timeout:
                last_error = "Connection timed out"
                print(f"[!] Attempt {attempt + 1}: {last_error}")
            except requests.exceptions.ConnectionError:
                last_error = "Connection failed"
                print(f"[!] Attempt {attempt + 1}: {last_error}")
            except requests.exceptions.HTTPError as e:
                last_error = f"HTTP error: {e.response.status_code}"
                print(f"[!] Attempt {attempt + 1}: {last_error}")
            except Exception as e:
                last_error = str(e)
                print(f"[!] Attempt {attempt + 1}: {last_error}")

        print(f"[ERROR] All {RETRY_CONFIG.max_attempts} attempts failed. Last error: {last_error}")
        return None

    def fetch(self) -> List[str]:
        """Fetch active gift codes"""
        print(f"[*] Fetching active codes from {self.url}...")

        html_content = self._fetch_with_retry()
        if not html_content:
            return []

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            all_text = soup.get_text()

            # Find all codes matching the pattern
            matches = self.pattern.findall(all_text)

            # Remove duplicates while preserving order
            seen = set()
            unique_codes = []
            for code in matches:
                if code not in seen:
                    seen.add(code)
                    unique_codes.append(code)

            # Limit to max codes
            active_codes = unique_codes[:MAX_CODES_TO_FETCH]

            if active_codes:
                print(f"[+] Found {len(active_codes)} active codes:")
                for code in active_codes:
                    print(f"    - {code}")
            else:
                print("[!] No active codes found")

            return active_codes

        except Exception as e:
            print(f"[ERROR] Failed to parse codes: {str(e)}")
            return []


class BrowserDetector:
    """Detects available Chromium-based browsers on the system"""

    def __init__(self):
        self.system = platform.system()

    def _get_paths_for_platform(self) -> Dict[str, List[str]]:
        """Get browser paths for current platform"""
        if self.system == "Windows":
            return BROWSER_PATHS.get_windows_paths()
        elif self.system == "Linux":
            return BROWSER_PATHS.get_linux_paths()
        elif self.system == "Darwin":
            return BROWSER_PATHS.get_macos_paths()
        return {}

    def _find_browser_path(self, paths: List[str]) -> Optional[str]:
        """Find first existing path from a list"""
        for path in paths:
            if os.path.exists(path):
                return path
        return None

    def detect(self) -> List[BrowserInfo]:
        """Detect all available Chromium-based browsers"""
        available = []
        paths_by_browser = self._get_paths_for_platform()

        for browser_name, paths in paths_by_browser.items():
            found_path = self._find_browser_path(paths)
            if found_path:
                # Edge has known issues with Selenium
                has_issues = browser_name == 'Edge'
                available.append(BrowserInfo(
                    name=browser_name,
                    path=found_path,
                    has_issues=has_issues
                ))

        return available

    def get_preferred(self) -> Optional[BrowserInfo]:
        """Get the preferred browser based on priority order"""
        browsers = self.detect()

        if not browsers:
            return None

        # Find first browser matching priority order
        for priority_name in BROWSER_PRIORITY:
            for browser in browsers:
                if browser.name == priority_name:
                    return browser

        # Return first available if none match priority
        return browsers[0]


# =============================================================================
# Legacy function wrappers for backwards compatibility
# =============================================================================

def check_and_install_dependencies() -> Optional[List[str]]:
    """Check if required dependencies are installed and return missing packages"""
    missing = DependencyManager.check_missing()
    return missing if missing else None


def install_packages(packages: List[str]) -> bool:
    """Install missing packages using pip"""
    return DependencyManager.install(packages)


def fetch_active_gift_codes() -> List[str]:
    """Fetch active gift codes from kingshot.net"""
    fetcher = CodeFetcher()
    return fetcher.fetch()


def detect_available_browsers() -> List[Tuple[str, str]]:
    """
    Detect which Chromium-based browsers are installed.
    Returns list of (name, path) tuples for backwards compatibility.
    """
    detector = BrowserDetector()
    browsers = detector.detect()

    # Convert to legacy format
    return [(str(b), b.path) for b in browsers]


def get_preferred_browser() -> Tuple[Optional[str], Optional[str]]:
    """Get the preferred browser (first available in priority order)"""
    detector = BrowserDetector()
    browser = detector.get_preferred()

    if browser:
        return browser.name, browser.path
    return None, None
