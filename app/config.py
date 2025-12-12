"""Application configuration management."""

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings with validation."""

    # Kafka Configuration
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        env="KAFKA_BOOTSTRAP_SERVERS"
    )
    kafka_topic: str = Field(
        default="sourcedb.public.users",
        env="KAFKA_TOPIC"
    )
    kafka_consumer_group: str = Field(
        default="cdc-consumer-group",
        env="KAFKA_CONSUMER_GROUP"
    )

    # Postgres Configuration
    postgres_host: str = Field(
        default="localhost",
        env="POSTGRES_HOST"
    )
    postgres_port: int = Field(
        default=5432,
        env="POSTGRES_PORT"
    )
    postgres_user: str = Field(
        default="postgres",
        env="POSTGRES_USER"
    )
    postgres_password: str = Field(
        default="postgres",
        env="POSTGRES_PASSWORD"
    )
    postgres_db: str = Field(
        default="sourcedb",
        env="POSTGRES_DB"
    )

    # Application Configuration
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL"
    )
    data_contract_schema_path: str = Field(
        default="config/schemas/user_schema.json",
        env="DATA_CONTRACT_SCHEMA_PATH"
    )

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def postgres_connection_string(self) -> str:
        """Get Postgres connection string."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def schema_file_path(self) -> Path:
        """Get absolute path to schema file."""
        base_dir = Path(__file__).parent.parent
        return base_dir / self.data_contract_schema_path


# Global settings instance
settings = Settings()

