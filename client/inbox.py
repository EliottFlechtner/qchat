import oqs
from api import fetch_inbox
from crypto import decapsulate_key, decrypt_message
from login import get_local_keypair
from utils import b64d


def fetch_and_decrypt_inbox(username):
    private_key = get_local_keypair(username)[0]
    if not private_key:
        print("User not registered or keys not found.")
        return

    messages = fetch_inbox(username)
    if not messages:
        print("[Inbox empty]")
        return

    for msg in messages:
        ciphertext = b64d(msg["ciphertext"])
        nonce = b64d(msg["nonce"])
        encapsulated_key = b64d(msg["encapsulated_key"])

        try:
            shared_secret = decapsulate_key(encapsulated_key, private_key)
            plain = decrypt_message(shared_secret, nonce, ciphertext)
            print(f"[{msg['sender']}] ➤ {plain}")
        except Exception as e:
            print(f"❌ Error decrypting message: {e}")
