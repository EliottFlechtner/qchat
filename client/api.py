import requests
import sys
from typing import List, Dict, Any

from client.utils.helpers import b64e, b64d, get_api_url


def register_user(username: str, kem_pk: bytes, sig_pk: bytes) -> Dict[str, str]:
    """Registers a new user with their post-quantum public keys on the server.

    Sends KEM and signature public keys to the registration endpoint for storage.
    The server will use these keys for encrypting messages to this user and verifying
    messages from this user.

    API Endpoint: POST /register
    Request: {"username": str, "kem_pk": base64, "sig_pk": base64}
    Response: {"status": "registered"}

    :param username: Unique username for registration.
    :param kem_pk: Kyber512 public key for message encryption (800 bytes).
    :param sig_pk: Falcon-512 public key for signature verification (897 bytes).
    :return: Server response with registration status.
    :raises ValueError: If any parameter is empty.
    :raises Exception: If registration fails (username taken, invalid keys, server error).
    """
    # Validate all required parameters
    if (
        not isinstance(username, str)
        or not isinstance(kem_pk, bytes)
        or not isinstance(sig_pk, bytes)
    ):
        raise TypeError("Invalid input types: username must be str, keys must be bytes")

    if not username or not username.strip() or not kem_pk or not sig_pk:
        raise ValueError("Username and public keys cannot be empty")

    print(f"[CLIENT] Registering user: {username}", file=sys.stderr)

    try:
        # Register user with base64-encoded public keys
        req = requests.post(
            f"{get_api_url()}/register",
            json={
                "username": username,
                "kem_pk": b64e(kem_pk),  # Kyber512 public key for encryption
                "sig_pk": b64e(sig_pk),  # Falcon-512 public key for signatures
            },
        )

        # Check registration success
        if req.status_code != 200:
            error_detail = req.json().get("detail", "Unknown error")
            raise Exception(f"Failed to register user: {error_detail}")

        return req.json()  # {"status": "registered"}

    except requests.RequestException as e:
        raise Exception(f"Network error during registration: {e}")


def get_public_key(username: str, field: str = "kem_pk") -> bytes:
    """Retrieves a user's public key from the server for cryptographic operations.

    Fetches either KEM public key (for encrypting messages to the user) or signature
    public key (for verifying messages from the user) from the server's key database.

    API Endpoint: GET /pubkey/{username}
    Response: {"kem_pk": base64, "sig_pk": base64}

    :param username: Username whose public key to retrieve.
    :param field: Key type to retrieve ("kem_pk" for encryption, "sig_pk" for verification).
    :return: Decoded public key bytes ready for cryptographic use.
    :raises ValueError: If username is empty or field is invalid.
    :raises Exception: If key retrieval fails (user not found, server error).
    """
    # Validate field parameter
    if field not in ["kem_pk", "sig_pk"]:
        raise ValueError("Invalid field, must be 'kem_pk' or 'sig_pk'")
    if not username:
        raise ValueError("Username cannot be empty")

    print(f"[CLIENT] Fetching {field} for user: {username}", file=sys.stderr)

    try:
        # Fetch user's public keys from server
        res = requests.get(f"{get_api_url()}/pubkey/{username}")

        # Check if key retrieval was successful
        if res.status_code != 200:
            error_detail = res.json().get("detail", "Unknown error")
            raise Exception(f"Failed to fetch public key: {error_detail}")

        # Return requested public key decoded from base64
        return b64d(res.json()[field])

    except requests.RequestException as e:
        raise Exception(f"Network error fetching public key: {e}")


def send_message(
    sender: str,
    recipient: str,
    ciphertext: bytes,
    nonce: bytes,
    encap_key: bytes,
    signature: bytes,
) -> Dict[str, str]:
    """Sends an encrypted message with all cryptographic components to the server.

    Transmits a complete encrypted message package including the AES-GCM ciphertext,
    KEM-encapsulated key for the recipient, and digital signature for authenticity.

    API Endpoint: POST /send
    Request: {
        "sender": str, "recipient": str,
        "ciphertext": base64, "nonce": base64,
        "encapsulated_key": base64, "signature": base64,
        "expires_at": null  # TODO for future message expiration support
    }
    Response: {"status": "message stored"}

    :param sender: Username of message sender.
    :param recipient: Username of message recipient.
    :param ciphertext: AES-GCM encrypted message content.
    :param nonce: AES-GCM nonce for decryption (12 bytes).
    :param encap_key: KEM-encapsulated shared secret for recipient.
    :param signature: Falcon-512 signature over ciphertext for authenticity.
    :return: Server response confirming message storage.
    :raises ValueError: If any parameter is empty or has wrong type.
    :raises Exception: If message sending fails (recipient not found, server error).
    """
    # Validate string parameters
    if not sender or not recipient:
        raise ValueError("Sender and recipient cannot be empty")

    # Validate cryptographic components
    if not ciphertext or not nonce or not encap_key or not signature:
        raise ValueError("Message components cannot be empty")
    if (
        not isinstance(ciphertext, bytes)
        or not isinstance(nonce, bytes)
        or not isinstance(encap_key, bytes)
        or not isinstance(signature, bytes)
    ):
        raise ValueError("Message components must be bytes")

    print(f"[CLIENT] Sending message from {sender} to {recipient}", file=sys.stderr)

    try:
        # Send encrypted message with all cryptographic components
        req = requests.post(
            f"{get_api_url()}/send",
            json={
                # Message identifiers
                "sender": sender,
                "recipient": recipient,
                # Cryptographic components (base64-encoded for JSON)
                "ciphertext": b64e(ciphertext),  # AES-GCM encrypted content
                "nonce": b64e(nonce),  # AES-GCM nonce (12 bytes)
                "encapsulated_key": b64e(encap_key),  # KEM-encrypted shared secret
                "signature": b64e(signature),  # Digital signature for auth
                "expires_at": None,  # No message expiration
            },
        )

        # Check if message was stored successfully
        if req.status_code != 200:
            error_detail = req.json().get("detail", "Unknown error")
            raise Exception(f"Failed to send message: {error_detail}")

        return req.json()  # {"status": "message stored"}

    except requests.RequestException as e:
        raise Exception(f"Network error sending message: {e}")


def get_inbox(username: str) -> List[Dict[str, Any]]:
    """Retrieves all encrypted messages from the user's server inbox.

    Fetches a list of encrypted messages waiting for the user. Each message contains
    all cryptographic components needed for decryption and verification.

    API Endpoint: GET /inbox/{username}
    Response: [
        {
            "sender": str, "ciphertext": base64, "nonce": base64,
            "encapsulated_key": base64, "signature": base64
        }, ...
    ]

    :param username: Username whose inbox to retrieve.
    :return: List of encrypted message dictionaries (empty if no messages).
    :raises ValueError: If username is empty.
    """
    # Validate username parameter
    if not username:
        raise ValueError("Username cannot be empty")

    print(f"[CLIENT] Fetching inbox for user: {username}", file=sys.stderr)

    try:
        # Fetch user's inbox messages from server
        res = requests.get(f"{get_api_url()}/inbox/{username}")

        # Handle unsuccessful requests
        if res.status_code != 200:
            error_detail = res.json().get("detail", "Unknown error")
            print(f"[CLIENT] Failed to fetch inbox: {error_detail}", file=sys.stderr)
            return []

        # Handle empty inbox
        inbox_data = res.json()
        if not inbox_data:
            print("[CLIENT] Inbox is empty", file=sys.stderr)
            return []

        return inbox_data  # List of encrypted message dictionaries

    except requests.RequestException as e:
        print(f"[CLIENT] Network error fetching inbox: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"[CLIENT] Unexpected error fetching inbox: {e}", file=sys.stderr)
        return []


def get_conversations(username: str) -> List[Dict[str, Any]]:
    """Retrieves all conversations for a user.

    Fetches a list of conversations the user is participating in, along with
    the other participant's username and conversation metadata.

    API Endpoint: GET /conversations/{username}
    Response: {
        "conversations": [
            {
                "id": str, "other_user": str,
                "created_at": datetime, "updated_at": datetime
            }, ...
        ]
    }

    :param username: Username whose conversations to retrieve.
    :return: List of conversation dictionaries (empty if no conversations).
    :raises ValueError: If username is empty.
    """
    # Validate username parameter
    if not username:
        raise ValueError("Username cannot be empty")

    print(f"[CLIENT] Fetching conversations for user: {username}", file=sys.stderr)

    try:
        # Fetch user's conversations from server
        res = requests.get(f"{get_api_url()}/conversations/{username}")

        # Handle unsuccessful requests
        if res.status_code != 200:
            error_detail = res.json().get("detail", "Unknown error")
            print(
                f"[CLIENT] Failed to fetch conversations: {error_detail}",
                file=sys.stderr,
            )
            return []

        # Handle empty conversations
        conversations_data = res.json()
        if not conversations_data or not conversations_data.get("conversations"):
            print("[CLIENT] No conversations found", file=sys.stderr)
            return []

        return conversations_data["conversations"]  # List of conversation dictionaries

    except requests.RequestException as e:
        print(f"[CLIENT] Network error fetching conversations: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"[CLIENT] Unexpected error fetching conversations: {e}", file=sys.stderr)
        return []


def get_conversation_messages(
    username: str, conversation_id: str
) -> List[Dict[str, Any]]:
    """Retrieves all messages in a specific conversation.

    Fetches all messages in the conversation that the user is authorized to access.
    Messages are returned in chronological order (oldest first).

    API Endpoint: GET /conversations/{username}/{conversation_id}/messages
    Response: {
        "conversation_id": str,
        "messages": [
            {
                "sender": str, "ciphertext": str, "nonce": str,
                "encapsulated_key": str, "signature": str, "sent_at": datetime
            }, ...
        ]
    }

    :param username: Username requesting the messages.
    :param conversation_id: UUID of the conversation as string.
    :return: List of message dictionaries (empty if no messages).
    :raises ValueError: If username or conversation_id is empty.
    """
    # Validate parameters
    if not username:
        raise ValueError("Username cannot be empty")
    if not conversation_id:
        raise ValueError("Conversation ID cannot be empty")

    print(
        f"[CLIENT] Fetching messages for conversation {conversation_id} for user: {username}",
        file=sys.stderr,
    )

    try:
        # Fetch conversation messages from server
        res = requests.get(
            f"{get_api_url()}/conversations/{username}/{conversation_id}/messages"
        )

        # Handle unsuccessful requests
        if res.status_code != 200:
            error_detail = res.json().get("detail", "Unknown error")
            print(
                f"[CLIENT] Failed to fetch conversation messages: {error_detail}",
                file=sys.stderr,
            )
            return []

        # Handle empty messages
        messages_data = res.json()
        if not messages_data or not messages_data.get("messages"):
            print("[CLIENT] No messages found in conversation", file=sys.stderr)
            return []

        return messages_data["messages"]  # List of message dictionaries

    except requests.RequestException as e:
        print(
            f"[CLIENT] Network error fetching conversation messages: {e}",
            file=sys.stderr,
        )
        return []
    except Exception as e:
        print(
            f"[CLIENT] Unexpected error fetching conversation messages: {e}",
            file=sys.stderr,
        )
        return []
