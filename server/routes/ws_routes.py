from fastapi import APIRouter, Depends, WebSocket
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from server.utils.logger import logger
from server.db.database import get_db
from server.db.database_models import Message
from server.routes.http_routes import connected_clients

# Router is prefixed with "/ws" to indicate WebSocket routes
# on the main app, NO NEED to prefix here

# Router dedicated to WebSocket-related routes
ws_router = APIRouter()


@ws_router.websocket("/{username}")
async def message_websocket(
    websocket: WebSocket, username: str, db: Session = Depends(get_db)
):
    await websocket.accept()
    connected_clients[username] = websocket
    logger.debug(f"[WebSocket] {username} connected.")

    try:
        now_utc = datetime.now(timezone.utc)

        # Retrieve undelivered messages for the user
        pending_messages = (
            db.query(Message)
            .filter(
                Message.recipient == username,
                Message.delivered == False,
                # TODO filter expired messages here
                # (Message.expires_at.is_(None) | (Message.expires_at > now_utc))
            )
            .all()
        )

        # Notify the client about new messages (one text for whole batch)
        if pending_messages:
            logger.debug(
                f"[WebSocket] Sending {len(pending_messages)} undelivered messages to {username}"
            )
            await websocket.send_text(f"new_messages:{len(pending_messages)}")
        else:
            logger.debug(f"[WebSocket] No undelivered messages for {username}")

        # Send each undelivered message over WebSocket
        for msg in pending_messages:
            # Mark as delivered in DB
            msg.delivered = True
            # TODO fix timestamp
            # msg.delivered_timestamp = now_utc.isoformat()

        db.commit()

        # Keep connection alive
        while True:
            await websocket.receive_text()

    except Exception as e:
        logger.debug(f"[WebSocket] {username} disconnected: {e}")
    finally:
        connected_clients.pop(username, None)
