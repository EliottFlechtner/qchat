import os
import json
from typing import Dict, Tuple, Any

from client.utils.helpers import b64e, b64d
from client.api import register_user
from client.crypto.kem import generate_kem_keypair
from client.crypto.signature import generate_signature_keypair

# Local file to store user cryptographic keys in JSON format
USER_KEYS_FILE = "user_keys.json"


def load_all_local_keys() -> Dict[str, Any]:
    """Loads all user cryptographic keys from the local JSON file.

    This function reads the keys file and returns all stored user keys as a dictionary.
    If the file doesn't exist, it returns an empty dictionary. The keys are stored
    in base64 format for JSON compatibility.

    File format:
    {
        "username1": {
            "kem_sk": "base64_encoded_kem_private_key",
            "kem_pk": "base64_encoded_kem_public_key",
            "sig_sk": "base64_encoded_signature_private_key",
            "sig_pk": "base64_encoded_signature_public_key"
        },
        "username2": { ... }
    }

    :return: Dictionary containing all user keys, or empty dict if file doesn't exist.
    :raises RuntimeError: If file exists but cannot be read or parsed.
    """
    try:
        if os.path.exists(USER_KEYS_FILE):
            with open(USER_KEYS_FILE, "r", encoding="utf-8") as f:
                keys_data = json.load(f)
                # Validate that loaded data is a dictionary
                if not isinstance(keys_data, dict):
                    raise ValueError("Keys file contains invalid data format")
                return keys_data
        return {}
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse keys file '{USER_KEYS_FILE}': {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to load keys file '{USER_KEYS_FILE}': {e}")


def save_all_local_keys(keys_data: Dict[str, Any]) -> None:
    """Saves all user cryptographic keys to the local JSON file.

    This function writes the complete keys dictionary to the JSON file with proper
    formatting. It overwrites the entire file with the new data.

    :param keys_data: Dictionary containing all user keys to save.
    :raises TypeError: If keys_data is not a dictionary.
    :raises RuntimeError: If file cannot be written.
    """
    # Validate input parameter
    if not isinstance(keys_data, dict):
        raise TypeError("Keys data must be a dictionary")

    try:
        # Write keys to file with indentation for readability
        with open(USER_KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(keys_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise RuntimeError(f"Failed to save keys to file '{USER_KEYS_FILE}': {e}")


def save_local_keys(
    username: str, kems: Tuple[bytes, bytes], sigs: Tuple[bytes, bytes]
) -> None:
    """Saves cryptographic keys for a specific user to the local storage.

    This function stores both KEM (Key Encapsulation Mechanism) and digital signature
    keypairs for a user. The keys are base64-encoded for JSON storage compatibility.

    Key storage process:
    1. Validate all input parameters
    2. Load existing keys from file
    3. Encode keys to base64 format
    4. Store keys in the dictionary structure
    5. Save updated dictionary back to file

    :param username: The username to associate with these keys.
    :param kems: Tuple of (kem_public_key, kem_private_key) as bytes.
    :param sigs: Tuple of (sig_public_key, sig_private_key) as bytes.
    :raises TypeError: If parameters have wrong types.
    :raises ValueError: If username is empty or keys are invalid.
    :raises RuntimeError: If key saving fails.
    """
    # Validate username parameter
    if not isinstance(username, str):
        raise TypeError("Username must be a string")
    if not username or not username.strip():
        raise ValueError("Username cannot be empty")

    # Validate KEM keys parameter
    if not isinstance(kems, tuple) or len(kems) != 2:
        raise ValueError("KEM keys must be a tuple of 2 elements")
    if not kems[0] or not kems[1]:
        raise ValueError("KEM keys cannot be empty")

    # Validate signature keys parameter
    if not isinstance(sigs, tuple) or len(sigs) != 2:
        raise ValueError("Signature keys must be a tuple of 2 elements")
    if not sigs[0] or not sigs[1]:
        raise ValueError("Signature keys cannot be empty")

    # Unpack keys for clarity
    kem_pub, kem_priv = kems
    sig_pub, sig_priv = sigs

    # Validate key types - all must be bytes
    if not isinstance(kem_pub, bytes) or not isinstance(kem_priv, bytes):
        raise TypeError("KEM keys must be bytes")
    if not isinstance(sig_pub, bytes) or not isinstance(sig_priv, bytes):
        raise TypeError("Signature keys must be bytes")

    try:
        # Load existing keys from file
        keys = load_all_local_keys()

        # Warn if overwriting existing keys
        if username in keys:
            print(f"[!] Overwriting existing keys for '{username}'")
        else:
            print(f"[+] Saving new keys for '{username}'")

        # Encode keys to base64 and store in dictionary
        keys[username] = {
            "kem_sk": b64e(kem_priv),  # KEM private key
            "kem_pk": b64e(kem_pub),  # KEM public key
            "sig_sk": b64e(sig_priv),  # Signature private key
            "sig_pk": b64e(sig_pub),  # Signature public key
        }

        # Save updated keys dictionary to file
        save_all_local_keys(keys)
        print(f"[✔] Keys saved successfully for '{username}'")

    except Exception as e:
        raise RuntimeError(f"Failed to save keys for '{username}': {e}")


def get_local_keypair(username: str, field: str = "kem") -> Tuple[bytes, bytes]:
    """Retrieves a specific keypair for a user from local storage.

    This function loads and decodes cryptographic keys for a specific user and key type.
    The keys are returned as raw bytes after base64 decoding from the JSON storage.

    Key retrieval process:
    1. Validate input parameters
    2. Check if keys file exists
    3. Load and verify user keys exist
    4. Decode base64 keys back to bytes
    5. Return the requested keypair

    :param username: The username whose keys to retrieve.
    :param field: The key type to retrieve ("kem" or "sig").
    :return: Tuple of (private_key, public_key) as bytes.
    :raises TypeError: If parameters have wrong types.
    :raises ValueError: If username is empty or field is invalid.
    :raises FileNotFoundError: If keys file or user keys don't exist.
    :raises RuntimeError: If key retrieval fails.
    """
    # Validate field parameter
    if not isinstance(field, str):
        raise TypeError("Field must be a string")
    if field not in ["kem", "sig"]:
        raise ValueError("Invalid field. Expected 'kem' or 'sig'")

    # Validate username parameter
    if not isinstance(username, str):
        raise TypeError("Username must be a string")
    if not username or not username.strip():
        raise ValueError("Username cannot be empty")

    # Check if keys file exists
    if not os.path.exists(USER_KEYS_FILE):
        raise FileNotFoundError(
            f"No keys found. Please register user '{username}' first."
        )

    try:
        # Load all keys from file
        keys = load_all_local_keys()
        if not keys:
            raise FileNotFoundError("No keys found. Please register a user first.")

        # Check if user has keys
        if username not in keys:
            raise FileNotFoundError(f"No keys found for user '{username}'.")

        # Get user-specific keys
        user_keys = keys.get(username)
        if not user_keys or not isinstance(user_keys, dict):
            raise FileNotFoundError(f"Invalid keys data for user '{username}'.")

        # Validate required key fields exist
        private_key_field = f"{field}_sk"
        public_key_field = f"{field}_pk"

        if private_key_field not in user_keys or public_key_field not in user_keys:
            raise FileNotFoundError(f"Incomplete {field} keys for user '{username}'.")

        # Decode keys from base64 and return as tuple (private_key, public_key)
        private_key = b64d(user_keys[private_key_field])
        public_key = b64d(user_keys[public_key_field])

        # Validate decoded keys are not empty
        if not private_key or not public_key:
            raise RuntimeError(f"Decoded {field} keys are empty for user '{username}'")

        return private_key, public_key

    except Exception as e:
        if isinstance(e, (FileNotFoundError, RuntimeError)):
            raise  # Re-raise the specific exceptions
        raise RuntimeError(f"Failed to retrieve {field} keys for '{username}': {e}")


def login_or_register(username: str) -> Dict[str, Tuple[bytes, bytes]]:
    """Handles user login or registration by managing cryptographic keys.

    This function implements the complete user onboarding workflow:
    - If user already has local keys, loads them (login)
    - If user is new, generates keys and registers with server (registration)

    Registration workflow:
    1. Generate post-quantum KEM keypair for encryption
    2. Generate post-quantum signature keypair for authentication
    3. Save both keypairs locally for future use
    4. Register public keys with the server
    5. Return all keypairs for immediate use

    Login workflow:
    1. Load existing keys from local storage
    2. Return all keypairs for immediate use

    :param username: The username to login or register.
    :return: Dictionary containing both keypairs: {"kem": (priv, pub), "sig": (priv, pub)}.
    :raises TypeError: If username is not a string.
    :raises ValueError: If username is empty.
    :raises RuntimeError: If key generation, storage, or server registration fails.
    """
    # Validate username parameter
    if not isinstance(username, str):
        raise TypeError("Username must be a string")
    if not username or not username.strip():
        raise ValueError("Username cannot be empty")

    print(f"[+] Attempting to register or login user '{username}'...")

    try:
        # Load existing keys if any
        keys = load_all_local_keys()

        if username in keys:
            # User already exists - login workflow
            print(f"[✔] Found existing keys for '{username}'")
            print(f"[+] Loading existing keypairs for '{username}'...")

        else:
            # New user - registration workflow
            print(f"[!] No existing keys found for '{username}'")
            print("[+] Starting registration process...")

            # Generate post-quantum cryptographic keypairs
            print("[+] Generating new KEM and Signature keypairs...")
            try:
                kem_keys = generate_kem_keypair()
                sig_keys = generate_signature_keypair()

                # Validate generated keys
                if not kem_keys or len(kem_keys) != 2:
                    raise RuntimeError("Failed to generate valid KEM keypair")
                if not sig_keys or len(sig_keys) != 2:
                    raise RuntimeError("Failed to generate valid signature keypair")

            except Exception as e:
                raise RuntimeError(f"Keypair generation failed: {e}")

            # Save keys locally for persistent storage
            print("[+] Saving keys locally...")
            try:
                save_local_keys(username, kem_keys, sig_keys)
                print("[✔] Local KEM and signature keypairs generated and saved")
            except Exception as e:
                raise RuntimeError(f"Failed to save keys locally: {e}")

            # Register public keys with the server
            print("[+] Registering public keys with server...")
            try:
                # Extract public keys for server registration
                kem_public_key = kem_keys[0]  # KEM public key
                sig_public_key = sig_keys[0]  # Signature public key

                register_user(username, kem_public_key, sig_public_key)
                print("[✔] Public keys registered with server successfully")
            except Exception as e:
                raise RuntimeError(f"Failed to register with server: {e}")

        # Load and return all keypairs for immediate use
        try:
            kem_keypair = get_local_keypair(username, field="kem")
            sig_keypair = get_local_keypair(username, field="sig")

            return {
                "kem": kem_keypair,  # (kem_private_key, kem_public_key)
                "sig": sig_keypair,  # (sig_private_key, sig_public_key)
            }
        except Exception as e:
            raise RuntimeError(f"Failed to load keypairs after registration: {e}")

    except Exception as e:
        if isinstance(e, (TypeError, ValueError, RuntimeError)):
            raise  # Re-raise the specific exceptions
        raise RuntimeError(f"Login/registration failed for '{username}': {e}")
