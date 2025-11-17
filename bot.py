# -*- coding: utf-8 -*-
"""
Kingshot Bot - Headless Version with Logging
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sys
import logging
from datetime import datetime
import re

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_SCRAPING = True
except ImportError:
    HAS_SCRAPING = False


def fetch_active_gift_codes():
    if not HAS_SCRAPING:
        print("[ERROR] You need to install requests and beautifulsoup4:")
        print("        pip install requests beautifulsoup4")
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
            print(f"[+] Encontrados {len(active_codes)} active codes:")
            for code in active_codes:
                print(f"    - {code}")
            return active_codes
        else:
            print("[!] No active codes found")
            return []

    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        return []

class KingshotBotHeadless:
    def __init__(self, player_id, headless=True):
        self.player_id = player_id
        self.url = "https://ks-giftcode.centurygame.com/"
        self.headless = headless

        # Configure logging
        self.setup_logging()

        # Configure Chrome
        options = webdriver.ChromeOptions()

        if headless:
            # Multiple flags to ensure headless mode
            options.add_argument('--headless=new')
            options.add_argument('--headless')  # Sintaxis antigua por compatibilidad
            options.add_argument('--disable-gpu')
            options.add_argument('--window-position=-2400,-2400')  # Off screen
            self.log_info("Headless mode enabled (INVISIBLE browser)")
        else:
            self.log_info("Visible mode enabled")

        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        # Suppress Chrome logs
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        self.log_info("Starting ChromeDriver...")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 20)
        self.log_success("ChromeDriver started successfully")

    def setup_logging(self):
        """Configure logging system"""
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"bot_log_{timestamp}.txt"

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info("="*70)
        self.logger.info("KINGSHOT GIFT CODE BOT")
        self.logger.info("="*70)
        self.logger.info(f"Log file: {log_filename}")
        self.logger.info(f"Player ID: {self.player_id}")

    def log_info(self, msg):
        """INFO level log"""
        self.logger.info(f"[*] {msg}")

    def log_success(self, msg):
        """Success log"""
        self.logger.info(f"[+] {msg}")

    def log_error(self, msg):
        """Error log"""
        self.logger.error(f"[ERROR] {msg}")

    def log_warning(self, msg):
        """Warning log"""
        self.logger.warning(f"[!] {msg}")

    def log_debug(self, msg):
        """Debug log"""
        self.logger.debug(f"[DEBUG] {msg}")

    def wait_for_vue(self):
        """Wait for Vue.js to finish loading"""
        self.log_info("Waiting for Vue.js to load...")
        time.sleep(3)
        self.wait.until(lambda d: len(d.find_element(By.ID, "app").text) > 0)
        time.sleep(1)
        self.log_success("Vue.js loaded successfully")

    def find_all_clickables(self):
        """Find all clickable elements"""
        clickables = []
        selectors = ["div[class*='btn']", "div[class*='button']", "button"]

        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed():
                        clickables.append(elem)
            except:
                continue

        return clickables

    def take_screenshot(self, name):
        """Take screenshot and log it (DISABLED)"""
        # Screenshots disabled - do nothing
        pass

    def dismiss_modal(self):
        """Close any modal or mask blocking the interface"""
        try:
            self.log_info("Checking for active modal...")
            time.sleep(1)

            # Try to find and close modal
            # Method 1: Find close button (X, OK, Close, etc)
            close_selectors = [
                "div[class*='close']",
                "button[class*='close']",
                "div[class*='btn-close']",
                "div[class*='modal'] button",
                "div[class*='dialog'] button"
            ]

            for selector in close_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons:
                        if btn.is_displayed():
                            self.log_info(f"Found close button: {btn.text or 'no text'}")
                            btn.click()
                            time.sleep(1)
                            self.log_success("Modal closed with button")
                            return True
                except:
                    continue

            # Method 2: Click on background mask
            try:
                mask = self.driver.find_element(By.CSS_SELECTOR, "div.mask")
                if mask.is_displayed():
                    self.log_info("Found background mask, clicking to close...")
                    mask.click()
                    time.sleep(1)
                    self.log_success("Modal closed by clicking mask")
                    return True
            except:
                pass

            # Method 3: Force close with JavaScript
            try:
                self.driver.execute_script("""
                    var masks = document.querySelectorAll('.mask, [class*="mask"]');
                    masks.forEach(function(mask) {
                        mask.style.display = 'none';
                        mask.remove();
                    });
                    var modals = document.querySelectorAll('[class*="modal"], [class*="dialog"]');
                    modals.forEach(function(modal) {
                        modal.style.display = 'none';
                    });
                """)
                self.log_success("Modal force closed with JavaScript")
                time.sleep(1)
                return True
            except:
                pass

            self.log_info("No active modal found")
            return False

        except Exception as e:
            self.log_warning(f"Error trying to close modal: {str(e)}")
            return False

    def login(self):
        """Login with Player ID"""
        self.log_info(f"Opening {self.url}")
        self.driver.get(self.url)

        try:
            # Wait for Vue.js
            self.wait_for_vue()
            self.take_screenshot("step_01_inicial")

            # Find Player ID field
            self.log_info("Looking for Player ID field...")
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")

            if not inputs:
                all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                inputs = [inp for inp in all_inputs if inp.is_displayed()]

            if not inputs:
                self.log_error("Player ID field not found")
                return False

            player_id_field = inputs[0]
            placeholder = player_id_field.get_attribute('placeholder') or ''
            self.log_success(f"Field found: '{placeholder}'")

            # Enter Player ID
            self.log_info(f"Entering Player ID: {self.player_id}")
            player_id_field.click()
            time.sleep(0.5)
            player_id_field.clear()
            player_id_field.send_keys(self.player_id)
            time.sleep(0.5)
            self.log_success("Player ID entered successfully")

            self.take_screenshot("step_02_player_id_ingresado")

            # Find login button
            self.log_info("Looking for login button...")
            clickables = self.find_all_clickables()
            self.log_info(f"Encontrados {len(clickables)} clickable elements")

            login_button = None
            for elem in clickables:
                text = elem.text.strip().lower()
                if text and ('login' in text or 'iniciar' in text or 'sesion' in text):
                    login_button = elem
                    self.log_success(f"Button found: '{elem.text}'")
                    break

            if not login_button:
                self.log_error("Login button not found")
                return False

            # Click login
            self.log_info("Clicking login button...")
            login_button.click()
            self.log_success("Click performed")

            # Wait for response
            self.log_info("Waiting for server response (7 seconds)...")
            time.sleep(7)

            self.take_screenshot("step_03_despues_login")
            self.log_success("Login completed successfully")

            return True

        except Exception as e:
            self.log_error(f"Login error: {str(e)}")
            self.take_screenshot("error_login")
            return False

    def redeem_code(self, code):
        """Redeem a gift code"""
        self.logger.info("\n" + "="*60)
        self.logger.info(f"REDEEMING CODE: {code}")
        self.logger.info("="*60)

        try:
            # Wait for update
            self.log_info("Waiting for page update...")
            time.sleep(3)

            # Find Gift Code field
            self.log_info("Looking for Gift Code field...")
            all_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")

            if not all_inputs:
                all_inputs = self.driver.find_elements(By.TAG_NAME, "input")

            visible_inputs = []
            for i, inp in enumerate(all_inputs):
                try:
                    if inp.is_displayed():
                        placeholder = inp.get_attribute('placeholder') or ''
                        maxlength = inp.get_attribute('maxlength') or ''
                        self.log_info(f"Input {i}: placeholder='{placeholder}', maxlength='{maxlength}'")
                        visible_inputs.append(inp)
                except:
                    continue

            self.log_info(f"Total: {len(visible_inputs)} visible inputs")

            # Find gift code field
            gift_code_field = None

            # By maxlength="20"
            for inp in visible_inputs:
                if inp.get_attribute('maxlength') == '20':
                    gift_code_field = inp
                    self.log_success("Field found by maxlength=20")
                    break

            # By placeholder
            if not gift_code_field:
                for inp in visible_inputs:
                    placeholder = inp.get_attribute('placeholder') or ''
                    if 'codigo' in placeholder.lower() or 'code' in placeholder.lower():
                        gift_code_field = inp
                        self.log_success("Field found by placeholder")
                        break

            # First visible input
            if not gift_code_field and visible_inputs:
                gift_code_field = visible_inputs[0]
                self.log_warning("Using first visible input")

            if not gift_code_field:
                self.log_error("Gift Code field not found")
                self.take_screenshot("error_no_gift_field")
                return False

            # Enter code
            self.log_info(f"Entering code: {code}")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", gift_code_field)
            time.sleep(0.5)

            gift_code_field.click()
            time.sleep(0.5)
            gift_code_field.clear()
            time.sleep(0.3)
            gift_code_field.send_keys(code)
            time.sleep(1)
            self.log_success("Code entered successfully")

            self.take_screenshot(f"step_04_codigo_{code}_ingresado")

            # Find confirm button
            self.log_info("Looking for confirm button...")
            clickables = self.find_all_clickables()

            confirm_button = None
            for elem in clickables:
                try:
                    text = elem.text.strip().lower()
                    if text and ('confirm' in text or 'confirmar' in text):
                        class_attr = elem.get_attribute('class') or ''
                        if 'disabled' not in class_attr.lower():
                            confirm_button = elem
                            self.log_success(f"Button found: '{elem.text}'")
                            break
                except:
                    continue

            if not confirm_button:
                self.log_error("Confirm button not found")
                return False

            # Click confirm
            self.log_info("Clicking confirm button...")
            confirm_button.click()
            self.log_success("Click performed")

            # Wait for response
            self.log_info("Waiting for server response (5 seconds)...")
            time.sleep(5)

            self.take_screenshot(f"step_05_resultado_{code}")

            # Analyze result
            page_text = self.driver.page_source.lower()

            result_success = False
            if any(word in page_text for word in ['success', 'exitoso', 'mail', 'correo']):
                self.log_success(f"Codigo {code} redeemed successfully!")
                result_success = True
            elif any(word in page_text for word in ['error', 'not found', 'no existe']):
                self.log_error(f"Error redeeming code {code}")
                result_success = False
            else:
                self.log_warning("Could not determine result with certainty")
                result_success = True

            # Close modal if exists (important for next code)
            self.dismiss_modal()

            return result_success

        except Exception as e:
            self.log_error(f"Redemption error: {str(e)}")
            self.take_screenshot(f"error_redeem_{code}")
            return False

    def close(self):
        """Close browser"""
        self.log_info("Closing browser...")
        try:
            self.driver.quit()
            self.log_success("Browser closed successfully")
        except:
            pass


if __name__ == "__main__":
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

    print("="*70)
    print("KINGSHOT GIFT CODE BOT")
    print("="*70)
    print(f"Player ID: {player_id}")
    print(f"Codes to redeem: {len(codes)}")
    for i, code in enumerate(codes, 1):
        print(f"  {i}. {code}")
    print("="*70)
    print()

    bot = KingshotBotHeadless(player_id, headless=headless)

    try:
        if not bot.login():
            bot.log_error("Login failed. Aborting.")
            bot.close()
            sys.exit(1)

        successful = 0
        failed = 0

        for code in codes:
            if bot.redeem_code(code):
                successful += 1
            else:
                failed += 1

            if len(codes) > 1:
                time.sleep(3)

        bot.logger.info("\n" + "="*70)
        bot.logger.info("FINAL SUMMARY")
        bot.logger.info("="*70)
        bot.logger.info(f"[+] Successful: {successful}")
        bot.logger.info(f"[-] Failed: {failed}")
        bot.logger.info(f"[*] Total: {successful + failed}")
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
