import oqs, os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_keypair():
    with oqs.KeyEncapsulation("Kyber512") as kem:
        pub = kem.generate_keypair()
        priv = kem.export_secret_key()
    return pub, priv


def encapsulate_key(pubkey: bytes):
    with oqs.KeyEncapsulation("Kyber512") as kem:
        ciphertext_kem, shared_secret = kem.encap_secret(pubkey)
    return ciphertext_kem, shared_secret


def decapsulate_key(encapsulated: bytes, privkey: bytes):
    with oqs.KeyEncapsulation("Kyber512", secret_key=privkey) as kem:
        shared_secret = kem.decap_secret(encapsulated)
    return shared_secret


def encrypt_message(shared_secret: bytes, plaintext: str):
    aesgcm = AESGCM(shared_secret[:16])
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return nonce, ciphertext


def decrypt_message(shared_secret: bytes, nonce: bytes, ciphertext: bytes):
    aesgcm = AESGCM(shared_secret[:16])
    return aesgcm.decrypt(nonce, ciphertext, None).decode()
