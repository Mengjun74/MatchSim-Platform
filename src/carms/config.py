"""
Configuration management for the CaRMS Platform.
Uses Pydantic Settings to manage environment variables and defaults.
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    """
    DATABASE_URL: str = "postgresql+psycopg2://carms_user:carms_password@localhost:5432/carms_db"
    RAW_DATA_DIR: str = "data/raw"

    def __init__(self, **data):
        super().__init__(**data)
        import os
        # Fallback for Docker environments where host might be 'postgres' instead of 'localhost'
        if os.getenv("DAGSTER_HOME") and "localhost" in self.DATABASE_URL:
             self.DATABASE_URL = self.DATABASE_URL.replace("localhost", "postgres")

    class Config:
        env_file = ".env"
        extra = "ignore"

import os

# Default database URL fallback based on environment
default_db = "postgresql+psycopg2://carms_user:carms_password@localhost:5432/carms_db"
if os.getenv("DAGSTER_HOME") and not os.getenv("DATABASE_URL"):
    default_db = "postgresql+psycopg2://carms_user:carms_password@postgres:5432/carms_db"

settings = Settings()
print(f"LOADING SETTINGS: DATABASE_URL={settings.DATABASE_URL}")

