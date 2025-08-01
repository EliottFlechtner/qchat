import sys
from client.api.api import get_inbox, get_public_key
from client.crypto.kem import decapsulate_key, decrypt_message
from client.services.login import get_local_keypair
from client.crypto.utils import b64d, b64e
from client.crypto.signature import verify_signature


def fetch_and_decrypt_inbox(username):
    if not username:
        raise ValueError("Username cannot be empty.")

    # Fetch the inbox messages
    messages = get_inbox(username)
    if not messages:
        print("[Inbox empty]")
        return

    # Decrypt each message
    for msg in messages:
        try:
            # Decode all required fields from base64
            sender = msg["sender"]
            ciphertext = b64d(msg["ciphertext"])
            nonce = b64d(msg["nonce"])
            encapsulated_key = b64d(msg["encapsulated_key"])
            signature = b64d(msg["signature"])

            # Get sender's public key for signature verification
            sender_sig_pk = get_public_key(sender, field="sig_pk")
            if not sender_sig_pk:
                print(f"[ERROR] Could not get public key for {sender}", file=sys.stderr)
                continue

            # 1. Verify the signature
            if not verify_signature(sender_sig_pk, ciphertext, signature):
                print(
                    f"[WARNING] Signature invalid from {sender}, skipping.",
                    file=sys.stderr,
                )
                continue

            # Get the recipient's private key
            kem_sk = get_local_keypair(username, field="kem")[0]  # KEM private key
            if not kem_sk:
                raise ValueError(f"No KEM private key found for user '{username}'.")

            # 2. Decapsulate the shared secret (decrypt the message)
            shared_secret = decapsulate_key(encapsulated_key, kem_sk)
            plain = decrypt_message(shared_secret, nonce, ciphertext)

            print(
                f"[CLIENT] Message decrypted successfully from {sender}.",
                file=sys.stderr,
            )

            # 3. Print the decrypted message to chat (console)
            print(f"[{sender}] ➤ {plain}")
        except Exception as e:
            print(f"[ERROR] Error decrypting message: {e}", file=sys.stderr)
