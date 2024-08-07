import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Other config parameters...
    CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH', '/usr/local/bin/chromedriver')

    # Rate limiting configuration
    GLOBAL_RATE_LIMIT = float(os.getenv('GLOBAL_RATE_LIMIT', '10'))  # requests per second
    GLOBAL_TIME_PERIOD = float(os.getenv('GLOBAL_TIME_PERIOD', '1'))  # in seconds
    DOMAIN_RATE_LIMIT = float(os.getenv('DOMAIN_RATE_LIMIT', '5'))  # requests per second per domain
    DOMAIN_TIME_PERIOD = float(os.getenv('DOMAIN_TIME_PERIOD', '1'))  # in seconds

config = Config()