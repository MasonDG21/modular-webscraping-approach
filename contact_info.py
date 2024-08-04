import re
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class ContactInfoExtractor:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.name_patterns = [
            re.compile(r'^[A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+))* [A-Z][a-z]+$'),
            re.compile(r'^[A-Z][a-z]+ [A-Z][a-z]+(?:-[A-Z][a-z]+)?$')
        ]
        self.title_keywords = [
            'engineer', 'manager', 'director', 'ceo', 'cto', 'founder', 'president', 
            'vice president', 'vp', 'lead', 'head', 'chief', 'cfo', 'coo', 'cio', 
            'officer', 'scientist', 'analyst', 'consultant', 'partner', 'principal', 
            'executive', 'administrator', 'supervisor', 'owner', 'entrepreneur', 
            'co-founder', 'associate', 'senior', 'junior', 'intern', 'assistant'
        ]
        self.ignore_keywords = ['privacy', 'cookie', 'contact us', 'sign up', 'updates']

    def extract_contact_info(self, url, html):
        self.logger.info(f"Extracting contact info from: {url}")
        soup = BeautifulSoup(html, 'html.parser')
        team_pages = self.find_team_pages(url, soup)
        self.logger.debug(f"Found {len(team_pages)} team pages: {team_pages}")
        
        all_members = []
        for page_url in team_pages:
            self.logger.info(f"Team page found: {page_url}")
            if "cuaerospace.com/about/engineering-team" in page_url:
                all_members.extend(self.extract_cuaerospace_engineering_team(page_url, soup))
            elif "cuaerospace.com" in page_url:
                all_members.extend(self.extract_cuaerospace_team(page_url, soup))
            else:
                all_members.extend(self.extract_team_info(page_url, soup))
        
        if not all_members:
            self.logger.info("No team pages found, extracting from original URL")
            all_members = self.extract_team_info(url, soup)
        
        deduplicated_members = self.deduplicate_members(all_members)
        self.logger.debug(f"Deduplicated members: {deduplicated_members}")
        return deduplicated_members

    def find_team_pages(self, url, soup):
        team_keywords = [
            'team', 'about', 'staff', 'people', 'leadership', 'management', 'directory', 
            'employees', 'our team', 'meet the team', 'who we are', 'company', 
            'executives', 'founders', 'board', 'advisors', 'bios', 'personnel'
        ]
        
        team_pages = []
        for link in soup.find_all('a', href=True):
            if any(keyword in link.text.lower() for keyword in team_keywords):
                team_pages.append(urljoin(url, link['href']))
        
        self.logger.debug(f"Team pages found: {team_pages}")
        return team_pages

    def extract_cuaerospace_engineering_team(self, url, soup):
        self.logger.info(f"Extracting CU Aerospace engineering team info from: {url}")
        team_members = []

        member_elements = soup.find_all('div', class_='team-member')
        self.logger.debug(f"Found {len(member_elements)} team member elements")
        
        for element in member_elements:
            name_elem = element.find('h3', class_='team-member-name')
            title_elem = element.find('h4', class_='team-member-position')
            email_elem = element.find('a', class_='team-member-email')
            
            if name_elem and title_elem:
                name = name_elem.text.strip()
                title = title_elem.text.strip()
                email = email_elem['href'].replace('mailto:', '') if email_elem else 'not_found'
                
                member_info = {
                    'name': name,
                    'title': title,
                    'email': email,
                    'linkedin': 'not_found',
                    'src_url': url
                }
                team_members.append(member_info)
                self.logger.info(f"Found member: {name}, {title}, {email}")

        return team_members

    def extract_cuaerospace_team(self, url, soup):
        self.logger.info(f"Extracting CU Aerospace team info from: {url}")
        team_members = []

        member_elements = soup.find_all('div', class_='team-member')
        self.logger.debug(f"Found {len(member_elements)} team member elements")
        
        for element in member_elements:
            name_elem = element.find('h3', class_='team-member-name')
            title_elem = element.find('h4', class_='team-member-position')
            email_elem = element.find('a', class_='team-member-email')
            
            if name_elem and title_elem:
                name = name_elem.text.strip()
                title = title_elem.text.strip()
                email = email_elem['href'].replace('mailto:', '') if email_elem else 'not_found'
                
                member_info = {
                    'name': name,
                    'title': title,
                    'email': email,
                    'linkedin': 'not_found',
                    'src_url': url
                }
                team_members.append(member_info)
                self.logger.info(f"Found member: {name}, {title}, {email}")

        return team_members

    def extract_team_info(self, url, soup):
        self.logger.info(f"Extracting team info from: {url}")
        team_members = []

        member_elements = soup.find_all(['div', 'section', 'article'])
        self.logger.debug(f"Found {len(member_elements)} potential member elements")
        
        for element in member_elements:
            member_info = self.extract_member_info(element, url)
            if member_info:
                team_members.append(member_info)

        self.logger.debug(f"Extracted {len(team_members)} team members")
        return team_members

    def extract_member_info(self, element, url):
        name = self.find_name(element)
        if not name or any(keyword in name.lower() for keyword in self.ignore_keywords):
            self.logger.debug(f"Ignoring element with name: {name}")
            return None

        title = self.find_title(element, name)
        email = self.find_email(element)
        linkedin = self.find_linkedin(element)

        if not title and not email and not linkedin:
            self.logger.debug(f"No contact info found for element: {element}")
            return None

        self.logger.info(f"Found member: {name}, {title}, {email}, {linkedin}")
        return {
            'name': name,
            'title': title or 'not_found',
            'email': email or 'not_found',
            'linkedin': linkedin or 'not_found',
            'src_url': url
        }

    def find_name(self, element):
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b', 'span', 'p']:
            name_element = element.find(tag)
            if name_element:
                name = name_element.text.strip()
                if any(pattern.match(name) for pattern in self.name_patterns):
                    self.logger.debug(f"Found name: {name}")
                    return name
        return None

    def find_title(self, element, name):
        name_element = element.find(text=name)
        if name_element:
            next_element = name_element.find_next()
            if next_element and any(keyword in next_element.text.lower() for keyword in self.title_keywords):
                title = next_element.text.strip()
                self.logger.debug(f"Found title near name {name}: {title}")
                return title
        
        for tag in ['p', 'span', 'div', 'h6']:
            title_element = element.find(tag, string=lambda text: text and any(keyword in text.lower() for keyword in self.title_keywords))
            if title_element:
                title = title_element.text.strip()
                self.logger.debug(f"Found title: {title}")
                return title
        return None

    def find_email(self, element):
        email_element = element.find('a', href=lambda href: href and href.startswith('mailto:'))
        if email_element:
            email = email_element['href'].replace('mailto:', '')
            self.logger.debug(f"Found email: {email}")
            return email
        
        emails = self.email_pattern.findall(str(element))
        if emails:
            self.logger.debug(f"Found email in text: {emails[0]}")
        return emails[0] if emails else None

    def find_linkedin(self, element):
        linkedin_element = element.find('a', href=lambda href: href and 'linkedin.com' in href)
        if linkedin_element:
            linkedin = linkedin_element['href']
            self.logger.debug(f"Found LinkedIn profile: {linkedin}")
            return linkedin
        return None

    def deduplicate_members(self, members):
        seen = set()
        unique_members = []
        for member in members:
            key = (member['name'], member['title'])
            if key not in seen:
                seen.add(key)
                unique_members.append(member)
        self.logger.debug(f"Deduplicated members: {len(unique_members)} out of {len(members)}")
        return unique_members
