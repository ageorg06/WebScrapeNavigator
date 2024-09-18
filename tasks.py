from celery import Celery
from scraper.scraper import WebScraper
from database.db import Database
import json

# Initialize Celery app
celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

# Initialize database connection
db = Database()

@celery_app.task(bind=True)
def scrape_website(self, url, max_pages=200, ignore_robots=False, max_workers=5, auth=None, preprocessing_options=None):
    job_id = db.create_job(url)
    self.update_state(state='PROGRESS', meta={'job_id': job_id, 'status': 'started', 'pages_scraped': 0, 'url_tree': []})

    try:
        scraper = WebScraper(url, max_pages=max_pages, ignore_robots=ignore_robots, max_workers=max_workers, auth=auth, preprocessing_options=preprocessing_options)
        
        def update_progress(url, depth, pages_scraped):
            self.update_state(state='PROGRESS', meta={
                'job_id': job_id,
                'status': 'in_progress',
                'pages_scraped': pages_scraped,
                'url_tree': scraper.url_tree
            })

        content = scraper.scrape(progress_callback=update_progress)
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
            'skipped_urls': data['skipped_urls'],
            'url_tree': scraper.url_tree
        }
    except Exception as e:
        db.update_job_status(job_id, 'failed')
        return {'status': 'error', 'job_id': job_id, 'message': str(e)}
