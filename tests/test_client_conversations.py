"""Tests for client conversation functionality."""

import pytest
from unittest.mock import patch, Mock
from client.api import get_conversations, get_conversation_messages


class TestConversationAPI:
    """Test conversation API functions."""

    @patch("client.api.requests.get")
    def test_get_conversations_success(self, mock_get):
        """Test successful conversation retrieval."""
        # Mock successful API response
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

        # Test the function
        result = get_conversations("alice")

        # Verify results
        assert len(result) == 1
        assert result[0]["other_user"] == "bob"
        assert result[0]["id"] == "conv-123"

        # Verify API call
        mock_get.assert_called_once()

    @patch("client.api.requests.get")
    def test_get_conversations_empty(self, mock_get):
        """Test conversation retrieval with no conversations."""
        # Mock empty response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"conversations": []}
        mock_get.return_value = mock_response

        # Test the function
        result = get_conversations("alice")

        # Verify empty result
        assert result == []

    @patch("client.api.requests.get")
    def test_get_conversations_error(self, mock_get):
        """Test conversation retrieval with API error."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "User not found"}
        mock_get.return_value = mock_response

        # Test the function
        result = get_conversations("nonexistent")

        # Verify empty result on error
        assert result == []

    @patch("client.api.requests.get")
    def test_get_conversation_messages_success(self, mock_get):
        """Test successful conversation message retrieval."""
        # Mock successful API response
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

        # Test the function
        result = get_conversation_messages("alice", "conv-123")

        # Verify results
        assert len(result) == 1
        assert result[0]["sender"] == "bob"
        assert result[0]["ciphertext"] == "encrypted_content"

        # Verify API call
        mock_get.assert_called_once()

    @patch("client.api.requests.get")
    def test_get_conversation_messages_empty(self, mock_get):
        """Test conversation message retrieval with no messages."""
        # Mock empty response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "conversation_id": "conv-123",
            "messages": [],
        }
        mock_get.return_value = mock_response

        # Test the function
        result = get_conversation_messages("alice", "conv-123")

        # Verify empty result
        assert result == []

    @patch("client.api.requests.get")
    def test_get_conversation_messages_error(self, mock_get):
        """Test conversation message retrieval with API error."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {"detail": "Not authorized"}
        mock_get.return_value = mock_response

        # Test the function
        result = get_conversation_messages("alice", "conv-123")

        # Verify empty result on error
        assert result == []

    def test_get_conversations_invalid_username(self):
        """Test conversation retrieval with invalid username."""
        with pytest.raises(ValueError):
            get_conversations("")

    def test_get_conversation_messages_invalid_params(self):
        """Test conversation message retrieval with invalid parameters."""
        with pytest.raises(ValueError):
            get_conversation_messages("", "conv-123")

        with pytest.raises(ValueError):
            get_conversation_messages("alice", "")
