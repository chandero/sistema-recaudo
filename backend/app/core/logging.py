import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path


def setup_logger(name: str, log_file: str = None, level: int = logging.INFO):
    """Function to setup as many loggers as you want"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    
    # Create handler
    if log_file:
        handler = RotatingFileHandler(
            log_dir / log_file,
            maxBytes=10000000,  # 10MB
            backupCount=5
        )
    else:
        handler = logging.StreamHandler()
    
    handler.setFormatter(formatter)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    
    return logger


# Create the main logger instance
logger = setup_logger(__name__, "app.log")