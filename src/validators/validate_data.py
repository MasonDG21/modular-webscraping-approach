import re
import spacy
from spacy.matcher import Matcher
from fuzzywuzzy import fuzz

from src.utils.logging_utils import setup_logging, validator_logs
setup_logging()
vLog = validator_logs()

class DataValidator:
    def __init__(self):
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.linkedin_pattern = re.compile(r'^https?://(?:www\.)?linkedin\.com/in/[\w\-]+/?$')
        self.phone_pattern = re.compile(r'^\+?[\d\s.-]+\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$')
        self.nlp = spacy.load("en_core_web_sm")
        self.matcher = Matcher(self.nlp.vocab)
        self.logger = vLog
        self.logger.debug("DataValidator initialized")
        
        # Add patterns for job titles
        self.matcher.add("JOB_TITLE", [
            [{"POS": "PROPN"}, {"LOWER": "of"}, {"POS": "PROPN"}],
            [{"POS": "ADJ"}, {"POS": "NOUN"}],
            [{"POS": "NOUN"}, {"POS": "NOUN"}],
        ])

    def validate_contact_info(self, info):
        self.logger.debug(f"Validating contact info: {info}")
        if not isinstance(info, dict):
            self.logger.error(f"info is not a dictionary: {info}")
            return False

        # Check if at least one of email, name, or linkedin is present
        if not any(key in info for key in ['email', 'name', 'linkedin', 'title', 'phone']):
            self.logger.warning("None of the required keys (email, name, linkedin, title) are present")
            return False

        validated_info = {}
        for key in ['email', 'name', 'linkedin', 'title', 'phone']:
            self.logger.info("Key: {key}")
            if key in info and info[key] != 'not_found':
                validated_info[key] = getattr(self, f'validate_{key}')(info[key])
                self.logger.info("")
                
        # Enrich the validated info with NLP
        self.enrich_with_nlp(validated_info)

        # Update the original info with validated data
        info.update(validated_info)
        self.logger.debug(f"Validated info: {validated_info}")

        return any(validated_info.values())

    def validate_name(self, name):
        self.logger.debug(f"Validating name: {name}")
        doc = self.nlp(name)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                self.logger.info(f"Validated name: {ent.text}")
                return ent.text
        self.logger.warning(f"Name validation failed for: {name}")
        return None

    def validate_email(self, email):
        self.logger.debug(f"Validating email: {email}")
        valid = self.email_pattern.match(email)
        if valid:
            self.logger.info(f"Validated email: {email}")
        else:
            self.logger.warning(f"Email validation failed for: {email}")
        return email if valid else None
    
    def validate_phone(self, phone):
        self.logger.debug(f"Validating phone: {phone}")
        valid = self.phone_pattern.match(phone)
        if valid:
            self.logger.info(f"Validated phone: {phone}")
        else:
            self.logger.warning(f"Phone validation failed for: {phone}")
        return phone if valid else None

    def validate_linkedin(self, linkedin):
        self.logger.debug(f"Validating LinkedIn URL: {linkedin}")
        valid = self.linkedin_pattern.match(linkedin)
        if valid:
            self.logger.info(f"Validated LinkedIn URL: {linkedin}")
        else:
            self.logger.warning(f"LinkedIn URL validation failed for: {linkedin}")
        return linkedin if valid else None

    def validate_title(self, title):
        self.logger.debug(f"Validating title: {title}")
        doc = self.nlp(title)
        matches = self.matcher(doc)
        if matches:
            valid_title = doc[matches[0][1]:matches[0][2]].text
            self.logger.info(f"Validated title: {valid_title}")
            return valid_title
        self.logger.warning(f"Title validation failed for: {title}")
        return None

    def enrich_with_nlp(self, info):
        self.logger.debug(f"Enriching info with NLP: {info}")
        if 'name' in info and info['name']:
            doc = self.nlp(info['name'])
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    info['organization'] = ent.text
                    self.logger.info(f"Enriched organization from name: {ent.text}")

        if 'title' in info and info['title']:
            doc = self.nlp(info['title'])
            for token in doc:
                if token.pos_ == "PROPN" and token.text not in info.get('name', ''):
                    info['organization'] = token.text
                    self.logger.info(f"Enriched organization from title: {token.text}")
                    break

    def fuzzy_match(self, str1, str2, threshold=50):
        self.logger.debug(f"Fuzzy matching between '{str1}' and '{str2}' with threshold {threshold}")
        match_result = fuzz.ratio(str1.lower(), str2.lower()) >= threshold
        self.logger.info(f"Fuzzy match result: {match_result}")
        return match_result


if __name__ == "__main__":
    validator = DataValidator()
    validator.logger.debug("Test debug message")
    validator.logger.info("Test info message")
    validator.logger.warning("Test warning message")
    validator.logger.error("Test error message")