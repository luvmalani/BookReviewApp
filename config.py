import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database configuration
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/bookreview")
    
    # Redis configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_cache_ttl: int = int(os.getenv("REDIS_CACHE_TTL", "300"))  # 5 minutes
    
    # Application configuration
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Pagination
    default_page_size: int = int(os.getenv("DEFAULT_PAGE_SIZE", "10"))
    max_page_size: int = int(os.getenv("MAX_PAGE_SIZE", "100"))
    
    class Config:
        env_file = ".env"

settings = Settings()
