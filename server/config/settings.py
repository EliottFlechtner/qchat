"""
Configuration management for QChat application.

This module provides centralized configuration using Pydantic settings with
environment variable support. All configuration values are validated and
type-checked automatically.

Usage:
    from server.config.settings import settings
    database_url = settings.database_url
"""

from pydantic_settings import BaseSettings
from pydantic import Field, computed_field, field_validator
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    All settings can be overridden via environment variables.
    Boolean values accept: true/false, 1/0, yes/no, on/off (case insensitive).
    """

    # Database Configuration
    postgres_user: str = Field(default="admin", description="PostgreSQL username")
    postgres_password: str = Field(default="admin", description="PostgreSQL password")
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_db: str = Field(default="qchatdb", description="PostgreSQL database name")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")

    # Security Configuration
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT tokens and other cryptographic operations",
    )
    jwt_expiration_hours: int = Field(
        default=24, description="JWT token expiration time in hours"
    )
    bcrypt_rounds: int = Field(default=12, description="BCrypt hashing rounds")

    # Application Configuration
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    max_message_size: int = Field(
        default=1024, description="Maximum message size in bytes"
    )
    max_connections_per_user: int = Field(
        default=5, description="Maximum WebSocket connections per user"
    )

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(
        default=False, description="Enable auto-reload for development"
    )

    # Cryptography Configuration
    kem_algorithm: str = Field(
        default="Kyber512", description="Post-quantum KEM algorithm"
    )
    sig_algorithm: str = Field(
        default="Dilithium2", description="Post-quantum signature algorithm"
    )

    # Redis Configuration (optional for future message queue implementation)
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_db: int = Field(default=0, description="Redis database number")

    # Rate Limiting
    rate_limit_requests: int = Field(
        default=100, description="Rate limit requests per minute"
    )
    rate_limit_window: int = Field(
        default=60, description="Rate limit window in seconds"
    )

    @computed_field
    @property
    def database_url(self) -> str:
        """Construct PostgreSQL database URL from individual components."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field
    @property
    def redis_url(self) -> str:
        """Construct Redis URL from individual components."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

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

    @field_validator("max_message_size")
    @classmethod
    def validate_max_message_size(cls, v):
        """Ensure message size is reasonable (1KB to 10MB)."""
        if not (1024 <= v <= 10 * 1024 * 1024):
            raise ValueError("Max message size must be between 1KB and 10MB")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Allow environment variables to override settings
        # e.g., POSTGRES_USER -> postgres_user
        extra = "ignore"  # Ignore extra environment variables


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Dependency function to get settings instance.

    This function can be used with FastAPI's Depends() to inject
    settings into route handlers and other functions.

    Returns:
        Settings: The global settings instance
    """
    return settings
