import sys

from client.api import get_public_key, send_message
from client.crypto.kem import encapsulate_key, encrypt_message
from client.crypto.signature import sign_message
from client.services.login import get_local_keypair


def send_encrypted_message(sender: str, recipient: str, plaintext: str) -> None:
    if not sender or not recipient or not plaintext:
        raise ValueError("Sender, recipient, and plaintext cannot be empty.")
    if sender == recipient:
        raise ValueError("Sender and recipient cannot be the same.")

    print(
        f"[CLIENT] Sending encrypted message from {sender} to {recipient}.",
        file=sys.stderr,
    )

    # 1. Get recipient's Kyber public key
    recipient_kem_pk = get_public_key(recipient, field="kem_pk")
    if not recipient_kem_pk:
        raise ValueError(f"Recipient '{recipient}' does not have a KEM public key.")

    # 2. Encrypt the message
    encap_key, shared_secret = encapsulate_key(recipient_kem_pk)
    nonce, ciphertext = encrypt_message(shared_secret, plaintext)

    # 3. Sign the encrypted message
    sender_sig_sk = get_local_keypair(sender, field="sig")[0]
    signature = sign_message(sender_sig_sk, ciphertext)

    # 4. Send encrypted message and signature through the API
    send_message(
        sender,
        recipient,
        ciphertext,
        nonce,
        encap_key,
        signature,
    )

    print(
        f"[CLIENT] Encrypted message sent from {sender} to {recipient}.",
        file=sys.stderr,
    )
