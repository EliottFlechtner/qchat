import base64
from client.config.settings import client_settings


def get_api_url() -> str:
    """Get the API URL from configuration."""
    return client_settings.server_url


def get_ws_url() -> str:
    """Get the WebSocket URL from configuration."""
    return client_settings.ws_url


def b64e(data: bytes) -> str:
    return base64.b64encode(data).decode()


def b64d(data: str) -> bytes:
    return base64.b64decode(data.encode())
