"""User service handling user registration and public key operations."""

import uuid
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError

from .base import BaseService
from server.db.database_models import User
from server.utils.logger import logger


class UserService(BaseService):
    """Service for managing user operations."""

    def create_user(self, username: str, kem_pk: str, sig_pk: str) -> tuple[bool, str]:
        """Create a new user with cryptographic keys.

        :param username: Username for the new user
        :param kem_pk: Base64-encoded KEM public key
        :param sig_pk: Base64-encoded signature public key
        :return: Tuple of (success: bool, status: str)
        """
        try:
            # Check if username already exists
            existing_user = self.db.query(User).filter_by(username=username).first()
            if existing_user:
                logger.info(f"[USER_SERVICE] User '{username}' already exists")
                return True, "already_registered"

            # Create new user
            new_user = User(
                username=username,
                kem_pk=kem_pk,
                sig_pk=sig_pk,
            )

            self.db.add(new_user)
            self.db.commit()

            logger.info(f"[USER_SERVICE] User '{username}' created successfully")
            return True, "registered"

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(
                f"[USER_SERVICE] Database error creating user '{username}': {e}"
            )
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"[USER_SERVICE] Unexpected error creating user '{username}': {e}"
            )
            raise

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieve user by username.

        :param username: Username to search for
        :return: User object if found, None otherwise
        """
        try:
            user = self.db.query(User).filter_by(username=username).first()
            if user:
                logger.debug(f"[USER_SERVICE] Found user: {username}")
            else:
                logger.debug(f"[USER_SERVICE] User not found: {username}")
            return user
        except Exception as e:
            logger.error(f"[USER_SERVICE] Error retrieving user '{username}': {e}")
            raise

    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Retrieve user by UUID.

        :param user_id: User UUID to search for
        :return: User object if found, None otherwise
        """
        try:
            user = self.db.query(User).filter_by(id=user_id).first()
            if user:
                logger.debug(f"[USER_SERVICE] Found user by ID: {user_id}")
            else:
                logger.debug(f"[USER_SERVICE] User not found by ID: {user_id}")
            return user
        except Exception as e:
            logger.error(f"[USER_SERVICE] Error retrieving user by ID '{user_id}': {e}")
            raise

    def get_public_keys(self, username: str) -> Optional[tuple[str, str]]:
        """Get user's public keys.

        :param username: Username whose keys to retrieve
        :return: Tuple of (kem_pk, sig_pk) if user found, None otherwise
        """
        try:
            user = self.get_user_by_username(username)
            if not user:
                return None

            if not user.kem_pk or not user.sig_pk:
                logger.error(
                    f"[USER_SERVICE] Incomplete public keys for user: {username}"
                )
                return None

            logger.info(f"[USER_SERVICE] Retrieved public keys for user: {username}")
            return user.kem_pk, user.sig_pk

        except Exception as e:
            logger.error(
                f"[USER_SERVICE] Error retrieving public keys for '{username}': {e}"
            )
            raise

    def validate_username(self, username: str) -> bool:
        """Validate username format.

        :param username: Username to validate
        :return: True if valid, False otherwise
        """
        return bool(username and username.strip())
