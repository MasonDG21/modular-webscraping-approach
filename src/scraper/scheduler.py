"""
Module schedules Web page downloads.
it "crawls" new links it discovers.
And routes downloaded Web pages to appropriate callbacks.

# Example Usage
```
def callback(url, success, html):
    print(html)

s = DownloadScheduler(callback, initial=['https://www.google.com/search?q=shark+week'])
s.schedule()
```
"""
import asyncio
import os
import subprocess
from collections import deque, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from urllib.parse import urlparse

import chardet
from aiolimiter import AsyncLimiter

from src.config import config
from src.scraper.urls import urls_from_html
from src.scraper.downloader import download_with_rate_limit
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class RateLimitedScheduler:
    def __init__(self):
        self.global_limiter = AsyncLimiter(config.GLOBAL_RATE_LIMIT, config.GLOBAL_TIME_PERIOD)
        self.domain_limiters = defaultdict(
            lambda: AsyncLimiter(config.DOMAIN_RATE_LIMIT, config.DOMAIN_TIME_PERIOD)
        )
        self.queue = asyncio.Queue()

    def extract_domain(self, url):
        return urlparse(url).netloc

    async def add_url(self, url):
        await self.queue.put(url)

    async def get_url(self):
        url = await self.queue.get()
        domain = self.extract_domain(url)
        try:
            async with self.global_limiter:
                async with self.domain_limiters[domain]:
                    logger.debug(f"Rate limit check passed for URL: {url}")
                    return url
        except asyncio.TimeoutError:
            logger.warning(f"Rate limit exceeded for domain: {domain}. Requeueing URL: {url}")
            await self.add_url(url)  # Requeue the URL
            return None
        
    # asynchronous generator that yields rate-limited URLs.
    async def schedule(self):
        while True:
            url = await self.get_url()
            if url:
                yield url
            else:
                await asyncio.sleep(1)  # Wait before trying again

# Download Scheduler uses RateLimitedScheduler to download Web pages
class DownloadScheduler:
    def __init__(self, callback, initial=None, processes=5, url_filter=None):
        """ DownloadScheduler downloads Web pages at certain URLs
        Schedules newly discovered links, adding them to a queue, in a "crawling" fashion
        Args:
            callback (func): Callback function whenever a Web page downloads
            initial ([Url]): List of `Url`s to start the "crawling"
            processes (int): The maximum number of download processes to parallelize
        """
        self.logger = get_logger(self.__class__.__name__)
        self.callback = callback
        self.queue = deque(initial or [])
        self.visited = set()
        self.processes = processes
        self.url_filter = url_filter
        self.logger.debug(f"DownloadScheduler initialized with {len(self.queue)} initial URLs")
        self.rate_limiter = RateLimitedScheduler()


    def download_complete(self, future, url):
        """ Callback when a download completes
        Args:
            future (Future): the (completed) future containing a Web site's HTML content.
            url (Url): the URL of downloaded Web page.
        """
        try:
            html = future.result()
            self.logger.debug(f"Downloaded content length for {url.url}: {len(html)}")
        except Exception as e:
            self.logger.error(f'Exception downloading {url.url}: {e}', exc_info=True)
        else:
            urls = list(filter(self.url_filter, urls_from_html(html, url.url)))
            self.queue.extendleft(urls)
            self.callback(url.url, html)


    async def rate_limited_download(self, url):
        await self.rate_limiter.add_url(url)
        rate_limited_url = await self.rate_limiter.get_url()
        if rate_limited_url:
            return await download_with_rate_limit(rate_limited_url, self.rate_limiter)
        return None


    def schedule(self):
        self.logger.info("Starting the scheduler")
        
        # Add initial URLs to the rate limiter.
        for url in self.queue:
            asyncio.get_event_loop().run_until_complete(self.rate_limiter.add_url(url))
        self.queue.clear()
        
        with ProcessPoolExecutor(max_workers=self.processes) as executor:
            while True:
                urls = []
                for _ in range(self.processes):
                    url = asyncio.get_event_loop().run_until_complete(self.rate_limiter.get_url())
                    if url and url not in self.visited:
                        urls.append(url)
                        self.visited.add(url)
                        
                if not urls:
                    if self.queue:
                        continue # Try again if there are more URLs in the queue
                    else:
                        break # Exit if there are no more URLs
                
                loop = asyncio.get_event_loop()
                future_to_url = {
                    executor.submit(lambda u: loop.run_until_complete(self.rate_limited_download(u)), url): url 
                    for url in urls
                }
                for future in as_completed(future_to_url):
                    self.download_complete(future, future_to_url[future])
        
        self.logger.info("Scheduler finished")