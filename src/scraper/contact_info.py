import sys
import os
import re
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from urllib.parse import urljoin
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.logging_utils import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

class BaseExtractor(ABC):
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def extract(self, content):
        pass

    def clean_text(self, text):
        """Remove extra whitespace and normalize text."""
        return ' '.join(text.split())

    def find_all_matches(self, pattern, text):
        """Find all matches of a regex pattern in the text."""
        return re.findall(pattern, text)

    def log_extraction(self, content_type, results):
        """Log the results of an extraction."""
        self.logger.info(f"Extracted {len(results)} {content_type}(s)")
        for result in results:
            self.logger.debug(f"Extracted {content_type}: {result['value']}")

    def safe_extract(self, content):
        """Safely perform extraction with error handling."""
        try:
            results = self.extract(content)
            self.log_extraction(self.__class__.__name__.replace('Extractor', '').lower(), results)
            return results
        except Exception as e:
            self.logger.error(f"Error during extraction: {str(e)}")
            return []

class EmailExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    def extract(self, content):
        cleaned_content = self.clean_text(content)
        emails = self.find_all_matches(self.email_pattern, cleaned_content)
        return [{'type': 'email', 'value': email} for email in emails]

class FullNameExtractor(BaseExtractor):
    def __init__(self):
        self.name_pattern = re.compile(r'\b(?!(?:Email|Contact|sent by)\b)(?:Dr\.|Mr\.|Ms\.|Mrs\.|Prof\.)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b')
        super().__init__()  # Ensure BaseExtractor's constructor is called
        
    def extract(self, content):
        matches = self.name_pattern.findall(content)
        return [{'type': 'name', 'value': name.strip()} for name in matches]

class PhoneExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()
        self.phone_pattern = r'\+?[\d\s.-]+\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'

    def extract(self, content):
        cleaned_content = self.clean_text(content)
        phone_numbers = self.find_all_matches(self.phone_pattern, cleaned_content)
        return [{'type': 'phone', 'value': phone.strip()} for phone in phone_numbers]

class TitleExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()
        self.title_keywords = [
            'CEO', 'CTO', 'CFO', 'COO', 'President', 'Vice President', 'Director',
            'Manager', 'Engineer', 'Developer', 'Designer', 'Analyst', 'Specialist',
            # ... (rest of the keywords)
        ]
        self.title_pattern = r'\b(' + '|'.join(self.title_keywords) + r')\b'

    def extract(self, content):
        cleaned_content = self.clean_text(content)
        matches = self.find_all_matches(self.title_pattern, cleaned_content)
        return [{'type': 'title', 'value': title} for title in matches]

class HTMLParser:
    def parse(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        parsed_content = {
            'text': soup.get_text(),
            'meta': self._extract_meta(soup),
            'links': self._extract_links(soup),
            'contact_elements': self._extract_contact_elements(soup)
        }
        return parsed_content

    def _extract_meta(self, soup):
        return [tag.get('content', '') for tag in soup.find_all('meta') if 'description' in tag.get('name', '').lower() or 'keywords' in tag.get('name', '').lower()]

    def _extract_links(self, soup):
        return [{'text': a.get_text(), 'href': a.get('href')} for a in soup.find_all('a', href=True)]

    def _extract_contact_elements(self, soup):
        return [elem.get_text() for elem in soup.find_all(['a', 'p', 'div', 'span']) if 'contact' in elem.get('class', []) or 'contact' in elem.get('id', '')]

class ResultAggregator:
    def aggregate(self, results):
        aggregated = {}
        for result in results:
            if result['type'] not in aggregated:
                aggregated[result['type']] = set()
            aggregated[result['type']].add(result['value'])
        
        return [{'type': k, 'value': v} for k, vs in aggregated.items() for v in vs]
    

class ExtractorRegistry:
    def __init__(self):
        self.extractors = {}

    def register(self, name, extractor_class):
        if not issubclass(extractor_class, BaseExtractor):
            raise ValueError("Extractor must inherit from BaseExtractor")
        self.extractors[name] = extractor_class()

    def get_extractor(self, name):
        return self.extractors.get(name)

    def get_all_extractors(self):
        return list(self.extractors.values())


class ContactInfoExtractor:
    def __init__(self):
        self.registry = ExtractorRegistry()
        self.registry.register('email', EmailExtractor)
        self.registry.register('name', FullNameExtractor)
        self.registry.register('phone', PhoneExtractor)
        self.registry.register('title', TitleExtractor)
        self.html_parser = HTMLParser()
        self.result_aggregator = ResultAggregator()

    def extract_contact_info(self, url, html):
        try:
            parsed_content = self.html_parser.parse(html)
            results = []
            for extractor in self.registry.get_all_extractors():
                results.extend(extractor.extract(parsed_content['text']))
                for meta in parsed_content['meta']:
                    results.extend(extractor.extract(meta))
                for link in parsed_content['links']:
                    results.extend(extractor.extract(link['text']))
                    if isinstance(extractor, EmailExtractor) and link['href'].startswith('mailto:'):
                        results.append({'type': 'email', 'value': link['href'][7:]})
                for element in parsed_content['contact_elements']:
                    results.extend(extractor.extract(element))

            return self.result_aggregator.aggregate(results)
        except Exception as e:
            logger.error(f"Error extracting contact info from {url}: {str(e)}")
            return []

# Usage example
if __name__ == "__main__":
    extractor = ContactInfoExtractor()
    sample_html = """
    <html><body>
    <p>John Doe - CEO</p>
    <p>Email: john.doe@example.com</p>
    <a href="mailto:jane@example.com">Contact Jane</a>
    <div class="contact">Phone: (123) 456-7890</div>
    </body></html>
    """
    results = extractor.extract_contact_info("https://example.com", sample_html)
    print(results)
