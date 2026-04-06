import oqs

from client.crypto.aes256 import derive_aes_key, encrypt_with_aes, decrypt_with_aes
from client.config.settings import client_settings


def generate_kem_keypair() -> tuple[bytes, bytes]:
    """Generates a KEM keypair using the configured algorithm.

    This function uses the OQS library to generate a keypair for the KEM algorithm
    specified in the client configuration. The algorithm is configurable via
    environment variables or the default settings.

    :return: A tuple containing the public key and the private key.
    :raises RuntimeError: If the KEM algorithm is not supported or if key generation fails.
    :raises TypeError: If the KEM algorithm is not of type str.
    :raises ValueError: If the KEM algorithm is an empty string.
    """
    # Get algorithm from configuration
    kem_algorithm = client_settings.kem_algorithm

    # Validate algorithm parameter
    if not isinstance(kem_algorithm, str):
        raise TypeError("KEM algorithm must be a string")
    if not kem_algorithm:
        raise ValueError("KEM algorithm must not be an empty string")

    try:
        # Generate keypair using OQS library context manager for proper cleanup
        with oqs.KeyEncapsulation(kem_algorithm) as kem:
            # Returns public key, stores private key in kem instance
            pub = kem.generate_keypair()
            # Extract private key from the KEM instance
            priv = kem.export_secret_key()
    except Exception as e:
        raise RuntimeError(f"KEM keypair generation failed: {e}")

    return pub, priv


def encapsulate_key(kem_pk: bytes) -> tuple[bytes, bytes]:
    """Encapsulates a shared secret using the provided public key.

    This function uses the OQS library to encapsulate a shared secret with the given public key.
    The encapsulation process generates a random shared secret and encrypts it with the public key,
    producing both the encrypted secret (ciphertext) and the original shared secret.

    Security properties:
    - TODO Forward secrecy: Each encapsulation generates a new random shared secret
    - Post-quantum security: Uses Kyber512 lattice-based cryptography
    - IND-CCA2 security: Secure against adaptive chosen-ciphertext attacks

    :param kem_pk: The public key to use for encapsulation (must be valid Kyber512 public key).
    :return: A tuple containing the ciphertext and the shared secret.
    :raises TypeError: If the public key is not of type bytes.
    :raises ValueError: If the public key is not a non-empty bytes object.
    :raises RuntimeError: If key encapsulation fails (invalid public key or library error).
    """
    # Validate public key parameter
    if not isinstance(kem_pk, bytes):
        raise TypeError("Public key must be bytes")
    if not kem_pk or len(kem_pk) == 0:
        raise ValueError("Public key must be a non-empty bytes object")

    try:
        # Get algorithm from configuration
        kem_algorithm = client_settings.kem_algorithm
        # Perform key encapsulation using the recipient's public key
        with oqs.KeyEncapsulation(kem_algorithm) as kem:
            # Generate random shared secret and encapsulate it with the public key
            # This produces both the ciphertext (for transmission) and shared secret (for local use)
            ciphertext_kem, shared_secret = kem.encap_secret(kem_pk)
    except Exception as e:
        raise RuntimeError(f"Key encapsulation failed: {e}")

    return ciphertext_kem, shared_secret


def decapsulate_key(encapsulated: bytes, kem_sk: bytes) -> bytes:
    """Decapsulates a shared secret using the provided private key and encapsulated data.

    This function uses the private key to decrypt the encapsulated shared secret,
    recovering the original shared secret that was generated during encapsulation.
    The recovered shared secret should be identical to the one generated during encapsulation.

    Security properties:
    - Key consistency: Always recovers the same shared secret from the same ciphertext
    - Private key protection: Requires the correct private key for decapsulation
    - Tamper detection: Invalid ciphertext will cause decapsulation to fail

    :param encapsulated: The encapsulated ciphertext containing the shared secret.
    :param kem_sk: The private key corresponding to the public key used for encapsulation.
    :return: The decapsulated shared secret as bytes (32 bytes for Kyber512).
    :raises TypeError: If encapsulated data or private key is not bytes.
    :raises ValueError: If encapsulated data or private key is empty.
    :raises RuntimeError: If decapsulation fails (invalid ciphertext or private key).
    """
    # Validate encapsulated data parameter
    if not isinstance(encapsulated, bytes):
        raise TypeError("Encapsulated data must be bytes")
    if not encapsulated or len(encapsulated) == 0:
        raise ValueError("Encapsulated data must be a non-empty bytes object")

    # Validate private key parameter
    if not isinstance(kem_sk, bytes):
        raise TypeError("Private key must be bytes")
    if not kem_sk or len(kem_sk) == 0:
        raise ValueError("Private key must be a non-empty bytes object")

    try:
        # Get algorithm from configuration
        kem_algorithm = client_settings.kem_algorithm
        # Use private key to decrypt the encapsulated shared secret
        with oqs.KeyEncapsulation(kem_algorithm, secret_key=kem_sk) as kem:
            # Recover the original shared secret from the ciphertext
            shared_secret = kem.decap_secret(encapsulated)
    except Exception as e:
        raise RuntimeError(f"Decapsulation failed: {e}")

    return shared_secret


def encrypt_message(shared_secret: bytes, plaintext: str):
    """Encrypts a plaintext message using AES-GCM with a key derived from the shared secret.

    This is a high-level function that combines KEM shared secret derivation with AES encryption.
    The shared secret is processed through HKDF to produce a suitable AES-256 key, then the
    message is encrypted using AES-GCM for authenticated encryption.

    Encryption process:
    1. Validate input parameters for security
    2. Derive AES-256 key from KEM shared secret using HKDF
    3. Encrypt plaintext with AES-GCM (provides confidentiality + authenticity)
    4. Return nonce and ciphertext for transmission

    :param shared_secret: The shared secret obtained from KEM encapsulation/decapsulation.
    :param plaintext: The message to encrypt as a string.
    :return: A tuple containing (nonce, ciphertext) - both needed for decryption.
    :raises TypeError: If shared secret is not bytes or plaintext is not string.
    :raises ValueError: If shared secret is not 32 bytes or plaintext is empty.
    :raises RuntimeError: If AES encryption fails.
    """
    # Validate shared secret parameter - Kyber512 produces 32-byte shared secrets
    if not isinstance(shared_secret, bytes):
        raise TypeError("Shared secret must be bytes")
    if not shared_secret or len(shared_secret) != 32:
        raise ValueError("Shared secret must be 32 bytes long (256 bits)")

    # Validate plaintext parameter
    if not isinstance(plaintext, str):
        raise TypeError("Plaintext must be a string")
    if not plaintext:
        raise ValueError("Plaintext must be a non-empty string")

    try:
        # Derive AES-256 key from the KEM shared secret using HKDF
        aes_key = derive_aes_key(shared_secret)

        # Encrypt the plaintext message using AES-GCM authenticated encryption
        # Returns (nonce, ciphertext) tuple
        return encrypt_with_aes(aes_key, plaintext)
    except Exception as e:
        raise RuntimeError(f"Message encryption failed: {e}")


def decrypt_message(shared_secret: bytes, nonce: bytes, ciphertext: bytes):
    """Decrypts a ciphertext message using AES-GCM with a key derived from the shared secret.

    This is a high-level function that combines KEM shared secret derivation with AES decryption.
    The shared secret must be the same one used for encryption to successfully decrypt the message.
    AES-GCM provides authenticated encryption, so this function also verifies message authenticity.

    Decryption process:
    1. Validate all input parameters for security
    2. Derive the same AES-256 key from KEM shared secret using HKDF
    3. Decrypt and authenticate ciphertext with AES-GCM
    4. Return the plaintext message as a string

    :param shared_secret: The shared secret obtained from KEM encapsulation/decapsulation.
    :param nonce: The nonce/IV used during encryption (required for AES-GCM).
    :param ciphertext: The encrypted message data to decrypt.
    :return: Decrypted plaintext message as string.
    :raises TypeError: If any parameter has wrong type.
    :raises ValueError: If shared secret is not 32 bytes, nonce is not 12 bytes, or ciphertext is empty.
    :raises RuntimeError: If AES decryption fails.
    :raises cryptography.exceptions.InvalidTag: If authentication fails (wrong key or tampered data).
    """
    # Validate shared secret parameter - must match the one used for encryption
    if not isinstance(shared_secret, bytes):
        raise TypeError("Shared secret must be bytes")
    if not shared_secret or len(shared_secret) != 32:
        raise ValueError("Shared secret must be 32 bytes long (256 bits)")

    # Validate nonce parameter - must be the same nonce used during encryption
    if not isinstance(nonce, bytes):
        raise TypeError("Nonce must be bytes")
    if not nonce or len(nonce) != 12:
        raise ValueError("Nonce must be 12 bytes long (96 bits)")

    # Validate ciphertext parameter
    if not isinstance(ciphertext, bytes):
        raise TypeError("Ciphertext must be bytes")
    if not ciphertext:
        raise ValueError("Ciphertext must be a non-empty bytes object")

    try:
        # Derive the same AES-256 key from the KEM shared secret
        aes_key = derive_aes_key(shared_secret)

        # Decrypt and authenticate the ciphertext using AES-GCM
        # Will raise InvalidTag if authentication fails
        return decrypt_with_aes(aes_key, nonce, ciphertext)
    except Exception as e:
        raise RuntimeError(f"Message decryption failed: {e}")
