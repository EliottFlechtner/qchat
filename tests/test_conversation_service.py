"""Tests for the conversation service functionality."""

import uuid
import pytest
from sqlalchemy.orm import Session

from server.services.conversation_service import ConversationService
from server.services.user_service import UserService
from server.db.database_models import User, Conversation


def test_conversation_service_creation(db_session: Session):
    """Test conversation creation between two users."""
    # Create test users
    user_service = UserService(db_session)
    conversation_service = ConversationService(db_session)

    # Create two test users
    success1, _ = user_service.create_user("alice", "alice_kem_pk", "alice_sig_pk")
    success2, _ = user_service.create_user("bob", "bob_kem_pk", "bob_sig_pk")

    assert success1 and success2

    # Get user objects
    alice = user_service.get_user_by_username("alice")
    bob = user_service.get_user_by_username("bob")

    assert alice is not None
    assert bob is not None

    # Create conversation
    conversation = conversation_service.get_or_create_conversation(alice.id, bob.id)

    assert conversation is not None
    assert conversation.id is not None
    assert {conversation.user1_id, conversation.user2_id} == {alice.id, bob.id}


def test_conversation_bidirectional(db_session: Session):
    """Test that conversations are bidirectional."""
    user_service = UserService(db_session)
    conversation_service = ConversationService(db_session)

    # Create test users
    user_service.create_user("charlie", "charlie_kem_pk", "charlie_sig_pk")
    user_service.create_user("diana", "diana_kem_pk", "diana_sig_pk")

    charlie = user_service.get_user_by_username("charlie")
    diana = user_service.get_user_by_username("diana")

    assert charlie is not None
    assert diana is not None

    # Create conversation from charlie to diana
    conv1 = conversation_service.get_or_create_conversation(charlie.id, diana.id)

    # Try to create conversation from diana to charlie (should return same conversation)
    conv2 = conversation_service.get_or_create_conversation(diana.id, charlie.id)

    assert conv1.id == conv2.id


def test_user_conversations_list(db_session: Session):
    """Test retrieving all conversations for a user."""
    user_service = UserService(db_session)
    conversation_service = ConversationService(db_session)

    # Create test users
    user_service.create_user("eve", "eve_kem_pk", "eve_sig_pk")
    user_service.create_user("frank", "frank_kem_pk", "frank_sig_pk")
    user_service.create_user("grace", "grace_kem_pk", "grace_sig_pk")

    eve = user_service.get_user_by_username("eve")
    frank = user_service.get_user_by_username("frank")
    grace = user_service.get_user_by_username("grace")

    assert eve is not None
    assert frank is not None
    assert grace is not None

    # Create conversations
    conv1 = conversation_service.get_or_create_conversation(eve.id, frank.id)
    conv2 = conversation_service.get_or_create_conversation(eve.id, grace.id)

    # Get Eve's conversations
    eve_conversations = conversation_service.get_user_conversations(eve.id)

    assert len(eve_conversations) == 2
    conversation_ids = [conv.id for conv in eve_conversations]
    assert conv1.id in conversation_ids
    assert conv2.id in conversation_ids


def test_user_authorization(db_session: Session):
    """Test user authorization for conversations."""
    user_service = UserService(db_session)
    conversation_service = ConversationService(db_session)

    # Create test users
    user_service.create_user("henry", "henry_kem_pk", "henry_sig_pk")
    user_service.create_user("iris", "iris_kem_pk", "iris_sig_pk")
    user_service.create_user("jack", "jack_kem_pk", "jack_sig_pk")

    henry = user_service.get_user_by_username("henry")
    iris = user_service.get_user_by_username("iris")
    jack = user_service.get_user_by_username("jack")

    assert henry is not None
    assert iris is not None
    assert jack is not None

    # Create conversation between henry and iris
    conversation = conversation_service.get_or_create_conversation(henry.id, iris.id)

    # Test authorization
    assert conversation_service.is_user_in_conversation(henry.id, conversation.id)
    assert conversation_service.is_user_in_conversation(iris.id, conversation.id)
    assert not conversation_service.is_user_in_conversation(jack.id, conversation.id)


def test_get_other_user_in_conversation(db_session: Session):
    """Test getting the other user in a conversation."""
    user_service = UserService(db_session)
    conversation_service = ConversationService(db_session)

    # Create test users
    user_service.create_user("kate", "kate_kem_pk", "kate_sig_pk")
    user_service.create_user("liam", "liam_kem_pk", "liam_sig_pk")

    kate = user_service.get_user_by_username("kate")
    liam = user_service.get_user_by_username("liam")

    assert kate is not None
    assert liam is not None

    # Create conversation
    conversation = conversation_service.get_or_create_conversation(kate.id, liam.id)

    # Test getting other user
    other_from_kate = conversation_service.get_other_user_in_conversation(
        kate.id, conversation
    )
    other_from_liam = conversation_service.get_other_user_in_conversation(
        liam.id, conversation
    )

    assert other_from_kate == liam.id
    assert other_from_liam == kate.id


def test_same_user_conversation_error(db_session: Session):
    """Test that creating a conversation with the same user raises an error."""
    user_service = UserService(db_session)
    conversation_service = ConversationService(db_session)

    # Create test user
    user_service.create_user("mia", "mia_kem_pk", "mia_sig_pk")
    mia = user_service.get_user_by_username("mia")

    assert mia is not None

    # Try to create conversation with same user
    with pytest.raises(
        ValueError, match="Cannot create conversation with the same user"
    ):
        conversation_service.get_or_create_conversation(mia.id, mia.id)
