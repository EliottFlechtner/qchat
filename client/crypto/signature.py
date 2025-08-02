from pqcrypto.sign import falcon_512


def generate_signature_keypair():
    """Generates a Falcon signature keypair.
    Returns:
        tuple: (public_key, private_key) where both are bytes.
    """
    pub, priv = falcon_512.generate_keypair()
    return pub, priv


def sign_message(sender_private_key: bytes, message: bytes) -> bytes:
    if len(sender_private_key) != falcon_512.SECRET_KEY_SIZE:
        raise ValueError(
            f"Private key must be {falcon_512.SECRET_KEY_SIZE} bytes, got {len(sender_private_key)} bytes"
        )
    return falcon_512.sign(sender_private_key, message)


def verify_signature(
    sender_public_key: bytes, message: bytes, signature: bytes
) -> bool:
    try:
        falcon_512.verify(sender_public_key, message, signature)
        return True
    except Exception:
        return False
