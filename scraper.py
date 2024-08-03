from contact_info import ContactInfoExtractor

class ScraperEngine:
    def __init__(self):
        self.extractor = ContactInfoExtractor()

    def scrape_urls(self, urls):
        results = []
        for url in urls:
            try:
                contact_info = self.extractor.extract_contact_info(url)
                if contact_info:
                    results.extend(contact_info)
            except Exception as e:
                print(f"Error scraping {url}: {str(e)}")
        return results