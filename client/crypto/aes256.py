import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


def derive_aes_key(shared_secret: bytes) -> bytes:
    """Derives a 256-bit AES key from the shared secret using HKDF.

    HKDF (HMAC-based Key Derivation Function) is a cryptographically secure key derivation
    function that expands and extracts randomness from the input key material. This function
    converts the raw shared secret from KEM into a suitable AES-256 key.

    The derivation process:
    1. Uses SHA-256 as the underlying hash function
    2. Applies application-specific info string for domain separation
    3. Outputs exactly 32 bytes for AES-256 compatibility

    :param shared_secret: The shared secret from KEM (must be exactly 32 bytes).
    :return: A 32-byte AES-256 key suitable for encryption.
    :raises ValueError: If the shared secret is not 32 bytes long or is empty.
    :raises TypeError: If the shared secret is not of type bytes.
    """
    # Validate input parameters - shared secret must be exactly 32 bytes for security
    if not isinstance(shared_secret, bytes):
        raise TypeError("Shared secret must be bytes")
    if not shared_secret or len(shared_secret) != 32:
        raise ValueError("Shared secret must be 32 bytes long (256 bits)")

    # Create HKDF instance with cryptographic parameters
    # - SHA-256: Provides 256-bit security level, resistant to quantum attacks via Grover's algorithm
    # - Length 32: Output 256-bit key for AES-256
    # - Salt None: Using no salt for simplicity (could be improved with per-session salts)
    # - Info string: Domain separation to prevent key reuse across different contexts
    hkdf = HKDF(
        algorithm=hashes.SHA256(),  # Cryptographic hash function
        length=32,  # Output key length in bytes (256 bits for AES-256)
        salt=None,  # TODO: Consider using unique salt per session/user pair
        info=b"pqchat-aes256-key",  # Application-specific context info for domain separation
        backend=default_backend(),  # Use system's default cryptographic backend
    )

    # Derive the key from the shared secret
    # This transforms the raw KEM output into a properly formatted AES key
    return hkdf.derive(shared_secret)


def encrypt_with_aes(key: bytes, plaintext: str) -> tuple[bytes, bytes]:
    """Encrypts plaintext using AES-256-GCM with the provided key.

    AES-GCM (Galois/Counter Mode) provides both confidentiality and authenticity:
    - Confidentiality: The plaintext is encrypted and unreadable without the key
    - Authenticity: The ciphertext includes an authentication tag to detect tampering

    The encryption process:
    1. Encrypt plaintext using AES-256 in GCM mode
    2. Generate a random 96-bit nonce (unique per encryption)
    3. Return both nonce and authenticated ciphertext

    :param key: The AES-256 key (must be exactly 32 bytes).
    :param plaintext: The plaintext message to encrypt.
    :return: A tuple containing (nonce, ciphertext) where nonce is 12 bytes.
    :raises ValueError: If key is not 32 bytes or plaintext is empty.
    :raises TypeError: If key is not bytes or plaintext is not string.
    """
    # Validate encryption key - must be exactly 32 bytes for AES-256
    if not isinstance(key, bytes):
        raise TypeError("Key must be bytes")
    if not key or len(key) != 32:
        raise ValueError("Key must be 32 bytes long (256 bits)")

    # Validate plaintext input
    if not isinstance(plaintext, str):
        raise TypeError("Plaintext must be a string")
    if not plaintext:
        raise ValueError("Plaintext must be a non-empty string")

    # Create AES-GCM cipher instance with the provided key
    aesgcm = AESGCM(key)

    # Generate cryptographically secure random nonce
    # 12 bytes (96 bits) is the recommended nonce size for GCM mode
    # Each nonce must be unique for the same key to maintain security
    nonce = os.urandom(12)

    # Encrypt the plaintext message
    # - Convert string to bytes using UTF-8 encoding
    # - No associated data (AAD) is used in this implementation
    # - Returns ciphertext with embedded authentication tag
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)

    # Validate output before returning (defensive programming)
    if not isinstance(nonce, bytes) or len(nonce) != 12:
        raise ValueError("Nonce must be 12 bytes long (96 bits)")
    if not isinstance(ciphertext, bytes):
        raise TypeError("Ciphertext must be bytes")

    # Return nonce and ciphertext - both needed for decryption
    return nonce, ciphertext


def decrypt_with_aes(key: bytes, nonce: bytes, ciphertext: bytes) -> str:
    """Decrypts ciphertext using AES-256-GCM with the provided key and nonce.

    AES-GCM decryption verifies both the ciphertext integrity and authenticity:
    - Decrypts the ciphertext back to plaintext
    - Verifies the authentication tag to detect any tampering
    - Throws an exception if authentication fails

    The decryption process:
    1. Validate all input parameters
    2. Create AES-GCM cipher with the same key used for encryption
    3. Decrypt and authenticate using the original nonce
    4. Return the decrypted plaintext as a string

    :param key: The AES-256 key used for encryption (must be 32 bytes).
    :param nonce: The nonce used during encryption (must be 12 bytes).
    :param ciphertext: The authenticated ciphertext to decrypt.
    :return: The decrypted plaintext as a UTF-8 string.
    :raises ValueError: If key/nonce have wrong length or ciphertext is empty.
    :raises TypeError: If any parameter has wrong type.
    :raises cryptography.exceptions.InvalidTag: If authentication fails (wrong key or tampered data).
    """
    # Validate decryption key - must match the encryption key exactly
    if not isinstance(key, bytes):
        raise TypeError("Key must be bytes")
    if not key or len(key) != 32:
        raise ValueError("Key must be 32 bytes long (256 bits)")

    # Validate nonce - must be the same nonce used during encryption
    if not isinstance(nonce, bytes):
        raise TypeError("Nonce must be bytes")
    if not nonce or len(nonce) != 12:
        raise ValueError("Nonce must be 12 bytes long (96 bits)")

    # Validate ciphertext input
    if not isinstance(ciphertext, bytes):
        raise TypeError("Ciphertext must be bytes")
    if not ciphertext:
        raise ValueError("Ciphertext must be a non-empty bytes object")

    # Create AES-GCM cipher instance with the same key used for encryption
    aesgcm = AESGCM(key)

    # Decrypt and authenticate the ciphertext
    # - Uses the same nonce that was used during encryption
    # - Automatically verifies the authentication tag
    # - Raises InvalidTag exception if authentication fails
    # - No associated data (AAD) was used during encryption
    plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, associated_data=None)

    # Convert decrypted bytes back to string using UTF-8 encoding
    # This reverses the encoding done during encryption
    return plaintext_bytes.decode("utf-8")
