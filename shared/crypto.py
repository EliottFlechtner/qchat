from pqc.kem import kyber512 as kem
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os


def generate_kem_keypair():
    return kem.keypair()  # (pubkey, privkey)


def encapsulate(pubkey):
    return kem.encapsulate()  # (ct, shared_secret)


def decapsulate(ciphertext, privkey):
    return kem.decapsulate(ciphertext, privkey)


def encrypt_message(message: str, shared_key: bytes):
    aesgcm = AESGCM(shared_key[:32])  # truncate Kyber key
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, message.encode(), None)
    return nonce, ct


def decrypt_message(nonce: bytes, ciphertext: bytes, shared_key: bytes):
    aesgcm = AESGCM(shared_key[:32])
    return aesgcm.decrypt(nonce, ciphertext, None).decode()
