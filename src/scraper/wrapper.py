import re
from collections import defaultdict

from bs4 import BeautifulSoup

class Wrapper:
    def __init__(self):
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.name_pattern = re.compile(r'\b[A-Z][a-z]+(?: [A-Z][a-z]+)+\b')
        self.phone_pattern = re.compile(r'\b(?:\+\d{1,2}\s?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b')
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


    def extract_info(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        results = defaultdict(list)

        # Extract information from text content
        for text in soup.stripped_strings:
            self._extract_from_text(text, results)

        # Extract information from specific HTML elements
        self._extract_from_elements(soup, results)

        # Process and format results
        return self._process_results(results)

    def _extract_from_text(self, text, results):
        # Extract email
        emails = self.email_pattern.findall(text)
        results['email'].extend(emails)

        # Extract names
        names = self.name_pattern.findall(text)
        results['name'].extend(names)

        # Extract phone numbers
        phones = self.phone_pattern.findall(text)
        results['phone'].extend(phones)

        # Extract titles
        for keyword in self.title_keywords:
            if keyword.lower() in text.lower():
                results['title'].append(text)
                break

    def _extract_from_elements(self, soup, results):
        # Extract from meta tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            name = tag.get('name', '').lower()
            content = tag.get('content', '')
            if 'description' in name or 'keywords' in name:
                self._extract_from_text(content, results)

        # Extract from specific elements often used for contact info
        for elem in soup.find_all(['a', 'p', 'div', 'span']):
            if 'contact' in elem.get('class', []) or 'contact' in elem.get('id', ''):
                self._extract_from_text(elem.get_text(), results)

            # Extract emails from href attributes
            href = elem.get('href', '')
            if href.startswith('mailto:'):
                results['email'].append(href[7:])

    def _process_results(self, results):
        processed = []
        for category, items in results.items():
            unique_items = list(set(items))  # Remove duplicates
            for item in unique_items:
                processed.append({"type": category, "value": item})
        
        return sorted(processed, key=lambda x: self._relevance_score(x), reverse=True)

    def _relevance_score(self, item):
        if item['type'] == 'email':
            return 5
        elif item['type'] == 'name':
            return 4
        elif item['type'] == 'phone':
            return 3
        elif item['type'] == 'title':
            return 2
        else:
            return 1

# Usage
if __name__ == "__main__":
    wrapper = Wrapper()
    sample_html = """
    <html>
        <body>
            <p class="contact">John Doe - CEO</p>
            <p>Email: john.doe@example.com</p>
            <p>Phone: (123) 456-7890</p>
            <div id="team">
                <p>Jane Smith | Chief Technology Officer</p>
                <a href="mailto:jane.smith@tech-example.com">Contact Jane</a>
            </div>
            <meta name="description" content="Contact our team: Alice Johnson, Marketing Director">
        </body>
    </html>
    """
    results = wrapper.extract_info(sample_html)
    print(results)