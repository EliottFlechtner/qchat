"""
Comprehensive tests for client services including send, inbox, login, and conversation services.

Tests the high-level service functions that combine multiple API calls and cryptographic operations.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock, call
from client.services.send import send_encrypted_message
from client.services.inbox import fetch_and_decrypt_inbox
from client.services.login import get_local_keypair, save_local_keys, login_or_register
from client.services.conversation import (
    fetch_user_conversations,
    fetch_conversation_messages,
)


class TestSendEncryptedMessage:
    """Test encrypted message sending service."""

    @patch("client.services.send.send_message")
    @patch("client.services.send.sign_message")
    @patch("client.services.send.encrypt_message")
    @patch("client.services.send.encapsulate_key")
    @patch("client.services.send.get_public_key")
    @patch("client.services.send.get_local_keypair")
    def test_send_encrypted_message_success(
        self,
        mock_get_local_keypair,
        mock_get_public_key,
        mock_encapsulate_key,
        mock_encrypt_message,
        mock_sign_message,
        mock_send_message,
    ):
        """Test successful encrypted message sending."""
        # Setup mocks
        mock_get_local_keypair.return_value = (b"kem_sk", b"sig_sk")
        mock_get_public_key.return_value = b"recipient_kem_pk"
        mock_encapsulate_key.return_value = (b"encap_key", b"shared_secret")
        mock_encrypt_message.return_value = (b"ciphertext", b"nonce")
        mock_sign_message.return_value = b"signature"
        mock_send_message.return_value = {"status": "message stored"}

        # Test the function
        send_encrypted_message("alice", "bob", "Hello, Bob!")

        # Verify all calls were made
        mock_get_local_keypair.assert_called_once_with("alice")
        mock_get_public_key.assert_called_once_with("bob", field="kem_pk")
        mock_encapsulate_key.assert_called_once_with(b"recipient_kem_pk")
        mock_encrypt_message.assert_called_once_with("Hello, Bob!", b"shared_secret")
        mock_sign_message.assert_called_once_with(b"ciphertext", b"sig_sk")
        mock_send_message.assert_called_once_with(
            "alice", "bob", b"ciphertext", b"nonce", b"encap_key", b"signature"
        )

    def test_send_encrypted_message_validation_errors(self):
        """Test message sending with invalid parameters."""
        # Type validation
        with pytest.raises(TypeError, match="Sender must be a string"):
            send_encrypted_message(123, "bob", "message")  # type: ignore

        with pytest.raises(TypeError, match="Recipient must be a string"):
            send_encrypted_message("alice", 456, "message")  # type: ignore

        with pytest.raises(TypeError, match="Plaintext must be a string"):
            send_encrypted_message("alice", "bob", 789)  # type: ignore

        # Empty value validation
        with pytest.raises(ValueError, match="Sender cannot be empty"):
            send_encrypted_message("", "bob", "message")

        with pytest.raises(ValueError, match="Recipient cannot be empty"):
            send_encrypted_message("alice", "", "message")

        with pytest.raises(ValueError, match="Plaintext cannot be empty"):
            send_encrypted_message("alice", "bob", "")

        # Self-messaging validation
        with pytest.raises(ValueError, match="Sender and recipient cannot be the same"):
            send_encrypted_message("alice", "alice", "message")

    @patch("client.services.send.get_public_key")
    def test_send_encrypted_message_recipient_not_found(self, mock_get_public_key):
        """Test message sending to non-existent recipient."""
        mock_get_public_key.side_effect = RuntimeError(
            "Failed to retrieve KEM public key"
        )

        with pytest.raises(RuntimeError, match="Failed to retrieve KEM public key"):
            send_encrypted_message("alice", "nonexistent", "message")

    @patch("client.services.send.encapsulate_key")
    @patch("client.services.send.get_public_key")
    @patch("client.services.send.get_local_keypair")
    def test_send_encrypted_message_kem_failure(
        self, mock_get_local_keypair, mock_get_public_key, mock_encapsulate_key
    ):
        """Test message sending with KEM encapsulation failure."""
        mock_get_local_keypair.return_value = (b"kem_sk", b"sig_sk")
        mock_get_public_key.return_value = b"recipient_kem_pk"
        mock_encapsulate_key.side_effect = Exception("KEM failed")

        with pytest.raises(RuntimeError, match="KEM encapsulation failed"):
            send_encrypted_message("alice", "bob", "message")


class TestFetchAndDecryptInbox:
    """Test inbox fetching and decryption service."""

    @patch("client.services.inbox.decrypt_message")
    @patch("client.services.inbox.verify_signature")
    @patch("client.services.inbox.decapsulate_key")
    @patch("client.services.inbox.get_public_key")
    @patch("client.services.inbox.get_local_keypair")
    @patch("client.services.inbox.get_inbox")
    def test_fetch_and_decrypt_inbox_success(
        self,
        mock_get_inbox,
        mock_get_local_keypair,
        mock_get_public_key,
        mock_decapsulate_key,
        mock_verify_signature,
        mock_decrypt_message,
    ):
        """Test successful inbox fetching and decryption."""
        # Setup mocks
        mock_get_inbox.return_value = [
            {
                "sender": "bob",
                "ciphertext": "Y2lwaGVydGV4dA==",  # base64 encoded
                "nonce": "bm9uY2U=",  # base64 encoded
                "encapsulated_key": "a2V5",  # base64 encoded
                "signature": "c2ln",  # base64 encoded
            }
        ]
        mock_get_local_keypair.return_value = (b"kem_sk", b"sig_sk")
        mock_get_public_key.return_value = b"sender_sig_pk"
        mock_decapsulate_key.return_value = b"shared_secret"
        mock_verify_signature.return_value = True
        mock_decrypt_message.return_value = "Hello, Alice!"

        # Test the function
        result = fetch_and_decrypt_inbox("alice")

        # Verify calls
        mock_get_inbox.assert_called_once_with("alice")
        mock_get_local_keypair.assert_called_once_with("alice")

    @patch("client.services.inbox.get_inbox")
    def test_fetch_and_decrypt_inbox_empty(self, mock_get_inbox):
        """Test inbox fetching with empty inbox."""
        mock_get_inbox.return_value = []

        result = fetch_and_decrypt_inbox("alice")

        # Function doesn't return anything for empty inbox
        assert result is None

    def test_fetch_and_decrypt_inbox_validation_error(self):
        """Test inbox fetching with invalid username."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            fetch_and_decrypt_inbox("")

    @patch("client.services.inbox.verify_signature")
    @patch("client.services.inbox.decapsulate_key")
    @patch("client.services.inbox.get_public_key")
    @patch("client.services.inbox.get_local_keypair")
    @patch("client.services.inbox.get_inbox")
    def test_fetch_and_decrypt_inbox_signature_verification_failure(
        self,
        mock_get_inbox,
        mock_get_local_keypair,
        mock_get_public_key,
        mock_decapsulate_key,
        mock_verify_signature,
    ):
        """Test inbox fetching with signature verification failure."""
        mock_get_inbox.return_value = [
            {
                "sender": "bob",
                "ciphertext": "Y2lwaGVydGV4dA==",
                "nonce": "bm9uY2U=",
                "encapsulated_key": "a2V5",
                "signature": "c2ln",
            }
        ]
        mock_get_local_keypair.return_value = (b"kem_sk", b"sig_sk")
        mock_get_public_key.return_value = b"sender_sig_pk"
        mock_decapsulate_key.return_value = b"shared_secret"
        mock_verify_signature.return_value = False

        # This should not raise an error, just skip invalid messages
        result = fetch_and_decrypt_inbox("alice")

        # Function completes but prints error for invalid signature
        assert result is None


class TestLoginService:
    """Test login service functions."""

    @patch("client.services.login.generate_kem_keypair")
    @patch("client.services.login.generate_signature_keypair")
    @patch("client.services.login.save_local_keys")
    @patch("client.services.login.register_user")
    @patch("client.services.login.load_all_local_keys")
    def test_login_or_register_new_user(
        self,
        mock_load_keys,
        mock_register_user,
        mock_save_keys,
        mock_gen_sig,
        mock_gen_kem,
    ):
        """Test registration workflow for new user."""
        mock_load_keys.return_value = {}  # No existing keys
        mock_gen_kem.return_value = (b"kem_pk", b"kem_sk")
        mock_gen_sig.return_value = (b"sig_pk", b"sig_sk")
        mock_register_user.return_value = {"status": "registered"}

        # Mock get_local_keypair calls for loading keys after registration
        with patch("client.services.login.get_local_keypair") as mock_get_keys:
            mock_get_keys.side_effect = [
                (b"kem_sk", b"kem_pk"),  # KEM keypair
                (b"sig_sk", b"sig_pk"),  # Signature keypair
            ]

            result = login_or_register("alice")

            assert result == {
                "kem": (b"kem_sk", b"kem_pk"),
                "sig": (b"sig_sk", b"sig_pk"),
            }

        # Verify registration workflow
        mock_gen_kem.assert_called_once()
        mock_gen_sig.assert_called_once()
        mock_save_keys.assert_called_once()
        mock_register_user.assert_called_once()

    @patch("client.services.login.load_all_local_keys")
    @patch("client.services.login.get_local_keypair")
    def test_login_or_register_existing_user(self, mock_get_keys, mock_load_keys):
        """Test login workflow for existing user."""
        mock_load_keys.return_value = {"alice": {"kem_sk": "base64_key"}}
        mock_get_keys.side_effect = [
            (b"kem_sk", b"kem_pk"),
            (b"sig_sk", b"sig_pk"),
        ]

        result = login_or_register("alice")

        assert result == {
            "kem": (b"kem_sk", b"kem_pk"),
            "sig": (b"sig_sk", b"sig_pk"),
        }

    @patch("builtins.open", create=True)
    def test_get_local_keypair_success(self, mock_open):
        """Test successful local keypair retrieval."""
        # Mock JSON file content
        mock_file_content = {
            "alice": {
                "kem_sk": "a2VtX3NrX2RhdGE=",  # base64 for "kem_sk_data"
                "kem_pk": "a2VtX3BrX2RhdGE=",  # base64 for "kem_pk_data"
            }
        }

        with patch("client.services.login.load_all_local_keys") as mock_load:
            mock_load.return_value = mock_file_content

            result = get_local_keypair("alice", "kem")

            assert result == (b"kem_sk_data", b"kem_pk_data")

    @patch("client.services.login.load_all_local_keys")
    def test_get_local_keypair_user_not_found(self, mock_load):
        """Test local keypair retrieval with missing user."""
        mock_load.return_value = {"bob": {"kem_sk": "key"}}

        with pytest.raises(FileNotFoundError, match="No keys found for user 'alice'"):
            get_local_keypair("alice", "kem")

    def test_get_local_keypair_validation_errors(self):
        """Test local keypair retrieval with invalid parameters."""
        with pytest.raises(ValueError, match="Invalid field"):
            get_local_keypair("alice", "invalid")

        with pytest.raises(ValueError, match="Username cannot be empty"):
            get_local_keypair("", "kem")

    @patch("client.services.login.save_all_local_keys")
    @patch("client.services.login.load_all_local_keys")
    def test_save_local_keys_success(self, mock_load, mock_save):
        """Test successful local keys saving."""
        mock_load.return_value = {}

        save_local_keys("alice", (b"kem_pk", b"kem_sk"), (b"sig_pk", b"sig_sk"))

        # Verify save was called with encoded keys
        mock_save.assert_called_once()
        saved_data = mock_save.call_args[0][0]
        assert "alice" in saved_data
        assert "kem_sk" in saved_data["alice"]


class TestConversationService:
    """Test conversation service functions."""

    @patch("client.services.conversation.get_conversations")
    def test_fetch_user_conversations_success(self, mock_get_conversations):
        """Test successful user conversations fetching."""
        mock_get_conversations.return_value = [
            {
                "id": "conv-123",
                "other_user": "bob",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:30:00Z",
            }
        ]

        result = fetch_user_conversations("alice")

        assert len(result) == 1
        assert result[0]["other_user"] == "bob"

    def test_fetch_user_conversations_validation_error(self):
        """Test conversations fetching with invalid username."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            fetch_user_conversations("")

    @patch("client.services.conversation.get_conversations")
    def test_fetch_user_conversations_empty(self, mock_get_conversations):
        """Test conversations fetching with no conversations."""
        mock_get_conversations.return_value = []

        result = fetch_user_conversations("alice")

        assert result == []

    @patch("client.services.conversation.get_conversation_messages")
    def test_fetch_conversation_messages_success(self, mock_get_conversation_messages):
        """Test successful conversation messages fetching."""
        mock_get_conversation_messages.return_value = [
            {
                "sender": "bob",
                "ciphertext": "encrypted_content",
                "nonce": "nonce_data",
                "encapsulated_key": "key_data",
                "signature": "sig_data",
                "sent_at": "2024-01-01T12:00:00Z",
            }
        ]

        result = fetch_conversation_messages("alice", "conv-123")

        assert len(result) == 1
        assert result[0]["sender"] == "bob"

    def test_fetch_conversation_messages_validation_errors(self):
        """Test conversation messages fetching with invalid parameters."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            fetch_conversation_messages("", "conv-123")

        with pytest.raises(ValueError, match="Conversation ID cannot be empty"):
            fetch_conversation_messages("alice", "")
