"""
Client module for quantum-secure messaging application.

This module provides client-side functionality for secure messaging.
"""

from .api import register_user, get_public_key, send_message, get_inbox

__all__ = [
    "register_user",
    "get_public_key",
    "send_message",
    "get_inbox",
]
