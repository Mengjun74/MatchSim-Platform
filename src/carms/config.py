from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://carms_user:carms_password@localhost:5432/carms_db"
    RAW_DATA_DIR: str = "data/raw"

    class Config:
        env_file = ".env"

settings = Settings()
