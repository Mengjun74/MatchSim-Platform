from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://carms_user:carms_password@localhost:5432/carms_db"
    RAW_DATA_DIR: str = "data/raw"

    # Override default if in Docker and no env var set
    def __init__(self, **data):
        super().__init__(**data)
        import os
        if os.getenv("DAGSTER_HOME") and "localhost" in self.DATABASE_URL:
             # We are likely in Docker but got localhost default. 
             # Check if we should switch to postgres host.
             # This is a fallback patch.
             self.DATABASE_URL = self.DATABASE_URL.replace("localhost", "postgres")

    class Config:
        env_file = ".env"
        extra = "ignore"

# Logic to handle Docker vs Local if Pydantic fails (debugging hack + fix)
import os
# If we are in docker (DAGSTER_HOME is set), default to postgres host
default_db = "postgresql+psycopg2://carms_user:carms_password@localhost:5432/carms_db"
if os.getenv("DAGSTER_HOME") and not os.getenv("DATABASE_URL"):
    # Fallback for docker if env var missing
    default_db = "postgresql+psycopg2://carms_user:carms_password@postgres:5432/carms_db"

# However, let's rely on Pydantic, but print what we got
settings = Settings()
print(f"LOADING SETTINGS: DATABASE_URL={settings.DATABASE_URL}")

