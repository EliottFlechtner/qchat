import uuid
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

from server.utils.logger import logger
from server.db.database import get_db
from server.db.database_models import User, Message
from server.routes.http_routes import connected_clients

# Router is prefixed with "/ws" to indicate WebSocket routes
# on the main app, NO NEED to prefix here

# Router dedicated to WebSocket-related routes
ws_router = APIRouter()


@ws_router.websocket("/{username}")
async def websocket_endpoint(
    websocket: WebSocket, username: str, db: Session = Depends(get_db)
) -> None:
    """WebSocket endpoint for real-time message notifications.

    Establishes a persistent WebSocket connection for a user to receive instant
    notifications when new messages arrive. The connection performs user validation,
    maintains a keep-alive loop, and handles graceful disconnection.

    Connection workflow:
    1. Accept WebSocket connection from client
    2. Validate username exists in database
    3. Store connection in global registry for message notifications
    4. Maintain keep-alive loop until client disconnects
    5. Clean up connection on disconnect

    Endpoint: WS /ws/{username}
    Protocol: WebSocket with text message keep-alive
    Notifications: Server sends "new_message" when messages arrive

    :param websocket: WebSocket connection instance from client.
    :param username: Username to establish connection for.
    :param db: Database session dependency injection.
    """
    user_id = None

    try:
        # Validate username parameter
        if not username or not username.strip():
            logger.warning("[WebSocket] Connection attempt with empty username")
            await websocket.close(code=1008, reason="Username cannot be empty")
            return

        username = username.strip()

        # Accept the WebSocket connection
        logger.debug(f"[WebSocket] User '{username}' attempting to connect")
        await websocket.accept()
        logger.info(f"[WebSocket] Connection accepted for '{username}'")

        # Resolve username to user ID from database
        try:
            user = db.query(User).filter_by(username=username).first()
            if not user:
                logger.warning(
                    f"[WebSocket] Connection rejected: user '{username}' not found"
                )
                await websocket.close(code=1008, reason="User not found")
                return

            user_id = user.id
            logger.debug(f"[WebSocket] User '{username}' resolved to ID: {user_id}")

        except SQLAlchemyError as e:
            logger.error(f"[WebSocket] Database error resolving user '{username}': {e}")
            await websocket.close(code=1011, reason="Database error")
            return
        except Exception as e:
            logger.error(
                f"[WebSocket] Unexpected error resolving user '{username}': {e}"
            )
            await websocket.close(code=1011, reason="Internal server error")
            return

        # Check for existing connection and handle reconnection
        existing_connection = connected_clients.get(user_id)
        if existing_connection:
            try:
                # Close existing connection gracefully
                logger.info(f"[WebSocket] Closing existing connection for '{username}'")
                await existing_connection.close(
                    code=1000, reason="New connection established"
                )
            except Exception as e:
                logger.debug(
                    f"[WebSocket] Error closing existing connection for '{username}': {e}"
                )

        # Store the new WebSocket connection in the global registry
        connected_clients[user_id] = websocket
        logger.info(
            f"[WebSocket] User '{username}' (ID: {user_id}) connected successfully"
        )

        # Enter keep-alive loop to maintain connection
        logger.debug(f"[WebSocket] Starting keep-alive loop for '{username}'")
        try:
            while True:
                # Receive keep-alive messages from client
                # Client doesn't need to send meaningful data, just maintain connection
                message = await websocket.receive_text()
                logger.debug(
                    f"[WebSocket] Keep-alive received from '{username}': {message}"
                )

        except WebSocketDisconnect as e:
            # Normal client disconnection
            logger.info(
                f"[WebSocket] User '{username}' disconnected normally (code: {e.code})"
            )
        except Exception as e:
            # Unexpected disconnection or error
            logger.warning(
                f"[WebSocket] User '{username}' disconnected unexpectedly: {e}"
            )

    except Exception as e:
        # Handle any unexpected errors during connection setup
        logger.error(
            f"[WebSocket] Critical error in connection setup for '{username}': {e}"
        )
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass  # Connection might already be closed

    finally:
        # Clean up connection registry on disconnect
        if user_id and user_id in connected_clients:
            removed_connection = connected_clients.pop(user_id, None)
            if removed_connection:
                logger.info(
                    f"[WebSocket] Cleaned up connection for '{username}' (ID: {user_id})"
                )
            else:
                logger.debug(
                    f"[WebSocket] No connection found to clean up for '{username}'"
                )

        logger.debug(f"[WebSocket] Connection handler finished for '{username}'")


# async def notify_user(user_id: uuid.UUID, message: str) -> bool:
#     """Sends a notification message to a connected user via WebSocket.

#     Utility function to send real-time notifications to users. Used primarily
#     for notifying users about new message arrivals. Handles connection errors
#     gracefully and removes stale connections.

#     :param user_id: Database ID of the user to notify.
#     :param message: Notification message to send (typically "new_message").
#     :return: True if notification sent successfully, False otherwise.
#     """
#     websocket = connected_clients.get(user_id)
#     if not websocket:
#         logger.debug(f"[WebSocket] No active connection for user ID {user_id}")
#         return False

#     try:
#         await websocket.send_text(message)
#         logger.debug(f"[WebSocket] Notification sent to user ID {user_id}: {message}")
#         return True

#     except Exception as e:
#         # Connection is stale or broken, remove it from registry
#         logger.warning(
#             f"[WebSocket] Failed to notify user ID {user_id}, removing connection: {e}"
#         )
#         connected_clients.pop(user_id, None)
#         return False


# def get_connected_users_count() -> int:
#     """Returns the number of currently connected WebSocket clients.

#     Utility function for monitoring and debugging purposes.

#     :return: Number of active WebSocket connections.
#     """
#     return len(connected_clients)


# def is_user_connected(user_id: int) -> bool:
#     """Checks if a specific user has an active WebSocket connection.

#     :param user_id: Database ID of the user to check.
#     :return: True if user is connected, False otherwise.
#     """
#     return user_id in connected_clients


# async def disconnect_user(
#     user_id: uuid.UUID, code: int = 1000, reason: str = "Server disconnect"
# ) -> bool:
#     """Forcefully disconnects a user's WebSocket connection.

#     Administrative function for server-side connection management.

#     :param user_id: Database ID of the user to disconnect.
#     :param code: WebSocket close code (default: 1000 for normal closure).
#     :param reason: Human-readable reason for disconnection.
#     :return: True if user was connected and disconnected, False if not connected.
#     """
#     websocket = connected_clients.get(user_id)
#     if not websocket:
#         logger.debug(f"[WebSocket] User ID {user_id} not connected, cannot disconnect")
#         return False

#     try:
#         await websocket.close(code=code, reason=reason)
#         connected_clients.pop(user_id, None)
#         logger.info(f"[WebSocket] Forcefully disconnected user ID {user_id}: {reason}")
#         return True

#     except Exception as e:
#         logger.warning(f"[WebSocket] Error disconnecting user ID {user_id}: {e}")
#         # Remove from registry even if close failed
#         connected_clients.pop(user_id, None)
#         return True
