import asyncio
import argparse
import json
import socket
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

from src.scraper.extractors import ContactInfoExtractor
from src.utils.logging_utils import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

class AsyncScraper:
    def __init__(self, max_depth=3, max_pages_per_domain=50):
        self.logger = get_logger(self.__class__.__name__)
        self.extractor = ContactInfoExtractor()
        self.max_depth = max_depth
        self.max_pages_per_domain = max_pages_per_domain
        self.seen_urls = set()
        self.relevant_keywords = [
            'our-story', 'join-us', 'company-info', 'about-company', 'employees',
            'get-in-touch', 'people', 'divisions', 'team', 'board', 'contact-us',
            'directors', 'leadership', 'about-team', 'history', 'social',
            'departments', 'news', 'reach-us', 'offices', 'executives', 'work-with-us',
            'awards', 'directory', 'company', 'what-we-do', 'media', 'careers',
            'meet-the-team', 'press', 'corporate', 'insights', 'staff', 'publications',
            'events', 'blog', 'support', 'founder', 'who-we-are', 'management',
            'about-us', 'mission', 'locations', 'values', 'help', 'our-team', 'contact'
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    async def scrape(self, start_url):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            queue = asyncio.PriorityQueue()
            await queue.put((0, start_url, 0))  # (priority, url, depth)
            results = {}

            while not queue.empty():
                _, url, depth = await queue.get()
                if depth > self.max_depth or len(self.seen_urls) >= self.max_pages_per_domain:
                    continue

                if not self.is_valid_url(start_url, url):
                    continue

                self.seen_urls.add(url)
                html = await self.fetch_html(session, url)
                if html:
                    
                    # make sure html is a string before passing it to extract_contact_info
                    if isinstance(html, list):
                        self.logger.info(f"HTML received in `scrape` was type: `list` for URL: {url}")
                        html = ' '.join(map(str, html))
                    page_results = self.extractor.extract_contact_info(url, html)
                    self.logger.info(f"Results from ContactInfoExtractor() for {url}: {page_results}")
                    
                    if isinstance(page_results, dict):
                        page_results = [page_results]
                        
                    elif not isinstance(page_results, list):
                        self.logger.error(f"Unexpected result from extract_contact_info for URL {url}: {type(page_results)}")
                        page_results = []
                        
                    # Store results for each URL 
                    results[url] = page_results  

                    if depth < self.max_depth:
                        await self.enqueue_related_urls(queue, html, url, depth)

            return results

    async def fetch_html(self, session, url, max_retries=3):
        retries = 0
        while retries < max_retries:
            try:
                # First, try to resolve the domain
                domain = urlparse(url).netloc
                try:
                    socket.gethostbyname(domain)
                except socket.gaierror:
                    self.logger.error(f"DNS resolution failed for {domain}")
                    return None

                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        html = await response.text()
                        if isinstance(html, list):
                            self.logger.info(f"HTML received by `fetch_html` is type: `list` for URL: {url}")
                            html = ' '.join(map(str, html))
                        self.logger.info(f"Successfully scraped {url}")
                        return html
                    else:
                        self.logger.error(f"Error fetching {url}: HTTP status {response.status}")
            except aiohttp.ClientConnectorError as e:
                self.logger.error(f"Connection error for {url}: {str(e)}")
            except aiohttp.ClientError as e:
                self.logger.error(f"Client error for {url}: {str(e)}")
            except asyncio.TimeoutError:
                self.logger.error(f"Timeout error fetching {url}")
            except Exception as e:
                self.logger.error(f"Unexpected error fetching {url}: {str(e)}")
            
            retries += 1
            if retries < max_retries:
                wait_time = 2 ** retries  # Exponential backoff
                self.logger.info(f"Retrying {url} in {wait_time} seconds...")
                await asyncio.sleep(wait_time)

        self.logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None

    def is_valid_url(self, start_url, url):
        start_domain = urlparse(start_url).netloc
        url_domain = urlparse(url).netloc
        return start_domain == url_domain and url not in self.seen_urls

    async def enqueue_related_urls(self, queue, html, base_url, current_depth):
        if current_depth >= self.max_depth or len(self.seen_urls) >= self.max_pages_per_domain:
            return

        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a', href=True)
        
        for link in links:
            url = urljoin(base_url, link['href'])
            if self.is_valid_url(base_url, url):
                relevance_score = self.calculate_relevance_score(link, url)
                if relevance_score > 0:
                    await queue.put((100 - relevance_score, url, current_depth + 1))  # Lower score = higher priority

    def calculate_relevance_score(self, link, url):
        relevance_score = 0
        
        # check URL structure
        url_path = urlparse(url).path.lower()
        if any(keyword in url_path for keyword in self.relevant_keywords):
            relevance_score += 5
        
        # check link text
        link_text = link.text.lower()
        if any(keyword in link_text for keyword in self.relevant_keywords):
            relevance_score += 3
        
        # prioritize shorter paths
        path_depth = url_path.count('/')
        relevance_score += max(0, 3 - path_depth)
        
        return relevance_score

async def main(urls):
    scraper = AsyncScraper()
    all_results = {}
    for url in urls:
        try:
            if not url.startswith('http'):
                url = 'http://' + url
            results = await scraper.scrape(url)
            all_results[url] = results
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            all_results[url] = []
    return all_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Asynchronous web scraper for contact information.")
    parser.add_argument("urls", nargs="+", help="URLs to scrape")
    args = parser.parse_args()

    results = asyncio.run(main(args.urls))
    print(json.dumps(results, indent=2))