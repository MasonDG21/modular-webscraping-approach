import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from contact_info import ContactInfoExtractor
import argparse
import json

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

    async def scrape(self, start_url):
        async with aiohttp.ClientSession() as session:
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
                    page_results = self.extractor.extract_contact_info(url)
                    results.extend(page_results)

                    if depth < self.max_depth:
                        await self.enqueue_related_urls(queue, html, url, depth)

            return results

    async def fetch_html(self, session, url):
        try:
            async with session.get(url) as response:
                return await response.text()
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None

    async def enqueue_related_urls(self, queue, html, base_url, current_depth):
        if current_depth >= self.max_depth or len(self.seen_urls) >= self.max_pages_per_domain:
            return

        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a', href=True)
        
        for link in links:
            url = urljoin(base_url, link['href'])
            if self.is_valid_url(base_url, url) and url not in self.seen_urls:
                relevance_score = self.calculate_relevance_score(link, url)
                if relevance_score > 0:
                    await queue.put((100 - relevance_score, url, current_depth + 1))  # Lower score = higher priority

    def is_valid_url(self, start_url, url):
        base_domain = urlparse(start_url).netloc
        url_domain = urlparse(url).netloc
        return base_domain == url_domain and url not in self.seen_urls
    
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

# Usage
async def main(urls):
    scraper = AsyncScraper()
    all_results = {}
    for url in urls:
        results = await scraper.scrape(url)
        all_results[url] = results
    return all_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Asynchronous web scraper for contact information.")
    parser.add_argument("urls", nargs="+", help="URLs to scrape")
    args = parser.parse_args()

    results = asyncio.run(main(args.urls))
    print(json.dumps(results, indent=2))