import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    
    MODERATION_SERVICE_URL = os.getenv("MODERATION_SERVICE_URL", "http://localhost:8001")
    # Legacy names remain as fallbacks; direction-specific names follow the canonical event contract.
    MODERATION_SERVICE_KEY = os.getenv("MODERATION_SERVICE_KEY", "moderation-secret-key-123")
    B2B_TO_MOD_KEY = os.getenv("B2B_TO_MOD_KEY", "b2b-secret-key-123")
    MOD_TO_B2B_KEY = os.getenv("MOD_TO_B2B_KEY", MODERATION_SERVICE_KEY)
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./neomarket.db")
    
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

    B2C_SERVICE_URL = os.getenv("B2C_SERVICE_URL", "http://localhost:8002")

    B2C_SERVICE_KEY = os.getenv("B2C_SERVICE_KEY", "b2c-secret-key-123")
    B2C_TO_B2B_KEY = os.getenv("B2C_TO_B2B_KEY", B2C_SERVICE_KEY)
    B2B_TO_B2C_KEY = os.getenv("B2B_TO_B2C_KEY", B2C_SERVICE_KEY)

settings = Settings()