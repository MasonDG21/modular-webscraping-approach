import argparse
import os
import asyncio
from sys import platform

from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEnginePage

from src.utils.logging_utils import setup_logging, get_logger
from src.config import config
from aiolimiter import AsyncLimiter

# configure the logging utility
setup_logging()
logger = get_logger(__name__)

class WebkitRenderer(QWebEnginePage):
    """ Class to render a given URL """

    def __init__(self, rendered_callback, rate_limiter=None):
        """
        Args:
            rendered_callback (func): called once a Web page is rendered.

        Callback Args:
            url (str): The URL of the Web page.
            html (str): HTML of the rendered Web page.
        """
        self.logger = get_logger(self.__class__.__name__)
        self.app = QApplication([])
        super(WebkitRenderer, self).__init__()
        self.loadFinished.connect(self._loadFinished)
        self.rendered_callback = rendered_callback
        self.rate_limiter = rate_limiter
        self.logger.debug("WebkitRenderer initialized")

    def javaScriptConsoleMessage(self, msg_level, p_str, p_int, p_str_1):
        """ Ignore console messages """
        pass

    async def render(self, url):
        """ Download and render the URL
        Args:
            url (str): The URL to load.
        """
        self.logger.info(f"Rendering URL: {url}")
        if self.rate_limiter:
            async with self.rate_limiter:
                self.load(QUrl(url))
                await asyncio.get_event_loop().run_in_executor(None, self.app.exec_)
        else:
            self.load(QUrl(url))
            self.app.exec()  # put app into infinite loop, listening to signals/events

    def _loadFinished(self, result):
        """ Event handler - A Web page finished loading
        Args:
            result (bool): success indicator
        """
        url = self.url().toString()
        if result:
            self.logger.info(f"Successfully loaded URL: {url}")
            self.toHtml(self.html_callback)  # async and takes a callback
        else:
            self.logger.error(f"Failed to load URL: {url}")
            self.rendered_callback(url, None)
            self.app.quit()

    def html_callback(self, data):
        """ Receives rendered Web Page's HTML """
        url = self.url().toString()
        if data:
            self.logger.info(f"Received HTML for URL: {url}")
            self.logger.debug(f"HTML content length: {len(data)}")
        else:
            self.logger.warning(f"No HTML received for URL: {url}")
        self.rendered_callback(url, data)
        self.app.quit()  # break app out of infinite loop

async def download_with_rate_limit(url, rate_limiter):
    """ Download a URL with rate limiting
    Args:
        url (str): The URL to download
        rate_limiter (AsyncLimiter): The rate limiter
    Returns:
        str: The HTML content of the URL
    """
    def callback(url, html):
        if html:
            logger.info(f"Successfully downloaded URL: {url}")
            logger.debug(f"HTML content length: {len(html)}")
        else:
            logger.error(f"Failed to download URL: {url}")
        print(html.encode('utf-8').decode('utf-8'))
        
    wr = WebkitRenderer(callback)
    await wr.render(url)

if __name__ == '__main__':
    if platform == 'darwin':  # if mac: hide python launch icons
        from PyQt5 import AppKit
        info = AppKit.NSBundle.mainBundle().infoDictionary()
        info["LSBackgroundOnly"] = "1"
    # render_engine.py needs to be able to run as a
    # standalone script to achieve parallelization.
    parser = argparse.ArgumentParser()
    parser.add_argument('url', type=str)
    args = parser.parse_args()
    
    # Create a rate limiter when running as a standalone script
    rate_limiter = AsyncLimiter(config.GLOBAL_RATE_LIMIT, config.GLOBAL_TIME_PERIOD)
    
    def cb(url, html):
        if html:
            logger.info(f"Successfully rendered URL: {url}")
            logger.debug(f"HTML content length: {len(html)}")
        else:
            logger.error(f"Failed to render URL: {url}")
        print(html.encode('utf-8').decode('utf-8'))
        
    logger.info(f"Starting rendering for URL: {args.url}")
    asyncio.run(download_with_rate_limit(args.url, rate_limiter))