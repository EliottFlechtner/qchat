import uuid
from fastapi import APIRouter, HTTPException, Depends, WebSocket
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from typing import Dict, List, cast

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

# Create FastAPI router for all HTTP endpoints
router = APIRouter()

# Global WebSocket client tracking for real-time notifications
connected_clients: Dict[uuid.UUID, WebSocket] = {}


@router.post("/register", response_model=RegisterResponse)
def register_user(
    req: RegisterRequest, db: Session = Depends(get_db)
) -> RegisterResponse:
    """Registers a new user with their post-quantum cryptographic public keys.

    Stores the user's KEM and signature public keys in the database for message
    encryption and signature verification. Handles duplicate registrations gracefully.

    Endpoint: POST /register
    Request: {"username": str, "kem_pk": str, "sig_pk": str}
    Response: {"status": "registered" | "already_registered"}

    :param req: Registration request containing username and base64-encoded public keys.
    :param db: Database session dependency injection.
    :return: Registration status response.
    :raises HTTPException: 400 for missing fields, 500 for database errors.
    """
    # Validate required fields are present
    if not req.username or not req.kem_pk or not req.sig_pk:
        logger.warning("[SERVER] Registration attempt with missing required fields")
        raise HTTPException(status_code=400, detail="Missing required fields")

    # Validate username format
    if not req.username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty")

    username = req.username.strip()

    try:
        # Check if username already exists in database
        existing_user = db.query(User).filter_by(username=username).first()
        if existing_user:
            logger.info(
                f"[SERVER] User '{username}' already registered, returning existing status"
            )
            return RegisterResponse(status="already_registered")

        logger.info(f"[SERVER] Registering new user: {username}")

        # Create new user record with current timestamp
        current_time = datetime.now(timezone.utc)
        new_user = User(
            username=username,
            kem_pk=req.kem_pk,  # Kyber512 public key for message encryption
            sig_pk=req.sig_pk,  # Falcon-512 public key for signature verification
            created_at=current_time,
            updated_at=current_time,
        )

        # Add user to database session
        db.add(new_user)

        # Commit transaction to persist user
        db.commit()

        logger.info(f"[SERVER] User '{username}' registered successfully")
        return RegisterResponse(status="registered")

    except SQLAlchemyError as e:
        # Handle database-specific errors with rollback
        db.rollback()
        logger.error(f"[SERVER] Database error registering user '{username}': {e}")
        raise HTTPException(
            status_code=500, detail="Database error during registration"
        )
    except Exception as e:
        # Handle unexpected errors
        db.rollback()
        logger.error(f"[SERVER] Unexpected error registering user '{username}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pubkey/{username}", response_model=GetPublicKeysResponse)
def get_public_key(
    username: str, db: Session = Depends(get_db)
) -> GetPublicKeysResponse:
    """Retrieves a user's public keys for cryptographic operations.

    Returns both KEM and signature public keys needed for sending encrypted
    messages to the user and verifying messages from the user.

    Endpoint: GET /pubkey/{username}
    Response: {"username": str, "kem_pk": str, "sig_pk": str}

    :param username: Username whose public keys to retrieve.
    :param db: Database session dependency injection.
    :return: User's public keys response.
    :raises HTTPException: 404 if user or keys not found, 500 for database errors.
    """
    # Validate username parameter
    if not username or not username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty")

    username = username.strip()

    try:
        # Query user from database
        user = db.query(User).filter_by(username=username).first()
        if not user:
            logger.warning(
                f"[SERVER] Public key request for non-existent user: {username}"
            )
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"[SERVER] Fetching public keys for user: {username}")

        # Validate user has required public keys
        if not user.kem_pk or not user.sig_pk:
            logger.error(f"[SERVER] Incomplete public keys for user: {username}")
            raise HTTPException(
                status_code=404, detail="Public keys not found for this user"
            )

        logger.info(f"[SERVER] Public keys for '{username}' retrieved successfully")

        return GetPublicKeysResponse(
            username=user.username,
            kem_pk=user.kem_pk,  # KEM public key for encryption
            sig_pk=user.sig_pk,  # Signature public key for verification
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"[SERVER] Error fetching public keys for '{username}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/send", response_model=SendResponse)
async def send_message(req: SendRequest, db: Session = Depends(get_db)) -> SendResponse:
    """Stores an encrypted message and notifies the recipient via WebSocket.

    Validates both sender and recipient exist, stores the encrypted message with
    all cryptographic components, and sends real-time notification if recipient
    is connected via WebSocket.

    Endpoint: POST /send
    Request: {
        "sender": str, "recipient": str,
        "ciphertext": str, "nonce": str,
        "encapsulated_key": str, "signature": str,
        "expires_at": datetime | null
    }
    Response: {"status": "sent"}

    :param req: Send message request with encrypted content and metadata.
    :param db: Database session dependency injection.
    :return: Message send confirmation response.
    :raises HTTPException: 404 if sender/recipient not found, 500 for database errors.
    """
    # Validate required fields
    if not req.sender or not req.recipient:
        raise HTTPException(status_code=400, detail="Sender and recipient are required")
    if (
        not req.ciphertext
        or not req.nonce
        or not req.encapsulated_key
        or not req.signature
    ):
        raise HTTPException(
            status_code=400, detail="All cryptographic components are required"
        )

    try:
        # Resolve sender from username
        sender = db.query(User).filter_by(username=req.sender.strip()).first()
        if not sender:
            logger.warning(f"[SERVER] Message from non-existent sender: {req.sender}")
            raise HTTPException(status_code=404, detail="Sender not found")

        # Resolve recipient from username
        recipient = db.query(User).filter_by(username=req.recipient.strip()).first()
        if not recipient:
            logger.warning(
                f"[SERVER] Message to non-existent recipient: {req.recipient}"
            )
            raise HTTPException(status_code=404, detail="Recipient not found")

        logger.info(
            f"[SERVER] Processing message from '{req.sender}' to '{req.recipient}'"
        )

        # Create encrypted message record
        new_message = Message(
            # User identifiers
            sender_id=sender.id,
            recipient_id=recipient.id,
            type="text",  # Message type (extensible for future media types)
            # Delivery status tracking
            sent=True,  # Marked as sent immediately upon storage
            delivered=False,  # Will be marked true when fetched by recipient
            read=False,  # Currently unused, for future read receipts
            # Timestamp tracking (sent_at auto-set by database trigger)
            sent_at=None,  # Set automatically by database
            delivered_at=None,  # Set when message fetched from inbox
            read_at=None,  # Reserved for future read receipt feature
            # Cryptographic components (base64-encoded strings)
            ciphertext=req.ciphertext,  # AES-GCM encrypted message content
            nonce=req.nonce,  # AES-GCM nonce (12 bytes)
            encapsulated_key=req.encapsulated_key,  # KEM-encrypted shared secret
            signature=req.signature,  # Digital signature for authenticity
            expires_at=req.expires_at,  # Optional message expiration
        )

        # Add message to database session
        db.add(new_message)

        # Commit message to database
        db.commit()

        logger.debug(
            f"[SERVER] Message stored from '{req.sender}' to '{req.recipient}'"
        )

        # Attempt real-time notification via WebSocket
        recipient_ws = connected_clients.get(recipient.id)
        if recipient_ws:
            try:
                logger.debug(f"[WebSocket] Notifying '{req.recipient}' of new message")
                await recipient_ws.send_text("new_message")
            except Exception as e:
                # WebSocket notification failure doesn't fail the message send
                logger.warning(f"[WebSocket] Failed to notify '{req.recipient}': {e}")
        else:
            logger.debug(f"[WebSocket] No active connection for '{req.recipient}'")

        logger.info(
            f"[SERVER] Message sent successfully from '{req.sender}' to '{req.recipient}'"
        )
        return SendResponse(status="sent")

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except SQLAlchemyError as e:
        # Handle database-specific errors
        db.rollback()
        logger.error(f"[SERVER] Database error sending message: {e}")
        raise HTTPException(status_code=500, detail="Database error storing message")
    except Exception as e:
        # Handle unexpected errors
        db.rollback()
        logger.error(f"[SERVER] Unexpected error sending message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/inbox/{username}", response_model=List[MessageResponse])
def get_inbox(username: str, db: Session = Depends(get_db)) -> List[MessageResponse]:
    """Retrieves and clears undelivered messages from user's inbox.

    Fetches all pending encrypted messages for the user, marks them as delivered,
    and removes them from the server. Messages are returned with sender information
    and all cryptographic components needed for decryption.

    Endpoint: GET /inbox/{username}
    Response: [
        {
            "sender": str, "ciphertext": str, "nonce": str,
            "encapsulated_key": str, "signature": str, "sent_at": datetime
        }, ...
    ]

    :param username: Username whose inbox to retrieve and clear.
    :param db: Database session dependency injection.
    :return: List of encrypted messages with metadata (empty if no messages).
    :raises HTTPException: 404 if user not found, 500 for database errors.
    """
    # Validate username parameter
    if not username or not username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty")

    username = username.strip()

    try:
        # Verify user exists in database
        user = db.query(User).filter_by(username=username).first()
        if not user:
            logger.warning(f"[SERVER] Inbox request for non-existent user: {username}")
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"[SERVER] Fetching inbox for user: {username}")

        # Fetch all undelivered messages for the user
        messages = (
            db.query(Message).filter_by(recipient_id=user.id, delivered=False).all()
        )

        if not messages:
            logger.info(f"[SERVER] No pending messages for user: {username}")
            return []

        logger.debug(
            f"[SERVER] Found {len(messages)} pending messages for user: {username}"
        )

        # Process each message for response
        response: List[MessageResponse] = []
        for msg in messages:
            try:
                # Validate message has sender information
                if not msg.sender_id:
                    logger.error(
                        f"[SERVER] Message {msg.id} missing sender_id, skipping"
                    )
                    continue

                # Resolve sender username from sender_id
                sender = db.query(User).filter_by(id=msg.sender_id).first()
                if not sender:
                    logger.error(
                        f"[SERVER] Message {msg.id} has invalid sender_id {msg.sender_id}, skipping"
                    )
                    continue

                # Create message response with all cryptographic components
                response.append(
                    MessageResponse(
                        sender=sender.username,  # Sender's username
                        ciphertext=msg.ciphertext,  # Encrypted message content
                        nonce=msg.nonce,  # AES-GCM nonce
                        encapsulated_key=msg.encapsulated_key,  # KEM-encrypted shared secret
                        signature=msg.signature,  # Digital signature
                        sent_at=cast(datetime, msg.sent_at),  # Message timestamp
                    )
                )

                # Mark message as delivered and remove from database
                # This implements a "consume-on-read" pattern for security
                db.delete(msg)

            except Exception as e:
                logger.error(f"[SERVER] Error processing message {msg.id}: {e}")
                continue

        # Commit all message deletions
        db.commit()

        logger.info(
            f"[SERVER] Delivered {len(response)} messages to '{username}' and cleared inbox"
        )

        # Return messages sorted by timestamp (oldest first)
        return sorted(
            response,
            key=lambda x: x.sent_at or datetime.min.replace(tzinfo=timezone.utc),
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except SQLAlchemyError as e:
        # Handle database-specific errors
        db.rollback()
        logger.error(f"[SERVER] Database error fetching inbox for '{username}': {e}")
        raise HTTPException(status_code=500, detail="Database error accessing inbox")
    except Exception as e:
        # Handle unexpected errors
        db.rollback()
        logger.error(f"[SERVER] Unexpected error fetching inbox for '{username}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
