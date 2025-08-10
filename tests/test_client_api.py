"""
Comprehensive tests for client API functions.

Tests all HTTP API interactions including success cases, error handling,
network failures, and edge cases.
"""

import pytest
import requests
from unittest.mock import patch, Mock, MagicMock
from client.api import (
    register_user,
    get_public_key,
    send_message,
    get_inbox,
    get_conversations,
    get_conversation_messages,
)


class TestRegisterUser:
    """Test user registration API function."""

    @patch("client.api.requests.post")
    @patch("client.api.get_api_url")
    def test_register_user_success(self, mock_get_api_url, mock_post):
        """Test successful user registration."""
        mock_get_api_url.return_value = "http://localhost:8000"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "registered"}
        mock_post.return_value = mock_response

        # Test data
        username = "testuser"
        kem_pk = b"kem_public_key_data" * 25  # 800 bytes for Kyber512
        sig_pk = b"sig_public_key_data" * 35  # ~897 bytes for Falcon-512

        result = register_user(username, kem_pk, sig_pk)

        assert result == {"status": "registered"}
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["username"] == username

    @patch("client.api.requests.post")
    def test_register_user_validation_errors(self, mock_post):
        """Test registration with invalid parameters."""
        with pytest.raises(
            ValueError, match="Username and public keys cannot be empty"
        ):
            register_user("", b"kem_pk", b"sig_pk")

        with pytest.raises(
            ValueError, match="Username and public keys cannot be empty"
        ):
            register_user("user", b"", b"sig_pk")

        with pytest.raises(
            ValueError, match="Username and public keys cannot be empty"
        ):
            register_user("user", b"kem_pk", b"")

    @patch("client.api.requests.post")
    @patch("client.api.get_api_url")
    def test_register_user_username_taken(self, mock_get_api_url, mock_post):
        """Test registration with taken username."""
        mock_get_api_url.return_value = "http://localhost:8000"
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Username already taken"}
        mock_post.return_value = mock_response

        with pytest.raises(
            Exception, match="Failed to register user: Username already taken"
        ):
            register_user("existing_user", b"kem_pk", b"sig_pk")

    @patch("client.api.requests.post")
    @patch("client.api.get_api_url")
    def test_register_user_network_error(self, mock_get_api_url, mock_post):
        """Test registration with network error."""
        mock_get_api_url.return_value = "http://localhost:8000"
        mock_post.side_effect = requests.ConnectionError("Connection failed")

        with pytest.raises(Exception, match="Network error during registration"):
            register_user("user", b"kem_pk", b"sig_pk")


class TestGetPublicKey:
    """Test public key retrieval API function."""

    @patch("client.api.requests.get")
    @patch("client.api.get_api_url")
    @patch("client.api.b64d")
    def test_get_public_key_success(self, mock_b64d, mock_get_api_url, mock_get):
        """Test successful public key retrieval."""
        mock_get_api_url.return_value = "http://localhost:8000"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "kem_pk": "base64_kem_key",
            "sig_pk": "base64_sig_key",
        }
        mock_get.return_value = mock_response
        mock_b64d.return_value = b"decoded_key_bytes"

        result = get_public_key("testuser", "kem_pk")

        assert result == b"decoded_key_bytes"
        mock_get.assert_called_once_with("http://localhost:8000/pubkey/testuser")
        mock_b64d.assert_called_once_with("base64_kem_key")

    def test_get_public_key_validation_errors(self):
        """Test public key retrieval with invalid parameters."""
        with pytest.raises(ValueError, match="Invalid field"):
            get_public_key("user", "invalid_field")

        with pytest.raises(ValueError, match="Username cannot be empty"):
            get_public_key("", "kem_pk")

    @patch("client.api.requests.get")
    @patch("client.api.get_api_url")
    def test_get_public_key_user_not_found(self, mock_get_api_url, mock_get):
        """Test public key retrieval for non-existent user."""
        mock_get_api_url.return_value = "http://localhost:8000"
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "User not found"}
        mock_get.return_value = mock_response

        with pytest.raises(
            Exception, match="Failed to fetch public key: User not found"
        ):
            get_public_key("nonexistent", "kem_pk")

    @patch("client.api.requests.get")
    @patch("client.api.get_api_url")
    def test_get_public_key_network_error(self, mock_get_api_url, mock_get):
        """Test public key retrieval with network error."""
        mock_get_api_url.return_value = "http://localhost:8000"
        mock_get.side_effect = requests.RequestException("Network error")

        with pytest.raises(Exception, match="Network error fetching public key"):
            get_public_key("user", "kem_pk")


class TestSendMessage:
    """Test message sending API function."""

    @patch("client.api.requests.post")
    @patch("client.api.get_api_url")
    def test_send_message_success(self, mock_get_api_url, mock_post):
        """Test successful message sending."""
        mock_get_api_url.return_value = "http://localhost:8000"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "message stored"}
        mock_post.return_value = mock_response

        result = send_message(
            sender="alice",
            recipient="bob",
            ciphertext=b"encrypted_message",
            nonce=b"nonce_12_bytes",
            encap_key=b"encapsulated_key",
            signature=b"digital_signature",
        )

        assert result == {"status": "message stored"}
        mock_post.assert_called_once()

    def test_send_message_validation_errors(self):
        """Test message sending with invalid parameters."""
        # Empty string parameters
        with pytest.raises(ValueError, match="Sender and recipient cannot be empty"):
            send_message("", "bob", b"cipher", b"nonce", b"key", b"sig")

        with pytest.raises(ValueError, match="Sender and recipient cannot be empty"):
            send_message("alice", "", b"cipher", b"nonce", b"key", b"sig")

        # Empty bytes parameters
        with pytest.raises(ValueError, match="Message components cannot be empty"):
            send_message("alice", "bob", b"", b"nonce", b"key", b"sig")

        # Wrong type parameters
        with pytest.raises(ValueError, match="Message components must be bytes"):
            send_message("alice", "bob", "not_bytes", b"nonce", b"key", b"sig")  # type: ignore

    @patch("client.api.requests.post")
    @patch("client.api.get_api_url")
    def test_send_message_recipient_not_found(self, mock_get_api_url, mock_post):
        """Test message sending to non-existent recipient."""
        mock_get_api_url.return_value = "http://localhost:8000"
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Recipient not found"}
        mock_post.return_value = mock_response

        with pytest.raises(
            Exception, match="Failed to send message: Recipient not found"
        ):
            send_message("alice", "nonexistent", b"cipher", b"nonce", b"key", b"sig")

    @patch("client.api.requests.post")
    @patch("client.api.get_api_url")
    def test_send_message_network_error(self, mock_get_api_url, mock_post):
        """Test message sending with network error."""
        mock_get_api_url.return_value = "http://localhost:8000"
        mock_post.side_effect = requests.RequestException("Connection timeout")

        with pytest.raises(Exception, match="Network error sending message"):
            send_message("alice", "bob", b"cipher", b"nonce", b"key", b"sig")


class TestGetInbox:
    """Test inbox retrieval API function."""

    @patch("client.api.requests.get")
    @patch("client.api.get_api_url")
    def test_get_inbox_success(self, mock_get_api_url, mock_get):
        """Test successful inbox retrieval."""
        mock_get_api_url.return_value = "http://localhost:8000"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "sender": "bob",
                "ciphertext": "encrypted_message",
                "nonce": "nonce_data",
                "encapsulated_key": "key_data",
                "signature": "signature_data",
            }
        ]
        mock_get.return_value = mock_response

        result = get_inbox("alice")

        assert len(result) == 1
        assert result[0]["sender"] == "bob"

    @patch("client.api.requests.get")
    @patch("client.api.get_api_url")
    def test_get_inbox_empty(self, mock_get_api_url, mock_get):
        """Test inbox retrieval with empty inbox."""
        mock_get_api_url.return_value = "http://localhost:8000"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        result = get_inbox("alice")

        assert result == []

    def test_get_inbox_validation_error(self):
        """Test inbox retrieval with invalid username."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            get_inbox("")

    @patch("client.api.requests.get")
    @patch("client.api.get_api_url")
    def test_get_inbox_user_not_found(self, mock_get_api_url, mock_get):
        """Test inbox retrieval for non-existent user."""
        mock_get_api_url.return_value = "http://localhost:8000"
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "User not found"}
        mock_get.return_value = mock_response

        result = get_inbox("nonexistent")

        assert result == []

    @patch("client.api.requests.get")
    @patch("client.api.get_api_url")
    def test_get_inbox_network_error(self, mock_get_api_url, mock_get):
        """Test inbox retrieval with network error."""
        mock_get_api_url.return_value = "http://localhost:8000"
        mock_get.side_effect = requests.RequestException("Network timeout")

        result = get_inbox("alice")

        assert result == []


class TestGetConversations:
    """Test conversations retrieval API function."""

    @patch("client.api.requests.get")
    @patch("client.api.get_api_url")
    def test_get_conversations_success(self, mock_get_api_url, mock_get):
        """Test successful conversations retrieval."""
        mock_get_api_url.return_value = "http://localhost:8000"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "conversations": [
                {
                    "id": "conv-123",
                    "other_user": "bob",
                    "created_at": "2024-01-01T12:00:00Z",
                    "updated_at": "2024-01-01T12:30:00Z",
                }
            ]
        }
        mock_get.return_value = mock_response

        result = get_conversations("alice")

        assert len(result) == 1
        assert result[0]["other_user"] == "bob"

    def test_get_conversations_validation_error(self):
        """Test conversations retrieval with invalid username."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            get_conversations("")


class TestGetConversationMessages:
    """Test conversation messages retrieval API function."""

    @patch("client.api.requests.get")
    @patch("client.api.get_api_url")
    def test_get_conversation_messages_success(self, mock_get_api_url, mock_get):
        """Test successful conversation messages retrieval."""
        mock_get_api_url.return_value = "http://localhost:8000"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "conversation_id": "conv-123",
            "messages": [
                {
                    "sender": "bob",
                    "ciphertext": "encrypted_content",
                    "nonce": "nonce_data",
                    "encapsulated_key": "key_data",
                    "signature": "sig_data",
                    "sent_at": "2024-01-01T12:00:00Z",
                }
            ],
        }
        mock_get.return_value = mock_response

        result = get_conversation_messages("alice", "conv-123")

        assert len(result) == 1
        assert result[0]["sender"] == "bob"

    def test_get_conversation_messages_validation_errors(self):
        """Test conversation messages retrieval with invalid parameters."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            get_conversation_messages("", "conv-123")

        with pytest.raises(ValueError, match="Conversation ID cannot be empty"):
            get_conversation_messages("alice", "")
