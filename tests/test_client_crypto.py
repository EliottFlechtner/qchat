"""
Tests for client cryptographic modules including AES, KEM, and signature operations.

Tests the post-quantum cryptographic functions and error handling.
"""

import pytest
from unittest.mock import patch, Mock
from client.crypto.aes256 import encrypt_with_aes, decrypt_with_aes
from client.crypto.kem import (
    generate_kem_keypair,
    encapsulate_key,
    decapsulate_key,
    encrypt_message,
    decrypt_message,
)
from client.crypto.signature import (
    generate_signature_keypair,
    sign_message,
    verify_signature,
)


class TestAES256:
    """Test AES-GCM encryption and decryption."""

    def test_encrypt_with_aes_success(self):
        """Test successful AES encryption."""
        plaintext = "Hello, World!"
        key = b"0" * 32  # 256-bit key

        ciphertext, nonce = encrypt_with_aes(key, plaintext)

        assert isinstance(ciphertext, bytes)
        assert isinstance(nonce, bytes)
        assert len(nonce) == 12  # AES-GCM nonce length
        assert ciphertext != plaintext.encode()

    def test_decrypt_with_aes_success(self):
        """Test successful AES decryption."""
        plaintext = "Hello, World!"
        key = b"0" * 32

        # Encrypt first
        ciphertext, nonce = encrypt_with_aes(key, plaintext)

        # Then decrypt
        decrypted = decrypt_with_aes(ciphertext, nonce, key)

        assert decrypted == plaintext

    def test_aes_round_trip(self):
        """Test encrypt-decrypt round trip."""
        original_message = "This is a test message with unicode: 🔒"
        key = b"abcdefghijklmnopqrstuvwxyz123456"  # 32 bytes

        # Encrypt
        ciphertext, nonce = encrypt_with_aes(key, original_message)

        # Decrypt
        decrypted_message = decrypt_with_aes(ciphertext, nonce, key)

        assert decrypted_message == original_message

    def test_aes_invalid_key_length(self):
        """Test AES with invalid key length."""
        with pytest.raises((ValueError, Exception)):
            encrypt_with_aes(b"short_key", "test")

    def test_aes_decrypt_wrong_key(self):
        """Test AES decryption with wrong key."""
        plaintext = "Secret message"
        correct_key = b"0" * 32
        wrong_key = b"1" * 32

        ciphertext, nonce = encrypt_with_aes(correct_key, plaintext)

        with pytest.raises((ValueError, Exception)):
            decrypt_with_aes(ciphertext, nonce, wrong_key)

    def test_aes_decrypt_tampered_ciphertext(self):
        """Test AES decryption with tampered ciphertext."""
        plaintext = "Secret message"
        key = b"0" * 32

        ciphertext, nonce = encrypt_with_aes(key, plaintext)

        # Tamper with ciphertext
        tampered_ciphertext = ciphertext[:-1] + b"X"

        with pytest.raises((ValueError, Exception)):
            decrypt_with_aes(tampered_ciphertext, nonce, key)


class TestKEM:
    """Test KEM (Key Encapsulation Mechanism) operations."""

    @patch("client.crypto.kem.oqs.KeyEncapsulation")
    def test_generate_kem_keypair_success(self, mock_kem_class):
        """Test successful KEM keypair generation."""
        mock_kem = Mock()
        mock_kem.generate_keypair.return_value = None
        mock_kem.public_key = b"public_key_data"
        mock_kem.secret_key = b"secret_key_data"
        mock_kem_class.return_value = mock_kem

        public_key, secret_key = generate_kem_keypair()

        assert public_key == b"public_key_data"
        assert secret_key == b"secret_key_data"
        mock_kem.generate_keypair.assert_called_once()

    @patch("client.crypto.kem.oqs.KeyEncapsulation")
    def test_encapsulate_key_success(self, mock_kem_class):
        """Test successful key encapsulation."""
        mock_kem = Mock()
        mock_kem.encap_secret.return_value = (b"ciphertext", b"shared_secret")
        mock_kem_class.return_value = mock_kem

        public_key = b"recipient_public_key"
        ciphertext, shared_secret = encapsulate_key(public_key)

        assert ciphertext == b"ciphertext"
        assert shared_secret == b"shared_secret"

    @patch("client.crypto.kem.oqs.KeyEncapsulation")
    def test_decapsulate_key_success(self, mock_kem_class):
        """Test successful key decapsulation."""
        mock_kem = Mock()
        mock_kem.decap_secret.return_value = b"shared_secret"
        mock_kem_class.return_value = mock_kem

        secret_key = b"recipient_secret_key"
        ciphertext = b"encapsulated_key"
        shared_secret = decapsulate_key(ciphertext, secret_key)

        assert shared_secret == b"shared_secret"

    @patch("client.crypto.kem.encrypt_with_aes")
    def test_encrypt_message_success(self, mock_encrypt_aes):
        """Test successful message encryption."""
        mock_encrypt_aes.return_value = (b"ciphertext", b"nonce")

        message = "Hello, World!"
        shared_secret = b"0" * 32

        ciphertext, nonce = encrypt_message(shared_secret, message)

        assert ciphertext == b"ciphertext"
        assert nonce == b"nonce"
        # Check that encrypt_with_aes was called with derived key and message
        mock_encrypt_aes.assert_called_once()

    @patch("client.crypto.kem.decrypt_with_aes")
    def test_decrypt_message_success(self, mock_decrypt_aes):
        """Test successful message decryption."""
        mock_decrypt_aes.return_value = "Hello, World!"

        shared_secret = b"0" * 32
        nonce = b"nonce_data"
        ciphertext = b"encrypted_data"

        plaintext = decrypt_message(shared_secret, nonce, ciphertext)

        assert plaintext == "Hello, World!"
        mock_decrypt_aes.assert_called_once()


class TestSignature:
    """Test digital signature operations."""

    @patch("client.crypto.signature.oqs.Signature")
    def test_generate_signature_keypair_success(self, mock_sig_class):
        """Test successful signature keypair generation."""
        mock_sig = Mock()
        mock_sig.generate_keypair.return_value = None
        mock_sig.public_key = b"public_key_data"
        mock_sig.secret_key = b"secret_key_data"
        mock_sig_class.return_value = mock_sig

        public_key, secret_key = generate_signature_keypair()

        assert public_key == b"public_key_data"
        assert secret_key == b"secret_key_data"
        mock_sig.generate_keypair.assert_called_once()

    @patch("client.crypto.signature.oqs.Signature")
    def test_sign_message_success(self, mock_sig_class):
        """Test successful message signing."""
        mock_sig = Mock()
        mock_sig.sign.return_value = b"signature_data"
        mock_sig_class.return_value = mock_sig

        message = b"message_to_sign"
        secret_key = b"secret_key_data"
        signature = sign_message(message, secret_key)

        assert signature == b"signature_data"

    @patch("client.crypto.signature.oqs.Signature")
    def test_verify_signature_success(self, mock_sig_class):
        """Test successful signature verification."""
        mock_sig = Mock()
        mock_sig.verify.return_value = True
        mock_sig_class.return_value = mock_sig

        message = b"message_to_verify"
        signature = b"signature_data"
        public_key = b"public_key_data"

        is_valid = verify_signature(message, signature, public_key)

        assert is_valid is True

    @patch("client.crypto.signature.oqs.Signature")
    def test_verify_signature_failure(self, mock_sig_class):
        """Test signature verification failure."""
        mock_sig = Mock()
        mock_sig.verify.return_value = False
        mock_sig_class.return_value = mock_sig

        message = b"message_to_verify"
        signature = b"invalid_signature"
        public_key = b"public_key_data"

        is_valid = verify_signature(message, signature, public_key)

        assert is_valid is False

    @patch("client.crypto.signature.oqs.Signature")
    def test_verify_signature_exception(self, mock_sig_class):
        """Test signature verification with exception."""
        mock_sig = Mock()
        mock_sig.verify.side_effect = Exception("Verification failed")
        mock_sig_class.return_value = mock_sig

        message = b"message_to_verify"
        signature = b"signature_data"
        public_key = b"public_key_data"

        is_valid = verify_signature(message, signature, public_key)

        assert is_valid is False

    def test_signature_validation_errors(self):
        """Test signature functions with invalid inputs."""
        # These would likely be caught by the actual implementations
        with pytest.raises((TypeError, ValueError, Exception)):
            sign_message(None, b"key")  # type: ignore

        with pytest.raises((TypeError, ValueError, Exception)):
            verify_signature(None, b"sig", b"key")  # type: ignore


class TestCryptoIntegration:
    """Integration tests for crypto components working together."""

    @patch("client.crypto.kem.oqs.KeyEncapsulation")
    @patch("client.crypto.signature.oqs.Signature")
    def test_full_crypto_workflow(self, mock_sig_class, mock_kem_class):
        """Test complete cryptographic workflow."""
        # Setup KEM mocks
        mock_kem = Mock()
        mock_kem.generate_keypair.return_value = None
        mock_kem.public_key = b"kem_public_key"
        mock_kem.secret_key = b"kem_secret_key"
        mock_kem.encap_secret.return_value = (b"encap_key", b"0" * 32)
        mock_kem.decap_secret.return_value = b"0" * 32
        mock_kem_class.return_value = mock_kem

        # Setup signature mocks
        mock_sig = Mock()
        mock_sig.generate_keypair.return_value = None
        mock_sig.public_key = b"sig_public_key"
        mock_sig.secret_key = b"sig_secret_key"
        mock_sig.sign.return_value = b"message_signature"
        mock_sig.verify.return_value = True
        mock_sig_class.return_value = mock_sig

        # 1. Generate keypairs
        kem_pk, kem_sk = generate_kem_keypair()
        sig_pk, sig_sk = generate_signature_keypair()

        # 2. Encrypt message
        message = "Secret message"
        encap_key, shared_secret = encapsulate_key(kem_pk)
        ciphertext, nonce = encrypt_message(shared_secret, message)

        # 3. Sign ciphertext
        signature = sign_message(ciphertext, sig_sk)

        # 4. Verify signature
        is_valid = verify_signature(ciphertext, signature, sig_pk)

        # 5. Decrypt message
        decrypted_secret = decapsulate_key(encap_key, kem_sk)
        decrypted_message = decrypt_message(decrypted_secret, nonce, ciphertext)

        assert is_valid is True
        assert decrypted_message == message
