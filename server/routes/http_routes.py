from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from typing import List, cast
import uuid

from server.utils.logger import logger
from server.db.database import get_db
from server.services import (
    UserService,
    MessageService,
    ConversationService,
    websocket_service,
)
from shared import (
    RegisterRequest,
    SendRequest,
    RegisterResponse,
    GetPublicKeysResponse,
    SendResponse,
    MessageResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationMessagesResponse,
)

# Create FastAPI router for all HTTP endpoints
http_router = APIRouter()


@http_router.post("/register", response_model=RegisterResponse)
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

    # Initialize user service
    user_service = UserService(db)

    # Validate username format
    if not user_service.validate_username(req.username):
        raise HTTPException(status_code=400, detail="Username cannot be empty")

    username = req.username.strip()

    try:
        success, status = user_service.create_user(username, req.kem_pk, req.sig_pk)
        if success:
            logger.info(f"[SERVER] User '{username}' registered successfully")
        else:
            logger.info(f"[SERVER] User '{username}' already registered")
        return RegisterResponse(status=status)

    except SQLAlchemyError as e:
        logger.error(f"[SERVER] Database error registering user '{username}': {e}")
        raise HTTPException(
            status_code=500, detail="Database error during registration"
        )
    except Exception as e:
        logger.error(f"[SERVER] Unexpected error registering user '{username}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@http_router.get("/pubkey/{username}", response_model=GetPublicKeysResponse)
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

    # Initialize user service
    user_service = UserService(db)

    try:
        # Get user's public keys
        keys = user_service.get_public_keys(username)
        if not keys:
            logger.warning(
                f"[SERVER] Public key request for non-existent user or incomplete keys: {username}"
            )
            raise HTTPException(
                status_code=404, detail="User not found or public keys not available"
            )

        kem_pk, sig_pk = keys
        logger.info(f"[SERVER] Public keys for '{username}' retrieved successfully")

        return GetPublicKeysResponse(
            username=username,
            kem_pk=kem_pk,  # KEM public key for encryption
            sig_pk=sig_pk,  # Signature public key for verification
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"[SERVER] Error fetching public keys for '{username}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@http_router.post("/send", response_model=SendResponse)
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

    # Initialize services
    user_service = UserService(db)
    message_service = MessageService(db)

    # Validate cryptographic components
    if not message_service.validate_message_components(
        req.ciphertext, req.nonce, req.encapsulated_key, req.signature
    ):
        raise HTTPException(
            status_code=400, detail="All cryptographic components are required"
        )

    try:
        # Resolve sender from username
        sender = user_service.get_user_by_username(req.sender.strip())
        if not sender:
            logger.warning(f"[SERVER] Message from non-existent sender: {req.sender}")
            raise HTTPException(status_code=404, detail="Sender not found")

        # Resolve recipient from username
        recipient = user_service.get_user_by_username(req.recipient.strip())
        if not recipient:
            logger.warning(
                f"[SERVER] Message to non-existent recipient: {req.recipient}"
            )
            raise HTTPException(status_code=404, detail="Recipient not found")

        logger.info(
            f"[SERVER] Processing message from '{req.sender}' to '{req.recipient}'"
        )

        # Store the message
        message_id = message_service.send_message(
            sender_id=sender.id,
            recipient_id=recipient.id,
            ciphertext=req.ciphertext,
            nonce=req.nonce,
            encapsulated_key=req.encapsulated_key,
            signature=req.signature,
            expires_at=req.expires_at,
        )

        logger.debug(
            f"[SERVER] Message stored from '{req.sender}' to '{req.recipient}' with ID: {message_id}"
        )

        # Attempt real-time notification via WebSocket
        notification_sent = await websocket_service.notify_user(
            recipient.id, "new_message"
        )

        if notification_sent:
            logger.debug(f"[WebSocket] Notified '{req.recipient}' of new message")
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
        logger.error(f"[SERVER] Database error sending message: {e}")
        raise HTTPException(status_code=500, detail="Database error storing message")
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"[SERVER] Unexpected error sending message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@http_router.get("/inbox/{username}", response_model=List[MessageResponse])
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

    # Initialize services
    user_service = UserService(db)
    message_service = MessageService(db)

    try:
        # Verify user exists in database
        user = user_service.get_user_by_username(username)
        if not user:
            logger.warning(f"[SERVER] Inbox request for non-existent user: {username}")
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"[SERVER] Fetching inbox for user: {username}")

        # Fetch all undelivered messages for the user
        messages = message_service.get_inbox_messages(user.id)

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
                sender = user_service.get_user_by_id(msg.sender_id)
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

            except Exception as e:
                logger.error(f"[SERVER] Error processing message {msg.id}: {e}")
                continue

        # Mark messages as delivered and remove from database
        processed_count = message_service.mark_messages_delivered(messages)

        logger.info(
            f"[SERVER] Delivered {processed_count} messages to '{username}' and cleared inbox"
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
        logger.error(f"[SERVER] Database error fetching inbox for '{username}': {e}")
        raise HTTPException(status_code=500, detail="Database error accessing inbox")
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"[SERVER] Unexpected error fetching inbox for '{username}': {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@http_router.get("/conversations/{username}", response_model=ConversationListResponse)
def get_user_conversations(
    username: str, db: Session = Depends(get_db)
) -> ConversationListResponse:
    """Retrieves all conversations for a user.

    Returns a list of conversations the user is participating in, along with
    the other participant's username and conversation metadata.

    Endpoint: GET /conversations/{username}
    Response: {
        "conversations": [
            {
                "id": str, "other_user": str,
                "created_at": datetime, "updated_at": datetime
            }, ...
        ]
    }

    :param username: Username whose conversations to retrieve.
    :param db: Database session dependency injection.
    :return: List of user's conversations.
    :raises HTTPException: 404 if user not found, 500 for database errors.
    """
    # Validate username parameter
    if not username or not username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty")

    username = username.strip()

    # Initialize services
    user_service = UserService(db)
    conversation_service = ConversationService(db)

    try:
        # Verify user exists
        user = user_service.get_user_by_username(username)
        if not user:
            logger.warning(
                f"[SERVER] Conversations request for non-existent user: {username}"
            )
            raise HTTPException(status_code=404, detail="User not found")

        # Get all conversations for the user
        conversations = conversation_service.get_user_conversations(user.id)

        # Build response with other user information
        conversation_responses = []
        for conv in conversations:
            try:
                # Get the other user in the conversation
                other_user_id = conversation_service.get_other_user_in_conversation(
                    user.id, conv
                )
                other_user = user_service.get_user_by_id(other_user_id)

                if not other_user:
                    logger.error(
                        f"[SERVER] Other user not found in conversation {conv.id}"
                    )
                    continue

                conversation_responses.append(
                    ConversationResponse(
                        id=str(conv.id),
                        other_user=other_user.username,
                        created_at=cast(datetime, conv.created_at),
                        updated_at=cast(datetime, conv.updated_at),
                    )
                )
            except Exception as e:
                logger.error(f"[SERVER] Error processing conversation {conv.id}: {e}")
                continue

        logger.info(
            f"[SERVER] Retrieved {len(conversation_responses)} conversations for '{username}'"
        )
        return ConversationListResponse(conversations=conversation_responses)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(
            f"[SERVER] Database error fetching conversations for '{username}': {e}"
        )
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(
            f"[SERVER] Unexpected error fetching conversations for '{username}': {e}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@http_router.get(
    "/conversations/{username}/{conversation_id}/messages",
    response_model=ConversationMessagesResponse,
)
def get_conversation_messages(
    username: str, conversation_id: str, db: Session = Depends(get_db)
) -> ConversationMessagesResponse:
    """Retrieves all messages in a specific conversation.

    Returns all messages in the conversation that the user is authorized to access.
    Messages are returned in chronological order (oldest first).

    Endpoint: GET /conversations/{username}/{conversation_id}/messages
    Response: {
        "conversation_id": str,
        "messages": [
            {
                "sender": str, "ciphertext": str, "nonce": str,
                "encapsulated_key": str, "signature": str, "sent_at": datetime
            }, ...
        ]
    }

    :param username: Username requesting the messages.
    :param conversation_id: UUID of the conversation as string.
    :param db: Database session dependency injection.
    :return: Messages in the conversation.
    :raises HTTPException: 400 for invalid UUID, 404 if user/conversation not found, 403 if unauthorized, 500 for database errors.
    """
    # Validate username parameter
    if not username or not username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty")

    username = username.strip()

    # Validate conversation_id format
    try:
        conversation_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")

    # Initialize services
    user_service = UserService(db)
    message_service = MessageService(db)
    conversation_service = ConversationService(db)

    try:
        # Verify user exists
        user = user_service.get_user_by_username(username)
        if not user:
            logger.warning(
                f"[SERVER] Messages request for non-existent user: {username}"
            )
            raise HTTPException(status_code=404, detail="User not found")

        # Verify conversation exists
        conversation = conversation_service.get_conversation_by_id(conversation_uuid)
        if not conversation:
            logger.warning(
                f"[SERVER] Messages request for non-existent conversation: {conversation_id}"
            )
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Verify user is authorized to access this conversation
        if not conversation_service.is_user_in_conversation(user.id, conversation_uuid):
            logger.warning(
                f"[SERVER] Unauthorized access to conversation {conversation_id} by user {username}"
            )
            raise HTTPException(
                status_code=403, detail="Not authorized to access this conversation"
            )

        # Get all messages in the conversation
        messages = message_service.get_conversation_messages(conversation_uuid, user.id)

        # Build response
        message_responses = []
        for msg in messages:
            try:
                # Get sender information
                sender = user_service.get_user_by_id(msg.sender_id)
                if not sender:
                    logger.error(f"[SERVER] Sender not found for message {msg.id}")
                    continue

                message_responses.append(
                    MessageResponse(
                        sender=sender.username,
                        ciphertext=msg.ciphertext,
                        nonce=msg.nonce,
                        encapsulated_key=msg.encapsulated_key,
                        signature=msg.signature,
                        sent_at=cast(datetime, msg.sent_at),
                    )
                )
            except Exception as e:
                logger.error(f"[SERVER] Error processing message {msg.id}: {e}")
                continue

        logger.info(
            f"[SERVER] Retrieved {len(message_responses)} messages from conversation {conversation_id} for '{username}'"
        )
        return ConversationMessagesResponse(
            conversation_id=conversation_id, messages=message_responses
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(
            f"[SERVER] Database error fetching messages for conversation {conversation_id}: {e}"
        )
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(
            f"[SERVER] Unexpected error fetching messages for conversation {conversation_id}: {e}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")
