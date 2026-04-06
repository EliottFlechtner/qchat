import uuid
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from server.utils.logger import logger
from server.db.database import get_db
from server.services import UserService, websocket_service

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

        # Initialize user service
        user_service = UserService(db)

        # Resolve username to user ID from database
        try:
            user = user_service.get_user_by_username(username)
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
        existing_connection = websocket_service.get_client(user_id)
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

        # Store the new WebSocket connection in the service
        websocket_service.add_client(user_id, websocket)
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
        if user_id and websocket_service.is_user_connected(user_id):
            websocket_service.remove_client(user_id)
            logger.info(
                f"[WebSocket] Cleaned up connection for '{username}' (ID: {user_id})"
            )

        logger.debug(f"[WebSocket] Connection handler finished for '{username}'")


# The WebSocket utility functions are now handled by the WebSocketService
# in server.services.websocket_service for better separation of concerns.
