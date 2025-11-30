# -*- coding: utf-8 -*-
"""
Core bot functionality for Kingshot Bot
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
import sys
import logging
from datetime import datetime
import tempfile
import os


class KingshotBotHeadless:
    """Main bot class for automating gift code redemption"""

    def __init__(self, player_id, headless=True, log_callback=None, browser_path=None, browser_name=None):
        self.player_id = player_id
        self.url = "https://ks-giftcode.centurygame.com/"
        self.headless = headless
        self.log_callback = log_callback
        self.browser_path = browser_path
        self.browser_name = browser_name or 'Chrome'

        # Configure logging
        self.setup_logging()

        # Configure Chrome/Chromium-based browser
        options = webdriver.ChromeOptions()

        # Set browser binary location if provided
        if browser_path:
            options.binary_location = browser_path
            self.log_info(f"Using {self.browser_name} browser: {browser_path}")

            # Additional Edge-specific configuration
            if self.browser_name == 'Edge':
                # Edge needs explicit user-data-dir to avoid data:, issue
                temp_dir = tempfile.gettempdir()
                edge_profile = os.path.join(temp_dir, 'edge-selenium-profile')
                options.add_argument(f'--user-data-dir={edge_profile}')
                options.add_argument('--profile-directory=Default')
                # Additional Edge-specific flags
                options.add_argument('--disable-features=msEdgeEnableNurturingFramework')
                options.add_argument('--disable-features=msSmartScreenProtection')
                options.add_argument('--inprivate')  # Use InPrivate mode

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

        # Fix for Edge browser navigation issues
        if self.browser_name == 'Edge':
            try:
                # First navigate to a simple page to initialize Edge properly
                self.driver.get('about:blank')
                time.sleep(1)
                # Clear any potential navigation state
                self.driver.execute_script('window.stop();')
                time.sleep(0.5)
            except:
                pass

    def setup_logging(self):
        """Configure logging system"""
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"bot_log_{timestamp}.txt"

        # Configure logging
        handlers = [logging.FileHandler(log_filename, encoding='utf-8')]

        # Only add StreamHandler if no GUI callback
        if not self.log_callback:
            handlers.append(logging.StreamHandler(sys.stdout))

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=handlers
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
        if self.log_callback:
            self.log_callback(f"[*] {msg}")

    def log_success(self, msg):
        """Success log"""
        self.logger.info(f"[+] {msg}")
        if self.log_callback:
            self.log_callback(f"[+] {msg}")

    def log_error(self, msg):
        """Error log"""
        self.logger.error(f"[ERROR] {msg}")
        if self.log_callback:
            self.log_callback(f"[ERROR] {msg}")

    def log_warning(self, msg):
        """Warning log"""
        self.logger.warning(f"[!] {msg}")
        if self.log_callback:
            self.log_callback(f"[!] {msg}")

    def log_debug(self, msg):
        """Debug log"""
        self.logger.debug(f"[DEBUG] {msg}")
        if self.log_callback:
            self.log_callback(f"[DEBUG] {msg}")

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

        # Additional handling for Edge browser
        if self.browser_name == 'Edge':
            try:
                # Clear session storage and cookies
                self.driver.delete_all_cookies()
                self.driver.execute_script('window.sessionStorage.clear();')
                self.driver.execute_script('window.localStorage.clear();')
                time.sleep(0.5)
            except:
                pass

        self.driver.get(self.url)

        # Verify navigation succeeded
        time.sleep(2)
        current_url = self.driver.current_url
        self.log_info(f"Current URL: {current_url}")

        if 'data:' in current_url or current_url == 'about:blank':
            self.log_warning("Browser didn't navigate properly, retrying...")
            time.sleep(1)
            self.driver.get(self.url)
            time.sleep(2)
            current_url = self.driver.current_url
            self.log_info(f"Current URL after retry: {current_url}")

        try:
            # Wait for Vue.js
            self.wait_for_vue()

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

            # Find login button
            self.log_info("Looking for login button...")
            login_button = None

            # Method 1: Try by CSS class (language-independent)
            try:
                login_button = self.driver.find_element(By.CSS_SELECTOR, ".login_btn")
                if login_button.is_displayed():
                    self.log_success(f"Login button found by class: '{login_button.text}'")
            except:
                self.log_info("Login button not found by class, trying text search...")

            # Method 2: Fallback to text search (multi-language)
            if not login_button:
                clickables = self.find_all_clickables()
                self.log_info(f"Found {len(clickables)} clickable elements")

                for elem in clickables:
                    text = elem.text.strip().lower()
                    # Multi-language support
                    login_keywords = ['login', 'iniciar', 'sesion', 'entrar', 'connexion',
                                     'anmelden', 'accedi', '登录', 'ログイン']
                    if text and any(keyword in text for keyword in login_keywords):
                        login_button = elem
                        self.log_success(f"Login button found by text: '{elem.text}'")
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

            self.log_success("Login completed successfully")

            return True

        except Exception as e:
            self.log_error(f"Login error: {str(e)}")
            return False

    def redeem_code(self, code, progress_callback=None):
        """
        Redeem a gift code
        Returns: 'success', 'already_claimed', or 'failed'
        progress_callback: Optional function(step, total_steps, description) to report progress
        """
        self.logger.info("\n" + "="*60)
        self.logger.info(f"REDEEMING CODE: {code}")
        self.logger.info("="*60)

        total_steps = 7  # Total steps in the redemption process
        current_step = 0

        def report_progress(description):
            nonlocal current_step
            current_step += 1
            if progress_callback:
                progress_callback(current_step, total_steps, description)

        try:
            # Step 1: Wait for update
            report_progress("Waiting for page update")
            self.log_info("Waiting for page update...")
            time.sleep(3)

            # Step 2: Find Gift Code field
            report_progress("Finding gift code field")
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
                return 'failed'

            # Step 3: Enter code
            report_progress(f"Entering code: {code}")
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

            # Step 4: Find confirm button
            report_progress("Finding confirm button")
            self.log_info("Looking for confirm button...")
            confirm_button = None

            # Method 1: Try by CSS class (language-independent)
            try:
                confirm_button = self.driver.find_element(By.CSS_SELECTOR, ".exchange_btn")
                class_attr = confirm_button.get_attribute('class') or ''
                if confirm_button.is_displayed() and 'disabled' not in class_attr.lower():
                    self.log_success(f"Confirm button found by class: '{confirm_button.text}'")
                else:
                    confirm_button = None
            except:
                self.log_info("Confirm button not found by class, trying text search...")

            # Method 2: Fallback to text search (multi-language)
            if not confirm_button:
                clickables = self.find_all_clickables()

                for elem in clickables:
                    try:
                        text = elem.text.strip().lower()
                        # Multi-language support
                        confirm_keywords = ['confirm', 'confirmar', 'confirmer', 'bestätigen',
                                          'conferma', 'exchange', 'canjear', 'échanger',
                                          '确认', '交换', '確認', '交換']
                        if text and any(keyword in text for keyword in confirm_keywords):
                            class_attr = elem.get_attribute('class') or ''
                            if 'disabled' not in class_attr.lower():
                                confirm_button = elem
                                self.log_success(f"Confirm button found by text: '{elem.text}'")
                                break
                    except:
                        continue

            if not confirm_button:
                self.log_error("Confirm button not found")
                return 'failed'

            # Step 5: Click confirm
            report_progress("Clicking confirm button")
            self.log_info("Clicking confirm button...")
            confirm_button.click()
            self.log_success("Click performed")

            # Step 6: Wait for response
            report_progress("Waiting for server response")
            self.log_info("Waiting for server response (5 seconds)...")
            time.sleep(5)

            # Step 7: Analyze result (multi-language support)
            report_progress("Analyzing result")

            page_text = self.driver.page_source.lower()

            # Already claimed keywords in multiple languages
            already_claimed_keywords = [
                'already', 'claimed', 'received', 'redeemed', 'used',
                'ya recogido', 'ya canjeado', 'ya reclamado', 'ya usado', 'ya obtenido',
                'déjà récupéré', 'déjà utilisé', 'déjà réclamé', 'déjà reçu',
                'bereits', 'schon', 'erhalten', 'eingelöst',
                'già riscattato', 'già utilizzato', 'già rivendicato', 'già ottenuto',
                '已领取', '已使用', '已兑换', '已获得',
                '既に', 'すでに', '受け取り済み', '使用済み',
                'já resgatado', 'já usado', 'já recebido', 'já obtido'
            ]

            # Success keywords in multiple languages
            success_keywords = [
                'success', 'successful', 'exitoso', 'éxito', 'succès', 'erfolg',
                'successo', 'mail', 'correo', 'e-mail', 'email', 'inbox',
                '成功', '成功了', 'メール', '正常', 'sucesso'
            ]

            # Error keywords in multiple languages
            error_keywords = [
                'error', 'fail', 'failed', 'invalid', 'expired', 'not found',
                'no existe', 'inválido', 'expirado', 'erreur', 'invalide', 'expiré',
                'fehler', 'ungültig', 'abgelaufen', 'errore', 'non valido', 'scaduto',
                '错误', '失败', '無効', '期限切れ', 'erro', 'inválido', 'expirado'
            ]

            # Log page content for debugging (first 500 chars)
            self.log_debug(f"Page content preview: {page_text[:500]}")

            # Determine result
            if any(word in page_text for word in already_claimed_keywords):
                self.log_warning(f"Code {code} was already claimed previously")
                result = 'already_claimed'
            elif any(word in page_text for word in success_keywords):
                self.log_success(f"Code {code} redeemed successfully!")
                result = 'success'
            elif any(word in page_text for word in error_keywords):
                self.log_error(f"Error redeeming code {code}")
                result = 'failed'
            else:
                self.log_warning(f"Could not determine result for code {code} - marking as failed")
                result = 'failed'  # Conservative approach: mark as failed if uncertain

            # Close modal if exists (important for next code)
            self.dismiss_modal()

            return result

        except Exception as e:
            self.log_error(f"Redemption error: {str(e)}")
            return 'failed'

    def close(self):
        """Close browser"""
        self.log_info("Closing browser...")
        try:
            self.driver.quit()
            self.log_success("Browser closed successfully")
        except:
            pass
