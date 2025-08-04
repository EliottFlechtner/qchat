import requests, sys

from client.utils.helpers import b64e, b64d, API_URL


def register_user(username, kem_pk: bytes, sig_pk: bytes) -> dict:
    if not username or not kem_pk or not sig_pk:
        raise ValueError("Username and public keys cannot be empty")

    print(f"[CLIENT] Registering user: {username}", file=sys.stderr)

    # Register a new user with their public keys
    req = requests.post(
        f"{API_URL}/register",
        json={
            "username": username,
            "kem_pk": b64e(kem_pk),
            "sig_pk": b64e(sig_pk),
        },
    )

    # Check if the registration was successful
    if req.status_code != 200:
        raise Exception(
            f"Failed to register user: {req.json().get('detail', 'Unknown error')}"
        )
    return req.json()  # {"status": "registered"}


def get_public_key(username: str, field: str = "kem_pk") -> bytes:
    if field not in ["kem_pk", "sig_pk"]:
        raise ValueError("Invalid field, must be 'kem_pk' or 'sig_pk'")
    if not username:
        raise ValueError("Username cannot be empty")

    print(f"[CLIENT] Fetching public key for user: {username}", file=sys.stderr)

    # Fetch the user's public key from the server
    res = requests.get(f"{API_URL}/pubkey/{username}")

    # Check if the server correctly returned the public key
    if res.status_code != 200:
        raise Exception(
            f"Failed to fetch public key: {res.json().get('detail', 'Unknown error')}"
        )
    return b64d(res.json()[field])  # Return requested pk (decoded from base64)


def send_message(
    sender: str,
    recipient: str,
    ciphertext: bytes,
    nonce: bytes,
    encap_key: bytes,
    signature: bytes,
) -> dict:
    if not sender or not recipient:
        raise ValueError("Sender and recipient cannot be empty")
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

    # Send a message to the recipient
    req = requests.post(
        f"{API_URL}/send",
        json={
            # Identifiers (ids & type)
            "sender": sender,
            "recipient": recipient,
            # Encryption metadata
            "ciphertext": b64e(ciphertext),
            "nonce": b64e(nonce),
            "encapsulated_key": b64e(encap_key),
            "signature": b64e(signature),
            "expires_at": None,  # Optional, can be set to None for no expiration
        },
    )

    # Check if the message was sent successfully
    if req.status_code != 200:
        raise Exception(
            f"Failed to send message: {req.json().get('detail', 'Unknown error')}"
        )
    return req.json()  # {"status": "message stored"}


def get_inbox(username: str) -> list[dict]:
    if not username:
        raise ValueError("Username cannot be empty")

    print(f"[CLIENT] Fetching inbox for user: {username}", file=sys.stderr)

    # Fetch the user's inbox messages
    res = requests.get(f"{API_URL}/inbox/{username}")

    if res.status_code != 200:
        print(
            f"[CLIENT] Failed to fetch inbox: {res.json().get('detail', 'Unknown error')}",
            file=sys.stderr,
        )
        return []

    # Return the inbox messages as a list of dictionaries
    if not res.json():
        print("[CLIENT] Inbox is empty", file=sys.stderr)
        return []
    return res.json()  # List of messages as dicts, not empty, not decrypted
