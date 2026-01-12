# -*- coding: utf-8 -*-
"""
Core bot functionality for Kingshot Gift Code Bot
Refactored with improved architecture, error handling, and type hints
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
import time
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, List, Optional, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException
)

from config import (
    REDEEM_URL, TIMEOUTS, SELECTORS, LANGUAGE_KEYWORDS,
    CHROME_OPTIONS, CHROME_HEADLESS_OPTIONS, EDGE_SPECIFIC_OPTIONS,
    CHROME_EXPERIMENTAL_OPTIONS, LOG_CONFIG, VERSION, APP_NAME
)


class RedeemResult(Enum):
    """Enumeration for code redemption results"""
    SUCCESS = "success"
    ALREADY_CLAIMED = "already_claimed"
    FAILED = "failed"
    INVALID = "invalid"
    EXPIRED = "expired"


@dataclass
class RedeemStats:
    """Statistics for redemption session"""
    successful: int = 0
    already_claimed: int = 0
    failed: int = 0

    @property
    def total(self) -> int:
        return self.successful + self.already_claimed + self.failed

    def update(self, result: RedeemResult) -> None:
        if result == RedeemResult.SUCCESS:
            self.successful += 1
        elif result == RedeemResult.ALREADY_CLAIMED:
            self.already_claimed += 1
        else:
            self.failed += 1


class BotLogger:
    """Dedicated logger class for the bot with GUI callback support"""

    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log_callback = log_callback
        self.logger: Optional[logging.Logger] = None
        self.log_filename: Optional[str] = None
        self._setup_complete = False

    def setup(self, player_id: str) -> str:
        """Initialize logging system"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = f"{LOG_CONFIG.file_prefix}{timestamp}{LOG_CONFIG.file_extension}"

        # Create a unique logger for this instance
        logger_name = f"kingshot_bot_{timestamp}"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)

        # Clear existing handlers to prevent duplicates
        self.logger.handlers.clear()

        # File handler
        file_handler = logging.FileHandler(self.log_filename, encoding=LOG_CONFIG.encoding)
        file_handler.setFormatter(logging.Formatter(LOG_CONFIG.format, LOG_CONFIG.date_format))
        self.logger.addHandler(file_handler)

        # Console handler (only if no GUI callback)
        if not self.log_callback:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter(LOG_CONFIG.format, LOG_CONFIG.date_format))
            self.logger.addHandler(console_handler)

        # Log header
        self.logger.info("=" * 70)
        self.logger.info(f"{APP_NAME} v{VERSION}")
        self.logger.info("=" * 70)
        self.logger.info(f"Log file: {self.log_filename}")
        self.logger.info(f"Player ID: {player_id}")

        self._setup_complete = True
        return self.log_filename

    def _log(self, level: str, prefix: str, msg: str) -> None:
        """Internal logging method"""
        formatted_msg = f"{prefix} {msg}"

        if self.logger and self._setup_complete:
            log_method = getattr(self.logger, level.lower(), self.logger.info)
            log_method(formatted_msg)

        if self.log_callback:
            self.log_callback(formatted_msg)

    def info(self, msg: str) -> None:
        self._log('info', '[*]', msg)

    def success(self, msg: str) -> None:
        self._log('info', '[+]', msg)

    def error(self, msg: str) -> None:
        self._log('error', '[ERROR]', msg)

    def warning(self, msg: str) -> None:
        self._log('warning', '[!]', msg)

    def debug(self, msg: str) -> None:
        self._log('debug', '[DEBUG]', msg)

    def section(self, title: str) -> None:
        """Log a section header"""
        if self.logger:
            self.logger.info("")
            self.logger.info("=" * 60)
            self.logger.info(title)
            self.logger.info("=" * 60)


class KingshotBotHeadless:
    """
    Main bot class for automating gift code redemption.
    Supports context manager protocol for automatic resource cleanup.
    """

    def __init__(
        self,
        player_id: str,
        headless: bool = True,
        log_callback: Optional[Callable[[str], None]] = None,
        browser_path: Optional[str] = None,
        browser_name: Optional[str] = None
    ):
        self.player_id = player_id
        self.url = REDEEM_URL
        self.headless = headless
        self.browser_path = browser_path
        self.browser_name = browser_name or 'Chrome'
        self.stats = RedeemStats()

        # Initialize logger
        self.bot_logger = BotLogger(log_callback)
        self.bot_logger.setup(player_id)

        # Initialize WebDriver
        self.driver: Optional[WebDriver] = None
        self.wait: Optional[WebDriverWait] = None
        self._initialize_driver()

    def __enter__(self) -> 'KingshotBotHeadless':
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - ensures browser is closed"""
        self.close()

    def _initialize_driver(self) -> None:
        """Initialize the WebDriver with proper configuration"""
        options = webdriver.ChromeOptions()

        # Set browser binary location if provided
        if self.browser_path:
            options.binary_location = self.browser_path
            self.bot_logger.info(f"Using {self.browser_name} browser: {self.browser_path}")

            # Edge-specific configuration
            if self.browser_name == 'Edge':
                self._configure_edge_options(options)

        # Headless mode configuration
        if self.headless:
            for opt in CHROME_HEADLESS_OPTIONS:
                options.add_argument(opt)
            self.bot_logger.info("Headless mode enabled (INVISIBLE browser)")
        else:
            self.bot_logger.info("Visible mode enabled")

        # Standard Chrome options
        for opt in CHROME_OPTIONS:
            options.add_argument(opt)

        # Experimental options
        for key, value in CHROME_EXPERIMENTAL_OPTIONS.items():
            options.add_experimental_option(key, value)

        # Initialize driver
        self.bot_logger.info("Starting ChromeDriver...")
        try:
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, TIMEOUTS.webdriver_wait)
            self.bot_logger.success("ChromeDriver started successfully")

            # Edge-specific initialization
            if self.browser_name == 'Edge':
                self._initialize_edge()

        except WebDriverException as e:
            self.bot_logger.error(f"Failed to start ChromeDriver: {str(e)}")
            raise

    def _configure_edge_options(self, options: webdriver.ChromeOptions) -> None:
        """Configure Edge-specific options"""
        temp_dir = tempfile.gettempdir()
        edge_profile = os.path.join(temp_dir, 'edge-selenium-profile')
        options.add_argument(f'--user-data-dir={edge_profile}')
        options.add_argument('--profile-directory=Default')

        for opt in EDGE_SPECIFIC_OPTIONS:
            options.add_argument(opt)

    def _initialize_edge(self) -> None:
        """Additional Edge initialization steps"""
        try:
            self.driver.get('about:blank')
            time.sleep(TIMEOUTS.edge_init)
            self.driver.execute_script('window.stop();')
            time.sleep(TIMEOUTS.edge_stop)
        except Exception as e:
            self.bot_logger.debug(f"Edge initialization note: {str(e)}")

    def _find_elements_safe(self, by: By, value: str) -> List[WebElement]:
        """Safely find elements with exception handling"""
        try:
            return self.driver.find_elements(by, value)
        except (NoSuchElementException, StaleElementReferenceException):
            return []

    def _find_element_safe(self, by: By, value: str) -> Optional[WebElement]:
        """Safely find a single element with exception handling"""
        try:
            return self.driver.find_element(by, value)
        except (NoSuchElementException, StaleElementReferenceException):
            return None

    def _click_element_safe(self, element: WebElement) -> bool:
        """Safely click an element with retry logic"""
        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                element.click()
                return True
            except ElementClickInterceptedException:
                self.bot_logger.debug(f"Click intercepted, attempt {attempt + 1}/{max_attempts}")
                time.sleep(TIMEOUTS.click_delay)

                # Try JavaScript click as fallback
                if attempt == max_attempts - 1:
                    try:
                        self.driver.execute_script("arguments[0].click();", element)
                        return True
                    except Exception:
                        pass
            except StaleElementReferenceException:
                self.bot_logger.debug("Element became stale")
                return False
            except Exception as e:
                self.bot_logger.debug(f"Click error: {str(e)}")
                return False

        return False

    def _wait_for_vue(self) -> bool:
        """Wait for Vue.js application to load"""
        self.bot_logger.info("Waiting for Vue.js to load...")

        try:
            time.sleep(TIMEOUTS.vue_load)
            self.wait.until(
                lambda d: len(d.find_element(By.CSS_SELECTOR, SELECTORS.vue_app).text) > 0
            )
            time.sleep(TIMEOUTS.vue_extra_wait)
            self.bot_logger.success("Vue.js loaded successfully")
            return True
        except TimeoutException:
            self.bot_logger.error("Vue.js failed to load within timeout")
            return False

    def _find_all_clickables(self) -> List[WebElement]:
        """Find all clickable button elements"""
        clickables = []

        for selector in SELECTORS.clickable_buttons:
            elements = self._find_elements_safe(By.CSS_SELECTOR, selector)
            for elem in elements:
                try:
                    if elem.is_displayed():
                        clickables.append(elem)
                except StaleElementReferenceException:
                    continue

        return clickables

    def _find_button_by_keywords(
        self,
        keywords: List[str],
        css_selector: Optional[str] = None
    ) -> Optional[WebElement]:
        """Find a button by CSS selector or text keywords"""
        # Method 1: Try CSS selector first
        if css_selector:
            button = self._find_element_safe(By.CSS_SELECTOR, css_selector)
            if button and button.is_displayed():
                self.bot_logger.success(f"Button found by selector: '{button.text}'")
                return button

        # Method 2: Search by text content
        clickables = self._find_all_clickables()
        self.bot_logger.info(f"Searching {len(clickables)} clickable elements...")

        for elem in clickables:
            try:
                text = elem.text.strip().lower()
                if text and any(keyword in text for keyword in keywords):
                    class_attr = elem.get_attribute('class') or ''
                    if 'disabled' not in class_attr.lower():
                        self.bot_logger.success(f"Button found by text: '{elem.text}'")
                        return elem
            except StaleElementReferenceException:
                continue

        return None

    def _find_input_field(
        self,
        field_type: str = "player_id",
        maxlength: Optional[str] = None
    ) -> Optional[WebElement]:
        """Find an input field by type and attributes"""
        # Try specific input types first
        inputs = self._find_elements_safe(By.CSS_SELECTOR, SELECTORS.text_inputs)

        if not inputs:
            all_inputs = self._find_elements_safe(By.TAG_NAME, "input")
            inputs = [inp for inp in all_inputs if self._is_element_visible(inp)]

        visible_inputs = [inp for inp in inputs if self._is_element_visible(inp)]
        self.bot_logger.info(f"Found {len(visible_inputs)} visible input fields")

        # Find by maxlength attribute
        if maxlength:
            for inp in visible_inputs:
                if inp.get_attribute('maxlength') == maxlength:
                    self.bot_logger.success(f"Field found by maxlength={maxlength}")
                    return inp

        # Find by placeholder
        for inp in visible_inputs:
            placeholder = (inp.get_attribute('placeholder') or '').lower()
            keywords = LANGUAGE_KEYWORDS.code_placeholder if field_type == "code" else ['player', 'id', 'jugador']

            if any(kw in placeholder for kw in keywords):
                self.bot_logger.success(f"Field found by placeholder: '{placeholder}'")
                return inp

        # Return first visible input as fallback
        if visible_inputs:
            self.bot_logger.warning("Using first visible input field")
            return visible_inputs[0]

        return None

    def _is_element_visible(self, element: WebElement) -> bool:
        """Check if an element is visible"""
        try:
            return element.is_displayed()
        except StaleElementReferenceException:
            return False

    def _clear_browser_state(self) -> None:
        """Clear browser session state (for Edge compatibility)"""
        if self.browser_name == 'Edge':
            try:
                self.driver.delete_all_cookies()
                self.driver.execute_script('window.sessionStorage.clear();')
                self.driver.execute_script('window.localStorage.clear();')
                time.sleep(TIMEOUTS.edge_stop)
            except Exception as e:
                self.bot_logger.debug(f"Could not clear browser state: {str(e)}")

    def dismiss_modal(self) -> bool:
        """Close any modal or overlay blocking the interface"""
        try:
            self.bot_logger.info("Checking for active modal...")
            time.sleep(TIMEOUTS.modal_check)

            # Method 1: Find and click close buttons
            for selector in SELECTORS.close_buttons:
                buttons = self._find_elements_safe(By.CSS_SELECTOR, selector)
                for btn in buttons:
                    if self._is_element_visible(btn):
                        self.bot_logger.info(f"Found close button: {btn.text or 'no text'}")
                        if self._click_element_safe(btn):
                            time.sleep(TIMEOUTS.modal_check)
                            self.bot_logger.success("Modal closed with button")
                            return True

            # Method 2: Click background mask
            mask = self._find_element_safe(By.CSS_SELECTOR, SELECTORS.mask)
            if mask and self._is_element_visible(mask):
                self.bot_logger.info("Clicking background mask...")
                if self._click_element_safe(mask):
                    time.sleep(TIMEOUTS.modal_check)
                    self.bot_logger.success("Modal closed by clicking mask")
                    return True

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
                self.bot_logger.success("Modal force-closed with JavaScript")
                time.sleep(TIMEOUTS.modal_check)
                return True
            except Exception:
                pass

            self.bot_logger.info("No active modal found")
            return False

        except Exception as e:
            self.bot_logger.warning(f"Error closing modal: {str(e)}")
            return False

    def login(self) -> bool:
        """Login with Player ID"""
        self.bot_logger.info(f"Opening {self.url}")

        # Clear browser state for Edge
        self._clear_browser_state()

        # Navigate to URL
        self.driver.get(self.url)

        # Verify navigation
        time.sleep(TIMEOUTS.navigation_retry)
        current_url = self.driver.current_url
        self.bot_logger.info(f"Current URL: {current_url}")

        # Retry navigation if failed
        if 'data:' in current_url or current_url == 'about:blank':
            self.bot_logger.warning("Navigation failed, retrying...")
            time.sleep(TIMEOUTS.navigation_retry)
            self.driver.get(self.url)
            time.sleep(TIMEOUTS.navigation_retry)
            current_url = self.driver.current_url
            self.bot_logger.info(f"URL after retry: {current_url}")

        try:
            # Wait for Vue.js
            if not self._wait_for_vue():
                return False

            # Find Player ID field
            self.bot_logger.info("Looking for Player ID field...")
            player_id_field = self._find_input_field("player_id")

            if not player_id_field:
                self.bot_logger.error("Player ID field not found")
                return False

            placeholder = player_id_field.get_attribute('placeholder') or ''
            self.bot_logger.success(f"Field found: '{placeholder}'")

            # Enter Player ID
            self.bot_logger.info(f"Entering Player ID: {self.player_id}")
            player_id_field.click()
            time.sleep(TIMEOUTS.click_delay)
            player_id_field.clear()
            player_id_field.send_keys(self.player_id)
            time.sleep(TIMEOUTS.click_delay)
            self.bot_logger.success("Player ID entered successfully")

            # Find login button
            self.bot_logger.info("Looking for login button...")
            login_button = self._find_button_by_keywords(
                LANGUAGE_KEYWORDS.login,
                SELECTORS.login_button
            )

            if not login_button:
                self.bot_logger.error("Login button not found")
                return False

            # Click login
            self.bot_logger.info("Clicking login button...")
            if not self._click_element_safe(login_button):
                self.bot_logger.error("Failed to click login button")
                return False

            self.bot_logger.success("Click performed")

            # Wait for response
            self.bot_logger.info(f"Waiting for server response ({TIMEOUTS.login_response}s)...")
            time.sleep(TIMEOUTS.login_response)

            self.bot_logger.success("Login completed successfully")
            return True

        except Exception as e:
            self.bot_logger.error(f"Login error: {str(e)}")
            self.bot_logger.debug(traceback.format_exc())
            return False

    def redeem_code(
        self,
        code: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> RedeemResult:
        """
        Redeem a gift code.

        Args:
            code: The gift code to redeem
            progress_callback: Optional callback(step, total_steps, description)

        Returns:
            RedeemResult enum value
        """
        self.bot_logger.section(f"REDEEMING CODE: {code}")

        total_steps = 7
        current_step = 0

        def report_progress(description: str) -> None:
            nonlocal current_step
            current_step += 1
            if progress_callback:
                progress_callback(current_step, total_steps, description)

        try:
            # Step 1: Wait for page update
            report_progress("Waiting for page update")
            self.bot_logger.info("Waiting for page update...")
            time.sleep(TIMEOUTS.page_update)

            # Step 2: Find gift code field
            report_progress("Finding gift code field")
            self.bot_logger.info("Looking for Gift Code field...")

            gift_code_field = self._find_input_field("code", maxlength="20")

            if not gift_code_field:
                self.bot_logger.error("Gift Code field not found")
                return RedeemResult.FAILED

            # Step 3: Enter code
            report_progress(f"Entering code: {code}")
            self.bot_logger.info(f"Entering code: {code}")

            # Scroll into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", gift_code_field)
            time.sleep(TIMEOUTS.click_delay)

            gift_code_field.click()
            time.sleep(TIMEOUTS.click_delay)
            gift_code_field.clear()
            time.sleep(TIMEOUTS.input_delay)
            gift_code_field.send_keys(code)
            time.sleep(TIMEOUTS.modal_check)
            self.bot_logger.success("Code entered successfully")

            # Step 4: Find confirm button
            report_progress("Finding confirm button")
            self.bot_logger.info("Looking for confirm button...")

            confirm_button = self._find_button_by_keywords(
                LANGUAGE_KEYWORDS.confirm,
                SELECTORS.exchange_button
            )

            if not confirm_button:
                self.bot_logger.error("Confirm button not found")
                return RedeemResult.FAILED

            # Step 5: Click confirm
            report_progress("Clicking confirm button")
            self.bot_logger.info("Clicking confirm button...")

            if not self._click_element_safe(confirm_button):
                self.bot_logger.error("Failed to click confirm button")
                return RedeemResult.FAILED

            self.bot_logger.success("Click performed")

            # Step 6: Wait for response
            report_progress("Waiting for server response")
            self.bot_logger.info(f"Waiting for server response ({TIMEOUTS.redeem_response}s)...")
            time.sleep(TIMEOUTS.redeem_response)

            # Step 7: Analyze result
            report_progress("Analyzing result")
            result = self._analyze_result(code)

            # Close modal for next code
            self.dismiss_modal()

            return result

        except Exception as e:
            self.bot_logger.error(f"Redemption error: {str(e)}")
            self.bot_logger.debug(traceback.format_exc())
            return RedeemResult.FAILED

    def _analyze_result(self, code: str) -> RedeemResult:
        """Analyze the page to determine redemption result"""
        page_text = self.driver.page_source.lower()

        # Log preview for debugging
        self.bot_logger.debug(f"Page content preview: {page_text[:500]}")

        # Check for "already claimed" first (most specific)
        if any(word in page_text for word in LANGUAGE_KEYWORDS.already_claimed):
            self.bot_logger.warning(f"Code {code} was already claimed previously")
            return RedeemResult.ALREADY_CLAIMED

        # Check for success
        if any(word in page_text for word in LANGUAGE_KEYWORDS.success):
            self.bot_logger.success(f"Code {code} redeemed successfully!")
            return RedeemResult.SUCCESS

        # Check for errors
        if any(word in page_text for word in LANGUAGE_KEYWORDS.error):
            self.bot_logger.error(f"Error redeeming code {code}")
            return RedeemResult.FAILED

        # Unknown result
        self.bot_logger.warning(f"Could not determine result for code {code} - marking as failed")
        return RedeemResult.FAILED

    def close(self) -> None:
        """Close the browser and clean up resources"""
        self.bot_logger.info("Closing browser...")
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            self.bot_logger.success("Browser closed successfully")
        except Exception as e:
            self.bot_logger.debug(f"Error closing browser: {str(e)}")

    # Legacy logging methods for backwards compatibility
    def log_info(self, msg: str) -> None:
        self.bot_logger.info(msg)

    def log_success(self, msg: str) -> None:
        self.bot_logger.success(msg)

    def log_error(self, msg: str) -> None:
        self.bot_logger.error(msg)

    def log_warning(self, msg: str) -> None:
        self.bot_logger.warning(msg)

    def log_debug(self, msg: str) -> None:
        self.bot_logger.debug(msg)
