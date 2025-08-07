import sys

from client.api import get_public_key, send_message
from client.crypto.kem import encapsulate_key, encrypt_message
from client.crypto.signature import sign_message
from client.services.login import get_local_keypair


def send_encrypted_message(sender: str, recipient: str, plaintext: str) -> None:
    """Sends an encrypted and authenticated message using post-quantum cryptography.

    This function implements a complete secure messaging protocol using hybrid post-quantum
    cryptography. It combines key encapsulation mechanism (KEM) for key exchange with
    symmetric encryption for message confidentiality and digital signatures for authenticity.

    Message sending workflow:
    1. Validate all input parameters for security
    2. Retrieve recipient's public KEM key from server
    3. Generate shared secret using post-quantum KEM
    4. Encrypt message content using AES-GCM with derived key
    5. Sign the ciphertext using sender's private signature key
    6. Transmit all cryptographic components to server
    7. Confirm successful message delivery

    Security properties:
    - Message confidentiality: Only recipient can decrypt the message
    - Message authenticity: Digital signature proves sender identity
    - Message integrity: Any tampering is detected and rejected
    - Forward secrecy: Each message uses a fresh shared secret
    - Post-quantum security: Resistant to quantum computer attacks

    Cryptographic components transmitted:
    - Ciphertext: AES-GCM encrypted message content
    - Nonce: Unique value for AES-GCM encryption
    - Encapsulated key: KEM-encrypted shared secret for recipient
    - Signature: Digital signature over the ciphertext for authenticity

    :param sender: Username of the message sender (must have local keys).
    :param recipient: Username of the message recipient (must be registered).
    :param plaintext: The message content to encrypt and send.
    :raises TypeError: If any parameter is not a string.
    :raises ValueError: If parameters are empty, invalid, or sender equals recipient.
    :raises RuntimeError: If cryptographic operations or API calls fail.
    """
    # Validate input parameters for security and correctness
    if not isinstance(sender, str):
        raise TypeError("Sender must be a string")
    if not isinstance(recipient, str):
        raise TypeError("Recipient must be a string")
    if not isinstance(plaintext, str):
        raise TypeError("Plaintext must be a string")

    if not sender or not sender.strip():
        raise ValueError("Sender cannot be empty")
    if not recipient or not recipient.strip():
        raise ValueError("Recipient cannot be empty")
    if not plaintext or not plaintext.strip():
        raise ValueError("Plaintext cannot be empty")

    # Prevent self-messaging for security and practical reasons
    if sender.strip() == recipient.strip():
        raise ValueError("Sender and recipient cannot be the same")

    print(
        f"[CLIENT] Sending encrypted message from '{sender}' to '{recipient}'",
        file=sys.stderr,
    )

    try:
        # Step 1: Retrieve recipient's public KEM key for encryption
        print(
            f"[SEND] Retrieving KEM public key for recipient '{recipient}'...",
            file=sys.stderr,
        )
        try:
            recipient_kem_pk = get_public_key(recipient, field="kem_pk")
            if not recipient_kem_pk:
                raise ValueError(f"No KEM public key found for recipient '{recipient}'")
            if not isinstance(recipient_kem_pk, bytes):
                raise ValueError(
                    f"Invalid KEM public key format for recipient '{recipient}'"
                )
        except Exception as e:
            raise RuntimeError(
                f"Failed to retrieve KEM public key for '{recipient}': {e}"
            )

        # Step 2: Generate shared secret using post-quantum KEM
        print(
            "[SEND] Generating shared secret using post-quantum KEM...", file=sys.stderr
        )
        try:
            encap_key, shared_secret = encapsulate_key(recipient_kem_pk)
            if not encap_key or not shared_secret:
                raise ValueError("KEM encapsulation produced empty results")
        except Exception as e:
            raise RuntimeError(f"KEM encapsulation failed: {e}")

        # Step 3: Encrypt message content using AES-GCM with derived key
        print("[SEND] Encrypting message content with AES-GCM...", file=sys.stderr)
        try:
            nonce, ciphertext = encrypt_message(shared_secret, plaintext)
            if not nonce or not ciphertext:
                raise ValueError("Message encryption produced empty results")
        except Exception as e:
            raise RuntimeError(f"Message encryption failed: {e}")

        # Step 4: Retrieve sender's private signature key for authentication
        print(
            f"[SEND] Retrieving signature private key for sender '{sender}'...",
            file=sys.stderr,
        )
        try:
            sender_keypair = get_local_keypair(sender, field="sig")
            if not sender_keypair or len(sender_keypair) < 1:
                raise ValueError(f"No signature keypair found for sender '{sender}'")
            sender_sig_sk = sender_keypair[0]  # Private key is first element
            if not sender_sig_sk:
                raise ValueError(f"Signature private key is None for sender '{sender}'")
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve signature key for '{sender}': {e}")

        # Step 5: Sign the ciphertext for message authenticity
        print(
            "[SEND] Generating digital signature for message authenticity...",
            file=sys.stderr,
        )
        try:
            signature = sign_message(sender_sig_sk, ciphertext)
            if not signature:
                raise ValueError("Digital signature generation produced empty result")
        except Exception as e:
            raise RuntimeError(f"Digital signature generation failed: {e}")

        # Step 6: Transmit all cryptographic components to the server
        print("[SEND] Transmitting encrypted message to server...", file=sys.stderr)
        try:
            send_message(
                sender=sender,
                recipient=recipient,
                ciphertext=ciphertext,  # AES-GCM encrypted message
                nonce=nonce,  # AES-GCM nonce for decryption
                encap_key=encap_key,  # KEM-encrypted shared secret
                signature=signature,  # Digital signature for authenticity
            )
        except Exception as e:
            raise RuntimeError(f"Failed to send message via API: {e}")

        # Step 7: Confirm successful message delivery
        print(
            f"[CLIENT] ✔ Encrypted message sent successfully from '{sender}' to '{recipient}'",
            file=sys.stderr,
        )

    except Exception as e:
        # Re-raise our specific exceptions, wrap others in RuntimeError
        if isinstance(e, (TypeError, ValueError, RuntimeError)):
            raise
        raise RuntimeError(
            f"Unexpected error sending message from '{sender}' to '{recipient}': {e}"
        )
