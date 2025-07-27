import oqs, os, requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from client_helpers import *


def get_public_key(username: str) -> bytes:
    res = requests.get(f"{API_URL}/pubkey/{username}")
    if res.status_code != 200:
        raise Exception("User not found")
    b64key = res.json()["public_key"]
    return b64d(b64key)


def send_encrypted_message(sender: str, recipient: str, message: str):
    recipient_pubkey = get_public_key(recipient)

    with oqs.KeyEncapsulation("Kyber512") as kem:
        ciphertext_kem, shared_secret = kem.encap_secret(recipient_pubkey)

    aesgcm = AESGCM(shared_secret[:16])  # AES-128 key
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, message.encode(), None)

    print(f"Shared secret (hex): {shared_secret.hex()}")
    print(f"Nonce (hex): {nonce.hex()}")
    print(f"Ciphertext (hex): {ciphertext.hex()}")

    payload = {
        "sender": sender,
        "recipient": recipient,
        "ciphertext": b64e(ciphertext),
        "nonce": b64e(nonce),
        "encapsulated_key": b64e(ciphertext_kem),
    }

    res = requests.post(f"{API_URL}/send", json=payload)
    print(res.json())


# # Example usage
# if __name__ == "__main__":
#     send_encrypted_message(
#         sender="alice", recipient="bob", message="Hello from Alice to Bob!"
#     )
