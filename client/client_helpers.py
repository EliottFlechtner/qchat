import os, base64, json

API_URL = "http://127.0.0.1:8000"
KEYS_FILE = "user_keys.json"


def load_user_keys():
    if not os.path.exists(KEYS_FILE):
        return {}

    with open(KEYS_FILE, "r") as f:
        data = json.load(f)

    # Decode base64 strings back to bytes
    user_keys = {}
    for username, keys in data.items():
        user_keys[username] = {
            "public_key": b64d(keys["public_key"]),
            "private_key": b64d(keys["private_key"]),
        }
    return user_keys


def save_user_keys(user_keys):
    # Encode bytes to base64 strings before saving JSON
    data = {}
    for username, keys in user_keys.items():
        data[username] = {
            "public_key": b64e(keys["public_key"]),
            "private_key": b64e(keys["private_key"]),
        }

    with open(KEYS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def b64e(data: bytes) -> str:
    return base64.b64encode(data).decode()


def b64d(data: str) -> bytes:
    return base64.b64decode(data.encode())
