"""Configuration management for the Slack Trophy backend."""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # Slack Configuration
    SLACK_USER_TOKEN: str = os.getenv("SLACK_USER_TOKEN", "")
    SLACK_SIGNING_SECRET: str = os.getenv("SLACK_SIGNING_SECRET", "")  # Optional, for webhooks
    
    # CORS Configuration
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Backend Configuration
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    # Cache Configuration
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "600"))  # 10 minutes default
    
    # Date Range Validation
    MAX_DATE_RANGE_DAYS: int = 365  # Maximum 1 year range to prevent DoS
    
    # Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    
    @classmethod
    def validate(cls) -> None:
        """Validate that required environment variables are set."""
        if not cls.SLACK_USER_TOKEN:
            raise ValueError("SLACK_USER_TOKEN environment variable is required")
        # SLACK_SIGNING_SECRET is optional (only needed for webhooks)
    
    @classmethod
    def get_cors_origins(cls) -> list[str]:
        """Get CORS allowed origins."""
        origins = [cls.FRONTEND_URL]
        # Always allow common dev ports
        for port in ("3000", "3001", "5500", "5173"):
            origin = f"http://localhost:{port}"
            if origin not in origins:
                origins.append(origin)
        return origins


# Global settings instance
settings = Settings()

