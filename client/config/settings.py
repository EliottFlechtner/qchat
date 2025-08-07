"""
Client configuration management for QChat application.

This module provides client-specific configuration settings including
server connection details and cryptographic algorithm preferences.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class ClientSettings(BaseSettings):
    """
    Client application settings with environment variable support.

    These settings control client behavior including server connection,
    cryptographic algorithms, and local preferences.
    """

    # Server Connection
    server_host: str = Field(default="localhost", description="QChat server host")
    server_port: int = Field(default=8000, description="QChat server port")
    use_https: bool = Field(
        default=False, description="Use HTTPS for server connection"
    )

    # WebSocket Configuration
    ws_reconnect_attempts: int = Field(
        default=5, description="WebSocket reconnection attempts"
    )
    ws_reconnect_delay: int = Field(
        default=2, description="WebSocket reconnection delay in seconds"
    )
    ws_ping_interval: int = Field(
        default=30, description="WebSocket ping interval in seconds"
    )

    # Cryptography Configuration
    kem_algorithm: str = Field(
        default="Kyber512", description="Post-quantum KEM algorithm"
    )
    sig_algorithm: str = Field(
        default="Dilithium2", description="Post-quantum signature algorithm"
    )

    # Client Behavior
    auto_retry_failed_messages: bool = Field(
        default=True, description="Automatically retry failed messages"
    )
    max_retry_attempts: int = Field(
        default=3, description="Maximum retry attempts for failed operations"
    )
    message_timeout: int = Field(default=30, description="Message timeout in seconds")

    # Local Storage
    keys_file_path: str = Field(
        default="user_keys.json", description="Path to store user keys"
    )
    cache_messages: bool = Field(default=True, description="Cache messages locally")
    max_cached_messages: int = Field(
        default=100, description="Maximum number of cached messages"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Client logging level")
    log_to_file: bool = Field(default=False, description="Enable logging to file")
    log_file_path: str = Field(default="qchat_client.log", description="Log file path")

    @property
    def server_url(self) -> str:
        """Construct server URL from host, port, and protocol."""
        protocol = "https" if self.use_https else "http"
        return f"{protocol}://{self.server_host}:{self.server_port}"

    @property
    def ws_url(self) -> str:
        """Construct WebSocket URL from host, port, and protocol."""
        protocol = "wss" if self.use_https else "ws"
        return f"{protocol}://{self.server_host}:{self.server_port}/ws"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level is one of the standard logging levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {", ".join(valid_levels)}')
        return v.upper()

    @field_validator("kem_algorithm")
    @classmethod
    def validate_kem_algorithm(cls, v):
        """Validate KEM algorithm is supported by liboqs."""
        # Common post-quantum KEM algorithms supported by liboqs
        valid_algorithms = [
            "Kyber512",
            "Kyber768",
            "Kyber1024",
            "NTRU-HPS-2048-509",
            "NTRU-HPS-2048-677",
            "NTRU-HPS-4096-821",
            "NTRU-HRSS-701",
            "NTRU-HRSS-1373",
            "saber",
            "LightSaber-KEM",
            "Saber-KEM",
            "FireSaber-KEM",
        ]
        if v not in valid_algorithms:
            raise ValueError(
                f'KEM algorithm must be one of: {", ".join(valid_algorithms)}'
            )
        return v

    @field_validator("sig_algorithm")
    @classmethod
    def validate_sig_algorithm(cls, v):
        """Validate signature algorithm is supported by liboqs."""
        # Common post-quantum signature algorithms supported by liboqs
        valid_algorithms = [
            "Dilithium2",
            "Dilithium3",
            "Dilithium5",
            "Falcon-512",
            "Falcon-1024",
            "SPHINCS+-HARAKA-128f-robust",
            "SPHINCS+-HARAKA-128s-robust",
            "SPHINCS+-SHA256-128f-robust",
            "SPHINCS+-SHA256-128s-robust",
        ]
        if v not in valid_algorithms:
            raise ValueError(
                f'Signature algorithm must be one of: {", ".join(valid_algorithms)}'
            )
        return v

    @field_validator("server_port")
    @classmethod
    def validate_server_port(cls, v):
        """Validate server port is in valid range."""
        if not (1 <= v <= 65535):
            raise ValueError("Server port must be between 1 and 65535")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_prefix = "QCHAT_CLIENT_"  # Prefix for client-specific env vars
        extra = "ignore"  # Ignore extra environment variables


# Create global client settings instance
client_settings = ClientSettings()


def get_client_settings() -> ClientSettings:
    """
    Get client settings instance.

    Returns:
        ClientSettings: The global client settings instance
    """
    return client_settings
