# src/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    
    # Moderation Service
    MODERATION_SERVICE_URL = os.getenv("MODERATION_SERVICE_URL", "http://localhost:8001")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./neomarket.db")
    
    # App
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

settings = Settings()