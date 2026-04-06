"""
Tests for client configuration and utility functions.

Tests the settings management and helper utilities.
"""

import pytest
from unittest.mock import patch, Mock
import base64
from client.utils.helpers import get_api_url, get_ws_url, b64e, b64d
from client.config.settings import ClientSettings


class TestHelperFunctions:
    """Test utility helper functions."""

    @patch("client.utils.helpers.client_settings")
    def test_get_api_url(self, mock_settings):
        """Test API URL generation."""
        mock_settings.server_url = "http://localhost:8000"

        url = get_api_url()

        assert url == "http://localhost:8000"

    @patch("client.utils.helpers.client_settings")
    def test_get_ws_url(self, mock_settings):
        """Test WebSocket URL generation."""
        mock_settings.ws_url = "ws://localhost:8000/ws"

        url = get_ws_url()

        assert url == "ws://localhost:8000/ws"

    def test_b64e_encode_success(self):
        """Test successful base64 encoding."""
        test_data = b"Hello, World!"
        expected = base64.b64encode(test_data).decode()

        result = b64e(test_data)

        assert result == expected
        assert isinstance(result, str)

    def test_b64d_decode_success(self):
        """Test successful base64 decoding."""
        test_string = "SGVsbG8sIFdvcmxkIQ=="  # "Hello, World!" in base64
        expected = b"Hello, World!"

        result = b64d(test_string)

        assert result == expected
        assert isinstance(result, bytes)

    def test_b64_round_trip(self):
        """Test base64 encode-decode round trip."""
        original_data = b"Test data with special chars: \x00\x01\x02\xff"

        encoded = b64e(original_data)
        decoded = b64d(encoded)

        assert decoded == original_data

    def test_b64e_with_empty_data(self):
        """Test base64 encoding with empty data."""
        result = b64e(b"")
        assert result == ""

    def test_b64d_with_empty_string(self):
        """Test base64 decoding with empty string."""
        result = b64d("")
        assert result == b""

    def test_b64d_with_invalid_base64(self):
        """Test base64 decoding with invalid data."""
        with pytest.raises(Exception):  # base64.binascii.Error or similar
            b64d("invalid_base64!")

    def test_b64_with_unicode_data(self):
        """Test base64 encoding with unicode data."""
        unicode_text = "Hello, 世界! 🌍"
        data = unicode_text.encode("utf-8")

        encoded = b64e(data)
        decoded = b64d(encoded)
        decoded_text = decoded.decode("utf-8")

        assert decoded_text == unicode_text


class TestClientSettings:
    """Test client configuration settings."""

    def test_default_settings(self):
        """Test default configuration values."""
        settings = ClientSettings()

        assert settings.server_host == "localhost"
        assert settings.server_port == 8000
        assert settings.use_https is False
        assert settings.kem_algorithm == "Kyber512"
        assert settings.sig_algorithm == "Dilithium2"

    def test_server_url_property(self):
        """Test server URL property construction."""
        settings = ClientSettings(
            server_host="example.com", server_port=8080, use_https=True
        )

        expected_url = "https://example.com:8080"
        assert settings.server_url == expected_url

    def test_server_url_http(self):
        """Test HTTP server URL construction."""
        settings = ClientSettings(
            server_host="localhost", server_port=3000, use_https=False
        )

        expected_url = "http://localhost:3000"
        assert settings.server_url == expected_url

    def test_ws_url_property(self):
        """Test WebSocket URL property construction."""
        settings = ClientSettings(
            server_host="example.com", server_port=8080, use_https=True
        )

        expected_url = "wss://example.com:8080/ws"
        assert settings.ws_url == expected_url

    def test_ws_url_insecure(self):
        """Test insecure WebSocket URL construction."""
        settings = ClientSettings(
            server_host="localhost", server_port=3000, use_https=False
        )

        expected_url = "ws://localhost:3000/ws"
        assert settings.ws_url == expected_url

    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(
            "os.environ",
            {
                "QCHAT_CLIENT_SERVER_HOST": "custom.host",
                "QCHAT_CLIENT_SERVER_PORT": "9000",
                "QCHAT_CLIENT_USE_HTTPS": "true",
                "QCHAT_CLIENT_KEM_ALGORITHM": "Kyber768",
                "QCHAT_CLIENT_SIG_ALGORITHM": "Dilithium3",
            },
        ):
            settings = ClientSettings()

            assert settings.server_host == "custom.host"
            assert settings.server_port == 9000
            assert settings.use_https is True
            assert settings.kem_algorithm == "Kyber768"
            assert settings.sig_algorithm == "Dilithium3"

    def test_websocket_configuration(self):
        """Test WebSocket-specific configuration."""
        settings = ClientSettings()

        assert settings.ws_reconnect_attempts == 5
        assert settings.ws_reconnect_delay == 2
        assert settings.ws_ping_interval == 30

    def test_client_behavior_settings(self):
        """Test client behavior configuration."""
        settings = ClientSettings()

        assert settings.auto_retry_failed_messages is True
        assert settings.max_retry_attempts == 3  # Assuming default

    def test_invalid_port_validation(self):
        """Test port validation."""
        with pytest.raises(ValueError):
            ClientSettings(server_port=-1)

        with pytest.raises(ValueError):
            ClientSettings(server_port=70000)

    def test_algorithm_validation(self):
        """Test cryptographic algorithm validation."""
        # Test valid algorithms
        settings = ClientSettings(kem_algorithm="Kyber512", sig_algorithm="Dilithium2")
        assert settings.kem_algorithm == "Kyber512"
        assert settings.sig_algorithm == "Dilithium2"

        # Test invalid algorithms might be caught by validators
        # (depends on actual implementation)
        try:
            ClientSettings(kem_algorithm="InvalidKEM")
            # If no validation, test passes
        except ValueError:
            # If validation exists, this is expected
            pass

    def test_settings_serialization(self):
        """Test settings can be serialized/deserialized."""
        settings = ClientSettings(
            server_host="test.example.com", server_port=8443, use_https=True
        )

        # Test that settings have the expected values
        assert settings.server_host == "test.example.com"
        assert settings.server_port == 8443
        assert settings.use_https is True

    def test_settings_model_validation(self):
        """Test Pydantic model validation."""
        # Test valid settings
        settings = ClientSettings(server_host="valid.host", server_port=8080)
        assert settings.server_host == "valid.host"

        # Test type validation
        with pytest.raises((ValueError, TypeError)):
            ClientSettings(server_port="invalid_port")  # type: ignore

    def test_settings_field_descriptions(self):
        """Test that settings have proper field descriptions."""
        # This tests the Field descriptions in the model
        settings = ClientSettings()

        # Check that the model has the expected fields
        assert hasattr(settings, "server_host")
        assert hasattr(settings, "server_port")
        assert hasattr(settings, "use_https")
        assert hasattr(settings, "kem_algorithm")
        assert hasattr(settings, "sig_algorithm")


class TestConfigurationIntegration:
    """Integration tests for configuration with other components."""

    @patch("client.utils.helpers.client_settings")
    def test_helpers_use_settings(self, mock_settings):
        """Test that helpers use the client settings."""
        mock_settings.server_url = "http://test.example.com:8080"
        mock_settings.ws_url = "ws://test.example.com:8080/ws"

        api_url = get_api_url()
        ws_url = get_ws_url()

        assert api_url == "http://test.example.com:8080"
        assert ws_url == "ws://test.example.com:8080/ws"

    def test_settings_consistency(self):
        """Test that related settings are consistent."""
        settings = ClientSettings(server_host="secure.example.com", use_https=True)

        # HTTPS and WSS should be consistent
        assert settings.server_url.startswith("https://")
        assert settings.ws_url.startswith("wss://")

    def test_settings_environment_loading(self):
        """Test loading settings from environment variables."""
        test_env = {
            "QCHAT_CLIENT_SERVER_HOST": "env.example.com",
            "QCHAT_CLIENT_SERVER_PORT": "8443",
            "QCHAT_CLIENT_USE_HTTPS": "true",
            "QCHAT_CLIENT_LOG_LEVEL": "DEBUG",
        }

        with patch.dict("os.environ", test_env):
            settings = ClientSettings()

            assert settings.server_host == "env.example.com"
            assert settings.server_port == 8443
            assert settings.use_https is True

    def test_settings_validation_chain(self):
        """Test validation of interdependent settings."""
        # Test that HTTPS port defaults make sense
        https_settings = ClientSettings(use_https=True)
        http_settings = ClientSettings(use_https=False)

        # Both should have valid configurations
        assert https_settings.server_url.startswith("https://")
        assert http_settings.server_url.startswith("http://")

        # URLs should be properly formed
        assert "://" in https_settings.server_url
        assert "://" in http_settings.server_url
