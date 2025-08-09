"""Message service handling message storage and retrieval operations."""

import uuid
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

from .base import BaseService
from .conversation_service import ConversationService
from server.db.database_models import Message, User
from server.utils.logger import logger


class MessageService(BaseService):
    """Service for managing message operations."""

    def send_message(
        self,
        sender_id: uuid.UUID,
        recipient_id: uuid.UUID,
        ciphertext: str,
        nonce: str,
        encapsulated_key: str,
        signature: str,
        expires_at: Optional[str] = None,
    ) -> uuid.UUID:
        """Store an encrypted message in the database.

        :param sender_id: UUID of the message sender
        :param recipient_id: UUID of the message recipient
        :param ciphertext: Base64-encoded encrypted message content
        :param nonce: Base64-encoded AES-GCM nonce
        :param encapsulated_key: Base64-encoded KEM-encrypted shared secret
        :param signature: Base64-encoded digital signature
        :param expires_at: Optional message expiration timestamp as ISO string
        :return: UUID of the created message
        """
        try:
            # Get or create conversation between sender and recipient
            conversation_service = ConversationService(self.db)
            conversation = conversation_service.get_or_create_conversation(
                sender_id, recipient_id
            )

            # Parse expires_at if provided
            parsed_expires_at = None
            if expires_at:
                try:
                    parsed_expires_at = datetime.fromisoformat(
                        expires_at.replace("Z", "+00:00")
                    )
                except ValueError as e:
                    logger.warning(
                        f"[MESSAGE_SERVICE] Invalid expires_at format: {expires_at}, error: {e}"
                    )
                    # Continue without expiration if format is invalid

            # Create new message record
            new_message = Message(
                conversation_id=conversation.id,
                sender_id=sender_id,
                recipient_id=recipient_id,
                type="text",
                delivered=False,
                sent_at=None,  # Set by database trigger
                delivered_at=None,
                ciphertext=ciphertext,
                nonce=nonce,
                encapsulated_key=encapsulated_key,
                signature=signature,
                expires_at=parsed_expires_at,
            )

            self.db.add(new_message)
            self.db.commit()

            logger.info(
                f"[MESSAGE_SERVICE] Message stored from '{sender_id}' to '{recipient_id}' "
                f"in conversation '{conversation.id}'"
            )
            return new_message.id

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"[MESSAGE_SERVICE] Database error storing message: {e}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"[MESSAGE_SERVICE] Unexpected error storing message: {e}")
            raise

    def get_inbox_messages(self, user_id: uuid.UUID) -> List[Message]:
        """Retrieve all undelivered messages for a user.

        :param user_id: UUID of the user whose inbox to retrieve
        :return: List of undelivered Message objects
        """
        try:
            messages = (
                self.db.query(Message)
                .filter_by(recipient_id=user_id, delivered=False)
                .all()
            )

            logger.debug(
                f"[MESSAGE_SERVICE] Found {len(messages)} undelivered messages for user: {user_id}"
            )
            return messages

        except Exception as e:
            logger.error(
                f"[MESSAGE_SERVICE] Error retrieving inbox for user '{user_id}': {e}"
            )
            raise

    def mark_messages_delivered(self, messages: List[Message]) -> int:
        """Mark messages as delivered and remove them from the database.

        Implements consume-on-read pattern for security.

        :param messages: List of Message objects to mark as delivered
        :return: Number of messages successfully processed
        """
        try:
            processed_count = 0

            for msg in messages:
                try:
                    # Delete message (consume-on-read pattern)
                    # self.db.delete(msg)
                    msg.delivered = True
                    # msg.delivered_at = datetime.now(timezone.utc)
                    self.db.add(msg)  # Update the message status
                    processed_count += 1
                except Exception as e:
                    logger.error(
                        f"[MESSAGE_SERVICE] Error processing message {msg.id}: {e}"
                    )
                    continue

            # Commit all deletions
            self.db.commit()

            logger.info(
                f"[MESSAGE_SERVICE] Successfully processed {processed_count} messages"
            )
            return processed_count

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(
                f"[MESSAGE_SERVICE] Database error marking messages delivered: {e}"
            )
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[MESSAGE_SERVICE] Unexpected error marking messages delivered: {e}"
            )
            raise

    def validate_message_components(
        self, ciphertext: str, nonce: str, encapsulated_key: str, signature: str
    ) -> bool:
        """Validate that all required cryptographic components are present.

        :param ciphertext: Encrypted message content
        :param nonce: AES-GCM nonce
        :param encapsulated_key: KEM-encrypted shared secret
        :param signature: Digital signature
        :return: True if all components are valid, False otherwise
        """
        return all(
            [
                ciphertext and ciphertext.strip(),
                nonce and nonce.strip(),
                encapsulated_key and encapsulated_key.strip(),
                signature and signature.strip(),
            ]
        )

    def get_conversation_messages(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[Message]:
        """Retrieve all messages in a conversation that the user is authorized to see.

        :param conversation_id: UUID of the conversation
        :param user_id: UUID of the requesting user (for authorization)
        :return: List of Message objects in the conversation
        """
        try:
            # Verify user is in the conversation
            conversation_service = ConversationService(self.db)
            if not conversation_service.is_user_in_conversation(
                user_id, conversation_id
            ):
                logger.warning(
                    f"[MESSAGE_SERVICE] User {user_id} not authorized for conversation {conversation_id}"
                )
                return []

            messages = (
                self.db.query(Message)
                .filter_by(conversation_id=conversation_id)
                .order_by(Message.sent_at.asc())
                .all()
            )

            logger.debug(
                f"[MESSAGE_SERVICE] Found {len(messages)} messages in conversation {conversation_id}"
            )
            return messages

        except Exception as e:
            logger.error(
                f"[MESSAGE_SERVICE] Error retrieving conversation messages: {e}"
            )
            raise


# TODO delivered_at, delivered to manage
