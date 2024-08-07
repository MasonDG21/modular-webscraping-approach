import logging
import os

def setup_logging(log_level=logging.INFO):
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "scraper.log")),
            logging.StreamHandler()
        ]
    )

def get_logger(name):
    return logging.getLogger(name)