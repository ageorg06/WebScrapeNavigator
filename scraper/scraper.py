import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json
from .utils import is_allowed_by_robots, respect_rate_limit

class WebScraper:
    def __init__(self, start_url, max_pages=100, ignore_robots=False):
        self.start_url = start_url
        self.domain = urlparse(start_url).netloc
        self.visited = set()
        self.content = []
        self.max_pages = max_pages
        self.pages_scraped = 0
        self.errors = []
        self.skipped_urls = []
        self.ignore_robots = ignore_robots

    def scrape(self):
        print(f"Starting scrape of {self.start_url}")
        self._scrape_page(self.start_url)
        return json.dumps({
            'start_url': self.start_url,
            'total_pages_attempted': len(self.visited),
            'total_pages_scraped': self.pages_scraped,
            'content': self.content,  # Return all content
            'errors': self.errors,
            'skipped_urls': self.skipped_urls
        })

    def _scrape_page(self, url):
        print(f"Processing URL: {url}")
        if url in self.visited:
            print(f"Skipping {url}: Already visited")
            return
        if not self.ignore_robots and not is_allowed_by_robots(url):
            print(f"Skipping {url}: Not allowed by robots.txt")
            self.skipped_urls.append({"url": url, "reason": "Not allowed by robots.txt"})
            return
        if self.pages_scraped >= self.max_pages:
            print(f"Skipping {url}: Max pages reached")
            self.skipped_urls.append({"url": url, "reason": "Max pages reached"})
            return

        print(f"Scraping {url}")
        self.visited.add(url)
        respect_rate_limit(self.domain)

        try:
            response = requests.get(url, headers={'User-Agent': 'LLMTrainingBot/1.0'})
            response.raise_for_status()
            print(f"Response status code: {response.status_code}")
        except requests.RequestException as e:
            error_message = f"Error scraping {url}: {e}"
            print(error_message)
            self.errors.append(error_message)
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract text content
        text_content = ' '.join(soup.stripped_strings)
        print(f"Extracted text content length: {len(text_content)}")
        
        self.content.append({'url': url, 'content': text_content})
        self.pages_scraped += 1
        print(f"Total pages scraped: {self.pages_scraped}")

        # Extract links
        links = soup.find_all('a', href=True)
        print(f"Found {len(links)} links on {url}")
        for link in links:
            next_url = urljoin(url, link['href'])
            if self._is_same_domain(next_url) and next_url not in self.visited:
                self._scrape_page(next_url)

    def _is_same_domain(self, url):
        return urlparse(url).netloc == self.domain
