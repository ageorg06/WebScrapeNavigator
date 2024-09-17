import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json
from .utils import is_allowed_by_robots, respect_rate_limit
from concurrent.futures import ThreadPoolExecutor, as_completed

class WebScraper:
    def __init__(self, start_url, max_pages=200, ignore_robots=False, max_workers=5, auth=None):
        self.start_url = start_url
        self.domain = urlparse(start_url).netloc
        self.visited = set()
        self.content = []
        self.max_pages = max_pages
        self.pages_scraped = 0
        self.errors = []
        self.skipped_urls = []
        self.ignore_robots = ignore_robots
        self.max_workers = max_workers
        self.auth = auth
        self.session = requests.Session()
        if self.auth:
            self.session.auth = (self.auth.get('username'), self.auth.get('password'))

    def scrape(self):
        print(f"Starting depth-first scrape of {self.start_url}")
        stack = [(self.start_url, 0)]  # (url, depth)
        while stack and self.pages_scraped < self.max_pages:
            url, depth = stack.pop()
            if url not in self.visited:
                self._log_url_tree(url, depth)
                new_urls = self._scrape_page_concurrent(url)
                for new_url in reversed(new_urls):  # Reverse to maintain original order in depth-first
                    if new_url not in self.visited:
                        stack.append((new_url, depth + 1))

        return json.dumps({
            'start_url': self.start_url,
            'total_pages_attempted': len(self.visited),
            'total_pages_scraped': self.pages_scraped,
            'content': self.content,
            'errors': self.errors,
            'skipped_urls': self.skipped_urls
        })

    def _log_url_tree(self, url, depth):
        indent = "  " * depth
        print(f"{indent}├─ {url}")

    def _scrape_page_concurrent(self, url):
        new_urls = []
        print(f"Processing URL: {url}")
        if url in self.visited:
            print(f"Skipping {url}: Already visited")
            return new_urls
        if not self.ignore_robots and not is_allowed_by_robots(url):
            print(f"Skipping {url}: Not allowed by robots.txt")
            self.skipped_urls.append({"url": url, "reason": "Not allowed by robots.txt"})
            return new_urls
        if self.pages_scraped >= self.max_pages:
            print(f"Skipping {url}: Max pages reached")
            self.skipped_urls.append({"url": url, "reason": "Max pages reached"})
            return new_urls

        print(f"Scraping {url}")
        self.visited.add(url)
        respect_rate_limit(self.domain)

        try:
            response = self.session.get(url, headers={'User-Agent': 'LLMTrainingBot/1.0'})
            response.raise_for_status()
            print(f"Response status code: {response.status_code}")
        except requests.RequestException as e:
            error_message = f"Error scraping {url}: {e}"
            print(error_message)
            self.errors.append(error_message)
            return new_urls

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
                new_urls.append(next_url)

        return new_urls

    def _is_same_domain(self, url):
        return urlparse(url).netloc == self.domain
