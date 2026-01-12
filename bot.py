# -*- coding: utf-8 -*-
"""
Kingshot Gift Code Bot - Main Entry Point
Automated bot for redeeming gift codes in Kingshot game

Usage:
    python bot.py          # Run GUI mode (default)
    python bot.py --cli    # Run CLI mode (headless)
    python bot.py --cli --visible  # Run CLI mode with visible browser
"""

from __future__ import annotations

import sys
import time
import traceback
import tkinter as tk
from typing import NoReturn

from config import (
    VERSION, APP_NAME, PLAYER_ID_FILE,
    TIMEOUTS, CODES_SOURCE_URL
)
from utils import (
    check_and_install_dependencies, install_packages,
    fetch_active_gift_codes, get_preferred_browser
)
from bot_core import KingshotBotHeadless, RedeemResult
from gui import KingshotBotGUI


def print_banner() -> None:
    """Print application banner"""
    print()
    print("=" * 70)
    print(f"  {APP_NAME} v{VERSION}")
    print("=" * 70)


def check_and_install_cli_dependencies() -> bool:
    """Check and optionally install missing dependencies for CLI mode"""
    missing = check_and_install_dependencies()

    if not missing:
        return True

    print("[ERROR] Missing required packages:")
    for pkg in missing:
        print(f"  - {pkg}")
    print()
    print("Would you like to install them now? (y/n): ", end='')

    try:
        response = input().strip().lower()
        if response in ['y', 'yes']:
            if install_packages(missing):
                print("\n[+] Packages installed successfully!")
                print("[!] Please restart the application.")
                return False
            else:
                print(f"\n[ERROR] Installation failed. Please run manually:")
                print(f"        pip install {' '.join(missing)}")
                return False
        else:
            print(f"\n[!] Cannot continue without required packages.")
            print(f"    Please install manually: pip install {' '.join(missing)}")
            return False
    except (KeyboardInterrupt, EOFError):
        print("\n\n[!] Installation cancelled.")
        return False


def load_player_id() -> str | None:
    """Load player ID from file"""
    try:
        with open(PLAYER_ID_FILE, 'r') as f:
            player_id = f.read().strip()
            if not player_id:
                print(f"[ERROR] The {PLAYER_ID_FILE} file is empty")
                return None
            return player_id
    except FileNotFoundError:
        print(f"[ERROR] {PLAYER_ID_FILE} file not found")
        print(f"        Create the file and add your player ID")
        return None


def run_cli() -> int:
    """
    Run bot in CLI mode.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    print_banner()

    # Check dependencies
    if not check_and_install_cli_dependencies():
        return 1

    # Load player ID
    player_id = load_player_id()
    if not player_id:
        return 1

    # Fetch active codes
    print()
    codes = fetch_active_gift_codes()
    if not codes:
        print("[ERROR] Could not fetch active codes")
        print(f"        Check your connection or visit: {CODES_SOURCE_URL}")
        return 1

    # Determine headless mode
    headless = '--visible' not in sys.argv

    # Detect browser
    browser_name, browser_path = get_preferred_browser()
    if not browser_name:
        print("[ERROR] No compatible browser found!")
        print("        Please install one of: Chrome, Brave, Edge")
        return 1

    # Print configuration
    print()
    print(f"Player ID: {player_id}")
    print(f"Browser: {browser_name}")
    print(f"Mode: {'Headless' if headless else 'Visible'}")
    print(f"Codes to redeem: {len(codes)}")
    print()
    print("=" * 70)
    print()

    # Initialize and run bot
    bot = None
    try:
        bot = KingshotBotHeadless(
            player_id,
            headless=headless,
            browser_path=browser_path,
            browser_name=browser_name
        )

        if not bot.login():
            bot.log_error("Login failed. Aborting.")
            return 1

        # Track results
        successful = 0
        already_claimed = 0
        failed = 0

        # Process each code
        for i, code in enumerate(codes, 1):
            result = bot.redeem_code(code)

            if result == RedeemResult.SUCCESS:
                successful += 1
            elif result == RedeemResult.ALREADY_CLAIMED:
                already_claimed += 1
            else:
                failed += 1

            # Wait between codes
            if i < len(codes):
                time.sleep(TIMEOUTS.between_codes)

        # Print summary
        print()
        print("=" * 70)
        print("FINAL SUMMARY")
        print("=" * 70)
        print(f"[+] Successful: {successful}")
        print(f"[!] Already claimed: {already_claimed}")
        print(f"[-] Failed: {failed}")
        print(f"[*] Total: {successful + already_claimed + failed}")
        print("=" * 70)
        print()
        print("[+] Process completed!")

        return 0

    except KeyboardInterrupt:
        print("\n[!] Process interrupted by user")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")
        traceback.print_exc()
        return 1
    finally:
        if bot:
            bot.close()


def run_gui() -> None:
    """Run bot in GUI mode"""
    root = tk.Tk()

    # Set app icon if available (optional)
    try:
        # You can add an icon file here
        pass
    except Exception:
        pass

    app = KingshotBotGUI(root)
    root.mainloop()


def main() -> int:
    """Main entry point"""
    # Parse command line arguments
    if '--cli' in sys.argv:
        return run_cli()
    elif '--help' in sys.argv or '-h' in sys.argv:
        print(f"{APP_NAME} v{VERSION}")
        print()
        print("Usage:")
        print("  python bot.py              Run GUI mode (default)")
        print("  python bot.py --cli        Run CLI mode (headless browser)")
        print("  python bot.py --cli --visible  Run CLI mode with visible browser")
        print("  python bot.py --help       Show this help message")
        return 0
    else:
        run_gui()
        return 0


if __name__ == "__main__":
    sys.exit(main())
