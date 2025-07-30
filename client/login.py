import os
import json
from oqs import KeyEncapsulation
from utils import b64e, b64d
from api import register_user

USER_KEYS_FILE = "user_keys.json"


def load_all_local_keys():
    if os.path.exists(USER_KEYS_FILE):
        with open(USER_KEYS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_all_local_keys(keys_data):
    with open(USER_KEYS_FILE, "w") as f:
        json.dump(keys_data, f, indent=2)


def save_local_key(username, private_key, public_key):
    keys = load_all_local_keys()
    keys[username] = {
        "private_key": b64e(private_key),
        "public_key": b64e(public_key),
    }
    save_all_local_keys(keys)


def key_exists_locally(username):
    keys = load_all_local_keys()
    return username in keys


def get_local_keypair(username):
    """Retrieve the local keypair for a given username.
    Returns (private_key, public_key) if found, else (None, None).
    """

    keys = load_all_local_keys()
    user_keys = keys.get(username)
    if not user_keys:
        return None, None
    private_key = b64d(user_keys["private_key"])
    public_key = b64d(user_keys["public_key"])
    return private_key, public_key


def login_or_register(username):
    if key_exists_locally(username):
        print(f"[✔] Found existing keypair for '{username}'")
        return get_local_keypair(username)

    print(f"[+] No keys found for '{username}'. Registering new user...")

    with KeyEncapsulation("Kyber512") as kem:
        public_key = kem.generate_keypair()
        private_key = kem.export_secret_key()

        # Save locally
        save_local_key(username, private_key, public_key)
        print("[✔] Local keypair generated and saved.")

        # Register with server
        register_user(username, public_key)
        print("[✔] Public key registered with server.")

        return private_key, public_key
