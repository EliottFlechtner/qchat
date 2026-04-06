"""
Pytest configuration and fixtures for the qchat test suite.
"""

import sys
import os
import pytest
from unittest.mock import Mock

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


@pytest.fixture
def mock_db():
    """Mock database session for testing."""
    return Mock()


@pytest.fixture
def mock_user():
    """Mock user object for testing."""
    user = Mock()
    user.id = "test-user-id"
    user.username = "testuser"
    user.kem_pk = "mock_kem_public_key"
    user.sig_pk = "mock_sig_public_key"
    return user


@pytest.fixture
def mock_message():
    """Mock message object for testing."""
    message = Mock()
    message.id = "test-message-id"
    message.sender_id = "sender-id"
    message.recipient_id = "recipient-id"
    message.ciphertext = "encrypted_data"
    message.nonce = "nonce_value"
    message.encapsulated_key = "key_value"
    message.signature = "signature_value"
    message.sent_at = "2025-08-08T12:00:00Z"
    return message
