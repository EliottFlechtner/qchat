import oqs, os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from client.crypto.aes256 import derive_aes_key, encrypt_with_aes, decrypt_with_aes

KEM_ALGORITHM = "Kyber512"


def generate_kem_keypair():
    """Generates a KEM keypair using the specified algorithm.
    Returns:
        tuple: (public_key, private_key) where both are bytes.
    """
    with oqs.KeyEncapsulation(KEM_ALGORITHM) as kem:
        pub = kem.generate_keypair()
        priv = kem.export_secret_key()
    return pub, priv


def encapsulate_key(pubkey: bytes):
    with oqs.KeyEncapsulation(KEM_ALGORITHM) as kem:
        ciphertext_kem, shared_secret = kem.encap_secret(pubkey)
    return ciphertext_kem, shared_secret


def decapsulate_key(encapsulated: bytes, privkey: bytes):
    with oqs.KeyEncapsulation(KEM_ALGORITHM, secret_key=privkey) as kem:
        shared_secret = kem.decap_secret(encapsulated)
    return shared_secret


def encrypt_message(shared_secret: bytes, plaintext: str):
    aes_key = derive_aes_key(shared_secret)
    return encrypt_with_aes(aes_key, plaintext)


def decrypt_message(shared_secret: bytes, nonce: bytes, ciphertext: bytes):
    aes_key = derive_aes_key(shared_secret)
    return decrypt_with_aes(aes_key, nonce, ciphertext)
