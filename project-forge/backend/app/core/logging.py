"""Logging configuration."""
import logging
import sys
from pathlib import Path
from app.core.config import settings

# Create logs directory if it doesn't exist
log_file_path = Path(settings.APP_LOG_FILE)
log_file_path.parent.mkdir(parents=True, exist_ok=True)

# Configure root logger
logging.basicConfig(
    level=logging.INFO if settings.APP_ENV == "dev" else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.APP_LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)

# Get logger for this module
logger = logging.getLogger("project-forge")


def setup_logging():
    """Setup application logging."""
    logger.info("Logging configured")
    logger.info(f"Log file: {settings.APP_LOG_FILE}")
    logger.info(f"Environment: {settings.APP_ENV}")



