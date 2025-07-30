import requests
from utils import b64e, b64d, API_URL


def register_user(username, public_key_bytes):
    req = requests.post(
        f"{API_URL}/register",
        json={
            "username": username,
            "public_key": b64e(public_key_bytes),
        },
    )
    if req.status_code != 200:
        raise Exception("Failed to register user")
    return req.json()


def get_public_key(username: str):
    res = requests.get(f"{API_URL}/pubkey/{username}")
    if res.status_code != 200:
        raise Exception("User not found")
    return b64d(res.json()["public_key"])


def send_message(sender, recipient, ciphertext, nonce, encap_key):
    req = requests.post(
        f"{API_URL}/send",
        json={
            "sender": sender,
            "recipient": recipient,
            "ciphertext": b64e(ciphertext),
            "nonce": b64e(nonce),
            "encapsulated_key": b64e(encap_key),
        },
    )
    if req.status_code != 200:
        raise Exception("Failed to send message")
    return req.json()


def fetch_inbox(username: str):
    res = requests.get(f"{API_URL}/inbox/{username}")
    if res.status_code != 200:
        return []
    return res.json()
