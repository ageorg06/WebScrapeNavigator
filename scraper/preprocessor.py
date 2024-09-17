import re
from bs4 import BeautifulSoup
import html
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('stopwords')

class ContentPreprocessor:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))

    def clean_html(self, content):
        """Remove HTML tags and decode HTML entities"""
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        return html.unescape(text)

    def remove_special_characters(self, text):
        """Remove special characters and numbers"""
        return re.sub(r'[^a-zA-Z\s]', '', text)

    def remove_extra_whitespace(self, text):
        """Remove extra whitespace"""
        return ' '.join(text.split())

    def remove_stopwords(self, text):
        """Remove common stopwords"""
        words = word_tokenize(text)
        return ' '.join([word for word in words if word.lower() not in self.stop_words])

    def preprocess(self, content, options):
        """Preprocess content based on selected options"""
        if options.get('clean_html', True):
            content = self.clean_html(content)
        
        if options.get('remove_special_chars', True):
            content = self.remove_special_characters(content)
        
        if options.get('remove_extra_whitespace', True):
            content = self.remove_extra_whitespace(content)
        
        if options.get('remove_stopwords', False):
            content = self.remove_stopwords(content)
        
        return content
