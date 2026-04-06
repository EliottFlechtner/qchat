"""
Cryptographic module for quantum-secure operations.

This module provides post-quantum cryptographic functions including
KEM (Key Encapsulation Mechanism), digital signatures, and AES encryption.
"""

from .aes256 import derive_aes_key, encrypt_with_aes, decrypt_with_aes
from .kem import (
    generate_kem_keypair,
    encapsulate_key,
    decapsulate_key,
    encrypt_message,
    decrypt_message,
)
from .signature import generate_signature_keypair, sign_message, verify_signature

__all__ = [
    # AES encryption functions
    "derive_aes_key",
    "encrypt_with_aes",
    "decrypt_with_aes",
    # KEM functions
    "generate_kem_keypair",
    "encapsulate_key",
    "decapsulate_key",
    "encrypt_message",
    "decrypt_message",
    # Signature functions
    "generate_signature_keypair",
    "sign_message",
    "verify_signature",
]
