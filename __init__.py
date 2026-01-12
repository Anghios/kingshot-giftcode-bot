# -*- coding: utf-8 -*-
"""
Kingshot Gift Code Bot Package
Automated bot for redeeming gift codes in Kingshot game

This package provides:
- Automated web scraping for active gift codes
- Selenium-based browser automation for code redemption
- Modern GUI interface with dark theme
- CLI mode for headless operation
- Multi-browser support (Chrome, Brave, Edge)
- Multi-language detection for result parsing
"""

from .config import VERSION, APP_NAME, AUTHOR

__version__ = VERSION
__author__ = AUTHOR
__app_name__ = APP_NAME

# Core utilities
from .utils import (
    check_and_install_dependencies,
    install_packages,
    fetch_active_gift_codes,
    detect_available_browsers,
    get_preferred_browser,
    BrowserDetector,
    BrowserInfo,
    CodeFetcher,
    DependencyManager,
)

# Bot core
from .bot_core import (
    KingshotBotHeadless,
    RedeemResult,
    RedeemStats,
    BotLogger,
)

# GUI components
from .gui import (
    KingshotBotGUI,
    ModernStyle,
    AnimatedProgressBar,
    StatsPanel,
    LogPanel,
)

# Configuration
from .config import (
    TIMEOUTS,
    RETRY_CONFIG,
    GUI_CONFIG,
    SELECTORS,
    LANGUAGE_KEYWORDS,
    REDEEM_URL,
    CODES_SOURCE_URL,
)

__all__ = [
    # Version info
    '__version__',
    '__author__',
    '__app_name__',

    # Utilities
    'check_and_install_dependencies',
    'install_packages',
    'fetch_active_gift_codes',
    'detect_available_browsers',
    'get_preferred_browser',
    'BrowserDetector',
    'BrowserInfo',
    'CodeFetcher',
    'DependencyManager',

    # Bot core
    'KingshotBotHeadless',
    'RedeemResult',
    'RedeemStats',
    'BotLogger',

    # GUI
    'KingshotBotGUI',
    'ModernStyle',
    'AnimatedProgressBar',
    'StatsPanel',
    'LogPanel',

    # Configuration
    'TIMEOUTS',
    'RETRY_CONFIG',
    'GUI_CONFIG',
    'SELECTORS',
    'LANGUAGE_KEYWORDS',
    'REDEEM_URL',
    'CODES_SOURCE_URL',
]
