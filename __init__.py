# -*- coding: utf-8 -*-
"""
Kingshot Gift Code Bot Package
Automated bot for redeeming gift codes in Kingshot game
"""

__version__ = "2.0.0"
__author__ = "Kingshot Bot GiftCodeCenter"

from .utils import check_and_install_dependencies, install_packages, fetch_active_gift_codes
from .bot_core import KingshotBotHeadless
from .gui import KingshotBotGUI

__all__ = [
    'check_and_install_dependencies',
    'install_packages',
    'fetch_active_gift_codes',
    'KingshotBotHeadless',
    'KingshotBotGUI',
]
