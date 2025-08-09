"""
Conversation service for handling conversation operations.

Provides high-level functions for retrieving conversations and conversation messages
with proper error handling and logging.
"""

import sys
from typing import List, Dict, Any, Optional

from client.api import get_conversations, get_conversation_messages
from client.utils.helpers import b64d
from client.crypto.aes256 import decrypt_with_aes
from client.crypto.kem import decapsulate_key
from client.crypto.signature import verify_signature


def fetch_user_conversations(username: str) -> List[Dict[str, Any]]:
    """Fetch all conversations for a user.

    Retrieves all conversations the user is participating in from the server.
    Each conversation includes the other participant's username and metadata.

    :param username: Username whose conversations to retrieve.
    :return: List of conversation dictionaries with id, other_user, created_at, updated_at.
    :raises ValueError: If username is empty.
    """
    if not username:
        raise ValueError("Username cannot be empty")

    print(f"[CLIENT] Fetching conversations for user: {username}", file=sys.stderr)

    try:
        conversations = get_conversations(username)

        if not conversations:
            print("[CLIENT] No conversations found", file=sys.stderr)
            return []

        print(f"[CLIENT] Retrieved {len(conversations)} conversations", file=sys.stderr)
        return conversations

    except Exception as e:
        print(f"[CLIENT] Error fetching conversations: {e}", file=sys.stderr)
        raise


def fetch_conversation_messages(
    username: str,
    conversation_id: str,
    decrypt: bool = False,
    kem_sk: Optional[bytes] = None,
    sig_pk_cache: Optional[Dict[str, bytes]] = None,
) -> List[Dict[str, Any]]:
    """Fetch all messages in a specific conversation.

    Retrieves all messages in the conversation that the user is authorized to access.
    Optionally decrypts messages if decrypt=True and keys are provided.

    :param username: Username requesting the messages.
    :param conversation_id: UUID of the conversation as string.
    :param decrypt: Whether to decrypt the messages (requires kem_sk).
    :param kem_sk: User's KEM secret key for decryption (required if decrypt=True).
    :param sig_pk_cache: Cache of sender public keys for signature verification.
    :return: List of message dictionaries with sender, content, and metadata.
    :raises ValueError: If required parameters are missing.
    """
    if not username:
        raise ValueError("Username cannot be empty")
    if not conversation_id:
        raise ValueError("Conversation ID cannot be empty")
    if decrypt and not kem_sk:
        raise ValueError("KEM secret key required for decryption")

    print(
        f"[CLIENT] Fetching messages for conversation {conversation_id}",
        file=sys.stderr,
    )

    try:
        messages = get_conversation_messages(username, conversation_id)

        if not messages:
            print("[CLIENT] No messages found in conversation", file=sys.stderr)
            return []

        print(
            f"[CLIENT] Retrieved {len(messages)} messages from conversation",
            file=sys.stderr,
        )

        if not decrypt:
            return messages

        # Decrypt messages if requested (kem_sk is guaranteed to be bytes here due to earlier validation)
        assert kem_sk is not None  # Help type checker understand this is not None
        decrypted_messages = []
        for msg in messages:
            try:
                decrypted_msg = _decrypt_message(msg, kem_sk, sig_pk_cache)
                if decrypted_msg:
                    decrypted_messages.append(decrypted_msg)
            except Exception as e:
                print(
                    f"[CLIENT] Failed to decrypt message from {msg.get('sender', 'unknown')}: {e}",
                    file=sys.stderr,
                )
                # Add undecrypted message with error indication
                decrypted_messages.append(
                    {
                        "sender": msg.get("sender", "unknown"),
                        "content": "[DECRYPTION FAILED]",
                        "sent_at": msg.get("sent_at"),
                        "decryption_error": str(e),
                    }
                )

        print(
            f"[CLIENT] Successfully decrypted {len(decrypted_messages)} messages",
            file=sys.stderr,
        )
        return decrypted_messages

    except Exception as e:
        print(f"[CLIENT] Error fetching conversation messages: {e}", file=sys.stderr)
        raise


def _decrypt_message(
    msg: Dict[str, Any], kem_sk: bytes, sig_pk_cache: Optional[Dict[str, bytes]] = None
) -> Optional[Dict[str, Any]]:
    """Decrypt a single message.

    Decrypts the message content and optionally verifies the signature.

    :param msg: Message dictionary with encrypted content.
    :param kem_sk: User's KEM secret key for decryption.
    :param sig_pk_cache: Cache of sender public keys for signature verification.
    :return: Decrypted message dictionary or None if decryption fails.
    """
    try:
        sender = msg["sender"]
        ciphertext = b64d(msg["ciphertext"])
        nonce = b64d(msg["nonce"])
        encapsulated_key = b64d(msg["encapsulated_key"])
        signature = b64d(msg["signature"])
        sent_at = msg["sent_at"]

        # Decrypt the shared secret using KEM
        shared_secret = decapsulate_key(encapsulated_key, kem_sk)

        # Decrypt the message content using AES-GCM
        plaintext = decrypt_with_aes(shared_secret, nonce, ciphertext)

        # Verify signature if we have the sender's public key
        signature_verified = False
        if sig_pk_cache and sender in sig_pk_cache:
            try:
                signature_verified = verify_signature(
                    sender_public_key=sig_pk_cache[sender],
                    message=ciphertext,
                    signature=signature,
                )
            except Exception as e:
                print(
                    f"[CLIENT] Signature verification failed for message from {sender}: {e}",
                    file=sys.stderr,
                )

        return {
            "sender": sender,
            "content": plaintext,
            "sent_at": sent_at,
            "signature_verified": signature_verified,
        }

    except Exception as e:
        print(f"[CLIENT] Error decrypting message: {e}", file=sys.stderr)
        return None


def get_or_create_conversation_id(username: str, other_user: str) -> Optional[str]:
    """Get the conversation ID between two users.

    Searches for an existing conversation between the two users.
    Returns the conversation ID if found, None if no conversation exists.

    :param username: Current user's username.
    :param other_user: Other user's username.
    :return: Conversation ID as string if found, None otherwise.
    """
    if not username or not other_user:
        raise ValueError("Both usernames cannot be empty")

    try:
        conversations = fetch_user_conversations(username)

        # Look for conversation with the other user
        for conv in conversations:
            if conv["other_user"] == other_user:
                return conv["id"]

        print(
            f"[CLIENT] No existing conversation found between {username} and {other_user}",
            file=sys.stderr,
        )
        return None

    except Exception as e:
        print(f"[CLIENT] Error searching for conversation: {e}", file=sys.stderr)
        return None
