#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI Module - Contains all UI components for the password manager
"""

from .base_page import BasePage
from .login_page import LoginPage
from .register_page import RegisterPage
from .unlock_page import UnlockPage
from .vault_page import VaultPage

__all__ = [
    'BasePage',
    'LoginPage',
    'RegisterPage',
    'UnlockPage',
    'VaultPage'
] 