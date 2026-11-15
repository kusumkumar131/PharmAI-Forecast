from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Pharmacy Medicine Demand & Expiry-Risk Forecasting"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "pharmacy_secret_key_production_grade_jwt_token_2026_super_secure"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "pharmacy_forecasting"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        extra = "allow"

settings = Settings()
