import os
from functools import lru_cache

class Settings:
    APP_NAME: str = "VEGA DEFENCE INTELLIGENCE"
    API_VERSION: str = "v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./gotham.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-only-change-in-production-gotham-india-32chars!")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
    SEED_DEMO: bool = os.getenv("SEED_DEMO", "true").lower() == "true"
    MAX_UPLOAD_MB: int = 25

@lru_cache
def get_settings() -> Settings:
    return Settings()
