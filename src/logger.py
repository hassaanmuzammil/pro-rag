import logging
from src.config import LOG_LEVEL

# Map config string to logging level
log_levels = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

log_level = log_levels.get(LOG_LEVEL.upper(), logging.INFO)

# Create logger
logger = logging.getLogger(__name__)   # safer than root logger
logger.setLevel(log_level)

# Create handler
stream_handler = logging.StreamHandler()
stream_handler.setLevel(log_level)

# Create formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
stream_handler.setFormatter(formatter)

# Avoid duplicate handlers if re-imported
if not logger.handlers:
    logger.addHandler(stream_handler)
