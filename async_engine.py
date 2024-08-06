import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from contact_info import ContactInfoExtractor
import argparse
import json
import logging
import socket

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AsyncScraper:
    def __init__(self, max_depth=3, max_pages_per_domain=50):
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
            results = []

            while not queue.empty():
                _, url, depth = await queue.get()
                if depth > self.max_depth or len(self.seen_urls) >= self.max_pages_per_domain:
                    continue

                if not self.is_valid_url(start_url, url):
                    continue

                self.seen_urls.add(url)
                html = await self.fetch_html(session, url)
                if html:
                    page_results = self.extractor.extract_contact_info(url, html)
                    results.extend(page_results)

                    if depth < self.max_depth:
                        await self.enqueue_related_urls(queue, html, url, depth)

            return results

    async def fetch_html(self, session, url):
        try:
            # First, try to resolve the domain
            domain = urlparse(url).netloc
            try:
                socket.gethostbyname(domain)
            except socket.gaierror:
                logging.error(f"DNS resolution failed for {domain}")
                return None

            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logging.error(f"Error fetching {url}: HTTP status {response.status}")
        except aiohttp.ClientConnectorError as e:
            logging.error(f"Connection error for {url}: {str(e)}")
        except aiohttp.ClientError as e:
            logging.error(f"Client error for {url}: {str(e)}")
        except asyncio.TimeoutError:
            logging.error(f"Timeout error fetching {url}")
        except Exception as e:
            logging.error(f"Unexpected error fetching {url}: {str(e)}")
        return None

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
            logging.error(f"Error scraping {url}: {str(e)}")
            all_results[url] = []
    return all_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Asynchronous web scraper for contact information.")
    parser.add_argument("urls", nargs="+", help="URLs to scrape")
    args = parser.parse_args()

    results = asyncio.run(main(args.urls))
    print(json.dumps(results, indent=2))