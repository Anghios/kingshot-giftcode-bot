# -*- coding: utf-8 -*-
"""
Kingshot Gift Code Bot - Main Entry Point
Automated bot for redeeming gift codes in Kingshot game
"""

import sys
import time
import tkinter as tk

from utils import (check_and_install_dependencies, install_packages,
                   fetch_active_gift_codes, get_preferred_browser)
from bot_core import KingshotBotHeadless
from gui import KingshotBotGUI


def run_cli():
    """Run bot in CLI mode (original behavior)"""
    # Check dependencies first
    missing = check_and_install_dependencies()
    if missing:
        print("[ERROR] Missing required packages:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nWould you like to install them now? (y/n): ", end='')

        try:
            response = input().strip().lower()
            if response in ['y', 'yes']:
                if install_packages(missing):
                    print("\n[+] Packages installed successfully!")
                    print("[!] Please restart the application.")
                    sys.exit(0)
                else:
                    print(f"\n[ERROR] Installation failed. Please run manually:")
                    print(f"        pip install {' '.join(missing)}")
                    sys.exit(1)
            else:
                print(f"\n[!] Cannot continue without required packages.")
                print(f"    Please install manually: pip install {' '.join(missing)}")
                sys.exit(1)
        except (KeyboardInterrupt, EOFError):
            print("\n\n[!] Installation cancelled.")
            sys.exit(1)

    try:
        with open('login_id.txt', 'r') as f:
            player_id = f.read().strip()
        if not player_id:
            print("[ERROR] The login_id.txt file is empty")
            sys.exit(1)
    except FileNotFoundError:
        print("[ERROR] login_id.txt file not found")
        sys.exit(1)

    codes = fetch_active_gift_codes()
    if not codes:
        print("[ERROR] Could not fetch active codes")
        print("Check your connection or visit: https://kingshot.net/gift-codes")
        sys.exit(1)

    headless = True
    if '--visible' in sys.argv:
        headless = False

    # Detect browser
    browser_name, browser_path = get_preferred_browser()
    if not browser_name:
        print("[ERROR] No compatible browser found!")
        print("Please install one of: Chrome, Brave, Edge")
        sys.exit(1)

    print("="*70)
    print("KINGSHOT GIFT CODE BOT")
    print("="*70)
    print(f"Player ID: {player_id}")
    print(f"Browser: {browser_name}")
    print(f"Codes to redeem: {len(codes)}")
    for i, code in enumerate(codes, 1):
        print(f"  {i}. {code}")
    print("="*70)
    print()

    bot = KingshotBotHeadless(player_id, headless=headless,
                             browser_path=browser_path,
                             browser_name=browser_name)

    try:
        if not bot.login():
            bot.log_error("Login failed. Aborting.")
            bot.close()
            sys.exit(1)

        successful = 0
        already_claimed = 0
        failed = 0

        for code in codes:
            result = bot.redeem_code(code)
            if result == 'success':
                successful += 1
            elif result == 'already_claimed':
                already_claimed += 1
            else:  # 'failed'
                failed += 1

            if len(codes) > 1:
                time.sleep(3)

        bot.logger.info("\n" + "="*70)
        bot.logger.info("FINAL SUMMARY")
        bot.logger.info("="*70)
        bot.logger.info(f"[+] Successful: {successful}")
        bot.logger.info(f"[!] Already claimed: {already_claimed}")
        bot.logger.info(f"[-] Failed: {failed}")
        bot.logger.info(f"[*] Total: {successful + already_claimed + failed}")
        bot.logger.info("="*70)

        bot.log_success("Process completed!")

    except KeyboardInterrupt:
        bot.log_warning("Process interrupted by user")
    except Exception as e:
        bot.log_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        bot.close()


def run_gui():
    """Run bot in GUI mode"""
    root = tk.Tk()
    app = KingshotBotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    # Check if CLI mode is requested
    if '--cli' in sys.argv:
        run_cli()
    else:
        # Run GUI mode by default
        run_gui()
