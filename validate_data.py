import re

class DataValidator:
    def __init__(self):
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.name_pattern = re.compile(r'^[A-Z][a-z]+(?: [A-Z][a-z]+)+$')
        self.linkedin_pattern = re.compile(r'^https?://(?:www\.)?linkedin\.com/in/[\w\-]+/?$')

    def validate_contact_info(self, info):
        if not self.validate_name(info['name']):
            return False
        if info['email'] != 'not_found' and not self.validate_email(info['email']):
            return False
        if info['linkedin'] != 'not_found' and not self.validate_linkedin(info['linkedin']):
            return False
        return True

    def validate_name(self, name):
        return bool(self.name_pattern.match(name))

    def validate_email(self, email):
        return bool(self.email_pattern.match(email))

    def validate_linkedin(self, linkedin):
        return bool(self.linkedin_pattern.match(linkedin))