from celery import Celery
from scraper.scraper import WebScraper
from database.db import Database
import json

# Initialize Celery app
celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

# Initialize database connection
db = Database()

@celery_app.task(bind=True)
def scrape_website(self, url, max_pages=200, ignore_robots=False, max_workers=5, auth=None):
    job_id = db.create_job(url)
    self.update_state(state='PROGRESS', meta={'job_id': job_id, 'status': 'started'})

    try:
        scraper = WebScraper(url, max_pages=max_pages, ignore_robots=ignore_robots, max_workers=max_workers, auth=auth)
        content = scraper.scrape()
        data = json.loads(content)

        db.update_job_status(job_id, 'completed')
        db.save_content(job_id, content)

        return {
            'status': 'success',
            'job_id': job_id,
            'start_url': data['start_url'],
            'total_pages_attempted': data['total_pages_attempted'],
            'total_pages_scraped': data['total_pages_scraped'],
            'content': data['content'],
            'errors': data['errors'],
            'skipped_urls': data['skipped_urls']
        }
    except Exception as e:
        db.update_job_status(job_id, 'failed')
        return {'status': 'error', 'job_id': job_id, 'message': str(e)}
