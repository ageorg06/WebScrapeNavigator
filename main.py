import os
import json
import time
from flask import Flask, render_template, request, jsonify, send_file
from scraper.scraper import WebScraper
from database.db import Database
import tempfile
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Initialize database connection with a simple retry mechanism
def init_db(max_retries=3, delay=1):
    for attempt in range(max_retries):
        try:
            return Database()
        except Exception as e:
            if attempt < max_retries - 1:
                app.logger.warning(f"Database connection failed. Attempting to reconnect... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                app.logger.error(f"Failed to connect to the database after {max_retries} attempts: {str(e)}")
                return None

db = init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.json['url']
    max_workers = request.json.get('max_workers', 5)
    auth = request.json.get('auth')
    preprocessing_options = request.json.get('preprocessing_options', {})
    
    app.logger.info(f"Received scrape request for URL: {url}")
    
    try:
        scraper = WebScraper(url, max_pages=2, ignore_robots=True, max_workers=max_workers, auth=auth, preprocessing_options=preprocessing_options)
        content = scraper.scrape()
        app.logger.info(f"Scraping completed. Content length: {len(content)}")
        
        data = json.loads(content)
        app.logger.info(f"Parsed JSON data. Keys: {data.keys()}")
        
        formatted_content = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)
        app.logger.info(f"Formatted content length: {len(formatted_content)}")
        
        if db:
            job_id = db.create_job(url)
            db.update_job_status(job_id, 'completed')
            db.save_content(job_id, content)
        else:
            job_id = None
            app.logger.warning("Database not available. Job and content not saved.")
        
        response_data = {
            'status': 'completed',
            'job_id': job_id,
            'total_pages_attempted': data.get('total_pages_attempted'),
            'total_pages_scraped': data.get('total_pages_scraped'),
            'url_tree': data.get('url_tree'),
            'content': data.get('content'),
            'errors': data.get('errors'),
            'formatted_content': formatted_content
        }
        app.logger.info(f"Sending response. Keys: {response_data.keys()}")
        app.logger.debug(f"Response data: {json.dumps(response_data, indent=2)}")
        return jsonify(response_data)
    except Exception as e:
        app.logger.error(f"Error during scraping: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/download/<int:job_id>')
def download(job_id):
    if not db:
        return jsonify({'status': 'error', 'message': 'Database not available'}), 500
    
    content = db.get_content(job_id)
    if content:
        if isinstance(content, str):
            data = json.loads(content)
        else:
            data = content
        
        formatted_content = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_file.write(formatted_content)
        
        return send_file(temp_file.name, as_attachment=True, download_name=f'scraped_content_{job_id}.json')
    else:
        return jsonify({'status': 'error', 'message': 'Content not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
