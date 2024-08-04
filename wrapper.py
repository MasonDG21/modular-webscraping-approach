from autoscraper import AutoScraper
import logging

class AutoScraperWrapper:
    def __init__(self):
        self.scraper = AutoScraper()
        self.logger = logging.getLogger(self.__class__.__name__)

    def build_scraper(self, url, wanted_list, update=False):
        try:
            result = self.scraper.build(url, wanted_list, update=update)
            self.logger.info(f"Built scraper for {url} with {len(result)} results")
            return result
        except Exception as e:
            self.logger.error(f"Error building scraper for {url}: {str(e)}")
            return None

    def get_result(self, url, grouped=False):
        try:
            result = self.scraper.get_result_similar(url, grouped=grouped)
            self.logger.info(f"Got {len(result)} results from {url}")
            return result
        except Exception as e:
            self.logger.error(f"Error getting results from {url}: {str(e)}")
            return None

    def save_scraper(self, filename):
        try:
            self.scraper.save(filename)
            self.logger.info(f"Saved scraper to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving scraper to {filename}: {str(e)}")

    def load_scraper(self, filename):
        try:
            self.scraper.load(filename)
            self.logger.info(f"Loaded scraper from {filename}")
        except Exception as e:
            self.logger.error(f"Error loading scraper from {filename}: {str(e)}")