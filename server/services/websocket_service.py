"""WebSocket service handling real-time notifications."""

import uuid
from typing import Dict, Optional
from fastapi import WebSocket

from server.utils.logger import logger


class WebSocketService:
    """Service for managing WebSocket connections and notifications."""

    def __init__(self):
        """Initialize WebSocket service with empty client registry."""
        self.connected_clients: Dict[uuid.UUID, WebSocket] = {}

    def add_client(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        """Register a new WebSocket connection for a user.

        :param user_id: UUID of the connected user
        :param websocket: WebSocket connection object
        """
        self.connected_clients[user_id] = websocket
        logger.info(f"[WEBSOCKET_SERVICE] Client connected: {user_id}")

    def remove_client(self, user_id: uuid.UUID) -> None:
        """Remove a WebSocket connection for a user.

        :param user_id: UUID of the user to disconnect
        """
        if user_id in self.connected_clients:
            del self.connected_clients[user_id]
            logger.info(f"[WEBSOCKET_SERVICE] Client disconnected: {user_id}")

    def get_client(self, user_id: uuid.UUID) -> Optional[WebSocket]:
        """Get WebSocket connection for a user.

        :param user_id: UUID of the user
        :return: WebSocket connection if user is connected, None otherwise
        """
        return self.connected_clients.get(user_id)

    async def notify_user(self, user_id: uuid.UUID, message: str) -> bool:
        """Send a notification to a connected user.

        :param user_id: UUID of the user to notify
        :param message: Notification message to send
        :return: True if notification sent successfully, False otherwise
        """
        websocket = self.get_client(user_id)
        if not websocket:
            logger.debug(
                f"[WEBSOCKET_SERVICE] No active connection for user: {user_id}"
            )
            return False

        try:
            await websocket.send_text(message)
            logger.debug(f"[WEBSOCKET_SERVICE] Notification sent to user: {user_id}")
            return True
        except Exception as e:
            logger.warning(f"[WEBSOCKET_SERVICE] Failed to notify user {user_id}: {e}")
            # Remove stale connection
            self.remove_client(user_id)
            return False

    def get_connected_count(self) -> int:
        """Get the number of currently connected clients.

        :return: Number of active WebSocket connections
        """
        return len(self.connected_clients)

    def is_user_connected(self, user_id: uuid.UUID) -> bool:
        """Check if a user is currently connected via WebSocket.

        :param user_id: UUID of the user to check
        :return: True if user is connected, False otherwise
        """
        return user_id in self.connected_clients


# Global WebSocket service instance
websocket_service = WebSocketService()
