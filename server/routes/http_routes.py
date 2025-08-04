from fastapi import APIRouter, HTTPException, Depends, WebSocket
from sqlalchemy.orm import Session
from datetime import datetime, timezone

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
connected_clients: dict[str, WebSocket] = {}


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
    recipient = db.query(User).filter_by(username=req.recipient).first()
    if not recipient:
        logger.error(f"[SERVER] Recipient '{req.recipient}' not found.")
        raise HTTPException(status_code=404, detail="Recipient not found")

    logger.info(f"[SERVER] Sending message from {req.sender} to {req.recipient}")

    # Create a new message object and add it to the database
    new_message = Message(
        # Identifiers (ids & type)
        sender=req.sender,
        recipient=req.recipient,
        type="text",  # Default type, can be extended later
        # Status flags
        sent=True,  # Mark as sent immediately
        delivered=False,  # Initially not delivered
        read=False,  # Initially not read
        # Timestamps
        sent_timestamp=None,  # TODO fix, use current time
        delivered_timestamp=None,
        read_timestamp=None,
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

    # Notify the recipient via WebSocket if they are connected
    ws = connected_clients.get(req.recipient)
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

    # Fetch all messages for the user
    messages = db.query(Message).filter_by(recipient=username).all()

    # Convert to response model
    response = [
        MessageResponse(
            sender=m.sender,
            ciphertext=m.ciphertext,
            nonce=m.nonce,
            encapsulated_key=m.encapsulated_key,
            signature=m.signature,
        )
        for m in messages
    ]

    # Clear inbox (delete messages)
    for msg in messages:
        db.delete(msg)  # Remove message from the session

    try:
        # Commit the deletion of messages
        logger.debug(f"[SERVER] Clearing inbox for user {username}")
        db.commit()
    except Exception as e:
        # db.rollback()  # TODO review if rollback on error is needed
        logger.error(f"[SERVER] Error clearing inbox for {username}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return response
