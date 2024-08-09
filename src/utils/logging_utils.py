import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(log_level=logging.INFO):
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                os.path.join(log_dir, "scraper.log"),
                maxBytes=10*1024*1024,
                backupCount=5
            ),
            logging.StreamHandler()
        ]
    )

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG) # set to DEBUG to see all logs
    return logger