import os, json

from client.utils.helpers import b64e, b64d
from client.api.api import register_user
from client.crypto.kem import generate_kem_keypair
from client.crypto.signature import generate_signature_keypair

USER_KEYS_FILE = "user_keys.json"


def load_all_local_keys() -> dict:
    if os.path.exists(USER_KEYS_FILE):
        with open(USER_KEYS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_all_local_keys(keys_data: dict):
    with open(USER_KEYS_FILE, "w") as f:
        json.dump(keys_data, f, indent=2)


def save_local_keys(
    username: str, kems: tuple[bytes, bytes], sigs: tuple[bytes, bytes]
) -> None:
    if not username:
        raise ValueError("Username cannot be empty.")
    if not kems or not sigs:
        raise ValueError("KEM and Signature keys cannot be empty.")

    # Unpack keys
    kem_pub, kem_priv = kems
    sig_pub, sig_priv = sigs

    # Validate key types
    if not isinstance(kem_pub, bytes) or not isinstance(kem_priv, bytes):
        raise ValueError("KEM keys must be bytes")
    if not isinstance(sig_pub, bytes) or not isinstance(sig_priv, bytes):
        raise ValueError("Signature keys must be bytes")

    # Load existing keys
    keys = load_all_local_keys()
    if username in keys:
        print(f"[!] Overwriting existing keys for '{username}'")
    else:
        print(f"[+] Saving new keys for '{username}'")

    # Save keys
    keys[username] = {
        "kem_sk": b64e(kem_priv),
        "kem_pk": b64e(kem_pub),
        "sig_sk": b64e(sig_priv),
        "sig_pk": b64e(sig_pub),
    }

    # Save all keys to file
    save_all_local_keys(keys)


def get_local_keypair(username: str, field: str = "kem") -> tuple[bytes, bytes]:
    if field not in ["kem", "sig"]:
        raise ValueError("Invalid field. Expected 'kem' or 'sig'.")
    if not username:
        raise ValueError("Username cannot be empty.")
    if not os.path.exists(USER_KEYS_FILE):
        raise FileNotFoundError(
            f"No keys found. Please register user '{username}' first."
        )

    # Load all keys
    keys = load_all_local_keys()
    if not keys:
        raise FileNotFoundError("No keys found. Please register a user first.")
    if username not in keys:
        raise FileNotFoundError(f"No keys found for user '{username}'.")

    # Get user keys
    user_keys = keys.get(username)
    if not user_keys:
        raise FileNotFoundError(f"No keys found for user '{username}'.")

    # Decode keys from base64 & return tuple according to field
    return b64d(user_keys[f"{field}_sk"]), b64d(user_keys[f"{field}_pk"])


def login_or_register(username: str):
    if not username:
        raise ValueError("Username cannot be empty.")

    print(f"[+] Attempting to register or login user '{username}'...")

    # Load existing keys if any
    keys = load_all_local_keys()
    if username in keys:
        print(f"[✔] Found existing keys for '{username}'")
    else:
        print(f"[!] No existing keys found for '{username}'")

        # Generate KEM & Signature keypairs
        print("[+] Generating new KEM and Signature keypairs.*7=..")
        kem_keys = generate_kem_keypair()
        sig_keys = generate_signature_keypair()
        if not kem_keys or not sig_keys:
            raise RuntimeError("Failed to generate KEM or Signature keypairs.")

        # Save locally
        print("[+] Saving keys locally...")
        save_local_keys(username, kem_keys, sig_keys)
        print("[✔] Local KEM and SIG keypairs generated and saved.")

        # Register public keys with server
        print("[+] Registering public keys with server...")
        register_user(username, kem_keys[0], sig_keys[0])
        print("[✔] Public keys registered with server.")

    return {
        "kem": get_local_keypair(username, field="kem"),
        "sig": get_local_keypair(username, field="sig"),
    }
