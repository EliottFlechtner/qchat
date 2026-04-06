import sys

from client.api import get_inbox, get_public_key
from client.crypto.kem import decapsulate_key, decrypt_message
from client.services.login import get_local_keypair
from client.utils.helpers import b64d
from client.crypto.signature import verify_signature


def fetch_and_decrypt_inbox(username: str) -> None:
    """Fetches and decrypts all messages from the user's inbox.

    This function retrieves encrypted messages from the server, decrypts them using
    post-quantum cryptography, and verifies their authenticity using digital signatures.
    It implements a complete secure messaging workflow with proper error handling.

    Message processing workflow:
    1. Fetch encrypted messages from server inbox API
    2. For each message, decode base64-encoded cryptographic data
    3. Verify sender's digital signature for message authenticity
    4. Retrieve recipient's private key for decryption
    5. Decapsulate the shared secret using post-quantum KEM
    6. Decrypt the message content using AES-GCM
    7. Display the decrypted message to the user

    Security properties:
    - Message confidentiality: Only the intended recipient can decrypt messages
    - Message authenticity: Digital signatures prove sender identity
    - Message integrity: Any tampering is detected and rejected
    - Post-quantum security: Resistant to quantum computer attacks

    :param username: The username whose inbox should be fetched and decrypted.
    :raises TypeError: If username is not a string.
    :raises ValueError: If username is empty or invalid or if any message fields are missing or invalid.
    :raises RuntimeError: If critical operations fail (key retrieval, API calls).
    """
    # Validate username parameter
    if not isinstance(username, str):
        raise TypeError("Username must be a string")
    if not username or not username.strip():
        raise ValueError("Username cannot be empty")

    try:
        # Fetch encrypted messages from the server inbox API
        print(f"[INBOX] Fetching inbox for user '{username}'...")
        messages = get_inbox(username)

        # Handle empty inbox case
        if not messages:
            print("[INBOX] No new messages")
            return

        print(f"[INBOX] Found {len(messages)} message(s) to decrypt")

    except Exception as e:
        raise RuntimeError(f"Failed to fetch inbox for '{username}': {e}")

    # Process each encrypted message in the inbox
    successful_decryptions = 0
    for i, msg in enumerate(messages, 1):
        try:
            print(f"[INBOX] Processing message {i}/{len(messages)}...")

            # Extract and validate message structure
            if not isinstance(msg, dict):
                raise ValueError("Message must be a dictionary")

            required_fields = [
                "sender",
                "ciphertext",
                "nonce",
                "encapsulated_key",
                "signature",
            ]
            for field in required_fields:
                if field not in msg:
                    raise ValueError(f"Missing required field: {field}")

            # Decode all cryptographic data from base64 encoding
            sender = msg["sender"]
            if not isinstance(sender, str) or not sender.strip():
                raise ValueError("Sender must be a non-empty string")

            try:
                ciphertext = b64d(msg["ciphertext"])
                nonce = b64d(msg["nonce"])
                encapsulated_key = b64d(msg["encapsulated_key"])
                signature = b64d(msg["signature"])
            except Exception as e:
                raise ValueError(f"Failed to decode base64 data: {e}")

            # Retrieve sender's public key for signature verification
            print(f"[INBOX] Retrieving public key for sender '{sender}'...")
            try:
                sender_sig_pk = get_public_key(sender, field="sig_pk")
                if not sender_sig_pk:
                    raise ValueError(f"No public key found for sender '{sender}'")
            except Exception as e:
                print(
                    f"[ERROR] Could not get public key for {sender}: {e}",
                    file=sys.stderr,
                )
                continue

            # Step 1: Verify the digital signature for message authenticity
            print(f"[INBOX] Verifying digital signature from '{sender}'...")
            try:
                if not verify_signature(sender_sig_pk, ciphertext, signature):
                    print(
                        f"[WARNING] Invalid signature from {sender}, message rejected",
                        file=sys.stderr,
                    )
                    continue
                print(f"[INBOX] Signature verification successful for '{sender}'")
            except Exception as e:
                print(
                    f"[ERROR] Signature verification failed for {sender}: {e}",
                    file=sys.stderr,
                )
                continue

            # Step 2: Retrieve recipient's private key for decryption
            print(f"[INBOX] Retrieving private key for recipient '{username}'...")
            try:
                keypair_result = get_local_keypair(username, field="kem")
                if not keypair_result or len(keypair_result) < 1:
                    raise ValueError(f"No KEM keypair found for user '{username}'")
                kem_sk = keypair_result[0]  # KEM private key
                if not kem_sk:
                    raise ValueError(f"KEM private key is None for user '{username}'")
            except Exception as e:
                print(
                    f"[ERROR] Failed to retrieve private key for {username}: {e}",
                    file=sys.stderr,
                )
                continue

            # Step 3: Decapsulate the shared secret using post-quantum KEM
            print("[INBOX] Decapsulating shared secret...")
            try:
                shared_secret = decapsulate_key(encapsulated_key, kem_sk)
                if not shared_secret:
                    raise ValueError("Decapsulation returned empty shared secret")
            except Exception as e:
                print(f"[ERROR] Key decapsulation failed: {e}", file=sys.stderr)
                continue

            # Step 4: Decrypt the message content using AES-GCM
            print("[INBOX] Decrypting message content...")
            try:
                plaintext = decrypt_message(shared_secret, nonce, ciphertext)
                if not plaintext:
                    raise ValueError("Decryption returned empty plaintext")
            except Exception as e:
                print(f"[ERROR] Message decryption failed: {e}", file=sys.stderr)
                continue

            # Step 5: Display the successfully decrypted message
            print(
                f"[INBOX] Message {i} decrypted successfully from '{sender}'",
                file=sys.stderr,
            )
            print(f"[{sender}] ➤ {plaintext}")
            successful_decryptions += 1

        except ValueError as e:
            print(f"[ERROR] Invalid message {i} format: {e}", file=sys.stderr)
            continue
        except Exception as e:
            print(
                f"[ERROR] Unexpected error processing message {i}: {e}", file=sys.stderr
            )
            continue

    # Summary of inbox processing results
    if successful_decryptions > 0:
        print(
            f"[INBOX] Successfully decrypted {successful_decryptions}/{len(messages)} message(s)",
            file=sys.stderr,
        )
    else:
        print("[INBOX] No messages were successfully decrypted", file=sys.stderr)
