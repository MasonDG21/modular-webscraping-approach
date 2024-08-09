import re
import spacy
from spacy.matcher import Matcher
from fuzzywuzzy import fuzz

class DataValidator:
    def __init__(self):
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.linkedin_pattern = re.compile(r'^https?://(?:www\.)?linkedin\.com/in/[\w\-]+/?$')
        self.phone_pattern = re.compile(r'^\+?[\d\s.-]+\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$')
        self.nlp = spacy.load("en_core_web_sm")
        self.matcher = Matcher(self.nlp.vocab)
        
        # Add patterns for job titles
        self.matcher.add("JOB_TITLE", [
            [{"POS": "PROPN"}, {"LOWER": "of"}, {"POS": "PROPN"}],
            [{"POS": "ADJ"}, {"POS": "NOUN"}],
            [{"POS": "NOUN"}, {"POS": "NOUN"}],
        ])

    def validate_contact_info(self, info):
        if not isinstance(info, dict):
            return False

        # Check if at least one of email, name, or linkedin is present
        if not any(key in info for key in ['email', 'name', 'linkedin', 'title']):
            return False

        validated_info = {}

        if 'email' in info and info['email'] != 'not_found':
            validated_info['email'] = self.validate_email(info['email'])

        if 'name' in info and info['name'] != 'not_found':
            validated_info['name'] = self.validate_name(info['name'])

        if 'linkedin' in info and info['linkedin'] != 'not_found':
            validated_info['linkedin'] = self.validate_linkedin(info['linkedin'])

        if 'title' in info and info['title'] != 'not_found':
            validated_info['title'] = self.validate_title(info['title'])

        # Try NLP matching for job titles and names
        # Enrich data with NLP if possible
        if 'name' in validated_info or 'title' in validated_info:
            self.enrich_with_nlp(validated_info)

        # Update the original info with validated data
        info.update(validated_info)

        return any(validated_info.values())

    def validate_name(self, name):
        doc = self.nlp(name)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text
        return None

    def validate_email(self, email):
        return email if self.email_pattern.match(email) else None
    
    def validate_phone(self, phone):
        return phone if self.phone_pattern.match(phone) else None

    def validate_linkedin(self, linkedin):
        return linkedin if self.linkedin_pattern.match(linkedin) else None

    def validate_title(self, title):
        doc = self.nlp(title)
        matches = self.matcher(doc)
        if matches:
            return doc[matches[0][1]:matches[0][2]].text
        return None

    def enrich_with_nlp(self, info):
        if 'name' in info and info['name']:
            doc = self.nlp(info['name'])
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    info['organization'] = ent.text

        if 'title' in info and info['title']:
            doc = self.nlp(info['title'])
            for token in doc:
                if token.pos_ == "PROPN" and token.text not in info.get('name', ''):
                    info['organization'] = token.text
                    break

    def fuzzy_match(self, str1, str2, threshold=80):
        return fuzz.ratio(str1.lower(), str2.lower()) >= threshold