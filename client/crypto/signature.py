from pqcrypto.sign import falcon_512


def generate_signature_keypair() -> tuple[bytes, bytes]:
    """Generates a post-quantum digital signature keypair using Falcon-512.

    Falcon-512 is a post-quantum digital signature algorithm based on lattice cryptography.
    It provides security against both classical and quantum computer attacks while maintaining
    relatively small signature sizes and fast verification times.

    Security properties:
    - Post-quantum security: Resistant to quantum computer attacks
    - EUF-CMA security: Existentially unforgeable under chosen-message attacks
    - NIST standardized: Part of the NIST post-quantum cryptography standard
    - 128-bit security level: Equivalent to AES-128 against classical attacks

    Key characteristics:
    - Public key size: 897 bytes
    - Private key size: 1281 bytes
    - Signature size: ~690 bytes (variable length)
    - Fast verification: Suitable for real-time applications

    :return: A tuple containing (public_key, private_key) where both are bytes.
    :raises RuntimeError: If keypair generation fails due to system or library error.
    """
    try:
        # Generate Falcon-512 keypair using the pqcrypto library
        # This creates a new random keypair with cryptographically secure randomness
        pub, priv = falcon_512.generate_keypair()

        # Validate generated keys have correct sizes (defensive programming)
        if len(pub) != falcon_512.PUBLIC_KEY_SIZE:
            raise RuntimeError(
                f"Generated public key has invalid size: {len(pub)} bytes"
            )
        if len(priv) != falcon_512.SECRET_KEY_SIZE:
            raise RuntimeError(
                f"Generated private key has invalid size: {len(priv)} bytes"
            )

    except Exception as e:
        raise RuntimeError(f"Signature keypair generation failed: {e}")

    return pub, priv


def sign_message(sender_private_key: bytes, message: bytes) -> bytes:
    """Signs a message using Falcon-512 digital signature with the sender's private key.

    This function creates a digital signature that proves the message was created by the
    holder of the corresponding private key and that the message has not been tampered with.
    The signature can be verified by anyone with the corresponding public key.

    Signing process:
    1. Validate the private key format and size
    2. Validate the message input
    3. Generate signature using Falcon-512 algorithm
    4. Return the signature bytes for transmission

    Security properties:
    - Non-repudiation: Signer cannot deny having signed the message
    - Message integrity: Any modification to the message invalidates the signature
    - Authentication: Proves the message came from the private key holder

    :param sender_private_key: The signer's private key (must be exactly 1281 bytes).
    :param message: The message to sign as bytes.
    :return: The digital signature as bytes (~690 bytes).
    :raises TypeError: If private key or message is not bytes.
    :raises ValueError: If private key has wrong size or message is empty.
    :raises RuntimeError: If signature generation fails.
    """
    # Validate private key parameter
    if not isinstance(sender_private_key, bytes):
        raise TypeError("Private key must be bytes")
    if len(sender_private_key) != falcon_512.SECRET_KEY_SIZE:
        raise ValueError(
            f"Private key must be {falcon_512.SECRET_KEY_SIZE} bytes, got {len(sender_private_key)} bytes"
        )

    # Validate message parameter
    if not isinstance(message, bytes):
        raise TypeError("Message must be bytes")
    if not message:
        raise ValueError("Message must be a non-empty bytes object")

    try:
        # Generate digital signature using Falcon-512 algorithm
        # The signature is deterministic for the same key and message
        signature = falcon_512.sign(sender_private_key, message)

        # Validate signature was generated successfully
        if not isinstance(signature, bytes) or not signature:
            raise RuntimeError("Signature generation produced invalid output")

    except Exception as e:
        raise RuntimeError(f"Message signing failed: {e}")

    return signature


def verify_signature(
    sender_public_key: bytes, message: bytes, signature: bytes
) -> bool:
    """Verifies a Falcon-512 digital signature against a message and public key.

    This function verifies that a signature was created by the holder of the corresponding
    private key for the exact message provided. Verification succeeds only if:
    1. The signature was created with the matching private key
    2. The message has not been modified since signing
    3. The signature itself has not been tampered with

    Verification process:
    1. Validate all input parameters
    2. Use Falcon-512 verification algorithm
    3. Return True if signature is valid, False otherwise
    4. Handle any verification errors gracefully

    Security properties:
    - Public verification: Anyone can verify with just the public key
    - Tamper detection: Invalid signatures are reliably detected
    - No false positives: Valid signatures will always verify correctly

    :param sender_public_key: The signer's public key (must be exactly 897 bytes).
    :param message: The original message that was signed.
    :param signature: The signature to verify against the message.
    :return: True if signature is valid, False otherwise.
    :raises TypeError: If any parameter is not bytes.
    :raises ValueError: If public key has wrong size or any parameter is empty.
    """
    # Validate public key parameter
    if not isinstance(sender_public_key, bytes):
        raise TypeError("Public key must be bytes")
    if len(sender_public_key) != falcon_512.PUBLIC_KEY_SIZE:
        raise ValueError(
            f"Public key must be {falcon_512.PUBLIC_KEY_SIZE} bytes, got {len(sender_public_key)} bytes"
        )

    # Validate message parameter
    if not isinstance(message, bytes):
        raise TypeError("Message must be bytes")
    if not message:
        raise ValueError("Message must be a non-empty bytes object")

    # Validate signature parameter
    if not isinstance(signature, bytes):
        raise TypeError("Signature must be bytes")
    if not signature:
        raise ValueError("Signature must be a non-empty bytes object")

    try:
        # Verify the signature using Falcon-512 verification algorithm
        # This function raises an exception if verification fails
        falcon_512.verify(sender_public_key, message, signature)

        # If no exception was raised, the signature is valid
        return True

    except Exception:
        # Any exception during verification means the signature is invalid
        # This includes malformed signatures, wrong keys, or tampered messages
        return False
