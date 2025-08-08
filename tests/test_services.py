"""
Example unit tests for the service layer.

This demonstrates how the new architecture enables easy testing of business logic.
"""

import sys
import os
import pytest
import uuid
from unittest.mock import Mock, MagicMock, AsyncMock
from datetime import datetime, timezone

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import services for testing
from server.services.user_service import UserService
from server.services.message_service import MessageService
from server.services.websocket_service import WebSocketService
from server.db.database_models import User, Message


class TestUserService:
    """Test cases for UserService business logic."""

    def test_create_user_success(self, mock_db):
        """Test successful user creation."""
        # Arrange
        mock_db.query.return_value.filter_by.return_value.first.return_value = (
            None  # No existing user
        )

        user_service = UserService(mock_db)

        # Act
        success, status = user_service.create_user("testuser", "kem_key", "sig_key")

        # Assert
        assert success is True
        assert status == "registered"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_user_already_exists(self, mock_db, mock_user):
        """Test user creation when user already exists."""
        # Arrange
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_user

        user_service = UserService(mock_db)

        # Act
        success, status = user_service.create_user("testuser", "kem_key", "sig_key")

        # Assert
        assert success is True
        assert status == "already_registered"
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_validate_username(self, mock_db):
        """Test username validation logic."""
        # Arrange
        user_service = UserService(mock_db)

        # Act & Assert
        assert user_service.validate_username("valid_user") is True
        assert user_service.validate_username("") is False
        assert user_service.validate_username("   ") is False

    def test_get_public_keys_success(self, mock_db, mock_user):
        """Test successful public key retrieval."""
        # Arrange
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_user

        user_service = UserService(mock_db)

        # Act
        result = user_service.get_public_keys("testuser")

        # Assert
        assert result == ("mock_kem_public_key", "mock_sig_public_key")

    def test_get_public_keys_user_not_found(self, mock_db):
        """Test public key retrieval when user doesn't exist."""
        # Arrange
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        user_service = UserService(mock_db)

        # Act
        result = user_service.get_public_keys("nonexistent")

        # Assert
        assert result is None


class TestMessageService:
    """Test cases for MessageService business logic."""

    def test_validate_message_components(self, mock_db):
        """Test message component validation."""
        # Arrange
        message_service = MessageService(mock_db)

        # Act & Assert
        assert (
            message_service.validate_message_components("cipher", "nonce", "key", "sig")
            is True
        )
        assert (
            message_service.validate_message_components("", "nonce", "key", "sig")
            is False
        )
        assert (
            message_service.validate_message_components("cipher", "", "key", "sig")
            is False
        )
        assert (
            message_service.validate_message_components("cipher", "nonce", "", "sig")
            is False
        )
        assert (
            message_service.validate_message_components("cipher", "nonce", "key", "")
            is False
        )

    def test_send_message_success(self, mock_db, monkeypatch):
        """Test successful message sending."""
        # Arrange
        mock_message = Mock()
        mock_message.id = uuid.uuid4()

        # Mock the Message constructor to return our mock
        monkeypatch.setattr(
            "server.services.message_service.Message", lambda **kwargs: mock_message
        )

        message_service = MessageService(mock_db)

        # Act
        result = message_service.send_message(
            sender_id=uuid.uuid4(),
            recipient_id=uuid.uuid4(),
            ciphertext="encrypted_data",
            nonce="nonce_value",
            encapsulated_key="key_value",
            signature="signature_value",
        )

        # Assert
        assert result == mock_message.id
        mock_db.add.assert_called_once_with(mock_message)
        mock_db.commit.assert_called_once()

    def test_get_inbox_messages(self, mock_db):
        """Test inbox message retrieval."""
        # Arrange
        user_id = uuid.uuid4()
        mock_messages = [Mock(), Mock()]
        mock_db.query.return_value.filter_by.return_value.all.return_value = (
            mock_messages
        )

        message_service = MessageService(mock_db)

        # Act
        result = message_service.get_inbox_messages(user_id)

        # Assert
        assert result == mock_messages
        mock_db.query.return_value.filter_by.assert_called_with(
            recipient_id=user_id, delivered=False
        )


class TestWebSocketService:
    """Test cases for WebSocketService."""

    def test_add_and_remove_client(self):
        """Test client connection management."""
        # Arrange
        ws_service = WebSocketService()
        user_id = uuid.uuid4()
        mock_websocket = Mock()

        # Act
        ws_service.add_client(user_id, mock_websocket)

        # Assert
        assert ws_service.is_user_connected(user_id) is True
        assert ws_service.get_connected_count() == 1
        assert ws_service.get_client(user_id) == mock_websocket

        # Act - Remove client
        ws_service.remove_client(user_id)

        # Assert
        assert ws_service.is_user_connected(user_id) is False
        assert ws_service.get_connected_count() == 0
        assert ws_service.get_client(user_id) is None

    @pytest.mark.asyncio
    async def test_notify_user_success(self):
        """Test successful user notification."""
        # Arrange
        ws_service = WebSocketService()
        user_id = uuid.uuid4()
        mock_websocket = Mock()
        mock_websocket.send_text = AsyncMock()

        ws_service.add_client(user_id, mock_websocket)

        # Act
        result = await ws_service.notify_user(user_id, "test_message")

        # Assert
        assert result is True
        mock_websocket.send_text.assert_called_once_with("test_message")

    @pytest.mark.asyncio
    async def test_notify_user_not_connected(self):
        """Test notification when user is not connected."""
        # Arrange
        ws_service = WebSocketService()
        user_id = uuid.uuid4()

        # Act
        result = await ws_service.notify_user(user_id, "test_message")

        # Assert
        assert result is False


# Example of how to run these tests:
# pytest tests/test_services.py -v
