import uuid
from fastapi import APIRouter, HTTPException, Depends, WebSocket
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import cast

from server.utils.logger import logger
from server.db.database import get_db
from server.db.database_models import User, Message
from shared.requests_models import (
    RegisterRequest,
    SendRequest,
)
from shared.response_models import (
    RegisterResponse,
    GetPublicKeysResponse,
    SendResponse,
    MessageResponse,
)

# Create a router for the API endpoints (coupled with the main app in ./main.py)
router = APIRouter()

# Track connected clients
connected_clients: dict[uuid.UUID, WebSocket] = {}


@router.post("/register", response_model=RegisterResponse)
def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    if not req.username or not req.kem_pk or not req.sig_pk:
        raise HTTPException(status_code=400, detail="Missing required fields")

    # TODO revisit this logic to handle existing users more gracefully?
    # Check if the username already exists
    existing_user = db.query(User).filter_by(username=req.username).first()
    if existing_user:
        return RegisterResponse(status="already_registered")

    logger.info(f"[SERVER] Registering user: {req.username}")

    # Create new user and add to the database
    new_user = User(
        username=req.username,
        kem_pk=req.kem_pk,
        sig_pk=req.sig_pk,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(new_user)  # Add the user to the session

    try:
        # Submit the new user to the database
        db.commit()
    except Exception as e:
        # db.rollback() # TODO review if rollback on error is needed
        logger.error(f"[SERVER] Error registering user '{req.username}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    logger.info(f"[SERVER] User '{req.username}' registered successfully.")
    return RegisterResponse(status="registered")


@router.get("/pubkey/{username}", response_model=GetPublicKeysResponse)
def get_public_key(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=username).first()
    if not user:
        logger.error(f"[SERVER] User '{username}' not found.")
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"[SERVER] Fetching public key for user: {username}")

    # Decapsulate the public keys from the user object & return them
    if not user.kem_pk or not user.sig_pk:
        logger.error(f"[SERVER] Public keys not found for user: {username}")
        raise HTTPException(
            status_code=404, detail="Public keys not found for this user"
        )

    logger.info(f"[SERVER] Public keys for {username} fetched successfully.")

    return GetPublicKeysResponse(
        username=user.username,
        kem_pk=user.kem_pk,
        sig_pk=user.sig_pk,
    )


@router.post("/send", response_model=SendResponse)
async def send_message(req: SendRequest, db: Session = Depends(get_db)):
    # TODO helpers to streamline function readability
    # Resolve's sender ID from username + ensure exists
    sender = db.query(User).filter_by(username=req.sender).first()
    if not sender:
        logger.error(f"[SERVER] Sender '{req.sender}' not found.")
        raise HTTPException(status_code=404, detail="Sender not found")

    # Resolve recipient ID from username + ensure exists
    recipient = db.query(User).filter_by(username=req.recipient).first()
    if not recipient:
        logger.error(f"[SERVER] Recipient '{req.recipient}' not found.")
        raise HTTPException(status_code=404, detail="Recipient not found")

    logger.info(f"[SERVER] Sending message from {req.sender} to {req.recipient}")

    # Create a new message object and add it to the database
    new_message = Message(
        # Identifiers (ids & type)
        sender_id=sender.id,
        recipient_id=recipient.id,
        type="text",  # Default type, can be extended later
        # Status flags
        sent=True,  # Mark as sent immediately
        delivered=False,  # Initially not delivered
        read=False,  # Initially not read
        # Timestamps
        sent_at=None,  # assigned by DB (func.now() on insert)
        delivered_at=None,  # when delivered to recipient websocket
        read_at=None,  # when read by recipient (fetched) TODO remove?
        # Encryption metadata
        ciphertext=req.ciphertext,
        nonce=req.nonce,
        encapsulated_key=req.encapsulated_key,
        signature=req.signature,
        expires_at=req.expires_at,  # Optional expiration time
    )
    db.add(new_message)  # Add the message to the session

    try:
        # Commit the new message to the database
        logger.debug(
            f"[SERVER] Committing message from {req.sender} to {req.recipient}"
        )
        db.commit()
    except Exception as e:
        logger.error(
            f"[SERVER] Error sending message from {req.sender} to {req.recipient}: {e}"
        )
        # db.rollback() # TODO review if rollback on error is needed
        raise HTTPException(status_code=500, detail="Internal server error")

    # Notify the recipient via WebSocket if they are connected that a new message has arrived
    ws = connected_clients.get(recipient.id)
    if ws:
        try:
            logger.debug(f"[WebSocket] Notifying {req.recipient} of new message")
            await ws.send_text("new_message")
        except Exception as e:
            logger.error(f"[WebSocket] Failed to notify {req.recipient}: {e}")
    else:
        logger.warning(
            f"[WebSocket] No active WebSocket for {req.recipient}, skipping notification"
        )

    logger.info(f"[SERVER] Message sent from {req.sender} to {req.recipient}")
    return SendResponse(status="sent")


@router.get("/inbox/{username}", response_model=list[MessageResponse])
def get_inbox(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=username).first()
    if not user:
        logger.error(f"[SERVER] User '{username}' not found.")
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"[SERVER] Fetching inbox for user: {username}")

    # Fetch all messages for the user (order doesn't matter here)
    messages = (
        db.query(Message).filter_by(recipient_id=user.id, delivered=False)
    ).all()  # Only fetch undelivered messages
    if not messages:
        logger.info(f"[SERVER] No messages found for user: {username}")
        return []

    logger.debug(f"[SERVER] Found {len(messages)} messages for user: {username}")

    # Fill response with message details to be returned and decrypted by client
    response = []
    for msg in messages:
        # Change the message's delivered status to True
        msg.delivered = True
        # TODO fix timestamps
        # msg.delivered_at = datetime.now(timezone.utc)  # Set delivered timestamp

        # Ensure the message has a sender_id
        if not msg.sender_id:
            logger.error(f"[SERVER] Message {msg.id} has no sender_id.")
            continue

        # Resolve the sender's username from sender_id
        sender = db.query(User).filter_by(id=msg.sender_id).first()
        if not sender:
            logger.error(f"[SERVER] Sender with ID {msg.sender_id} not found.")
            continue

        # Append the message to the response
        response.append(
            MessageResponse(
                sender=sender.username,  # client only uses username
                ciphertext=msg.ciphertext,
                nonce=msg.nonce,
                encapsulated_key=msg.encapsulated_key,
                signature=msg.signature,
                sent_at=cast(datetime, msg.sent_at),
            )
        )

        # Delete the message from the database (mark as "dealt with")
        db.delete(msg)  # Remove message from the session
        # TODO delete to review
    logger.info(f"[SERVER] Inbox for {username} fetched successfully.")

    try:
        # Commit the deletion of messages
        logger.debug(f"[SERVER] Clearing inbox for user {username}")
        db.commit()
    except Exception as e:
        # db.rollback()  # TODO review if rollback on error is needed
        logger.error(f"[SERVER] Error clearing inbox for {username}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    # Return the sorted response by sent_at (oldest first)
    return sorted(response, key=lambda x: x.sent_at or datetime.min)
