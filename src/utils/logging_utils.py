import logging
import os
from logging.handlers import RotatingFileHandler

class LevelFilter(logging.Filter):
    def __init__(self, level):
        self.level = level

    def filter(self, record):
        return record.levelno == self.level

def setup_logging(log_level=logging.DEBUG, console_output=True):
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create handlers for each log level
    handlers = {
        logging.DEBUG: RotatingFileHandler(os.path.join(log_dir, "debug.log"), maxBytes=10*1024*1024, backupCount=5),
        logging.INFO: RotatingFileHandler(os.path.join(log_dir, "info.log"), maxBytes=10*1024*1024, backupCount=5),
        logging.WARNING: RotatingFileHandler(os.path.join(log_dir, "warning.log"), maxBytes=10*1024*1024, backupCount=5),
        logging.ERROR: RotatingFileHandler(os.path.join(log_dir, "error.log"), maxBytes=10*1024*1024, backupCount=5),
        logging.CRITICAL: RotatingFileHandler(os.path.join(log_dir, "critical.log"), maxBytes=10*1024*1024, backupCount=5)
    }

    # Set formatter and filter for all handlers
    for level, handler in handlers.items():
        handler.setFormatter(formatter)
        handler.addFilter(LevelFilter(level))
        handler.setLevel(level)

    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add handlers to logger
    for handler in handlers.values():
        logger.addHandler(handler)

    # Add StreamHandler for console output
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)

def get_logger(name):
    return logging.getLogger(name)

def validator_logs(log_level=logging.DEBUG, console_output=True):
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    
    # Specific log file for DataValidator
    validator_log_handler = RotatingFileHandler(os.path.join(log_dir, "validator.log"), maxBytes=10*1024*1024, backupCount=5)
    validator_log_handler.setFormatter(formatter)
    validator_log_handler.setLevel(log_level)
    # validator_log_handler.flush = True

    # Create a logger for DataValidator
    logger = get_logger('DataValidator')
    logger.setLevel(log_level)
    logger.propagate = False

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add the handler to the logger
    logger.addHandler(validator_log_handler)

    # Add StreamHandler for console output if needed
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        logger.addHandler(console_handler)
    
    return logger