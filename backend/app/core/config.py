import os
from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "ResearchMatch"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = "default-insecure-secret-key-32-chars-min-for-dev-only"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours
    
    # Database
    DATABASE_URL: str = "postgresql://research_user:research_password@localhost:5433/researchmatch"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Providers
    OPENALEX_POLITE_EMAIL: str = "researchmatch@example.com"
    OPENALEX_API_KEY: Optional[str] = None
    SEMANTIC_SCHOLAR_API_KEY: Optional[str] = None
    CROSSREF_POLITE_EMAIL: str = "researchmatch@example.com"
    
    # Embedding Model
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # Data Retention (Days to keep user search query descriptions; 0 = delete immediately after search run)
    SEARCH_QUERY_RETENTION_DAYS: int = 30
    
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
