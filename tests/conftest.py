"""
Pytest configuration and fixtures for the qchat test suite.
"""

import sys
import os
import pytest
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.db.database import Base

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


@pytest.fixture
def mock_client_settings():
    """Mock client settings for testing."""
    settings = Mock()
    settings.server_host = "localhost"
    settings.server_port = 8000
    settings.use_https = False
    settings.server_url = "http://localhost:8000"
    settings.ws_url = "ws://localhost:8000/ws"
    settings.kem_algorithm = "Kyber512"
    settings.sig_algorithm = "Dilithium2"
    return settings


@pytest.fixture
def sample_keypair():
    """Sample cryptographic keypair for testing."""
    return {
        "kem": (b"kem_private_key", b"kem_public_key"),
        "sig": (b"sig_private_key", b"sig_public_key"),
    }


@pytest.fixture
def sample_message_data():
    """Sample message data for testing."""
    return {
        "sender": "alice",
        "recipient": "bob",
        "plaintext": "Hello, Bob!",
        "ciphertext": b"encrypted_message",
        "nonce": b"random_nonce",
        "encapsulated_key": b"encap_key",
        "signature": b"message_signature",
    }


@pytest.fixture
def db_session():
    """Provide an isolated in-memory database session for service tests."""
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# Mark all tests in specific files with appropriate markers
def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their file names and content."""
    for item in items:
        # Mark tests based on file names
        if "test_client_api" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "test_client_services" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "test_client_crypto" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "test_client_utils" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "test_client_websocket" in item.nodeid:
            item.add_marker(pytest.mark.asyncio)
            item.add_marker(pytest.mark.integration)
        elif "test_client_error_handling" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "test_conversation" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_services" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Mark slow tests
        if "performance" in item.nodeid or "load" in item.nodeid:
            item.add_marker(pytest.mark.slow)

        # Mark async tests
        if "async" in item.name or "websocket" in item.name:
            item.add_marker(pytest.mark.asyncio)
