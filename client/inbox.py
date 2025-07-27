import requests, base64, oqs
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from client_helpers import *

KEYS_FILE = "user_keys.json"
USER_KEYS = load_user_keys()


def register_local_user(username: str):
    if username in USER_KEYS:
        print(f"[!] User {username} already registered locally.")
        return

    with oqs.KeyEncapsulation("Kyber512") as kem:
        public_key = kem.generate_keypair()
        private_key = kem.export_secret_key()  # Save for decapsulation
        b64_pub = base64.b64encode(public_key).decode()

        USER_KEYS[username] = {"public_key": public_key, "private_key": private_key}

        res = requests.post(
            f"{API_URL}/register", json={"username": username, "public_key": b64_pub}
        )
        print(f"[+] Registered {username}: {res.json()}")

    save_user_keys(USER_KEYS)


def fetch_and_decrypt_inbox(username: str):
    keypair = USER_KEYS.get(username)
    if not keypair:
        print(f"No keys for user {username}. Did you register them?")
        return

    res = requests.get(f"{API_URL}/inbox/{username}")
    print(f"[+] Fetching inbox for {username}...")
    print(f"Response: {res.status_code} {res.reason}")

    if res.status_code != 200:
        print("Inbox error:", res.text)
        return

    messages = res.json()
    if not messages:
        print("[Inbox empty]")
        return

    with oqs.KeyEncapsulation("Kyber512", secret_key=keypair["private_key"]) as kem:
        for msg in messages:
            ciphertext = b64d(msg["ciphertext"])
            nonce = b64d(msg["nonce"])
            encapsulated_key = b64d(msg["encapsulated_key"])

            try:
                shared_secret = kem.decap_secret(encapsulated_key)
                aesgcm = AESGCM(shared_secret[:16])  # AES-128

                print(f"Shared secret (hex): {shared_secret.hex()}")
                print(f"Nonce (hex): {nonce.hex()}")
                print(f"Ciphertext (hex): {ciphertext.hex()}")

                plaintext = aesgcm.decrypt(nonce, ciphertext, None)
                print(f"[{msg['sender']}] ➤ {plaintext.decode()}")
            except Exception as e:
                print("❌ Failed to decrypt message:", e)

    print("[+] Inbox processed successfully")


# # Example run:
# if __name__ == "__main__":
#     usernames = ["alice", "bob"]
#     for username in usernames:
#         if username not in USER_KEYS:
#             print(f"[!] User {username} not registered locally. Registering now...")
#             register_local_user(username)  # Will skip if already registered
#         else:
#             print(f"[+] User {username} already registered. Fetching inbox...")
#             fetch_and_decrypt_inbox(username)
