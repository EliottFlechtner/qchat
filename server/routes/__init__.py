"""
Routes module for server HTTP and WebSocket endpoints.

This module provides route handlers for all API endpoints.
"""

from .http_routes import http_router as http_router
from .ws_routes import ws_router

__all__ = [
    "http_router",
    "ws_router",
]
