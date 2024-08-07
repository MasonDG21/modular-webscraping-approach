"""
Utilities to handle and deal with URLs.
"""

import re
from urllib.parse import urljoin, urlparse
from src.utils.logging_utils import setup_logging, get_logger

# configure the logging utility
logger = get_logger(__name__)

class Url:
    """ Validation, normalization of a URL.

    Note on Url "uniqueness":
        >>> Url('http://google.com') == Url('https://google.com') == Url('https://google.com?q=shark+week')
        True
    """
    def __init__(self, url):
        self.url = url.lower()
        parsed = urlparse(self.url)
        if not parsed.netloc:
            logger.error(f'Invalid URL: {self.url}. Not a complete URL.')
            raise ValueError(f'{self.url} is not a complete URL.')
        logger.debug(f"URL initialized (urls.py): {self.url}")

    def normalized(self):
        parsed = urlparse(self.url)
        normalized = f'http://{parsed.netloc}{parsed.path}'
        logger.debug(f"Normalized URL: {normalized}")
        return normalized

    def __hash__(self):
        return hash(self.normalized())

    def __eq__(self, other):
        return self.normalized() == other.normalized()

    def __str__(self):
        return self.normalized()

    def __repr__(self):
        return self.normalized()


def url_filter(url):
    """ Filter to remove non HTML URLs """
    if url.endswith(('.json', '.css', '.png', '.jpg', '.svg', '.ico', '.js', '.gif', '.pdf', '.xml')):
        logger.debug(f"Filtered out non-HTML URL: {url}")
        return False
    if url.startswith(('mailto',)):
        logger.debug(f"Filtered out 'mailto' URL: {url}")
        return False
    logger.debug(f"URL passed filter: {url}")
    return True


def urls_from_html(html, html_url, Class_=Url):
    """ Parses HTML for URLs

    Args:
        html (str): HTML content
        html_url (str): URL of the HTML content. Required to create full URLs from relative paths.
        Class_ (class): The type of URL objects to return

    Returns:
        ([Class_]) list of Class_ instances.
    """

    urls = re.findall(r'href="(.*?)"', html)
    logger.info(f'Found {len(urls)} raw URLs in HTML from: {html_url}')

    # build absolute URLs from relative paths
    for i, url in enumerate(urls):
        parsed = urlparse(url)
        if not parsed.netloc:
            urls[i] = urljoin(html_url, url)

    # Create `Class_` instances from URLs we found in the HTML
    unique = set()
    for u in urls:
        try:
            if url_filter(u):
                unique.add(Class_(u))
        except ValueError:
            logger.warning(f"Invalid URL found: {u}")
            pass
    logger.info(f'Extracted {len(unique)} unique, valid URLs from: {html_url}')
    return list(unique)
