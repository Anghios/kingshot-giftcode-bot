# -*- coding: utf-8 -*-
"""
Configuration file for Kingshot Gift Code Bot
Centralizes all constants, timeouts, and settings
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple
import os

# =============================================================================
# VERSION INFO
# =============================================================================
VERSION = "3.0.0"
APP_NAME = "Kingshot Gift Code Bot"
AUTHOR = "Kingshot Bot GiftCodeCenter"
GITHUB_URL = "https://github.com/Anghios/kingshot-giftcode-bot"

# =============================================================================
# URLs
# =============================================================================
REDEEM_URL = "https://ks-giftcode.centurygame.com/"
CODES_SOURCE_URL = "https://kingshot.net/gift-codes"

# =============================================================================
# TIMEOUTS (in seconds)
# =============================================================================
@dataclass
class Timeouts:
    """Timeout configuration for various operations"""
    vue_load: float = 3.0
    vue_extra_wait: float = 1.0
    login_response: float = 7.0
    redeem_response: float = 5.0
    between_codes: float = 3.0
    page_update: float = 3.0
    modal_check: float = 1.0
    click_delay: float = 0.5
    input_delay: float = 0.3
    webdriver_wait: int = 20
    http_request: int = 10
    edge_init: float = 1.0
    edge_stop: float = 0.5
    navigation_retry: float = 1.0

TIMEOUTS = Timeouts()

# =============================================================================
# RETRY CONFIGURATION
# =============================================================================
@dataclass
class RetryConfig:
    """Retry configuration for network operations"""
    max_attempts: int = 3
    delay_between: float = 2.0
    backoff_multiplier: float = 1.5

RETRY_CONFIG = RetryConfig()

# =============================================================================
# BROWSER CONFIGURATION
# =============================================================================
@dataclass
class BrowserPaths:
    """Default browser paths per platform"""

    @staticmethod
    def get_windows_paths() -> Dict[str, List[str]]:
        """Get Windows browser paths"""
        program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
        program_files_x86 = os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
        local_app_data = os.environ.get('LOCALAPPDATA', '')

        return {
            'Chrome': [
                os.path.join(program_files, 'Google\\Chrome\\Application\\chrome.exe'),
                os.path.join(program_files_x86, 'Google\\Chrome\\Application\\chrome.exe'),
                os.path.join(local_app_data, 'Google\\Chrome\\Application\\chrome.exe'),
            ],
            'Brave': [
                os.path.join(program_files, 'BraveSoftware\\Brave-Browser\\Application\\brave.exe'),
                os.path.join(program_files_x86, 'BraveSoftware\\Brave-Browser\\Application\\brave.exe'),
                os.path.join(local_app_data, 'BraveSoftware\\Brave-Browser\\Application\\brave.exe'),
            ],
            'Edge': [
                os.path.join(program_files, 'Microsoft\\Edge\\Application\\msedge.exe'),
                os.path.join(program_files_x86, 'Microsoft\\Edge\\Application\\msedge.exe'),
            ],
        }

    @staticmethod
    def get_linux_paths() -> Dict[str, List[str]]:
        """Get Linux browser paths"""
        return {
            'Chrome': ['/usr/bin/google-chrome', '/usr/bin/google-chrome-stable'],
            'Brave': ['/usr/bin/brave-browser', '/usr/bin/brave'],
            'Chromium': ['/usr/bin/chromium-browser', '/usr/bin/chromium'],
            'Edge': ['/usr/bin/microsoft-edge'],
        }

    @staticmethod
    def get_macos_paths() -> Dict[str, List[str]]:
        """Get macOS browser paths"""
        return {
            'Chrome': ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'],
            'Brave': ['/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'],
            'Edge': ['/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'],
        }

BROWSER_PATHS = BrowserPaths()
BROWSER_PRIORITY = ['Chrome', 'Brave', 'Edge', 'Chromium']

# =============================================================================
# SELENIUM OPTIONS
# =============================================================================
CHROME_OPTIONS = [
    '--disable-blink-features=AutomationControlled',
    '--window-size=1920,1080',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-extensions',
    '--disable-infobars',
]

CHROME_HEADLESS_OPTIONS = [
    '--headless=new',
    '--headless',  # Legacy compatibility
    '--disable-gpu',
    '--window-position=-2400,-2400',
]

EDGE_SPECIFIC_OPTIONS = [
    '--disable-features=msEdgeEnableNurturingFramework',
    '--disable-features=msSmartScreenProtection',
    '--inprivate',
]

CHROME_EXPERIMENTAL_OPTIONS = {
    'excludeSwitches': ['enable-automation', 'enable-logging'],
    'useAutomationExtension': False,
}

# =============================================================================
# CSS SELECTORS
# =============================================================================
@dataclass
class Selectors:
    """CSS selectors for web elements"""
    # Input fields
    text_inputs: str = "input[type='text']"
    all_inputs: str = "input"

    # Buttons
    login_button: str = ".login_btn"
    exchange_button: str = ".exchange_btn"
    clickable_buttons: List[str] = field(default_factory=lambda: [
        "div[class*='btn']",
        "div[class*='button']",
        "button"
    ])

    # Modals
    close_buttons: List[str] = field(default_factory=lambda: [
        "div[class*='close']",
        "button[class*='close']",
        "div[class*='btn-close']",
        "div[class*='modal'] button",
        "div[class*='dialog'] button"
    ])
    mask: str = "div.mask"

    # Vue.js
    vue_app: str = "#app"

SELECTORS = Selectors()

# =============================================================================
# MULTI-LANGUAGE KEYWORDS
# =============================================================================
@dataclass
class LanguageKeywords:
    """Keywords for multi-language support"""

    login: List[str] = field(default_factory=lambda: [
        'login', 'iniciar', 'sesion', 'entrar', 'connexion',
        'anmelden', 'accedi', '登录', 'ログイン', 'entrar'
    ])

    confirm: List[str] = field(default_factory=lambda: [
        'confirm', 'confirmar', 'confirmer', 'bestätigen',
        'conferma', 'exchange', 'canjear', 'échanger',
        '确认', '交换', '確認', '交換', 'trocar'
    ])

    already_claimed: List[str] = field(default_factory=lambda: [
        'already', 'claimed', 'received', 'redeemed', 'used',
        'ya recogido', 'ya canjeado', 'ya reclamado', 'ya usado', 'ya obtenido',
        'déjà récupéré', 'déjà utilisé', 'déjà réclamé', 'déjà reçu',
        'bereits', 'schon', 'erhalten', 'eingelöst',
        'già riscattato', 'già utilizzato', 'già rivendicato', 'già ottenuto',
        '已领取', '已使用', '已兑换', '已获得',
        '既に', 'すでに', '受け取り済み', '使用済み',
        'já resgatado', 'já usado', 'já recebido', 'já obtido'
    ])

    success: List[str] = field(default_factory=lambda: [
        'success', 'successful', 'exitoso', 'éxito', 'succès', 'erfolg',
        'successo', 'mail', 'correo', 'e-mail', 'email', 'inbox',
        '成功', '成功了', 'メール', '正常', 'sucesso', 'enviado'
    ])

    error: List[str] = field(default_factory=lambda: [
        'error', 'fail', 'failed', 'invalid', 'expired', 'not found',
        'no existe', 'inválido', 'expirado', 'erreur', 'invalide', 'expiré',
        'fehler', 'ungültig', 'abgelaufen', 'errore', 'non valido', 'scaduto',
        '错误', '失败', '無効', '期限切れ', 'erro', 'inválido', 'expirado'
    ])

    code_placeholder: List[str] = field(default_factory=lambda: [
        'codigo', 'code', 'código', 'gift', 'regalo'
    ])

LANGUAGE_KEYWORDS = LanguageKeywords()

# =============================================================================
# SCRAPING CONFIGURATION
# =============================================================================
SCRAPING_PATTERN = r'Active([A-Za-z0-9]{5,20})(?:Copy|Expires)'
MAX_CODES_TO_FETCH = 20
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# =============================================================================
# GUI CONFIGURATION
# =============================================================================
@dataclass
class GUIConfig:
    """GUI appearance and behavior configuration"""
    # Window
    window_title: str = f"{APP_NAME} v{VERSION}"
    window_size: str = "1100x750"
    min_width: int = 1000
    min_height: int = 650

    # Colors (Modern Dark Theme)
    bg_primary: str = "#1a1a2e"
    bg_secondary: str = "#16213e"
    bg_tertiary: str = "#0f3460"
    bg_card: str = "#1f2940"

    accent_primary: str = "#e94560"
    accent_secondary: str = "#0ea5e9"
    accent_success: str = "#10b981"
    accent_warning: str = "#f59e0b"
    accent_error: str = "#ef4444"

    text_primary: str = "#ffffff"
    text_secondary: str = "#94a3b8"
    text_muted: str = "#64748b"

    # Fonts
    font_family: str = "Segoe UI"
    font_family_mono: str = "Cascadia Code"
    font_size_title: int = 20
    font_size_heading: int = 14
    font_size_normal: int = 11
    font_size_small: int = 10

    # Spacing
    padding_large: int = 20
    padding_medium: int = 15
    padding_small: int = 10
    padding_tiny: int = 5

    # Components
    button_width: int = 15
    entry_width: int = 35
    log_height: int = 18
    log_width: int = 90

    # Animation
    progress_update_ms: int = 50
    log_queue_check_ms: int = 100

GUI_CONFIG = GUIConfig()

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
@dataclass
class LogConfig:
    """Logging configuration"""
    format: str = '%(asctime)s [%(levelname)s] %(message)s'
    date_format: str = '%Y-%m-%d %H:%M:%S'
    file_prefix: str = 'bot_log_'
    file_extension: str = '.txt'
    encoding: str = 'utf-8'
    level: str = 'INFO'

LOG_CONFIG = LogConfig()

# =============================================================================
# FILE PATHS
# =============================================================================
PLAYER_ID_FILE = 'login_id.txt'
