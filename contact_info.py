import re
from bs4 import BeautifulSoup
import requests

class ContactInfoExtractor:
    def __init__(self):
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.generic_emails = [
    'info@', 'contact@', 'support@', 'sales@', 'webmaster@', 'help@', 
    'admin@', 'office@', 'service@', 'no-reply@', 'noreply@', 'team@',
    'careers@', 'jobs@', 'hr@', 'billing@', 'inquiries@', 'enquiry@', 
    'enquiries@', 'customercare@', 'hello@', 'welcome@', 'marketing@', 
    'advertising@', 'media@', 'press@', 'pr@', 'business@', 'partnerships@', 
    'partners@', 'legal@', 'privacy@', 'compliance@', 'finance@', 'accounting@',
    'accounts@', 'payment@', 'payments@', 'orders@', 'order@', 'booking@', 
    'bookings@', 'reservations@', 'reserve@', 'feedback@', 'reviews@', 
    'review@', 'updates@', 'news@', 'newsletter@', 'subscribe@', 'subscriptions@',
    'unsubscribe@', 'admin@', 'administrator@', 'root@', 'system@', 
    'postmaster@', 'mailer-daemon@', 'bounce@', 'abuse@', 'security@'
]

    def extract_contact_info(self, url):
        team_page_url = self.find_team_page(url)
        if team_page_url:
            return self.extract_team_info(team_page_url)
        return self.extract_team_info(url)

    def find_team_page(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        team_keywords = ['team', 'about', 'staff', 'people', 'leadership']
        
        for link in soup.find_all('a', href=True):
            if any(keyword in link.text.lower() for keyword in team_keywords):
                return requests.compat.urljoin(url, link['href'])
        return None

    def extract_team_info(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        team_members = []

        for section in soup.find_all(['div', 'section']):
            if self.is_team_section(section):
                for member in section.find_all(['div', 'article']):
                    info = self.extract_member_info(member)
                    if info:
                        team_members.append(info)

        return team_members

    def is_team_section(self, section):
        text = section.get_text().lower()
        return any(keyword in text for keyword in ['team', 'staff', 'people', 'leadership'])

    def extract_member_info(self, element):
        name = element.find(['h2', 'h3', 'h4', 'strong'])
        if name:
            name = name.text.strip()
            title = element.find(['p', 'span'])
            title = title.text.strip() if title else ''
            email = self.find_email(element)
            linkedin = self.find_linkedin(element)
            
            return {
                'name': name,
                'title': title,
                'email': email,
                'linkedin': linkedin
            }
        return None

    def find_email(self, element):
        emails = self.email_pattern.findall(str(element))
        valid_emails = [email for email in emails if not any(generic in email.lower() for generic in self.generic_emails)]
        return valid_emails[0] if valid_emails else None

    def find_linkedin(self, element):
        linkedin_link = element.find('a', href=re.compile(r'linkedin\.com'))
        return linkedin_link['href'] if linkedin_link else None