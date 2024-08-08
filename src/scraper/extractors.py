import json
import sys
import os
import re
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from fuzzywuzzy import process
from collections import defaultdict
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
            'Coordinator', 'Administrator', 'Supervisor', 'Lead', 'Head', 'Chief',
            'Technician', 'Scientist', 'Pilot', 'Inspector', 'Consultant', 'Architect',
            'Operator', 'Instructor', 'Planner', 'Strategist', 'Estimator', 'Fabricator',
            'Assembler', 'Machinist', 'Welder', 'Mechanic', 'Tester', 'Trainer',
            'Project Manager', 'Program Manager', 'Systems Engineer', 'Avionics Engineer',
            'Test Engineer', 'Flight Engineer', 'Manufacturing Engineer', 'Quality Engineer',
            'Structural Engineer', 'Aerospace Engineer', 'Electrical Engineer', 'Software Engineer',
            'Mechanical Engineer', 'Materials Engineer', 'Safety Engineer', 'Reliability Engineer',
            'Design Engineer', 'Research Scientist', 'Principal Investigator', 'Field Service Engineer',
            'Compliance Manager', 'Logistics Manager', 'Supply Chain Manager', 'Production Manager',
            'Operations Manager', 'Business Development Manager', 'Customer Service Manager',
            'Integration Engineer', 'Mission Manager', 'Payload Specialist', 'Propulsion Engineer',
            'Satellite Engineer', 'Thermal Engineer', 'Dynamics Engineer', 'RF Engineer',
            'Guidance, Navigation, and Control (GNC) Engineer', 'Ordnance Engineer', 'Launch Director',
            'Ground Systems Engineer', 'Mission Operations Engineer', 'Systems Architect',
            'Configuration Manager', 'Risk Manager', 'Test Technician', 'Calibration Technician',
            'Electronics Technician', 'Maintenance Technician', 'Program Analyst', 'Budget Analyst',
            'Contract Administrator', 'Procurement Specialist', 'Inventory Manager', 'Supply Chain Analyst',
            'IT Manager', 'Cybersecurity Specialist', 'Data Scientist', 'AI Specialist', 'Robotics Engineer',
            'Control Systems Engineer', 'Optical Engineer', 'Spacecraft Operations Specialist',
            'Business Analyst', 'Marketing Manager', 'Sales Manager', 'Communications Manager',
            'Human Resources Manager', 'Talent Acquisition Specialist', 'Training Coordinator',
            'Safety Manager', 'Environmental Engineer', 'Sustainability Manager', 'Innovation Manager',
            'Customer Support Engineer', 'Technical Support Specialist', 'Field Operations Manager',
            'Quality Assurance Manager', 'Regulatory Affairs Manager', 'Patent Agent', 'Legal Counsel'
        ]

        self.title_pattern = r'\b(' + '|'.join(self.title_keywords) + r')\b'

    def extract(self, content):
        cleaned_content = self.clean_text(content)
        exact_matches = self.find_all_matches(self.title_pattern, cleaned_content)
        fuzzy_matches = self.fuzzy_match_titles(cleaned_content)
        
        results = [{'type': 'title', 'value': title, 'confidence': 1.0} for title in exact_matches]
        results.extend([{'type': 'title', 'value': title, 'confidence': score / 100} for title, score in fuzzy_matches])
        
        return results

    def fuzzy_match_titles(self, text):
        words = text.split()
        potential_titles = [' '.join(words[i:i+3]) for i in range(len(words))]
        matches = process.extract(potential_titles, self.title_keywords, limit=5)
        return [(match[0], match[1]) for match in matches if match[1] > 80]


class ContextualExtractor(BaseExtractor):
    """Extracts contextual information from HTML content.
    Attributes:
        registry (object): The registry object used to retrieve other extractors.
        context_keywords (dict): A dictionary containing contextual keywords categorized by weight.
    Methods:
        `extract(content)`: Extracts contextual information from the given HTML content.
        `find_contextual_elements(soup)`: Finds contextual elements in a BeautifulSoup object.
        `extract_from_element(element, context_weight)`: Extracts infor from a given element.
        `calculate_confidence(item, context_weight)`: Calculates confidence for extracted items.
        `extract_structured_data(soup)`: Extracts structured data from the BeautifulSoup object.
        """
    def __init__(self, registry):
        super().__init__()
        self.registry = registry
        self.context_keywords = {
            'high': ['about', 'team', 'contact', 'leadership', 'management', 'staff', 'employees', 'board', 'executives'],
            'medium': ['directory', 'people', 'department', 'faculty', 'personnel', 'crew', 'members'],
            'low': ['company', 'organization', 'group', 'division', 'unit']
        }

    def extract(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        contextual_elements = self.find_contextual_elements(soup)
        results = []
        for element, weight in contextual_elements:
            results.extend(self.extract_from_element(element, weight))
        
        # Extract structured data
        results.extend(self.extract_structured_data(soup))
        
        return results

    def find_contextual_elements(self, soup):
        elements = []
        for weight, keywords in self.context_keywords.items():
            for keyword in keywords:
                found_elements = soup.find_all(['div', 'section', 'article', 'aside', 'header', 'footer'], 
                                               class_=lambda x: x and keyword in x.lower())
                found_elements.extend(soup.find_all(['div', 'section', 'article', 'aside', 'header', 'footer'], 
                                                    id=lambda x: x and keyword in x.lower()))
                elements.extend([(elem, weight) for elem in found_elements])
        
        # Consider proximity to h1, h2, h3 tags with relevant keywords
        headers = soup.find_all(['h1', 'h2', 'h3'])
        for header in headers:
            if any(keyword in header.get_text().lower() for keywords in self.context_keywords.values() for keyword in keywords):
                next_sibling = header.find_next_sibling()
                if next_sibling:
                    elements.append((next_sibling, 'high'))
        
        return elements

    def extract_from_element(self, element, context_weight):
        results = []
        text = element.get_text()
        
        # Use other extractors
        for extractor_name in ['email', 'name', 'phone', 'title']:
            extractor = self.registry.get_extractor(extractor_name)
            if extractor:
                extracted = extractor.extract(text)
                for item in extracted:
                    confidence = self.calculate_confidence(item, context_weight)
                    results.append({**item, 'confidence': confidence})
        
        return results

    def calculate_confidence(self, item, context_weight):
        base_confidence = item.get('confidence', 0.5)
        weight_factor = {'high': 1.2, 'medium': 1.1, 'low': 1.0}
        return min(base_confidence * weight_factor[context_weight], 1.0)

    def extract_structured_data(self, soup):
        results = []
        
        # Extract vCard data
        vcard_elements = soup.find_all('div', class_='vcard')
        for vcard in vcard_elements:
            name = vcard.find(class_='fn')
            org = vcard.find(class_='org')
            email = vcard.find(class_='email')
            tel = vcard.find(class_='tel')
            
            if name:
                results.append({'type': 'name', 'value': name.get_text(), 'confidence': 0.9})
            if org:
                results.append({'type': 'organization', 'value': org.get_text(), 'confidence': 0.9})
            if email:
                results.append({'type': 'email', 'value': email.get_text(), 'confidence': 0.9})
            if tel:
                results.append({'type': 'phone', 'value': tel.get_text(), 'confidence': 0.9})
        
        # Extract JSON-LD data
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0]
                if data['@type'] in ['Person', 'Organization']:
                    if 'name' in data:
                        results.append({'type': 'name', 'value': data['name'], 'confidence': 0.95})
                    if 'email' in data:
                        results.append({'type': 'email', 'value': data['email'], 'confidence': 0.95})
                    if 'telephone' in data:
                        results.append({'type': 'phone', 'value': data['telephone'], 'confidence': 0.95})
                    if 'jobTitle' in data:
                        results.append({'type': 'title', 'value': data['jobTitle'], 'confidence': 0.95})
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse JSON-LD data")
        
        return results


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
    """A class that:
    1. Takes a list of results.
    2. Aggregates them based on type & value.
    
    Methods:
        aggregate: Aggregates the given list of results.
    """
    def aggregate(self, results):
        
        # Initialize an empty dictionary `aggregated` to store the final results
        aggregated = {}
        
        # Iterate over each result in the given list of results
        for result in results:
            if result['type'] not in aggregated:
                aggregated[result['type']] = {}
            value = result['value']
            if value not in aggregated[result['type']]:
                aggregated[result['type']][value] = result.get('confidence', 1.0)
            else:
                aggregated[result['type']][value] = max(aggregated[result['type']][value], result.get('confidence', 1.0))
        
        return [{'type': k, 'value': v, 'confidence': conf} for k, values in aggregated.items() for v, conf in values.items()]


class Registry:
    def __init__(self):
        self.extractors = {}
        
    def register(self, name, extractor):
        if isinstance(extractor, type) and issubclass(extractor, BaseExtractor):
            self.extractors[name] = extractor()
        elif isinstance(extractor, BaseExtractor):
            self.extractors[name] = extractor
        else:
            raise ValueError("Extractor must inherit from BaseExtractor")

    def get_extractor(self, name):
        return self.extractors.get(name)

    def get_all_extractors(self):
        return list(self.extractors.values())


class ContactInfoExtractor:
    def __init__(self):
        self.registry = Registry()
        self.registry.register('email', EmailExtractor)
        self.registry.register('name', FullNameExtractor)
        self.registry.register('phone', PhoneExtractor)
        self.registry.register('title', TitleExtractor)
        self.registry.register('contextual', ContextualExtractor(self.registry))
        self.html_parser = HTMLParser()
        self.result_aggregator = ResultAggregator()

    def extract_contact_info(self, url, html):
        try:
            parsed_content = self.html_parser.parse(html)
            results = []
            
            # Use Contextual Extractor First
            contextual_extractor = self.registry.get_extractor('contextual')
            results.extend(contextual_extractor.extract(html))
            
            # Then use other extractors for any remaining content
            for extractor_name in ['email', 'name', 'phone', 'title']:
                extractor = self.registry.get_extractor(extractor_name)
                results.extend(extractor.extract(parsed_content['text']))
                for meta in parsed_content['meta']:
                    results.extend(extractor.extract(meta))
                for link in parsed_content['links']:
                    results.extend(extractor.extract(link['text']))
                    if extractor_name == 'email' and link['href'].startswith('mailto:'):
                        results.append({'type': 'email', 'value': link['href'][7:], 'confidence': 1.0})

            return self.result_aggregator.aggregate(results)
        except Exception as e:
            logger.error(f"Error extracting contact info from {url}: {str(e)}")
            return []


# Usage example
if __name__ == "__main__":
    extractor = ContactInfoExtractor()
    sample_html = """
    <html><body>
    <div class="about-team">
        <p>John Doe - Chief Executive Officer</p>
        <p>Email: john.doe@example.com</p>
        <a href="mailto:jane@example.com">Contact Jane Smith, VP of Marketing</a>
        <div class="contact">Phone: (123) 456-7890</div>
    </div>
    </body></html>
    """
    results = extractor.extract_contact_info("https://example.com", sample_html)
    print(results)
