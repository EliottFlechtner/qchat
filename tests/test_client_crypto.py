"""Tests for client cryptographic modules (AES, KEM, signature)."""

from unittest.mock import Mock, patch

import pytest

from client.crypto.aes256 import decrypt_with_aes, encrypt_with_aes
from client.crypto.kem import (
    decapsulate_key,
    decrypt_message,
    encapsulate_key,
    encrypt_message,
    generate_kem_keypair,
)
from client.crypto.signature import (
    falcon_512,
    generate_signature_keypair,
    sign_message,
    verify_signature,
)


class TestAES256:
    def test_round_trip(self):
        key = b"0" * 32
        plaintext = "Hello, World!"

        nonce, ciphertext = encrypt_with_aes(key, plaintext)
        decrypted = decrypt_with_aes(key, nonce, ciphertext)

        assert len(nonce) == 12
        assert decrypted == plaintext

    def test_invalid_key_length(self):
        with pytest.raises(ValueError):
            encrypt_with_aes(b"short", "test")


class TestKEM:
    @patch("client.crypto.kem.oqs.KeyEncapsulation")
    def test_generate_kem_keypair_success(self, mock_kem_class):
        mock_kem = Mock()
        mock_kem.generate_keypair.return_value = b"public_key_data"
        mock_kem.export_secret_key.return_value = b"secret_key_data"
        mock_kem_class.return_value.__enter__.return_value = mock_kem

        public_key, secret_key = generate_kem_keypair()

        assert public_key == b"public_key_data"
        assert secret_key == b"secret_key_data"

    @patch("client.crypto.kem.oqs.KeyEncapsulation")
    def test_encapsulate_key_success(self, mock_kem_class):
        mock_kem = Mock()
        mock_kem.encap_secret.return_value = (b"ciphertext", b"shared_secret")
        mock_kem_class.return_value.__enter__.return_value = mock_kem

        ciphertext, shared_secret = encapsulate_key(b"recipient_public_key")

        assert ciphertext == b"ciphertext"
        assert shared_secret == b"shared_secret"

    @patch("client.crypto.kem.oqs.KeyEncapsulation")
    def test_decapsulate_key_success(self, mock_kem_class):
        mock_kem = Mock()
        mock_kem.decap_secret.return_value = b"shared_secret"
        mock_kem_class.return_value.__enter__.return_value = mock_kem

        shared_secret = decapsulate_key(b"encapsulated_key", b"recipient_secret_key")

        assert shared_secret == b"shared_secret"

    @patch("client.crypto.kem.encrypt_with_aes")
    @patch("client.crypto.kem.derive_aes_key")
    def test_encrypt_message_success(self, mock_derive_key, mock_encrypt_aes):
        mock_derive_key.return_value = b"k" * 32
        mock_encrypt_aes.return_value = (b"nonce", b"ciphertext")

        nonce, ciphertext = encrypt_message(b"0" * 32, "Hello")

        assert nonce == b"nonce"
        assert ciphertext == b"ciphertext"
        mock_encrypt_aes.assert_called_once_with(b"k" * 32, "Hello")

    @patch("client.crypto.kem.decrypt_with_aes")
    @patch("client.crypto.kem.derive_aes_key")
    def test_decrypt_message_success(self, mock_derive_key, mock_decrypt_aes):
        mock_derive_key.return_value = b"k" * 32
        mock_decrypt_aes.return_value = "Hello, World!"

        plaintext = decrypt_message(b"0" * 32, b"1" * 12, b"encrypted_data")

        assert plaintext == "Hello, World!"
        mock_decrypt_aes.assert_called_once_with(
            b"k" * 32, b"1" * 12, b"encrypted_data"
        )


class TestSignature:
    @patch("client.crypto.signature.falcon_512.generate_keypair")
    def test_generate_signature_keypair_success(self, mock_generate):
        pub = b"p" * falcon_512.PUBLIC_KEY_SIZE
        priv = b"s" * falcon_512.SECRET_KEY_SIZE
        mock_generate.return_value = (pub, priv)

        got_pub, got_priv = generate_signature_keypair()

        assert got_pub == pub
        assert got_priv == priv

    @patch("client.crypto.signature.falcon_512.sign")
    def test_sign_message_success(self, mock_sign):
        mock_sign.return_value = b"signature_data"

        signature = sign_message(b"s" * falcon_512.SECRET_KEY_SIZE, b"message")

        assert signature == b"signature_data"

    @patch("client.crypto.signature.falcon_512.verify")
    def test_verify_signature_success(self, mock_verify):
        mock_verify.return_value = None

        is_valid = verify_signature(
            b"p" * falcon_512.PUBLIC_KEY_SIZE,
            b"message",
            b"sig",
        )

        assert is_valid is True

    @patch("client.crypto.signature.falcon_512.verify")
    def test_verify_signature_failure(self, mock_verify):
        mock_verify.side_effect = Exception("invalid")

        is_valid = verify_signature(
            b"p" * falcon_512.PUBLIC_KEY_SIZE,
            b"message",
            b"sig",
        )

        assert is_valid is False
