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
import os
import subprocess
import chardet
from collections import deque
from concurrent.futures import ProcessPoolExecutor, as_completed
from .urls import urls_from_html
from src.utils.logging_utils import setup_logging, get_logger

# configure the logging utility
setup_logging()
logger = get_logger(__name__)

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

    def schedule(self):
        """ Begins downloading the Web pages in the queue.
        Calls `download_complete()` when a download finishes.
        """
        self.logger.info("Starting the scheduler")
        with ProcessPoolExecutor(max_workers=self.processes) as executor:
            while self.queue:
                urls = pop_chunk(self.processes, self.queue.pop)
                self.visited |= set(urls)
                future_to_url = {executor.submit(download, url): url for url in urls}
                for f in as_completed(future_to_url, timeout=15):
                    self.download_complete(f, future_to_url[f])
        self.logger.info("Scheduler finished")

def pop_chunk(n, fn):
    """ Calls fn() n-times, putting the return value in a list
    Args:
        n (int): maximum size of the chunk
        fn (func): function to call (probably some collection instance's pop() function)
    Returns:
        ([]) list of whatever items that were in 
    Example:
        >>> foo = [1, 2, 3, 4, 5]
        >>> pop_chunk(3, foo.pop)
        [5, 4, 3]
        >>> foo
        [1, 2]
    """
    return_values = []
    for _ in range(n):
        try:
            return_values.append(fn())
        except IndexError:
            break
    return return_values

def download(url):
    """ Uses 'downloader.py' to download a Web page's HTML content.
    Args:
        url (Url): The URL whose HTML we want to download/fetch
    Returns:
        (str) A string of the HTML content found at the given URL
    Note:
        This method is parallelized
    """
    logger = get_logger('DownloadScheduler.download')
    logger.debug(f"Starting download for URL: {url.url}")
    abs_path = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(abs_path, 'downloader.py')
    args = ['python', script_path, url.url]
    try:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            logger.error(f"Error downloading {url.url}: {stderr.decode('utf-8')}")
            return ""
        detected_encoding = chardet.detect(stdout)['encoding']
        logger.debug(f"Detected encoding for {url.url}: {detected_encoding}")
        html = stdout.decode(detected_encoding)
        logger.debug(f"Downloaded content length for {url.url}: {len(html)}")
        return html
    except Exception as e:
        logger.error(f"Exception during download of {url.url}: {e}", exc_info=True)
        return ""