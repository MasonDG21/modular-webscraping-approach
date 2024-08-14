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

MIN_QUERY_LENGTH = 3

class BaseExtractor(ABC):
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def extract(self, content):
        pass

    def clean_text(self, text):
        """Remove extra whitespace and normalize text."""
        cleaned = re.sub(r'\s+', ' ', text).strip()
        
        if not cleaned:
            # self.logger.warning(f"Cleaning resulted in empty string. Reverted to original: '{text}'")
            return text  # Return original text if cleaning results in empty string
        
        #self.logger.debug(f"Cleaned text. Original length: {len(text)}, Clean length: {len(cleaned)} | Clean Text: {cleaned}")
        return cleaned
    
    def find_all_matches(self, pattern, text):
        """Find all matches of a regex pattern in the text."""
        if not text:
            # self.logger.warning("Text for find_all_matches is empty. No matches found.")
            return []
        matches = re.findall(pattern, text)
        #self.logger.debug(f"Found {len(matches)} matches for pattern in text: {text}")
        return matches

    def log_extraction(self, content_type, results):
        """Log the results of an extraction."""
        # self.logger.info(f"Extracted {len(results)} {content_type}(s)")
        for result in results:
            self.logger.info(f"Extracted {content_type}: {result['value']}")

    def safe_extract(self, content):
        """Safely perform extraction with error handling."""
        if not content or len(content) < MIN_QUERY_LENGTH:
            # self.logger.warning(f"Content too short for extraction: {content}")
            return [{'type': self.__class__.__name__.replace('Extractor', '').lower(), 'value': 'not_found'}]
        try:
            results = self.extract(content)
            self.log_extraction(self.__class__.__name__.replace('Extractor', '').lower(), results)
            return results
        except Exception as e:
            self.logger.error(f"Error during extraction: {str(e)}")
            return content


class EmailExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    def extract(self, content):
        #self.logger.debug(f"Extracting emails from content (length: {len(content)}): {content}")
        
        # Ensure the content is always a string
        if not isinstance(content, str):
            self.logger.info(f"Content received was not a string (type: {type(content)}). Converted to string.")
            if isinstance(content, list):
                content = ' '.join(map(str, content))  # Convert list elements to strings and join
            else:
                content = str(content)  # Convert other types to string
            # self.logger.info("Content converted to string.")
            
        cleaned_content = self.clean_text(content)
        # self.logger.info(f"Cleaned Email: {cleaned_content}")
        emails = self.find_all_matches(self.email_pattern, cleaned_content)
        self.logger.info(f"Emails Matched: {len(emails)} emails.")
        return [{'type': 'email', 'value': email} for email in emails]


class FullNameExtractor(BaseExtractor):
    def __init__(self):
        self.name_pattern = re.compile(r'\b(?!(?:Email|Contact|sent by)\b)(?:Dr\.|Mr\.|Ms\.|Mrs\.|Prof\.)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b')
        super().__init__()  # Ensure BaseExtractor's constructor is called
        
    def extract(self, content):
        # Ensure the content is always a string
        if not isinstance(content, str):
            self.logger.debug(f"Content received was not a string (type: {type(content)}). Converting to string.")
            if isinstance(content, list):
                content = ' '.join(map(str, content))  # Convert list elements to strings and join
            else:
                content = str(content)  # Convert other types to string

        matches = self.name_pattern.findall(content)
        return [{'type': 'name', 'value': name.strip()} for name in matches]


class PhoneExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()
        self.phone_pattern = r'\+?[\d\s.-]+\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'

    def extract(self, content):
        # Ensure the content is always a string
        if not isinstance(content, str):
            self.logger.debug(f"Content received was not a string (type: {type(content)}). Converting to string.")
            if isinstance(content, list):
                content = ' '.join(map(str, content))  # Convert list elements to strings and join
            else:
                content = str(content)  # Convert other types to string

        cleaned_content = self.clean_text(content)
        phone_numbers = self.find_all_matches(self.phone_pattern, cleaned_content)
        return [{'type': 'phone', 'value': phone.strip()} for phone in phone_numbers]


class TitleExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()
        self.title_keywords = [
            'CEO', 'CTO', 'CFO', 'COO', 'President', 'Director', 'Chief', 'Strategist', 'Logistics',
            'Manager', 'Engineer', 'Developer', 'Designer', 'Analyst', 'Specialist', 'Supply Chain',
            'Coordinator', 'Administrator', 'Supervisor', 'Lead', 'Head', 'VP', 'Production',
            'Pilot', 'Technician', 'Scientist', 'Inspector', 'Consultant', 'Architect', 'Assistant',
            'Associate', 'Operator', 'Instructor', 'Planner', 'Estimator', 'Fabricator',
            'Assembler', 'Machinist', 'Welder', 'Mechanic', 'Tester', 'Trainer', 'Project',
            'Marketing', 'Systems', 'Avionics', 'Researcher', 'Flight', 'Manufacturing',
            'Investigator', 'Quality', 'Assurance', 'Service', 'Support', 'Relations', 'Compliance',
            'Electrical', 'IT', 'Structural', 'Mechanical', 'Aerospace', 'Business', 'Sales', 'HR',
            'Recruiter', 'Recruitment', 'Materials', 'Safety', 'Reliability', 'Research',
            'Field Service', 'Cybersecurity', 'Ordnance', 'Legal Counsel', 'Maintenance',
            'Agent', 'Human Resources', 'Procurement', 'Operations', 'Business Development',
            'Integration', 'Mission', 'Payload', 'Propulsion', 'Dr.', 'Regulatory Affairs',
            'Internal Affairs', 'External Affairs', 'Public Relations', 'Acquisition', 'Configuration',
            'Risk', 'Test', 'Calibration', 'Inventory', 'Contractor', 'Talent', 'Training', 'Officer',
            'Compliance Officer', 'Legal Advisor', 'Technical Lead', 'Data Scientist', 'Data Engineer',
            'Product Manager', 'Product Owner', 'Program Manager', 'Scrum Master', 'Product Designer',
            'User Experience', 'UX', 'UI', 'Security', 'Infrastructure', 'DevOps', 'Cloud', 'AI',
            'Machine Learning', 'Artificial Intelligence', 'Big Data', 'Data Analyst', 'Data Architect',
            'Solutions Architect', 'Enterprise Architect', 'Chief Information Officer', 'CIO',
            'Chief Security Officer', 'CSO', 'Chief Data Officer', 'CDO', 'Chief Technology Officer', 
            'Chief Marketing Officer', 'CMO', 'Chief Operations Officer', 'Chief Revenue Officer', 'CRO',
            'Chief Financial Officer', 'Financial Analyst', 'Investment Analyst', 'Portfolio Manager', 
            'Account Manager', 'Account Executive', 'Sales Executive', 'Sales Manager', 'Sales Director', 
            'Customer Success', 'Customer Support', 'Client Services', 'Partner Manager', 'Channel Manager', 
            'Vendor Manager', 'Supplier Manager', 'Procurement Specialist', 'Logistics Coordinator', 'Logistics Manager', 
            'Supply Chain Manager', 'Supply Chain Analyst', 'Material Planner', 'Material Manager', 'Material Coordinator', 
            'Warehouse Manager', 'Warehouse Supervisor', 'Operations Manager', 'Operations Coordinator', 
            'Operations Analyst', 'Operations Director', 'Human Resources Manager', 'HR Coordinator', 'HR Analyst', 
            'Talent Acquisition', 'Learning and Development', 'L&D', 'Employee Relations', 'Compensation and Benefits', 
            'Payroll Specialist', 'Payroll Manager', 'Risk Management', 'Compliance Manager', 'Internal Auditor', 
            'External Auditor', 'Financial Controller', 'Finance Director', 'Finance Manager', 'Budget Analyst', 
            'Financial Planner', 'Business Analyst', 'Business Intelligence', 'BI', 'BI Analyst', 'IT Manager', 
            'IT Director', 'Chief Digital Officer', 'Digital Transformation', 'Digital Marketing', 'SEO', 'SEM', 
            'Content Manager', 'Content Strategist', 'Content Creator', 'Social Media Manager', 'Social Media Strategist', 
            'Creative Director', 'Art Director', 'Copywriter', 'Content Writer', 'Editor', 'Proofreader', 'Technical Writer',
            'Software Engineer', 'Software Developer', 'Frontend Developer', 'Backend Developer', 'Full Stack Developer', 
            'Mobile Developer', 'iOS Developer', 'Android Developer', 'Web Developer', 'Game Developer', 
            'Embedded Systems Engineer', 'Hardware Engineer', 'Firmware Engineer', 'Network Engineer', 
            'Systems Administrator', 'IT Support', 'Help Desk', 'Technical Support', 'Customer Support Engineer', 
            'Service Desk', 'Field Technician', 'Site Reliability Engineer', 'Security Analyst', 'Security Engineer', 
            'Penetration Tester', 'Ethical Hacker', 'Security Consultant', 'Security Architect', 'Compliance Analyst', 
            'Regulatory Compliance', 'Data Protection Officer', 'DPO', 'General Counsel', 'Paralegal', 'Legal Assistant', 
            'Litigation Support', 'Contract Manager', 'Contract Administrator', 'Patent Agent', 'Patent Attorney', 
            'Trademark Attorney', 'Real Estate Manager', 'Property Manager', 'Facility Manager', 'Maintenance Technician', 
            'Maintenance Manager', 'Facilities Coordinator', 'Building Services', 'Environmental Health and Safety', 
            'EHS', 'Safety Officer', 'Safety Manager', 'HSE', 'Health and Safety', 'Construction Manager', 
            'Construction Engineer', 'Site Manager', 'Site Engineer', 'Project Coordinator', 'Project Manager', 
            'Senior Project Manager', 'Program Director', 'PMO', 'Change Manager', 'Organizational Change', 
            'Transformation Manager', 'Business Transformation', 'Business Process Analyst', 'Process Engineer', 
            'Continuous Improvement', 'Lean Manufacturing', 'Six Sigma', 'Agile Coach', 'Product Director', 'R&D', 
            'Research and Development', 'Innovation Manager', 'Innovation Director', 'Principal Engineer', 
            'Senior Engineer', 'Lead Engineer', 'Field Engineer', 'Field Service Engineer', 'Applications Engineer', 
            'Application Support', 'Technical Account Manager', 'TAM', 'Customer Engineer', 'Customer Success Manager', 
            'Customer Experience', 'CX', 'Client Relations', 'Client Success', 'Business Development Manager', 
            'BDM', 'Sales Engineer', 'Pre-Sales', 'Post-Sales', 'Technical Sales', 'Solution Engineer', 
            'Solution Architect', 'Solution Consultant', 'Implementation Specialist', 'Implementation Manager', 
            'Customer Implementation', 'Customer Onboarding', 'Customer Training', 'Training Manager', 'L&D Manager', 
            'Learning Specialist', 'Talent Development', 'Employee Development', 'Organizational Development', 'OD', 
            'HR Business Partner', 'HR Generalist', 'HR Specialist', 'HR Advisor', 'HR Consultant', 'HR Director', 
            'Chief People Officer', 'CPO', 'People Operations', 'People Manager', 'People Director', 'Talent Manager', 
            'Recruitment Manager', 'Recruitment Consultant', 'Headhunter', 'Executive Search', 'Talent Scout', 
            'Recruitment Specialist', 'Resourcing', 'Staffing', 'Workforce Planning', 'Workforce Manager', 'HRIS', 
            'HR Information Systems', 'HR Systems', 'HR Technology', 'Compensation Analyst', 'Benefits Manager', 
            'Reward Analyst', 'Reward Manager', 'Benefits Analyst', 'Employee Benefits', 'Labor Relations', 
            'Industrial Relations', 'Union Representative', 'Employee Engagement', 'Employee Experience', 
            'Wellness Manager', 'Wellbeing Manager', 'Corporate Social Responsibility', 'CSR', 'Diversity and Inclusion', 
            'D&I', 'Diversity Officer', 'Inclusion Officer', 'Ethics Officer', 'Code of Conduct', 'Governance', 
            'Board Director', 'Board Member', 'Non-Executive Director', 'Trustee', 'Chairperson', 'Vice Chairperson', 
            'Board Secretary', 'Audit Committee', 'Remuneration Committee', 'Nomination Committee', 'Risk Committee', 
            'Governance Committee', 'Advisory Board', 'Technical Advisor', 'Industry Expert', 'Consulting Engineer', 
            'Senior Consultant', 'Management Consultant', 'Strategy Consultant', 'Advisory Consultant', 
            'Business Consultant', 'Financial Consultant', 'IT Consultant', 'Technology Consultant', 'Systems Consultant', 
            'Engineering Consultant', 'Project Consultant', 'Sales Consultant', 'Marketing Consultant', 'Training Consultant',
            'Learning Consultant', 'Development Consultant', 'Organizational Consultant', 'Operations Consultant', 'Process Consultant',
            'Change Consultant', 'Transformation Consultant', 'Lean Consultant', 'Six Sigma Consultant', 'Agile Consultant',
            'Scrum Consultant', 'Product Consultant', 'Program Consultant', 'Innovation Consultant', 'Research Consultant', 
            'Data Consultant', 'Compliance Consultant', 'Regulatory Consultant', 'Legal Consultant', 'Contracts Manager',
            'Contracts Specialist', 'Bid Manager', 'Proposal Manager', 'Procurement Officer', 'Procurement Manager',
            'Purchasing Manager', 'Supply Chain Director', 'Logistics Director', 'Inventory Manager', 'Stock Manager',
            'Materials Manager', 'Demand Planner', 'Demand Manager', 'Factory Manager', 'Manufacturing Manager',
            'Production Manager', 'Production Supervisor', 'Production Coordinator', 'Maintenance Supervisor',
            'Maintenance Engineer', 'Reliability Engineer', 'Asset Manager', 'Asset Engineer', 'Plant Manager',
            'Facilities Manager'
        ]
        self.title_pattern = re.compile(r'\b(' + '|'.join(self.title_keywords) + r')\b', re.IGNORECASE)

    def extract(self, content):
        # self.logger.debug(f"Extracting Titles from content (length: {len(content)})")
        if not isinstance(content, str):
            self.logger.info(f"Title content recieved was not type: `str` in TitleExtractor.")
        if isinstance(content, list):
            content = ' '.join(map(str, content)) # Convert all elements to strings and join them
            # self.logger.info("List Converted to string.")
        else:
            content = str(content)
            # self.logger.info(f"{type(content)} converted to string.")
        
        cleaned_content = self.clean_text(content)
        exact_matches = self.find_all_matches(self.title_pattern, cleaned_content)
        fuzzy_matches = self.fuzzy_match_titles(cleaned_content)
        # score = 1.1
        # the Title Extractor is the only
        # results = [{'type': 'title', 'value': title} for title in exact_matches]
        # results.extend([{'type': 'title', 'value': title,} for title, score in fuzzy_matches])        
        results = [{'type': 'title', 'value': title} for title in exact_matches]
        results.extend([{'type': 'title', 'value': title} for title, _ in fuzzy_matches])
        self.logger.info(f"Found {len(results)} Titles.")
        return results

    def fuzzy_match_titles(self, text):
        # self.logger.info("Fuzzy matching titles.")
        words = text.split()
        
        # Dynamically generate potential titles by combining 3 words at a time
        potential_titles = []
        for n in range(2, 5):
            potential_titles = [' '.join(words[i:i+3]) for i in range(len(words) - n + 1)]
            
        matches = process.extract(' '.join(potential_titles), self.title_keywords, limit=5)
        # self.logger.info(f"Found {len(matches)} fuzzy matches.")
        return [(match[0], match[1]) for match in matches if match[1] > 30]


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
        # self.logger = get_logger(self.__class__.__name__)
        self.context_keywords = {
            'high': ['about', 'team', 'contact', 'leadership', 'management', 'staff', 'employees', 'board', 'executives'],
            'medium': ['directory', 'people', 'department', 'faculty', 'personnel', 'crew', 'members', 'positions', 'roles'],
            'low': ['company', 'organization', 'group', 'division', 'unit', 'leaders', 'managers']
        }

    def extract(self, content):
        self.logger.debug(f"Extracting contextual information from content (length: {len(content)})")
        
        # input content should always be a string.
        if not isinstance(content, str):
            self.logger.info(f"Content received was not a string (type: {type(content)}). Converting to string.")
            if isinstance(content, list):
                content = ' '.join(map(str, content))  # Convert list elements to strings and join
            else:
                content = str(content)  # Convert other types to string
                
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
                    results.append({'type': item['type'], 'value': item['value']})
        
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
                results.append({'type': 'name', 'value': name.get_text()})
            if org:
                results.append({'type': 'organization', 'value': org.get_text()})
            if email:
                results.append({'type': 'email', 'value': email.get_text()})
            if tel:
                results.append({'type': 'phone', 'value': tel.get_text()})
        
        # Extract JSON-LD data
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0]
                if isinstance(data, dict) and '@type' in data:
                    if data['@type'] in ['Person', 'Organization']:
                        if 'name' in data:
                            results.append({'type': 'name', 'value': data['name']})
                        if 'email' in data:
                            results.append({'type': 'email', 'value': data['email']})
                        if 'telephone' in data:
                            results.append({'type': 'phone', 'value': data['telephone']})
                        if 'jobTitle' in data:
                            results.append({'type': 'title', 'value': data['jobTitle']})
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.warning(f"Failed to parse JSON-LD data: {e}")
        
        return results


class HTMLParser:
    def parse(self, html):
        if isinstance(html, list):
            # self.logger.info("HTML content recieved was type: `list` in HTMLParser")
            html = ' '.join(map(str, html)) # Convert all elements to strings and join them
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
    """A class that takes a list of results and Aggregates them based on type & value.
    
    Methods:
        aggregate: Aggregates the given list of results.
    """
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
             
    def aggregate(self, results):
        self.logger.info(f"Aggregating {len(results)} results.")
        
        # Initialize an empty dictionary `aggregated` to store the final results
        aggregated = {}
        
        # Iterate over each result in the given list of results
        for result in results:
            self.logger.debug(f"Processing Result: {result}")
            if isinstance(result, str):
                self.logger.warning(f"String result (skipped): {result}")
                continue
            
            if not isinstance(result, dict) or 'type' not in result or 'value' not in result:
                self.logger.warning(f"Skipping improperly formatted result: {result}")
                continue
            
            result_type = result['type']
            value = result['value']
            
            # Skip any results where the value is 'not_found'
            if value == 'not_found':
                self.logger.debug(f"Skipping result with value 'not_found': {result}")
                continue
            
            # If result_type is not in aggregated, initialize it
            if result_type not in aggregated:
                aggregated[result_type] = set()  # Use a set to avoid duplicate values
            
            # Add the value to the set for this result_type
            aggregated[result_type].add(value)
    
        # Convert the aggregated dictionary back to a list of dictionaries without confidence
        return [{'type': k, 'value': v} for k, values in aggregated.items() for v in values]


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
        self.logger = get_logger(self.__class__.__name__)

    def extract_contact_info(self, url, html):
        status = {
            'url': url,
            'status': 'success',
            'errors': [],
            'warnings': [],
            'extracted_info': []
        }
        
        try:
            if not isinstance(html, str):
                # self.logger.debug(f"HTML content received was not a string (type: {type(html)}). Converting to string.")
                html = self.convert_to_string(html)
            
            if not html:
                self.logger.warning(f"No HTML content recieved for URL: {url}")
                status['warnings'].append("Empty HTML content")
                return status
            parsed_content = self.html_parser.parse(html)
            results = []
            
            # Try Contextual Extractor First
            contextual_extractor = self.registry.get_extractor('contextual')
            try:
                contextual_results = contextual_extractor.extract(html)
                results.extend(contextual_results)
                
            except Exception as e:
                status['warnings'].append(f"Contextual Extraction failed: {str(e)}")
                self.logger.warning(f"Contextual Extraction failed for {url}: {str(e)}", exc_info=True)
            
            # Try other extractors for any remaining content
            for extractor_name in ['email', 'name', 'title']:
                
                extractor = self.registry.get_extractor(extractor_name)
                self.logger.debug(f"Extracting ``{extractor_name}'s`` from: {url}")
                
                try:
                    results.extend(self.extract_from_parsed_content(extractor, parsed_content))
                except Exception as e:
                    status['warnings'].append(f"{extractor_name.capitalize()} extraction failed: {str(e)}")
                    self.logger.warning(f"{extractor_name.capitalize()} extraction failed for {url}: {str(e)}", exc_info=True)
            self.logger.info(f"Total results before aggregation: {len(results)}")
            count = 1
            for result in results:
                c = count++1
                self.logger.debug(f"Result Before Aggregation {c}. {result}")
            
            valid_results = [r for r in results if isinstance(r, dict) and 'type' in r and 'value' in r]
            self.logger.debug(f"Valid Results before aggregation: {valid_results}")
            
            aggregated_results = self.result_aggregator.aggregate(valid_results)
            status['extracted_info'] = aggregated_results
            self.logger.info(f"Successfully extracted and aggregated {len(aggregated_results)} results from URL: {url}")
            
            return status

        except Exception as e:
            status['status'] = 'failure'
            status['errors'].append(str(e))
            self.logger.error(f"Error extracting contact info from {url}: {str(e)}", exc_info=True)
            return status
    
    def convert_to_string(self, content):
        if isinstance(content, list):
            return ' '.join(map(str, content))
        return str(content)

    def extract_from_parsed_content(self, extractor, parsed_content):
        results = []
        
        # Handle text content
        text_content = self.convert_to_string(parsed_content['text'])
        results.extend(extractor.safe_extract(text_content))
        
        # Handle meta content
        meta_content = self.convert_to_string(parsed_content['meta'])
        results.extend(extractor.safe_extract(meta_content))
        
        # Handle links content
        for link in parsed_content['links']:
            link_text = self.convert_to_string(link['text'])
            results.extend(extractor.safe_extract(link_text))
            
            if isinstance(extractor, EmailExtractor) and link['href'].startswith('mailto:'):
                results.append({'type': 'email', 'value': link['href'][7:], 'confidence': 1.0})
        
        return results



# Usage example
if __name__ == "__main__":
    extractor = ContactInfoExtractor()
    
    html_file_path = "C:\\Users\\mason\\OneDrive\\Desktop\\Organized\\Projects\\Personal\\PythonProjects\\modular-webscraping-approach\\tests\\sample.html"
    
    # Read the HTML content from the file
    with open(html_file_path, 'r', encoding='utf-8') as file:
        sample_html = file.read()
    
    # Extract contact information
    results = extractor.extract_contact_info("https://grantcardonelicensee.com/licensee/aaron-goodwin-indiana/", sample_html)
    
    # Print the results
    print(results)

# if __name__ == "__main__":
#     # cIExtractor = ContactInfoExtractor()
#     emailExtractor = EmailExtractor()
    
#     # html_file_path = os.path.join(os.path.dirname(__file__), 'relative/path/to/your/directory', 'sample.html')
    
#     # with open(html_file_path, 'r', encoding='utf-8') as file:
#     #     sample_html = file.read()
        
#     sample_html = """
#     <html><body>
#     <div class="about-team">
#         <p>John Doe - Chief Executive Officer</p>
#         <p>Email: john.doe@example.com</p>
#         <a href="mailto:jane@example.com">Contact Jane Smith, VP of Marketing</a>
#         <div class="contact">Phone: (123) 456-7890</div>
#     </div>
#     </body></html>
#     """
#     #results = cIExtractor.extract_contact_info("https://example.com", sample_html)
    
#     email = emailExtractor.extract(sample_html)
    
#     print(email)