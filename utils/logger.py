import logging
import sys
from typing import Optional

def setup_logger(name: str = __name__, level: Optional[int] = None) -> logging.Logger:
    """
    Set up and configure a logger with console output.

    Args:
        name: Name of the logger
        level: Logging level (defaults to INFO)

    Returns:
        Configured logger instance
    """
    if level is None:
        level = logging.INFO

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding multiple handlers if logger already exists
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(console_handler)

    return logger

# Create a default logger for the application
logger = setup_logger('zabbix_template_generator')
