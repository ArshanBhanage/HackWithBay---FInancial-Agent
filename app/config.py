"""Configuration settings for the Financial Contract Drift Monitor."""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Pathway Configuration
    pathway_runtime_url: str = "http://localhost:8080"
    pathway_api_key: Optional[str] = None
    
    # LandingAI Configuration
    landingai_api_key: Optional[str] = None
    landingai_base_url: str = "https://api.landing.ai"
    
    # AI Agent Configuration
    anthropic_api_key: Optional[str] = None
    
    # Database Configuration
    database_url: str = "sqlite:///financial_contracts.db"
    redis_url: str = "redis://localhost:6379/0"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: str = "your_secret_key_here"
    
    # File Storage
    upload_dir: str = "./uploads"
    processed_dir: str = "./processed"
    
    # Webhook Configuration
    webhook_secret: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    crm_webhook_url: Optional[str] = None
    
    # Monitoring Configuration
    drift_check_interval: int = 3600  # seconds
    alert_retention_days: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Ensure directories exist
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.processed_dir, exist_ok=True)
