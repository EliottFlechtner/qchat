"""
Services module for client business logic.

This module provides high-level service functions for user operations.
"""

from .inbox import fetch_and_decrypt_inbox
from .login import (
    load_all_local_keys,
    save_all_local_keys,
    save_local_keys,
    get_local_keypair,
    login_or_register,
)
from .send import send_encrypted_message

__all__ = [
    # Inbox services
    "fetch_and_decrypt_inbox",
    # Login/auth services
    "load_all_local_keys",
    "save_all_local_keys",
    "save_local_keys",
    "get_local_keypair",
    "login_or_register",
    # Message sending services
    "send_encrypted_message",
]
