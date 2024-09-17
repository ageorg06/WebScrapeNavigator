import requests
from urllib import robotparser
from urllib.parse import urlparse
import time

def is_allowed_by_robots(url):
    domain = urlparse(url).netloc
    robots_url = f"https://{domain}/robots.txt"
    rp = robotparser.RobotFileParser()
    rp.set_url(robots_url)
    print(f"Checking robots.txt at: {robots_url}")
    
    try:
        rp.read()
        is_allowed = rp.can_fetch("*", url)
        print(f"Robots.txt check result for {url}: {'Allowed' if is_allowed else 'Not Allowed'}")
        return is_allowed
    except Exception as e:
        print(f"Error checking robots.txt for {url}: {e}")
        print(f"Assuming {url} is allowed, but proceed with caution.")
        return True

def respect_rate_limit(domain):
    time.sleep(1)  # Simple rate limiting: wait 1 second between requests
