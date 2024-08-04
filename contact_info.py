import re
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class ContactInfoExtractor:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.name_pattern = re.compile(r'^[A-Z][a-z]+(?: [A-Z][a-z]+)+$')
        self.title_keywords = [
            'engineer', 'manager', 'director', 'ceo', 'cto', 'founder', 'president', 
            'vice president', 'vp', 'lead', 'head', 'chief', 'scientist', 'analyst'
        ]

    def extract_contact_info(self, url, html):
        soup = BeautifulSoup(html, 'html.parser')
        contact_info = []

        # Extract from specific sections (adjust selectors based on target websites)
        team_section = soup.select_one('div.team-section, section.team, div.about-us')
        if team_section:
            for member in team_section.find_all('div', class_='team-member'):
                info = self.extract_member_info(member, url)
                if info:
                    contact_info.append(info)

        # If no team section found, try general extraction
        if not contact_info:
            for element in soup.find_all(['div', 'section', 'article']):
                info = self.extract_member_info(element, url)
                if info:
                    contact_info.append(info)

        return contact_info

    def extract_member_info(self, element, url):
        name = self.extract_name(element)
        if not name:
            return None

        email = self.extract_email(element)
        title = self.extract_title(element)
        linkedin = self.extract_linkedin(element)

        if email or title or linkedin:
            return {
                'name': name,
                'email': email or 'not_found',
                'title': title or 'not_found',
                'linkedin': linkedin or 'not_found',
                'src_url': url
            }
        return None

    def extract_name(self, element):
        name_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'strong'])
        if name_elem and self.name_pattern.match(name_elem.text.strip()):
            return name_elem.text.strip()
        return None

    def extract_email(self, element):
        email_elem = element.find('a', href=lambda href: href and href.startswith('mailto:'))
        if email_elem:
            return email_elem['href'].replace('mailto:', '')
        
        text = element.get_text()
        emails = self.email_pattern.findall(text)
        return emails[0] if emails else None

    def extract_title(self, element):
        title_elem = element.find(['p', 'span', 'div'], string=lambda text: text and any(keyword in text.lower() for keyword in self.title_keywords))
        return title_elem.text.strip() if title_elem else None

    def extract_linkedin(self, element):
        linkedin_elem = element.find('a', href=lambda href: href and 'linkedin.com' in href)
        return linkedin_elem['href'] if linkedin_elem else None