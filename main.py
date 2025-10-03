#!/usr/bin/env python3
"""
Financial Contract Drift Monitor
An Agent for Continuous Risk Tracking in Evolving Agreements

Main application entry point.
"""

import logging
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.api.main import app
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('financial_contract_monitor.log')
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting Financial Contract Drift Monitor...")
    logger.info(f"API will be available at http://{settings.api_host}:{settings.api_port}")
    logger.info(f"Upload directory: {settings.upload_dir}")
    logger.info(f"Processed directory: {settings.processed_dir}")
    
    # Log configuration status without exposing secrets
    logger.info("Configuration loaded from .env file")
    logger.info(f"LandingAI API configured: {'Yes' if settings.landingai_api_key else 'No (using mock extraction)'}")
    logger.info(f"Pathway API configured: {'Yes' if settings.pathway_api_key else 'No'}")
    logger.info(f"Database configured: {'Yes' if settings.database_url else 'No'}")
    logger.info(f"Webhook secret configured: {'Yes' if settings.webhook_secret else 'No'}")
    
    import uvicorn
    uvicorn.run(
        "app.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info"
    )
