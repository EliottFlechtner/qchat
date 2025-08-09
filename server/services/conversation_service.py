"""Conversation service handling conversation creation and management operations."""

import uuid
from typing import Optional, List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, and_

from .base import BaseService
from server.db.database_models import Conversation, User
from server.utils.logger import logger


class ConversationService(BaseService):
    """Service for managing conversation operations."""

    def get_or_create_conversation(
        self, user1_id: uuid.UUID, user2_id: uuid.UUID
    ) -> Conversation:
        """Get existing conversation between two users or create a new one.

        Conversations are bidirectional - the order of user1_id and user2_id doesn't matter.

        :param user1_id: UUID of the first user
        :param user2_id: UUID of the second user
        :return: Conversation object
        """
        try:
            # Ensure user1_id != user2_id
            if user1_id == user2_id:
                logger.error(
                    f"[CONVERSATION_SERVICE] Cannot create conversation with same user: {user1_id}"
                )
                raise ValueError("Cannot create conversation with the same user")

            # Look for existing conversation (bidirectional)
            existing_conversation = (
                self.db.query(Conversation)
                .filter(
                    or_(
                        and_(
                            Conversation.user1_id == user1_id,
                            Conversation.user2_id == user2_id,
                        ),
                        and_(
                            Conversation.user1_id == user2_id,
                            Conversation.user2_id == user1_id,
                        ),
                    )
                )
                .first()
            )

            if existing_conversation:
                logger.debug(
                    f"[CONVERSATION_SERVICE] Found existing conversation: {existing_conversation.id}"
                )
                return existing_conversation

            # Create new conversation
            # Always put the smaller UUID first for consistency
            if user1_id < user2_id:
                new_conversation = Conversation(user1_id=user1_id, user2_id=user2_id)
            else:
                new_conversation = Conversation(user1_id=user2_id, user2_id=user1_id)

            self.db.add(new_conversation)
            self.db.commit()

            logger.info(
                f"[CONVERSATION_SERVICE] Created new conversation: {new_conversation.id} "
                f"between users {user1_id} and {user2_id}"
            )
            return new_conversation

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(
                f"[CONVERSATION_SERVICE] Database error creating/getting conversation: {e}"
            )
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[CONVERSATION_SERVICE] Unexpected error creating/getting conversation: {e}"
            )
            raise

    def get_conversation_by_id(
        self, conversation_id: uuid.UUID
    ) -> Optional[Conversation]:
        """Retrieve conversation by UUID.

        :param conversation_id: Conversation UUID to search for
        :return: Conversation object if found, None otherwise
        """
        try:
            conversation = (
                self.db.query(Conversation).filter_by(id=conversation_id).first()
            )
            if conversation:
                logger.debug(
                    f"[CONVERSATION_SERVICE] Found conversation: {conversation_id}"
                )
            else:
                logger.debug(
                    f"[CONVERSATION_SERVICE] Conversation not found: {conversation_id}"
                )
            return conversation
        except Exception as e:
            logger.error(
                f"[CONVERSATION_SERVICE] Error retrieving conversation '{conversation_id}': {e}"
            )
            raise

    def get_user_conversations(self, user_id: uuid.UUID) -> List[Conversation]:
        """Get all conversations for a specific user.

        :param user_id: UUID of the user
        :return: List of Conversation objects where the user is a participant
        """
        try:
            conversations = (
                self.db.query(Conversation)
                .filter(
                    or_(
                        Conversation.user1_id == user_id,
                        Conversation.user2_id == user_id,
                    )
                )
                .order_by(Conversation.updated_at.desc())
                .all()
            )

            logger.debug(
                f"[CONVERSATION_SERVICE] Found {len(conversations)} conversations for user: {user_id}"
            )
            return conversations

        except Exception as e:
            logger.error(
                f"[CONVERSATION_SERVICE] Error retrieving conversations for user '{user_id}': {e}"
            )
            raise

    def is_user_in_conversation(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> bool:
        """Check if a user is a participant in a conversation.

        :param user_id: UUID of the user to check
        :param conversation_id: UUID of the conversation
        :return: True if user is in conversation, False otherwise
        """
        try:
            conversation = self.get_conversation_by_id(conversation_id)
            if not conversation:
                return False

            return conversation.user1_id == user_id or conversation.user2_id == user_id

        except Exception as e:
            logger.error(
                f"[CONVERSATION_SERVICE] Error checking user in conversation: {e}"
            )
            raise

    def get_other_user_in_conversation(
        self, user_id: uuid.UUID, conversation: Conversation
    ) -> uuid.UUID:
        """Get the other user's ID in a conversation.

        :param user_id: UUID of one user in the conversation
        :param conversation: Conversation object
        :return: UUID of the other user
        """
        if conversation.user1_id == user_id:
            return conversation.user2_id
        elif conversation.user2_id == user_id:
            return conversation.user1_id
        else:
            raise ValueError(f"User {user_id} is not in conversation {conversation.id}")
