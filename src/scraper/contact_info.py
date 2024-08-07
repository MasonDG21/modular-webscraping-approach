import re
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from src.utils.logging_utils import setup_logging, get_logger

setup_logging()
logging = get_logger(__name__)

class ContactInfoExtractor:
    def __init__(self):
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.name_pattern = re.compile(r'\b[A-Z][a-z]+(?: [A-Z][a-z]+)+\b')
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

    def extract_contact_info(self, url, html):
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            contact_info = []
            
            # Extract information from text content
            for text in soup.stripped_strings:
                info = self._extract_from_text(text)
                if info:
                    contact_info.append(info)
            
            # Extract information from specific HTML elements
            contact_info.extend(self._extract_from_elements(soup, url))
            
            # Ensure each item in contact_info has at least one required key
            contact_info = [item for item in contact_info if any(key in item for key in ['email', 'name', 'linkedin'])]
            
            return contact_info
        except Exception as e:
            self.logger.error(f"Error extracting contact info from {url}: {str(e)}")
            return []

    def _extract_from_text(self, text):
        info = {}
        
        try:
            # Extract email
            emails = self.email_pattern.findall(text)
            if emails:
                info['email'] = emails[0]
            
            # Extract names
            names = self.name_pattern.findall(text)
            if names:
                info['name'] = names[0]
            
            # Extract titles
            for keyword in self.title_keywords:
                if keyword.lower() in text.lower():
                    info['title'] = text
                    break
        except Exception as e:
            self.logger.error(f"Error extracting info from text: {str(e)}")
        
        return info if info else None

    def _extract_from_elements(self, soup, base_url):
        contact_info = []
        
        try:
            # Extract from meta tags
            for tag in soup.find_all('meta'):
                name = tag.get('name', '').lower()
                content = tag.get('content', '')
                if 'description' in name or 'keywords' in name:
                    info = self._extract_from_text(content)
                    if info:
                        contact_info.append(info)
            
            # Extract from specific elements often used for contact info
            for elem in soup.find_all(['a', 'p', 'div', 'span']):
                if 'contact' in elem.get('class', []) or 'contact' in elem.get('id', ''):
                    info = self._extract_from_text(elem.get_text())
                    if info:
                        contact_info.append(info)
                
                # Extract emails from href attributes
                href = elem.get('href', '')
                if href.startswith('mailto:'):
                    contact_info.append({'email': href[7:]})
                
                # Extract LinkedIn profiles
                if 'linkedin.com/in/' in href:
                    contact_info.append({'linkedin': urljoin(base_url, href)})
        except Exception as e:
            self.logger.error(f"Error extracting info from elements: {str(e)}")
        
        return contact_info

# Usage example
if __name__ == "__main__":
    extractor = ContactInfoExtractor()
    sample_html = """
    <html><body>
    <p>John Doe - CEO</p>
    <p>Email: john.doe@example.com</p>
    </body></html>
    """
    results = extractor.extract_contact_info("https://example.com", sample_html)
    print(results)