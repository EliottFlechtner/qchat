from client.api.api import get_public_key, send_message
from client.crypto.crypto import encapsulate_key, encrypt_message


def send_encrypted_message(sender, recipient, message):
    # Fetch the recipient's public key to encrypt the message
    recipient_pubkey = get_public_key(recipient)

    # Generate an encapsulated key and encrypt the message using KEM's
    encap_key, secret = encapsulate_key(recipient_pubkey)
    nonce, ciphertext = encrypt_message(secret, message)

    # Send the encrypted message to the server (API)
    send_message(sender, recipient, ciphertext, nonce, encap_key)
