from src.scraper.extractors import ContactInfoExtractor
from src.scraper.scheduler import DownloadScheduler
from src.scraper.urls import Url
from src.scraper.wrapper import Wrapper
from src.utils.logging_utils import get_logger

class ScraperEngine:
    def __init__(self, use_auto_scraper=False):
        self.logger = get_logger(self.__class__.__name__)
        self.extractor = ContactInfoExtractor()
        self.use_auto_scraper = use_auto_scraper
        if use_auto_scraper:
            self.auto_scraper = Wrapper()
        self.logger.debug(f"ScraperEngine initialized with use_auto_scraper={use_auto_scraper}")

    def scrape_urls(self, urls):
        results = []
        self.logger.info(f"Starting to scrape {len(urls)} URLs")

        def callback(url, html):
            try:
                self.logger.debug(f"Scraping URL: {url}")
                if self.use_auto_scraper:
                    contact_info = self.auto_scraper.get_result(url)
                else:
                    contact_info = self.extractor.extract_contact_info(url, html)
                if contact_info:
                    results.extend(contact_info)
                    self.logger.info(f"Found {len(contact_info)} contacts at {url}")
                else:
                    self.logger.info(f"No contacts found at {url}")
            except Exception as e:
                self.logger.error(f"Error scraping {url}: {str(e)}", exc_info=True)

        initial_urls = [Url(url) for url in urls]
        self.logger.debug(f"Initial URLs prepared: {initial_urls}")

        try:
            scheduler = DownloadScheduler(callback, initial=initial_urls, processes=4)
            self.logger.debug("DownloadScheduler initialized")
            scheduler.schedule()
            self.logger.info("Scheduler finished")
        except Exception as e:
            self.logger.error("Error during scheduling: ", exc_info=True)

        self.logger.info(f"Total results found: {len(results)}")
        return results

# import os
# import logging
# from contact_info import ContactInfoExtractor
# from scraper.scheduler import DownloadScheduler
# from scraper.urls import Url

# # Ensure the 'logs' directory exists
# log_dir = 'logs'
# if not os.path.exists(log_dir):
#     os.makedirs(log_dir)
    
# # Configure logging
# logging.basicConfig(
#     level=logging.DEBUG,  # Set to DEBUG to capture all types of logs
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler(os.path.join(log_dir, "scraper_engine.log")),
#         logging.StreamHandler()
#     ]
# )

# class ScraperEngine:
#     def __init__(self):
#         self.logger = logging.getLogger(self.__class__.__name__)
#         self.extractor = ContactInfoExtractor()
#         self.logger.debug("ScraperEngine initialized with ContactInfoExtractor")

#     def scrape_urls(self, urls):
#         results = []
#         self.logger.info(f"Starting to scrape {len(urls)} URLs")

#         def callback(url, html):
#             try:
#                 self.logger.debug(f"Scraping URL: {url}")
#                 self.logger.debug(f"HTML content length: {len(html)}")
#                 contact_info = self.extractor.extract_contact_info(url, html)
#                 if contact_info:
#                     results.extend(contact_info)
#                     self.logger.info(f"Found {len(contact_info)} contacts at {url}")
#                 else:
#                     self.logger.info(f"No contacts found at {url}")
#             except Exception as e:
#                 self.logger.error(f"Error scraping {url}: {str(e)}", exc_info=True)

#         initial_urls = [Url(url) for url in urls]
#         self.logger.debug(f"Initial URLs prepared: {initial_urls}")

#         try:
#             scheduler = DownloadScheduler(callback, initial=initial_urls, processes=4)
#             self.logger.debug("DownloadScheduler initialized")
#             scheduler.schedule()
#             self.logger.info("Scheduler finished")
#         except Exception as e:
#             self.logger.error("Error during scheduling: ", exc_info=True)

#         self.logger.info(f"Total results found: {len(results)}")
#         return results
