"""
Centralized Application Configuration
=====================================
Serves as the Single Source of Truth for all environment variables, 
infrastructure URIs, and application-wide constants.

Features:
- Strict Type Validation & Casting via Pydantic
- Deep Immutability (frozen=True)
- Fail-Fast Boot Process
"""

import sys
from typing import List
from pydantic import BaseModel, Field, PostgresDsn, RedisDsn, SecretStr, ConfigDict, ValidationError

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    raise ImportError(
        "The 'pydantic-settings' module is missing. In Pydantic v2, settings are in a separate package.\n"
        "Please install it by running: pip install pydantic-settings"
    )


# ============================================================================
# 1. INFRASTRUCTURE & THIRD-PARTY CONFIGURATIONS
# ============================================================================

class DatabaseConfig(BaseModel):
    """Database connection pool settings."""
    model_config = ConfigDict(frozen=True)
    
    uri: PostgresDsn = Field(..., description="PostgreSQL Connection URI")
    pool_size: int = Field(default=20, ge=1, le=100)
    max_overflow: int = Field(default=10, ge=0)
    echo_sql: bool = Field(default=False)


class RedisConfig(BaseModel):
    """Redis cache and queue settings."""
    model_config = ConfigDict(frozen=True)
    
    uri: RedisDsn = Field(..., description="Redis Connection URI")
    timeout_seconds: int = Field(default=5, ge=1)


class AWSConfig(BaseModel):
    """AWS Integration settings."""
    model_config = ConfigDict(frozen=True)
    
    access_key_id: str = Field(...)
    secret_access_key: SecretStr = Field(...) # SecretStr ensures it's never printed natively
    region: str = Field(default="us-east-1")
    s3_bucket_name: str = Field(...)


class StripeConfig(BaseModel):
    """Stripe Billing API settings."""
    model_config = ConfigDict(frozen=True)
    
    api_key: SecretStr = Field(...)
    webhook_secret: SecretStr = Field(...)


# ============================================================================
# 2. CENTRALIZED APP SETTINGS (The Root Schema)
# ============================================================================

class AppSettings(BaseSettings):
    """
    Main Configuration Object.
    Parses from `.env` and environment variables automatically.
    """
    # Pydantic v2 Settings Config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__", # e.g. DB__URI in .env maps to db.uri
        frozen=True,               # Makes the entire object immutable
        extra="ignore"             # Ignores unknown env vars safely
    )

    # --- General App Defaults ---
    environment: str = Field(default="development", pattern="^(development|staging|production)$")
    app_name: str = Field(default="BugFixer AI")
    debug_mode: bool = Field(default=False)
    
    # --- API & Security Defaults ---
    cors_allowed_origins: List[str] = Field(default=["http://localhost:3000"])
    rate_limit_per_minute: int = Field(default=100)
    jwt_secret_key: SecretStr = Field(...)
    jwt_algorithm: str = Field(default="HS256")
    
    # --- Pagination & Limits ---
    default_page_size: int = Field(default=20, le=100)
    max_upload_size_mb: int = Field(default=5)

    # --- Nested Infrastructure Configs ---
    db: DatabaseConfig
    redis: RedisConfig
    aws: AWSConfig
    stripe: StripeConfig


# ============================================================================
# 3. THE FAIL-FAST BOOT PROCESS
# ============================================================================

try:
    # Instantiating the class triggers parsing and validation instantly.
    # This occurs at module load time, guaranteeing no application code runs if config is invalid.
    settings = AppSettings()
except ValidationError as e:
    print("🔥 CRITICAL BOOT FAILURE: Invalid or missing Environment Variables!", file=sys.stderr)
    print(e.json(indent=2), file=sys.stderr)
    sys.exit(1) # Immediately kill the process with exit code 1