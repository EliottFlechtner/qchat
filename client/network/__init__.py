"""
Network module for client communication.

This module provides WebSocket communication functionality.
"""

from .websocket import start_ws_listener, start_websocket_thread

__all__ = [
    "start_ws_listener",
    "start_websocket_thread",
]
