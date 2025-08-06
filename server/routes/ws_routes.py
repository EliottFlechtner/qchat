from fastapi import APIRouter, Depends, WebSocket
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from server.utils.logger import logger
from server.db.database import get_db
from server.db.database_models import User, Message
from server.routes.http_routes import connected_clients

# Router is prefixed with "/ws" to indicate WebSocket routes
# on the main app, NO NEED to prefix here

# Router dedicated to WebSocket-related routes
ws_router = APIRouter()


# WebSocket endpoint watching & notifying for client connections
@ws_router.websocket("/{username}")  # No need for prefix, handled by main app
async def websocket_endpoint(
    websocket: WebSocket, username: str, db: Session = Depends(get_db)
) -> None:
    # Accept the WebSocket connection
    logger.debug(f"[WebSocket] {username} is trying to connect.")
    await websocket.accept()
    logger.debug(f"[WebSocket] {username} accepted connection.")

    # Resolve username's ID from the database
    user = db.query(User).filter_by(username=username).first()
    if not user:
        # Close connection with error code 1008 (policy violation)
        logger.error(f"[WebSocket] User '{username}' not found.")
        await websocket.close(code=1008)
        return

    # Store the WebSocket connection in the connected clients dictionary
    if user.id not in connected_clients:
        connected_clients[user.id] = websocket
    logger.debug(f"[WebSocket] {username} (id: {user.id}) connected.")

    try:
        while True:
            await websocket.receive_text()  # Just keep alive; client doesn't need to send.
    except Exception as e:
        logger.debug(f"[WEBSOCKET] {username} disconnected: {e}")
    finally:
        connected_clients.pop(user.id, None)


# @ws_router.websocket("/{username}")  # no need for prefix, handled by main app
# async def message_websocket(
#     websocket: WebSocket, username: str, db: Session = Depends(get_db)
# ):
#     await websocket.accept()

#     # # Resolve username's ID from the database
#     # user = db.query(User).filter_by(username=username).first()
#     # if not user:
#     #     # Close connection with error code 1008 (policy violation)
#     #     logger.error(f"[WebSocket] User '{username}' not found.")
#     #     await websocket.close(code=1008)
#     #     return

#     # # Store the WebSocket connection in the connected clients dictionary
#     # if user.id not in connected_clients:
#     #     connected_clients[user.id] = websocket
#     # logger.debug(f"[WebSocket] {username} (id: {user.id}) connected.")

#     # try:
#     #     now_utc = datetime.now(timezone.utc)

#     #     # Retrieve undelivered messages for the user
#     #     pending_messages = (
#     #         db.query(Message)
#     #         .filter(
#     #             Message.recipient_id == user.id,
#     #             Message.delivered == False,
#     #             # TODO filter expired messages here
#     #             # (Message.expires_at.is_(None) | (Message.expires_at > now_utc))
#     #         )
#     #         .all()
#     #     )

#     #     # Notify the client about new messages (one text for whole batch)
#     #     if pending_messages:
#     #         logger.debug(
#     #             f"[WebSocket] Sending {len(pending_messages)} undelivered messages to {username}"
#     #         )
#     #         await websocket.send_text(f"new_messages:{len(pending_messages)}")
#     #     else:
#     #         logger.debug(f"[WebSocket] No undelivered messages for {username}")

#     #     # Send each undelivered message over WebSocket
#     #     for msg in pending_messages:
#     #         # Mark as delivered in DB
#     #         msg.delivered = True
#     #         # TODO fix timestamp
#     #         # msg.delivered_at = datetime.now(timezone.utc)

#     #     db.commit()

#         # Keep connection alive
#         while True:
#             await websocket.receive_text()

#     except Exception as e:
#         logger.debug(f"[WebSocket] {username} disconnected: {e}")
#     finally:
#         connected_clients.pop(user.id, None)
